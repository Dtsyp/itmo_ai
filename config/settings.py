import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# API Keys
YANDEX_API_KEY: str = os.getenv("YANDEX_API_KEY")
YANDEX_FOLDER_ID: str = os.getenv("YANDEX_FOLDER_ID")
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID: str = os.getenv("GOOGLE_CSE_ID")

# Redis settings
REDIS_HOST: str = os.getenv("REDIS_HOST", "redis")
REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
CACHE_TTL: int = 600  # 10 минут

# URLs
ITMO_NEWS_RSS: str = "https://news.itmo.ru/ru/news/rss/"
ITMO_MAIN_URL: str = "https://itmo.ru"

# Model settings
YC_GPT_MODEL: str = "yandexgpt-lite"
MAX_TOKENS: int = 1000
TEMPERATURE: float = 0.7
GPT_TIMEOUT: int = 60  

# Search settings
MAX_SEARCH_RESULTS: int = 3
SEARCH_TIMEOUT: int = 20  

# Timeouts (in seconds)
HTTP_TIMEOUT: int = 20
FASTAPI_TIMEOUT: int = 90
REDIS_TIMEOUT: int = 2

# Concurrency settings
MAX_CONCURRENT_REQUESTS: int = 5  
THREAD_POOL_SIZE: int = 3  
