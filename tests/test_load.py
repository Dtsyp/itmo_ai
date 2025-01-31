import asyncio
import time
import aiohttp
import json
from typing import List, Dict
import random

# Список тестовых вопросов об ИТМО
TEST_QUESTIONS = [
    "Какой процент выпускников ИТМО трудоустраивается по специальности в первый год после выпуска?\n1. 65%\n2. 75%\n3. 85%\n4. 95%",
    "Сколько научных лабораторий было создано в ИТМО в рамках программы мегагрантов?\n1. 12\n2. 15\n3. 18\n4. 21",
    "Какое место занимает ИТМО в рейтинге QS по направлению Computer Science & Information Systems (2024)?\n1. 51-100\n2. 101-150\n3. 151-200\n4. 201-250",
    "Сколько процентов составляют иностранные студенты от общего числа обучающихся в ИТМО?\n1. 10%\n2. 15%\n3. 20%\n4. 25%",
    "В каком году была запущена программа ИТМО.Старт?\n1. 2016\n2. 2017\n3. 2018\n4. 2019",
    
    "Опишите структуру и основные направления исследований в международной лаборатории 'Информационные технологии в задачах управления' ИТМО",
    "Какие преимущества дает участие в программе ИТМО.Family для иностранных абитуриентов и как это влияет на процесс поступления?",
    "Расскажите о коллаборации ИТМО с MIT в области квантовых вычислений и фотоники. Какие основные результаты были достигнуты?",
    "Опишите процесс коммерциализации научных разработок через Центр трансфера технологий ИТМО. Приведите успешные примеры",
    "Как реализуется программа двойных дипломов между ИТМО и университетом Аалто (Финляндия)? Какие специальности доступны?",
    
    "Объясните принцип работы квантового компьютера, разрабатываемого в лаборатории квантовой информатики ИТМО",
    "Какие технологии машинного обучения используются в проекте ИТМО по распознаванию эмоций в образовательном процессе?",
    "Опишите архитектуру системы распределенных вычислений в суперкомпьютерном центре ИТМО",
    
    "Как в ИТМО реализуется концепция цифрового университета? Какие технологии и платформы используются?",
    "Расскажите о проекте ИТМО по созданию метавселенной для образования. Какие технологии и подходы используются?",
    
    "Какие совместные научные проекты реализуются между ИТМО и Гарвардским университетом в области биоинформатики?",
    "Опишите процесс организации международных научных конференций в ИТМО на примере METANANO",
    
    "Какие прорывные исследования ведутся в лаборатории метаматериалов ИТМО? Опишите последние достижения",
    "Расскажите о разработках ИТМО в области квантовой криптографии и их практическом применении",
    "Как исследования в области искусственного интеллекта в ИТМО влияют на развитие робототехники?"
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
