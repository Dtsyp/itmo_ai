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
    SEARCH_TIMEOUT
)

_executor = ThreadPoolExecutor(max_workers=3)
logger = logging.getLogger(__name__)

async def search_itmo_info(query: str) -> List[Dict[str, Any]]:
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        
        # Добавляем "ИТМО" к запросу для более релевантных результатов
        search_query = f"ИТМО {query}"
        
        def execute_search():
            return service.cse().list(
                q=search_query,
                cx=GOOGLE_CSE_ID,
                num=MAX_SEARCH_RESULTS
            ).execute()
        
        # Используем общий таймаут для всей операции поиска
        result = await asyncio.wait_for(asyncio.get_event_loop().run_in_executor(_executor, execute_search), timeout=SEARCH_TIMEOUT)
        
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
        results = await search_itmo_info(query)
        context = []
        
        for item in results:
            context_item = f"{item['title']}\n{item['snippet']}\nИсточник: {item['link']}"
            context.append(context_item)
        
        return context
        
    except Exception as e:
        logger.error(f"Error in search_google: {str(e)}")
        return []
