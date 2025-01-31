import json
import logging
import re
from typing import List, Optional, Dict, Any

import httpx

from config.settings import (
    YANDEX_API_KEY,
    YANDEX_FOLDER_ID,
    YC_GPT_MODEL,
    MAX_TOKENS,
    TEMPERATURE,
    GPT_TIMEOUT
)

logger = logging.getLogger(__name__)

def has_numbered_options(query: str) -> bool:
    lines = query.split('\n')
    for line in lines:
        if re.match(r'^\s*\d+\..*$', line):
            return True
    return False

def create_system_message() -> str:
    return """Ты - ассистент для ответов на вопросы об Университете ИТМО. Отвечай только в формате JSON.

ФОРМАТ ОТВЕТА (все поля обязательные):
{
    "answer": число или null,    // Если есть варианты ответов (1-4), укажи номер. Иначе null
    "reasoning": "объяснение",   // Краткое пояснение выбранного ответа
    "sources": ["ссылка1"],      // Список использованных источников (максимум 3)
    "model": "yandexgpt-lite"    // Название модели
}

ПРАВИЛА:
1. ВСЕГДА отвечай только в формате JSON
2. Поле answer: число от 1 до 4 при наличии вариантов, или null
3. Поле reasoning: максимум 2-3 предложения
4. Поле sources: максимум 3 ссылки
5. Поле model: всегда "yandexgpt-lite"
6. Все поля в ответе обязательны
"""

def extract_json_from_markdown(text: str) -> str:
    json_pattern = r'```(?:\w+)?\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```'
    match = re.search(json_pattern, text)
    if match:
        return match.group(1)
    return text

async def call_gpt(messages: List[dict]) -> Dict[str, Any]:
    try:
        logger.info("Sending request to YandexGPT API")
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "x-folder-id": YANDEX_FOLDER_ID,
            "Content-Type": "application/json"
        }
        
        data = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 2000
            },
            "messages": messages
        }
        
        logger.debug(f"Request data: {json.dumps(data, ensure_ascii=False)}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=data,
                timeout=60.0
            )
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            
            if response.status_code != 200:
                logger.error(f"YandexGPT API error: {response.status_code} - {response.text}")
                raise Exception(f"YandexGPT API error: {response.status_code}")
                
            result = response.json()

        try:
            response_text = result["result"]["alternatives"][0]["message"]["text"]
        except KeyError:
            logger.error(f"Unexpected API response format: {result}")
            raise Exception("Invalid API response format")

        json_text = extract_json_from_markdown(response_text)

        try:
            json_response = json.loads(json_text)
            
            if not isinstance(json_response, dict):
                raise ValueError("Response is not a dictionary")
            
            if "answer" not in json_response or "reasoning" not in json_response or "sources" not in json_response:
                raise ValueError("Missing required fields")
            
            if json_response["answer"] is not None and not isinstance(json_response["answer"], int):
                raise ValueError("Answer must be integer or null")
            if not isinstance(json_response["reasoning"], str):
                raise ValueError("Reasoning must be string")
            if not isinstance(json_response["sources"], list):
                raise ValueError("Sources must be array")
            
            json_response["sources"] = json_response["sources"][:3]
            json_response["model"] = "yandexgpt-lite"
            
            return json_response
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse response: {e}")
            logger.debug(f"Raw response: {response_text}")
            return {
                "answer": None,
                "reasoning": response_text,
                "sources": [],
                "model": "yandexgpt-lite"
            }

    except Exception as e:
        logger.error(f"Error calling Yandex GPT: {e}")
        return {
            "answer": None,
            "reasoning": "Извините, произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.",
            "sources": [],
            "model": "yandexgpt-lite"
        }

async def process_with_gpt(query: str, context: str = None) -> Dict[str, Any]:
    messages = [
        {"role": "system", "text": create_system_message()},
        {"role": "user", "text": query}
    ]

    if context:
        messages.insert(1, {"role": "system", "text": f"Context:\n{context}"})

    return await call_gpt(messages)
