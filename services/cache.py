import json
import time
import logging
from typing import Optional, Any

import redis.asyncio as redis
from config.settings import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    CACHE_TTL,
    CACHE_TTL_POPULAR,
    CACHE_TTL_SEARCH,
    REDIS_POOL_SIZE,
    REDIS_TIMEOUT,
    REDIS_MAX_MEMORY,
    REDIS_MAX_MEMORY_POLICY
)

logger = logging.getLogger(__name__)

redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    max_connections=REDIS_POOL_SIZE,
    socket_timeout=REDIS_TIMEOUT,
    decode_responses=True
)

redis_client = redis.Redis(
    connection_pool=redis_pool,
    decode_responses=True
)

async def configure_redis():
    try:
        await redis_client.config_set('maxmemory', REDIS_MAX_MEMORY)
        await redis_client.config_set('maxmemory-policy', REDIS_MAX_MEMORY_POLICY)
    except Exception as e:
        logger.error(f"Error configuring Redis: {str(e)}")

def get_cache_key(query: str, type: str = "general") -> str:
    if type == "popular":
        timestamp = int(time.time() / CACHE_TTL_POPULAR)
    elif type == "search":
        timestamp = int(time.time() / CACHE_TTL_SEARCH)
    else:
        timestamp = int(time.time() / CACHE_TTL)
    return f"{type}:{query}:{timestamp}"

async def get_cached_response(query: str, type: str = "general") -> Optional[dict]:
    try:
        cache_key = get_cache_key(query, type)
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        return None
    except Exception as e:
        logger.error(f"Error getting cached response: {str(e)}")
        return None

async def cache_response(query: str, response: dict, type: str = "general") -> None:
    try:
        cache_key = get_cache_key(query, type)
        ttl = CACHE_TTL_POPULAR if type == "popular" else (CACHE_TTL_SEARCH if type == "search" else CACHE_TTL)
        await redis_client.setex(cache_key, ttl, json.dumps(response))
    except Exception as e:
        logger.error(f"Error caching response: {str(e)}")

async def is_popular_query(query: str) -> bool:
    try:
        query_count_key = f"query_count:{query}"
        count = await redis_client.incr(query_count_key)
        await redis_client.expire(query_count_key, CACHE_TTL)
        return count > 5
    except Exception as e:
        logger.error(f"Error checking popular query: {str(e)}")
        return False
