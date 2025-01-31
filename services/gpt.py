import json
import logging
import re
from typing import List, Optional, Dict, Any

from openai import AsyncOpenAI

from config.settings import (
    OPENAI_API_KEY,
    GPT_MODEL,
    MAX_TOKENS,
    TEMPERATURE,
    GPT_TIMEOUT
)

logger = logging.getLogger(__name__)
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

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

3. В поле "sources" укажи до 3 наиболее релевантных источников
   Если источники не требуются, верни пустой массив []

4. В поле "model" всегда указывай "gpt-4o-mini"

ВАЖНО: 
- Ответ ДОЛЖЕН быть валидным JSON
- Поле "answer" должно быть числом от 1 до 10 или null
- Используй не более 3 источников
- Всегда указывай модель в поле "model"""

async def call_gpt(messages: List[dict]) -> Dict[str, Any]:
    try:
        completion = await client.chat.completions.create(
            model=GPT_MODEL,
            messages=messages,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )
        response_text = completion.choices[0].message.content.strip()
        
        # Remove markdown formatting if present
        if response_text.startswith('```') and response_text.endswith('```'):
            response_text = response_text[3:-3].strip()
            if response_text.startswith('json'):
                response_text = response_text[4:].strip()
        
        try:
            response_json = json.loads(response_text)
            if not isinstance(response_json, dict):
                raise ValueError("Response is not a dictionary")
            
            if "answer" not in response_json or "reasoning" not in response_json or "sources" not in response_json or "model" not in response_json:
                raise ValueError("Missing required fields")
            
            if response_json["answer"] is not None and not isinstance(response_json["answer"], int):
                raise ValueError("Answer must be integer or null")
            if not isinstance(response_json["reasoning"], str):
                raise ValueError("Reasoning must be string")
            if not isinstance(response_json["sources"], list):
                raise ValueError("Sources must be array")
            if not isinstance(response_json["model"], str):
                raise ValueError("Model must be string")
            
            response_json["sources"] = response_json["sources"][:3]
            
            return response_json
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT response as JSON: {e}")
            logger.debug(f"Raw response: {response_text}")
            return {
                "answer": None,
                "reasoning": "Извините, произошла ошибка при обработке ответа.",
                "sources": [],
                "model": GPT_MODEL
            }
            
    except Exception as e:
        logger.error(f"Error calling GPT: {str(e)}")
        raise

async def process_with_gpt(query: str, context: str = None) -> Dict[str, Any]:
    try:
        messages = [
            {"role": "system", "content": create_system_message()},
            {"role": "user", "content": query}
        ]
        
        if context:
            messages.append({
                "role": "user",
                "content": f"Вот дополнительный контекст:\n{context}"
            })
        
        return await call_gpt(messages)
        
    except Exception as e:
        logger.error(f"Error in process_with_gpt: {str(e)}")
        raise
