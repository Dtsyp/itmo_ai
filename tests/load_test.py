import asyncio
import aiohttp
import time
import json
import random
from typing import List, Dict, Any
from test_queries import QUERIES_WITH_OPTIONS, QUERIES_WITHOUT_OPTIONS

API_URL = "http://localhost:8080/api/request"
BATCH_SIZE = 16  # Максимальное количество одновременных запросов
TOTAL_SEQUENTIAL_REQUESTS = 40
TOTAL_BATCHES = 2  # Будет выполнено 2 группы по 16 запросов
TIMEOUT = 420  # 7 минут в секундах

async def make_request(session: aiohttp.ClientSession, query: Dict[str, Any]) -> Dict[str, Any]:
    """Make a request to the API."""
    start_time = time.time()
    try:
        async with session.post(API_URL, json={
            "id": str(query["id"]),
            "query": str(query["query"])  # Convert the query to string
        }) as response:
            end_time = time.time()
            if response.status != 200:
                response_text = await response.text()
                print(f"Request {query['id']}: Status {response.status}, Response: {response_text}")
                return {"success": False, "error": response_text, "time": end_time - start_time}
            
            response_json = await response.json()
            return {"success": True, "response": response_json, "time": end_time - start_time}
    except Exception as e:
        end_time = time.time()
        print(f"Request {query['id']}: Error: {str(e)}")
        return {"success": False, "error": str(e), "time": end_time - start_time}

async def run_batch_requests(session: aiohttp.ClientSession, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Выполняет запросы группами по BATCH_SIZE штук"""
    all_results = []
    for i in range(0, len(queries), BATCH_SIZE):
        batch = queries[i:i + BATCH_SIZE]
        print(f"\nProcessing batch {i//BATCH_SIZE + 1} ({len(batch)} requests)...")
        batch_results = await asyncio.gather(
            *[make_request(session, query) for query in batch],
            return_exceptions=True
        )
        all_results.extend(batch_results)
        # Небольшая пауза между батчами
        if i + BATCH_SIZE < len(queries):
            await asyncio.sleep(1)
    return all_results

async def run_sequential_requests(session: aiohttp.ClientSession, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for query in queries:
        result = await make_request(session, query)
        results.append(result)
    return results

def analyze_results(results: List[Dict[str, Any]], test_name: str):
    total_requests = len(results)
    successful_requests = sum(1 for r in results if r["success"])
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
    print(f"Total test time: {total_time:.2f} seconds")

    # Анализ ошибок
    errors = [r for r in results if not r["success"]]
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"Request: Error: {error['error']}")

async def main():
    # Подготовка тестовых данных
    parallel_queries = []
    for i in range(BATCH_SIZE * TOTAL_BATCHES):
        query = random.choice(QUERIES_WITH_OPTIONS)
        parallel_queries.append({"query": query, "id": i + 1})

    sequential_queries = []
    for i in range(TOTAL_SEQUENTIAL_REQUESTS):
        query = random.choice(QUERIES_WITHOUT_OPTIONS)
        sequential_queries.append({"query": query, "id": i + 1})

    # Создание сессии с таймаутом
    timeout = aiohttp.ClientTimeout(total=TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            # Тест 1: Батчевые запросы (2 группы по 16 запросов)
            print("\nStarting test 1: Batch requests...")
            results_1 = await run_batch_requests(session, parallel_queries)
            analyze_results(results_1, "Test 1 - Batch Requests")

            # Тест 2: Последовательные запросы
            print("\nStarting test 2: Sequential requests...")
            results_2 = await run_sequential_requests(session, sequential_queries)
            analyze_results(results_2, "Test 2 - Sequential Requests")

            # Тест 3: Еще одна группа батчевых запросов
            print("\nStarting test 3: Batch requests...")
            results_3 = await run_batch_requests(session, parallel_queries)
            analyze_results(results_3, "Test 3 - Batch Requests")

            # Общая статистика
            all_results = results_1 + results_2 + results_3
            print("\n=== Overall Statistics ===")
            total_time = time.time() - start_time
            print(f"Total test time: {total_time:.2f} seconds")
            if total_time > TIMEOUT:
                print("WARNING: Test exceeded 7 minutes timeout!")
            analyze_results(all_results, "Overall Results")

        except asyncio.TimeoutError:
            print("\nERROR: Test exceeded 7 minutes timeout!")
            return

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
