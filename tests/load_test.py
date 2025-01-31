import asyncio
import aiohttp
import time
import json
import random
from typing import List, Dict, Any
from test_queries import QUERIES_WITH_OPTIONS, QUERIES_WITHOUT_OPTIONS

API_URL = "http://localhost:8081/api/request"
TOTAL_PARALLEL_REQUESTS = 30
TOTAL_SEQUENTIAL_REQUESTS = 40
TOTAL_PARALLEL_REQUESTS_2 = 20

async def make_request(session: aiohttp.ClientSession, query: Dict[str, Any]) -> Dict[str, Any]:
    start_time = time.time()
    try:
        async with session.post(API_URL, json=query) as response:
            response_json = await response.json()
            end_time = time.time()
            return {
                "id": query["id"],
                "status": response.status,
                "response": response_json,
                "time": end_time - start_time
            }
    except Exception as e:
        end_time = time.time()
        return {
            "id": query["id"],
            "status": "error",
            "response": str(e),
            "time": end_time - start_time
        }

async def run_parallel_requests(session: aiohttp.ClientSession, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tasks = [make_request(session, query) for query in queries]
    return await asyncio.gather(*tasks)

async def run_sequential_requests(session: aiohttp.ClientSession, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for query in queries:
        result = await make_request(session, query)
        results.append(result)
    return results

def analyze_results(results: List[Dict[str, Any]], test_name: str):
    total_requests = len(results)
    successful_requests = sum(1 for r in results if isinstance(r["status"], int) and 200 <= r["status"] < 300)
    failed_requests = total_requests - successful_requests
    total_time = sum(r["time"] for r in results)
    avg_time = total_time / total_requests if total_requests > 0 else 0
    max_time = max(r["time"] for r in results)
    min_time = min(r["time"] for r in results)

    print(f"\n=== {test_name} ===")
    print(f"Total requests: {total_requests}")
    print(f"Successful requests: {successful_requests}")
    print(f"Failed requests: {failed_requests}")
    print(f"Average response time: {avg_time:.2f} seconds")
    print(f"Maximum response time: {max_time:.2f} seconds")
    print(f"Minimum response time: {min_time:.2f} seconds")

    # Анализ ошибок
    errors = [r for r in results if isinstance(r["status"], str) or r["status"] >= 300]
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"Request {error['id']}: Status {error['status']}, Response: {error['response']}")

async def main():
    # Подготовка запросов
    all_queries = QUERIES_WITH_OPTIONS + QUERIES_WITHOUT_OPTIONS
    
    # Выбор случайных запросов для каждого теста
    parallel_queries = random.sample(all_queries, TOTAL_PARALLEL_REQUESTS)
    sequential_queries = random.sample(all_queries, TOTAL_SEQUENTIAL_REQUESTS)
    parallel_queries_2 = random.sample(all_queries, TOTAL_PARALLEL_REQUESTS_2)

    async with aiohttp.ClientSession() as session:
        # Тест 1: 30 параллельных запросов
        print("\nStarting test 1: 30 parallel requests...")
        results_1 = await run_parallel_requests(session, parallel_queries)
        analyze_results(results_1, "Test 1 - 30 Parallel Requests")

        # Тест 2: 40 последовательных запросов
        print("\nStarting test 2: 40 sequential requests...")
        results_2 = await run_sequential_requests(session, sequential_queries)
        analyze_results(results_2, "Test 2 - 40 Sequential Requests")

        # Тест 3: 20 параллельных запросов
        print("\nStarting test 3: 20 parallel requests...")
        results_3 = await run_parallel_requests(session, parallel_queries_2)
        analyze_results(results_3, "Test 3 - 20 Parallel Requests")

if __name__ == "__main__":
    asyncio.run(main())
