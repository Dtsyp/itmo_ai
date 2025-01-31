import asyncio
import time
import aiohttp
import json
from typing import List, Dict
import random

# Список тестовых вопросов об ИТМО
TEST_QUESTIONS = [
    "В каком году был основан Университет ИТМО?\n1. 1900\n2. 1930\n3. 1940\n4. 1950",
    "Сколько факультетов в Университете ИТМО?\n1. 12\n2. 15\n3. 18\n4. 20",
    "Кто является ректором Университета ИТМО?\n1. Владимир Васильев\n2. Владимир Николаев\n3. Александр Иванов\n4. Михаил Петров",
    "Сколько раз команда Университета ИТМО становилась чемпионом мира по программированию ICPC?\n1. 6\n2. 7\n3. 8\n4. 9",
    "В каком году Университет ИТМО был включён в число Национальных исследовательских университетов России?\n1. 2007\n2. 2009\n3. 2011\n4. 2015",
    "Какой кампус является главным в Университете ИТМО?\n1. Кронверкский\n2. Ломоносова\n3. Биржевая линия\n4. Чайковского",
    "Расскажите о научных лабораториях ИТМО",
    "Какие международные программы есть в ИТМО?",
    "Как поступить в ИТМО?",
    "Какие стипендии доступны студентам ИТМО?",
    "Расскажите о студенческой жизни в ИТМО",
    "Какие спортивные секции есть в ИТМО?",
    "Где находятся общежития ИТМО?",
    "Какие научные конференции проводятся в ИТМО?",
    "Расскажите о программе ИТМО.STARS",
    "Какие партнерские программы есть у ИТМО с другими университетами?",
    "Какие требования для поступления в магистратуру ИТМО?",
    "Расскажите о научных достижениях ИТМО",
    "Какие студенческие организации есть в ИТМО?",
    "Как устроена система дистанционного обучения в ИТМО?",
    # Добавим еще вопросы для полного теста
]

async def send_request(session: aiohttp.ClientSession, question: str, request_id: int) -> Dict:
    """Отправляет один запрос к API с механизмом повторных попыток."""
    start_time = time.time()
    max_retries = 3
    retry_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            async with session.post(
                'https://itmo-ai.onrender.com/api/request',
                json={"id": request_id, "query": question},
                timeout=90
            ) as response:
                response_time = time.time() - start_time
                result = await response.json()
                return {
                    "id": request_id,
                    "question": question,
                    "success": response.status == 200,
                    "response_time": response_time,
                    "status": response.status,
                    "response_json": result
                }
        except Exception as e:
            if attempt == max_retries - 1:  # Последняя попытка
                return {
                    "id": request_id,
                    "question": question,
                    "success": False,
                    "response_time": time.time() - start_time,
                    "error": f"After {max_retries} attempts: {str(e)}",
                    "response_json": None
                }
            else:
                # Экспоненциальная задержка перед следующей попыткой
                await asyncio.sleep(retry_delay * (2 ** attempt))

async def run_load_test(total_requests: int = 100, concurrent_requests: int = 30):
    """Запускает нагрузочный тест."""
    async with aiohttp.ClientSession() as session:
        # Создаем список вопросов для теста
        questions = []
        while len(questions) < total_requests:
            questions.extend(TEST_QUESTIONS)
        questions = questions[:total_requests]
        
        # Разбиваем запросы на батчи по concurrent_requests
        results = []
        for i in range(0, len(questions), concurrent_requests):
            batch = questions[i:i + concurrent_requests]
            tasks = [
                send_request(session, q, i + idx)
                for idx, q in enumerate(batch)
            ]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Небольшая пауза между батчами
            await asyncio.sleep(0.1)
        
        return results

def analyze_results(results: List[Dict]):
    """Анализирует результаты теста."""
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    
    response_times = [r["response_time"] for r in results if r["success"]]
    avg_time = sum(response_times) / len(response_times) if response_times else 0
    max_time = max(response_times) if response_times else 0
    min_time = min(response_times) if response_times else 0
    
    print(f"\nLoad Test Results:")
    print(f"Total Requests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(successful/total)*100:.2f}%")
    print(f"Average Response Time: {avg_time:.2f}s")
    print(f"Max Response Time: {max_time:.2f}s")
    print(f"Min Response Time: {min_time:.2f}s")

    if successful > 0:
        print("\nSuccessful Responses (JSON):")
        for r in results:
            if r["success"]:
                print(f"\nRequest ID: {r['id']}")
                print(f"Question: {r['question'][:100]}...")
                print("Response JSON:")
                print(json.dumps(r['response_json'], indent=2, ensure_ascii=False))
                print("-"*50)

    # Анализ ошибок
    if failed > 0:
        print("\nError Analysis:")
        error_types = {}
        for r in results:
            if not r["success"]:
                error_msg = r.get("error", "Unknown error")
                error_type = "Timeout" if "timeout" in error_msg.lower() else error_msg.split(":")[0]
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append({
                    "id": r["id"],
                    "question": r["question"],
                    "response_time": r["response_time"]
                })

        for error_type, errors in error_types.items():
            print(f"\n{error_type}: {len(errors)} occurrences")
            for e in errors:
                print(f"  Request ID: {e['id']}")
                print(f"  Question: {e['question'][:100]}...")
                print(f"  Response Time: {e['response_time']:.2f}s")
                print("  " + "-"*50)

if __name__ == "__main__":
    start_time = time.time()
    
    # Запускаем тест
    results = asyncio.run(run_load_test(20, 5))
    
    # Анализируем результаты
    analyze_results(results)
    
    total_time = time.time() - start_time
    print(f"\nTotal Test Time: {total_time:.2f}s")
    
    # Проверяем уложились ли в 7 минут
    if total_time > 420:  # 7 minutes = 420 seconds
        print("\n❌ Test took longer than 7 minutes!")
    else:
        print(f"\n✅ Test completed within time limit! ({total_time:.2f}s < 420s)")
