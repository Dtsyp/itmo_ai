import os
import json
import aiohttp
from typing import Dict
from fastapi import HTTPException
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')

if not YANDEX_API_KEY or not YANDEX_FOLDER_ID:
    raise ValueError("Необходимо указать YANDEX_API_KEY и YANDEX_FOLDER_ID")

API_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
HEADERS = {
    "Authorization": f"Api-Key {YANDEX_API_KEY}",
    "x-folder-id": YANDEX_FOLDER_ID
}

def create_system_message() -> str:
    return """Ты - ассистент для ответов на вопросы об Университете ИТМО. Отвечай только в формате JSON.

ФОРМАТ ОТВЕТА (все поля обязательные):
{
    "answer": число или null,    // Число (1-10) ТОЛЬКО если в вопросе есть пронумерованные варианты ответов, иначе ВСЕГДА null
    "reasoning": "объяснение",   // Краткое пояснение выбранного ответа
    "sources": ["ссылка1"],      // Список использованных источников (максимум 3)
    "model": "имя модели"        // Название используемой модели
}

ПРАВИЛА:
1. ВСЕГДА отвечай только в формате JSON
2. Поле answer: число от 1 до 10 ТОЛЬКО при наличии пронумерованных вариантов, иначе СТРОГО null
3. Поле reasoning: максимум 2-3 предложения
4. Поле sources: максимум 3 ссылки
5. Поле model: название используемой модели
6. Все поля в ответе обязательны
"""

def check_numbered_options(query: str) -> bool:
    pattern = r'(?m)^[ \t]*(\d+)\.\s'
    matches = re.findall(pattern, query)
    return len(set(matches)) >= 2

async def _make_request(query: str, context: str = "") -> Dict:
    messages = [
        {"role": "system", "text": create_system_message()},
        {"role": "user", "text": f"Контекст:\n{context}\n\nВопрос:\n{query}" if context else query}
    ]
    
    data = {
        "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "2000"
        },
        "messages": messages
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=HEADERS, json=data) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"{response.status} - {error_text}")
                raise HTTPException(status_code=response.status, detail=error_text)
            
            result = await response.json()
            try:
                response_text = result["result"]["alternatives"][0]["message"]["text"]
                return json.loads(response_text)
            except Exception as e:
                logger.error(f"Error parsing response: {e}")
                raise HTTPException(status_code=500, detail="Failed to parse GPT response")

async def process_with_gpt(query: str, context: str = "") -> Dict:
    try:
        response = await _make_request(query, context)
        has_numbered_options = check_numbered_options(query)
        
        result = {
            "answer": None,
            "reasoning": response.get("reasoning", "Нет объяснения"),
            "sources": response.get("sources", []),
            "model": response.get("model", "yandexgpt-lite")
        }
        
        if has_numbered_options and isinstance(response.get("answer"), (int, float)):
            result["answer"] = int(response["answer"])
            
        return result
        
    except Exception as e:
        logger.error(f"YandexGPT API error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))