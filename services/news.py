import feedparser
import aiohttp
import asyncio
import logging
from typing import List, Dict, Any
from config.settings import ITMO_NEWS_RSS, HTTP_TIMEOUT

logger = logging.getLogger(__name__)

async def get_itmo_news() -> List[Dict[str, Any]]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ITMO_NEWS_RSS, timeout=HTTP_TIMEOUT) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch news, status code: {response.status}")
                    return []
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                if not feed.entries:
                    logger.warning("No news entries found in the feed")
                    return []
                
                return [
                    {
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', ''),
                        'published': entry.get('published', '')
                    }
                    for entry in feed.entries[:5]  # Берем только 5 последних новостей
                ]
    except asyncio.TimeoutError:
        logger.error(f"Timeout while fetching news (after {HTTP_TIMEOUT}s)")
        return []
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        return []
