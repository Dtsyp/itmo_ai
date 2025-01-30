import asyncio
import aiohttp
import time
import json
from datetime import datetime

async def make_request(session, request_id, query):
    url = 'http://localhost:8081/api/request'
    payload = {
        "id": request_id,
        "query": query
    }
    
    start_time = time.time()
    try:
        async with session.post(url, json=payload) as response:
            response_json = await response.json()
            end_time = time.time()
            return {
                'request_id': request_id,
                'status': response.status,
                'time': end_time - start_time,
                'response': response_json if response.status == 200 else None,
                'error': None if response.status == 200 else response_json.get('detail', 'Unknown error')
            }
    except Exception as e:
        end_time = time.time()
        return {
            'request_id': request_id,
            'status': 'error',
            'time': end_time - start_time,
            'response': None,
            'error': str(e)
        }

async def run_load_test():
    # Различные вопросы для тестирования
    questions = [
        "В каком году был основан Университет ИТМО?\n1. 1900\n2. 1930\n3. 1940\n4. 1950",
        "Сколько факультетов в Университете ИТМО?\n1. 12\n2. 15\n3. 18\n4. 20",
        "Кто является ректором Университета ИТМО?\n1. Владимир Васильев\n2. Владимир Николаев\n3. Александр Иванов\n4. Михаил Петров",
        "Сколько раз команда Университета ИТМО становилась чемпионом мира по программированию ICPC?\n1. 6\n2. 7\n3. 8\n4. 9",
        "В каком году Университет ИТМО был включён в число Национальных исследовательских университетов России?\n1. 2007\n2. 2009\n3. 2011\n4. 2015",
        "Какой кампус является главным в Университете ИТМО?\n1. Кронверкский\n2. Ломоносова\n3. Биржевая линия\n4. Чайковского",
        "Сколько научных лабораторий в Университете ИТМО?\n1. 50\n2. 75\n3. 100\n4. 150"
    ]
    
    print(f"Starting load test at {datetime.now()}")
    print(f"Making {len(questions)} parallel requests...")
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i, question in enumerate(questions, 1):
            task = make_request(session, i, question)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
    print("\nResults:")
    print("-" * 50)
    
    total_time = 0
    success_count = 0
    error_count = 0
    timeout_count = 0
    
    for result in results:
        print(f"\nRequest {result['request_id']}:")
        print(f"Time taken: {result['time']:.2f} seconds")
        print(f"Status: {result['status']}")
        
        if result['error']:
            print(f"Error: {result['error']}")
            if 'timeout' in str(result['error']).lower():
                timeout_count += 1
            else:
                error_count += 1
        elif result['response']:
            success_count += 1
            total_time += result['time']
            response = result['response']
            print(f"Answer: {response.get('answer')}")
            reasoning = response.get('reasoning', '')
            if reasoning:
                print(f"Reasoning: {reasoning[:100]}...")
            print(f"Sources: {len(response.get('sources', []))} sources")
    
    print("\nSummary:")
    print("-" * 50)
    print(f"Total requests: {len(questions)}")
    print(f"Successful requests: {success_count}")
    print(f"Failed requests: {error_count}")
    print(f"Timeout requests: {timeout_count}")
    if success_count > 0:
        print(f"Average response time: {total_time/success_count:.2f} seconds")
    print(f"Total test duration: {sum(r['time'] for r in results):.2f} seconds")

if __name__ == "__main__":
    asyncio.run(run_load_test())
