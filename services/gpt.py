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
    return """Ты - ассистент для ответов на вопросы об Университете ИТМО.
Твоя задача - предоставить точную информацию в структурированном формате.

ВАЖНО: Твой ответ ДОЛЖЕН быть в формате JSON со следующей структурой:
{
    "answer": number | null,  // номер правильного варианта (1-10) или null если нет вариантов
    "reasoning": string,      // объяснение ответа
    "sources": string[],     // до 3 наиболее релевантных источников или пустой массив
    "model": string         // название модели, которая генерирует ответ
}

Правила:
1. Если в вопросе есть пронумерованные варианты (1-10):
   - В поле "answer" укажи номер правильного варианта
   - В поле "reasoning" объясни свой выбор

2. Если вариантов ответа НЕТ:
   - В поле "answer" верни null
   - В поле "reasoning" дай развернутый ответ

3. В поле "sources" укажи до 3 наиболее релевантных источников информации
4. В поле "model" укажи название модели, которая генерирует ответ"""

def extract_json_from_markdown(text: str) -> str:
    json_pattern = r'```(?:\w+)?\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```'
    match = re.search(json_pattern, text)
    if match:
        return match.group(1)
    return text

async def call_gpt(messages: List[dict]) -> Dict[str, Any]:
    try:
        url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Authorization": f"Api-Key {YANDEX_API_KEY}",
            "x-folder-id": YANDEX_FOLDER_ID
        }
        data = {
            "modelUri": f"gpt://{YANDEX_FOLDER_ID}/{YC_GPT_MODEL}/latest",
            "completionOptions": {
                "stream": False,
                "temperature": TEMPERATURE,
                "maxTokens": MAX_TOKENS
            },
            "messages": [
                {
                    "role": msg["role"],
                    "text": msg["content"]
                }
                for msg in messages
            ]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                json=data,
                timeout=GPT_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()

        response_text = result["result"]["alternatives"][0]["message"]["text"]
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
            json_response["model"] = YC_GPT_MODEL
            
            return json_response
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse response: {e}")
            logger.debug(f"Raw response: {response_text}")
            return {
                "answer": None,
                "reasoning": response_text,
                "sources": [],
                "model": YC_GPT_MODEL
            }

    except Exception as e:
        logger.error(f"Error calling Yandex GPT: {e}")
        return {
            "answer": None,
            "reasoning": "Извините, произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже.",
            "sources": [],
            "model": YC_GPT_MODEL
        }

async def process_with_gpt(query: str, context: str = None) -> Dict[str, Any]:
    messages = [
        {"role": "system", "content": create_system_message()},
        {"role": "user", "content": query}
    ]

    if context:
        messages.insert(1, {"role": "system", "content": f"Context:\n{context}"})

    return await call_gpt(messages)
