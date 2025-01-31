import json
import time
from typing import Optional, Any

import redis.asyncio as redis
from config.settings import REDIS_HOST, REDIS_PORT, REDIS_DB, CACHE_TTL

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)

def get_cache_key(query: str) -> str:
    timestamp = int(time.time() / 60)
    return f"{query}:{timestamp}"

async def get_cached_response(query: str) -> Optional[dict]:
    try:
        cache_key = get_cache_key(query)
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    except Exception:
        return None

async def cache_response(query: str, response: Any) -> None:
    try:
        cache_key = get_cache_key(query)
        await redis_client.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(response)
        )
    except Exception:
        pass
