import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID")

# Model settings
GPT_MODEL: str = "gpt-4o-mini"
MAX_TOKENS: int = 1000
TEMPERATURE: float = 0.7
GPT_TIMEOUT: int = 45
GPT_MAX_RETRIES: int = 3
GPT_RETRY_DELAY: float = 1.0
GPT_MAX_CONTEXT_LENGTH: int = 2000

# Redis settings
REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
REDIS_POOL_SIZE: int = 50
REDIS_TIMEOUT: int = 5
REDIS_MAX_MEMORY: str = "2gb"
REDIS_MAX_MEMORY_POLICY: str = "allkeys-lru"
CACHE_TTL: int = 3600
CACHE_TTL_POPULAR: int = 86400
CACHE_TTL_SEARCH: int = 3600

# URLs
ITMO_NEWS_RSS: str = "https://news.itmo.ru/ru/news/rss/"
ITMO_MAIN_URL: str = "https://itmo.ru"

# Timeouts (in seconds)
HTTP_TIMEOUT: int = 30
SEARCH_TIMEOUT: int = 30
FASTAPI_TIMEOUT: int = 120

# Retry settings
MAX_RETRIES: int = 3
RETRY_DELAY: float = 1.0
RETRY_MAX_DELAY: float = 10.0
RETRY_EXPONENTIAL_BASE: float = 2.0

# Search settings
MAX_SEARCH_RESULTS: int = 5
SEARCH_WORKERS: int = 8

# Concurrency settings
MAX_CONCURRENT_REQUESTS: int = 30
RATE_LIMIT_REQUESTS: int = 100
RATE_LIMIT_WINDOW: int = 60
