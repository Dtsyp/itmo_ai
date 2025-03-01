# Запросы с вариантами ответов
QUERIES_WITH_OPTIONS = [
    {
        "query": "В каком году Университет ИТМО был включён в число Национальных исследовательских университетов России?\n1. 2007\n2. 2009\n3. 2011\n4. 2015",
        "id": 1
    },
    {
        "query": "Какой факультет ИТМО был создан первым?\n1. Факультет точной механики и технологий\n2. Факультет информационных технологий и программирования\n3. Факультет фотоники\n4. Факультет систем управления и робототехники",
        "id": 2
    },
    {
        "query": "Сколько мегафакультетов в ИТМО?\n1. 4\n2. 5\n3. 6\n4. 7",
        "id": 3
    },
    {
        "query": "В каком году ЛИТМО был переименован в ИТМО?\n1. 1991\n2. 1992\n3. 1993\n4. 1994",
        "id": 4
    },
    {
        "query": "Сколько раз команда ИТМО становилась чемпионом мира по программированию ICPC?\n1. 6\n2. 7\n3. 8\n4. 9",
        "id": 5
    },
    {
        "query": "Какое место занимает ИТМО в рейтинге программной инженерии?\n1. 76\n2. 85\n3. 91\n4. 100",
        "id": 6
    },
    {
        "query": "В каком году был основан первый в России музей оптики?\n1. 2006\n2. 2008\n3. 2010\n4. 2012",
        "id": 7
    },
    {
        "query": "Сколько корпусов у ИТМО?\n1. 5\n2. 7\n3. 9\n4. 11",
        "id": 8
    },
    {
        "query": "Какое количество студентов обучается в ИТМО?\n1. Около 10000\n2. Около 12000\n3. Около 14000\n4. Около 16000",
        "id": 9
    },
    {
        "query": "В каком году ИТМО получил статус университета?\n1. 1992\n2. 1994\n3. 1996\n4. 1998",
        "id": 10
    }
]

# Запросы без вариантов ответов
QUERIES_WITHOUT_OPTIONS = [
    {
        "query": "Расскажите о научных направлениях ИТМО",
        "id": 11
    },
    {
        "query": "Какие международные программы есть в ИТМО?",
        "id": 12
    },
    {
        "query": "Опишите студенческую жизнь в ИТМО",
        "id": 13
    },
    {
        "query": "Какие лаборатории есть в ИТМО?",
        "id": 14
    },
    {
        "query": "Расскажите о спортивных секциях ИТМО",
        "id": 15
    },
    {
        "query": "Какие стипендиальные программы доступны в ИТМО?",
        "id": 16
    },
    {
        "query": "Расскажите об общежитиях ИТМО",
        "id": 17
    },
    {
        "query": "Какие студенческие организации есть в ИТМО?",
        "id": 18
    },
    {
        "query": "Расскажите о библиотеке ИТМО",
        "id": 19
    },
    {
        "query": "Какие научные конференции проводятся в ИТМО?",
        "id": 20
    }
]

# Генерируем дополнительные вопросы с вариантами ответов
for i in range(21, 51):
    QUERIES_WITH_OPTIONS.append({
        "query": f"Тестовый вопрос с вариантами ответов #{i}\n1. Вариант 1\n2. Вариант 2\n3. Вариант 3\n4. Вариант 4",
        "id": i
    })

# Генерируем дополнительные вопросы без вариантов ответов
for i in range(51, 91):
    QUERIES_WITHOUT_OPTIONS.append({
        "query": f"Тестовый вопрос без вариантов ответов #{i}",
        "id": i
    })
