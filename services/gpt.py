import json
import logging
import re
from typing import List, Optional, Dict, Any
import asyncio

from openai import AsyncOpenAI

from config.settings import (
    OPENAI_API_KEY,
    GPT_MODEL,
    MAX_TOKENS,
    TEMPERATURE,
    GPT_TIMEOUT,
    GPT_MAX_RETRIES,
    GPT_RETRY_DELAY,
    GPT_MAX_CONTEXT_LENGTH
)
from services.cache import get_cached_response, cache_response, is_popular_query

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
- Всегда указывай модель в поле "model\""""

async def call_gpt_with_retry(messages: List[dict], max_retries: int = GPT_MAX_RETRIES) -> dict:
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                timeout=GPT_TIMEOUT
            )
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Final attempt failed: {str(e)}")
                raise
            delay = GPT_RETRY_DELAY * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay} seconds...")
            await asyncio.sleep(delay)

def optimize_context(context: str, max_length: int = GPT_MAX_CONTEXT_LENGTH) -> str:
    if not context:
        return ""
    parts = context.split("\n\n")
    if len(parts) > max_length:
        parts = parts[:max_length]
    return "\n\n".join(parts)

async def process_with_gpt(query: str, context: str = None) -> Dict[str, Any]:
    try:
        if not query:
            raise ValueError("Query cannot be empty")

        cached_response = await get_cached_response(query)
        if cached_response:
            return cached_response

        optimized_context = optimize_context(context)
        messages = [
            {"role": "system", "content": create_system_message()},
            {"role": "user", "content": f"Query: {query}\nContext: {optimized_context}"}
        ]

        response = await call_gpt_with_retry(messages)
        content = response.choices[0].message.content

        try:
            result = json.loads(content)
            if await is_popular_query(query):
                await cache_response(query, result, "popular")
            else:
                await cache_response(query, result)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing GPT response: {str(e)}")
            raise ValueError("Invalid response format from GPT")

    except Exception as e:
        logger.error(f"Error in process_with_gpt: {str(e)}")
        raise
