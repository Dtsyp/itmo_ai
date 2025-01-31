import asyncio
import aiohttp
import time
from test_queries import QUERIES_WITH_OPTIONS

API_URL = "https://bbabte66a7pllu4dhdub.containers.yandexcloud.net/api/request"

async def make_request():
    query = QUERIES_WITH_OPTIONS[0]  # Берем первый тестовый вопрос
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, json=query, timeout=30) as response:
                response_json = await response.json()
                end_time = time.time()
                print(f"\nRequest ID: {query['id']}")
                print(f"Query: {query['query']}")
                print(f"Status: {response.status}")
                print(f"Response: {response_json}")
                print(f"Time taken: {end_time - start_time:.2f} seconds")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(make_request())
