from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import (
    GOOGLE_API_KEY,
    GOOGLE_CSE_ID,
    MAX_SEARCH_RESULTS,
    SEARCH_TIMEOUT,
    SEARCH_WORKERS
)
from services.cache import get_cached_response, cache_response

_executor = ThreadPoolExecutor(max_workers=SEARCH_WORKERS)
logger = logging.getLogger(__name__)

class GoogleSearchService:
    _instance = None
    _service = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls):
        if not cls._instance:
            async with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
                    cls._service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        return cls._instance

    async def search(self, query: str) -> List[Dict[str, Any]]:
        try:
            search_query = f"ИТМО {query}"
            
            def execute_search():
                return self._service.cse().list(
                    q=search_query,
                    cx=GOOGLE_CSE_ID,
                    num=MAX_SEARCH_RESULTS
                ).execute()
            
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(_executor, execute_search),
                timeout=SEARCH_TIMEOUT
            )
            
            if "items" not in result:
                return []
            
            return [{
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "")
            } for item in result["items"]]
            
        except asyncio.TimeoutError:
            logger.error(f"Search timed out after {SEARCH_TIMEOUT} seconds")
            return []
        except HttpError as e:
            logger.error(f"Error performing Google search: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during search: {str(e)}")
            return []

async def search_google(query: str) -> List[str]:
    try:
        cached_results = await get_cached_response(query, type="search")
        if cached_results:
            return cached_results

        search_service = await GoogleSearchService.get_instance()
        results = await search_service.search(query)
        
        context_results = [
            f"Source: {result['link']}\nTitle: {result['title']}\n{result['snippet']}"
            for result in results
        ]
        
        await cache_response(query, context_results, type="search")
        return context_results
    except Exception as e:
        logger.error(f"Error in search_google: {str(e)}")
        return []
