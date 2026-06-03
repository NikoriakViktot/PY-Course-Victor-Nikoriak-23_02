# Урок 34 — Asyncio: Mermaid Діаграми

---

## Діаграма 1: Lifecycle Coroutine об'єкта

```mermaid
stateDiagram-v2
    direction LR

    [*] --> CREATED : async def func() виклик\nповертає coroutine object

    CREATED --> RUNNING : await func()\nабо asyncio.run(func())

    RUNNING --> SUSPENDED : await asyncio.sleep()\nабо await IO операція\n(стан збережено)

    SUSPENDED --> RUNNING : IO завершено\nEvent Loop відновлює

    RUNNING --> CLOSED : return statement\nабо кінець функції

    CREATED --> CLOSED : GC без await\n→ RuntimeWarning

    RUNNING --> CANCELLED : task.cancel()\n→ CancelledError

    CANCELLED --> CLOSED : [*]
    CLOSED --> [*]
```



---

## Діаграма 2: Event Loop — Алгоритм Планування

```mermaid
flowchart TD
    START([Event Loop старт]) --> READY{Ready Queue\nпорожня?}

    READY -- Ні --> EXEC[Виконати Task\nдо першого await]
    EXEC --> AWAIT{Task\nзустрів await?}

    AWAIT -- Так --> SUSPEND[Призупинити Task\nзберегти стан]
    SUSPEND --> REGISTER[Зареєструвати подію\nв I/O Selector]
    REGISTER --> READY

    AWAIT -- Ні/return --> DONE[Task завершено\nзберегти результат]
    DONE --> READY

    READY -- Так --> SELECT[ОС: select/epoll/kqueue\nЧекати на події]
    SELECT --> IO_READY{Подія\nготова?}

    IO_READY -- Так --> WAKE[Перемістити Task\nу Ready Queue]
    WAKE --> READY

    IO_READY -- Таймер --> TIMER[asyncio.sleep\nтаймер спрацював]
    TIMER --> WAKE

    IO_READY -- Немає задач --> STOP([Зупинити Event Loop])
```

---

## Діаграма 3: Sequence — await vs time.sleep

```mermaid
sequenceDiagram
    participant EL as Event Loop
    participant TA as Task A (time.sleep)
    participant TB as Task B (health_ping)
    participant OS as Операційна Система

    Note over EL,OS: ❌ НЕБЕЗПЕЧНО: time.sleep блокує Event Loop

    EL->>TA: Запустити Task A
    TA->>OS: time.sleep(3) — блокуючий syscall!
    Note over EL,TB: ⛔ Event Loop ЗАМОРОЖЕНО\nTask B не може виконатись!
    OS-->>TA: 3 секунди потому: прокинутись
    TA-->>EL: Завершено

    EL->>TB: Тепер можна запустити Task B
    TB-->>EL: Ping! Ping! Ping!

    Note over EL,OS: ✅ ПРАВИЛЬНО: await asyncio.sleep кооперативно

    EL->>TA: Запустити Task A
    TA->>EL: await asyncio.sleep(3) → SUSPEND
    EL->>TB: Task A чекає — запускаємо Task B
    TB->>EL: Ping! #1 → await sleep(0.5) → SUSPEND
    EL->>TB: Task B чекає → Ping! #2
    Note over EL: Через 3s: OS будить Task A
    EL->>TA: Відновити Task A → завершено
```

---

## Діаграма 4: asyncio.gather — Concurrent Execution

```mermaid
sequenceDiagram
    participant M as main()
    participant EL as Event Loop
    participant Q1 as DB Query 1 (1.0s)
    participant Q2 as DB Query 2 (0.8s)
    participant Q3 as DB Query 3 (0.6s)

    M->>EL: asyncio.gather(query1, query2, query3)
    EL->>Q1: Створити Task 1, запустити
    Q1->>EL: await asyncio.sleep(1.0) → SUSPEND
    EL->>Q2: Створити Task 2, запустити
    Q2->>EL: await asyncio.sleep(0.8) → SUSPEND
    EL->>Q3: Створити Task 3, запустити
    Q3->>EL: await asyncio.sleep(0.6) → SUSPEND

    Note over EL: [T=0.6s] OS сигналізує: Q3 готова
    EL->>Q3: Відновити
    Q3-->>EL: result_3 ✓

    Note over EL: [T=0.8s] OS сигналізує: Q2 готова
    EL->>Q2: Відновити
    Q2-->>EL: result_2 ✓

    Note over EL: [T=1.0s] OS сигналізує: Q1 готова
    EL->>Q1: Відновити
    Q1-->>EL: result_1 ✓

    EL-->>M: [result_1, result_2, result_3]\nЗагальний час: ~1.0s (не 2.4s!)
```

---

## Діаграма 5: FastAPI — Три типи ендпоінтів

```mermaid
flowchart TD
    REQ([HTTP Request]) --> ASGI[ASGI Server\nuvicorn/hypercorn]
    ASGI --> DETECT{Тип\nендпоінту?}

    DETECT -- async def + await --> LOOP[Event Loop\nголовний потік]
    LOOP --> AWAIT_IO[await asyncio.sleep\nawait asyncpg.fetch\nawait aiohttp.get]
    AWAIT_IO --> FREE[Event Loop ВІЛЬНИЙ\nобслуговує інших]
    FREE --> RESUME[Відновити при готовності]
    RESUME --> RESP1([✅ Response])

    DETECT -- async def + BLOCKING --> FREEZE[Event Loop ЗАМОРОЖЕНО!]
    FREEZE --> BLOCK[time.sleep\nrequests.get\npsycopg2.execute]
    BLOCK --> ALL_WAIT[⛔ ВСІ з'єднання чекають!]
    ALL_WAIT --> RESP2([❌ Timeout for others])

    DETECT -- def sync --> THREADPOOL[ThreadPoolExecutor\nокремий потік]
    THREADPOOL --> SYNC_IO[Blocking IO\nв потоці]
    SYNC_IO --> LOOP_FREE[Event Loop ВІЛЬНИЙ]
    LOOP_FREE --> RESP3([⚠️ Response\nобмежено кількістю потоків])
```

---

## Діаграма 6: Blocking Calls — Ланцюг впливу

```mermaid
flowchart LR
    subgraph WRONG["❌ Синхронний виклик у async"]
        A1["async def endpoint()"] --> B1["requests.get(url)\ntime.sleep(2)\npsycopg2.execute()"]
        B1 --> C1["OS Thread\nзаблокований"]
        C1 --> D1["Event Loop\nзаморожений"]
        D1 --> E1["Всі 10000\nз'єднань чекають"]
    end

    subgraph RIGHT["✅ Правильний async"]
        A2["async def endpoint()"] --> B2["await aiohttp.get(url)\nawait asyncio.sleep(2)\nawait asyncpg.fetch()"]
        B2 --> C2["OS повідомить\nколи готово"]
        C2 --> D2["Event Loop\nВИЛЬНИЙ"]
        D2 --> E2["Обслуговує\nінших клієнтів"]
    end
```

---

## Діаграма 7: Threading vs Multiprocessing vs Asyncio

```mermaid
quadrantChart
    title Python Concurrency Models

    x-axis Low IO --> Heavy CPU
    y-axis Few Connections --> Many Connections

    quadrant-1 Hybrid Systems
    quadrant-2 Async Networking
    quadrant-3 Threading
    quadrant-4 Parallel CPU

    Asyncio: [0.25, 0.655]
    FastAPI: [0.2, 0.75]
    WebSockets: [0.15, 0.85]

    ThreadPool: [0.25, 0.35]

    ProcessPool: [0.8, 0.3]
    Celery: [0.6, 0.35]

    ExecutorHybrid: [0.7, 0.7]
    
```

---

## Діаграма 8: Task States та Exception Handling

```mermaid
stateDiagram-v2
    direction TB

    [*] --> PENDING : asyncio.create_task()

    PENDING --> RUNNING : Event Loop обирає Task

    RUNNING --> SUSPENDED : await <something>
    SUSPENDED --> RUNNING : Event Loop відновлює

    RUNNING --> DONE_OK : return value
    RUNNING --> DONE_ERR : raise Exception
    RUNNING --> CANCELLED : CancelledError

    DONE_OK --> RETRIEVED : await task\nreturn result ✅

    DONE_ERR --> RETRIEVED_ERR : await task\nraise Exception ⚠️
    DONE_ERR --> SWALLOWED : GC без await\n⛔ Exception зникає мовчки!

    CANCELLED --> [*]
    RETRIEVED --> [*]
    RETRIEVED_ERR --> [*]

    note right of SWALLOWED
        "Task exception was never retrieved"
        Логується лише якщо debug=True
    end note
```

---

## Діаграма 9: run_in_executor — Міст між світами

```mermaid
sequenceDiagram
    participant EL as Event Loop\n(головний потік)
    participant CPU as CPU Thread\n(ProcessPool)
    participant IO as IO Thread\n(ThreadPool)

    Note over EL: FastAPI endpoint отримує запит

    EL->>CPU: run_in_executor(process_pool, heavy_math)
    EL->>IO: run_in_executor(thread_pool, legacy_db_query)

    Note over EL: Event Loop ВІЛЬНИЙ — обслуговує інших!

    par CPU task
        CPU->>CPU: sum(i*i for i in range(10**8))
        Note over CPU: GIL не заважає\n(окремий процес)
        CPU-->>EL: result via Future
    and IO task
        IO->>IO: psycopg2.execute(...)
        Note over IO: Blocking у потоці\n(OK — loop вільний)
        IO-->>EL: result via Future
    end

    EL->>EL: await обидва Future
    Note over EL: Відповідь клієнту з обома результатами
```

---

## Діаграма 10: Async Connection Pool

```mermaid
flowchart TD
    subgraph REQUESTS["5 одночасних запитів"]
        R1[Request 1]
        R2[Request 2]
        R3[Request 3]
        R4[Request 4]
        R5[Request 5]
    end

    subgraph POOL["Connection Pool (max=2)"]
        SEM[asyncio.Semaphore\nmax=2]
        C1[З'єднання #1]
        C2[З'єднання #2]
    end

    subgraph DB["PostgreSQL"]
        PG[(Database)]
    end

    R1 -- acquire() --> C1
    R2 -- acquire() --> C2
    R3 -- await acquire() --> SEM
    R4 -- await acquire() --> SEM
    R5 -- await acquire() --> SEM

    Note1["R3, R4, R5 — await у SUSPENDED\nподжидають вільне з'єднання"]

    C1 --> PG
    C2 --> PG

    C1 -- release() --> R3_WAKE["R3 прокидається\nотримує з'єднання #1"]
```
