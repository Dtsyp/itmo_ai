import os
import json
import aiohttp
from typing import Dict
from fastapi import HTTPException
import logging

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
    "model": "имя модели"    // Название используемой модели
}

ПРАВИЛА:
1. ВСЕГДА отвечай только в формате JSON
2. Поле answer: число от 1 до 10 ТОЛЬКО при наличии пронумерованных вариантов, иначе СТРОГО null
3. Поле reasoning: максимум 2-3 предложения
4. Поле sources: максимум 3 ссылки
5. Поле model: название используемой модели
6. Все поля в ответе обязательны
"""

async def _make_request(query: str) -> Dict:
    messages = [
        {"role": "system", "text": create_system_message()},
        {"role": "user", "text": query}
    ]
    
    data = {
        "modelUri": "gpt://b1gd1nj1c5t2ccnqn0qq/yandexgpt-lite",
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

async def call_gpt(query: str, request_id: int) -> Dict:
    try:
        response = await _make_request(query)
        
        has_numbered_options = any(line.strip().startswith(str(i)+'.') for i in range(1, 11) for line in query.split('\n'))
        
        result = {
            "id": request_id,
            "answer": None,
            "reasoning": response.get("reasoning", "Нет объяснения"),
            "sources": response.get("sources", []),
            "model": response.get("model", "unknown")
        }
        
        if has_numbered_options and "answer" in response and isinstance(response["answer"], (int, float)):
            result["answer"] = int(response["answer"])
            
        return result
        
    except Exception as e:
        logger.error(f"YandexGPT API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))