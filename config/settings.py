import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID")

# Redis settings
REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
CACHE_TTL: int = int(os.getenv("CACHE_TTL", 60))  # 60 секунд

# URLs
ITMO_NEWS_RSS: str = "https://news.itmo.ru/ru/news/rss/"
ITMO_MAIN_URL: str = "https://itmo.ru"

# Model settings
GPT_MODEL: str = "gpt-4o-mini"
MAX_TOKENS: int = 1000
TEMPERATURE: float = 0.7

# Search settings
MAX_SEARCH_RESULTS: int = 5
SEARCH_TIMEOUT: int = 20  # seconds

# Timeouts (in seconds)
HTTP_TIMEOUT: int = 20
GPT_TIMEOUT: int = 60
FASTAPI_TIMEOUT: int = 90
REDIS_TIMEOUT: int = 2

# Concurrency settings
MAX_CONCURRENT_REQUESTS: int = 5  # Максимальное количество одновременных запросов
THREAD_POOL_SIZE: int = 3  # Размер пула потоков для тяжелых операций
