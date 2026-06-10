# Урок 34 — Asyncio: Кооперативна Багатозадачність та Архітектура Event Loop

**Модуль:** 4 — Network & Concurrent Systems  
**Складність:** intermediate  
**Мова:** Українська

---

## Зміст

1. [Навіщо asyncio?](#1-навіщо-asyncio)
2. [Ключові концепції](#2-ключові-концепції)
3. [Coroutine Lifecycle](#3-coroutine-lifecycle)
4. [Event Loop Architecture](#4-event-loop-architecture)
5. [Cooperative vs Preemptive Multitasking](#5-cooperative-vs-preemptive-multitasking)
6. [asyncio API Reference](#6-asyncio-api-reference)
7. [Blocking vs Non-Blocking](#7-blocking-vs-non-blocking)
8. [FastAPI & Backend Integration](#8-fastapi--backend-integration)
9. [Threading vs Multiprocessing vs Asyncio](#9-threading-vs-multiprocessing-vs-asyncio)
10. [Типові помилки та антипатерни](#10-типові-помилки-та-антипатерни)
11. [Production Patterns](#11-production-patterns)
12. [Debugging Guide](#12-debugging-guide)

---

## 1. Навіщо asyncio?

### Проблема синхронних серверів

У традиційній WSGI-архітектурі кожне з'єднання вимагає окремий потік ОС. Потік займає ~8 MB RAM і блокується на весь час очікування I/O. При 10 000 одночасних користувачів сервер витрачає ~80 GB RAM лише на потоки — навіть якщо вони 99% часу просто чекають.

### Масштаб часу: Чому I/O така повільна

| Операція | Реальний час | "Людський" еквівалент |
|----------|--------------|-----------------------|
| CPU cache (L1) | 1 нс | 3 секунди |
| RAM | 100 нс | 5 хвилин |
| SSD read | 100 мкс | 4 дні |
| TCP round trip | 100 мс | 11 місяців |
| External API | 500 мс | **5.5 років** |

Asyncio вирішує це через **cooperative multitasking**: замість того щоб тримати потік заблокованим 5.5 "людських років", `await` звільняє Event Loop обслуговувати тисячі інших з'єднань.

---

## 2. Ключові концепції

### Coroutine

Спеціальна функція, визначена через `async def`, яка:
- При **виклику** повертає `coroutine object` (нічого не виконує)
- При `await` — виконується до першого внутрішнього `await`
- При `await asyncio.sleep()` — призупиняється, зберігає стан, передає контроль Event Loop

```python
async def my_coroutine():      # Визначення
    ...

obj = my_coroutine()           # Виклик → coroutine object (FROZEN)
result = await my_coroutine()  # Виконання та очікування результату
```

### Task

`asyncio.Task` — обгортка над coroutine, яка планує її виконання на Event Loop.

```python
task = asyncio.create_task(my_coroutine())  # Планує ЗАРАЗ, не чекає
result = await task                          # Явно чекаємо завершення
```

**Стани Task:**
```
create_task() → [PENDING] → [RUNNING] → [DONE / CANCELLED]
                                 ↑            ↓
                           при await    result або exception
```

### Event Loop

Центральний планувальник asyncio. Алгоритм роботи:

```
while True:
    1. Виконати всі READY задачі до першого await
    2. Запитати ОС: які сокети/таймери готові? (epoll/kqueue)
    3. Перемістити завершені задачі у READY чергу
    4. Повторити
```

---

## 3. Coroutine Lifecycle

```
Виклик async def func()
         │
         ▼
┌─────────────────┐
│ coroutine object│  ← СТАН: GEN_CREATED
│ code: рядки...  │    Нічого не виконується!
│ locals: {}      │
└────────┬────────┘
         │ await func() або asyncio.run(func())
         ▼
┌─────────────────┐
│   RUNNING       │  ← Виконується рядок за рядком
│                 │
│  ... код ...    │
│  await <awaitable>  ← ПАУЗА
└────────┬────────┘
         │ await
         ▼
┌─────────────────┐
│   SUSPENDED     │  ← Стан збережено (locals, position)
│ waiting for I/O │    Event Loop вільний!
└────────┬────────┘
         │ I/O завершено
         ▼
┌─────────────────┐
│   RUNNING       │  ← Відновлення з точки await
└────────┬────────┘
         │ return
         ▼
┌─────────────────┐
│   CLOSED        │  ← GEN_CLOSED, result доступний
└─────────────────┘
```

---

## 4. Event Loop Architecture

```
┌────────────────────────────────────────────────────────────┐
│                      EVENT LOOP (один потік)               │
│                                                            │
│  ┌──────────────────┐   ┌────────────────────────────────┐ │
│  │   Ready Queue    │   │  I/O Selector (epoll/kqueue)   │ │
│  │                  │   │                                │ │
│  │ [Task A] ──────► │   │ Socket A: HTTP ── WAITING      │ │
│  │ [Task C]         │   │ Socket B: DB   ── WAITING      │ │
│  │                  │   │ Socket C: API  ── READY! ◄──── │ │
│  └────────┬─────────┘   └──────────────┬─────────────────┘ │
│           │                             │                   │
│           ▼                             ▼                   │
│     Виконати Task                 Wake Task B              │
│     до await                      (перемістити в Queue)    │
└────────────────────────────────────────────────────────────┘
```

### Де насправді "чекання"?

Коли Python виконує `await asyncio.sleep(1)`:
1. Event Loop реєструє таймер у ОС
2. Coroutine переходить у SUSPENDED
3. ОС використовує `epoll`/`kqueue` — апаратний механізм сповіщення
4. Python thread сплять, використовуючи ~0% CPU
5. Через 1 секунду ОС будить Python, Event Loop відновлює coroutine

---

## 5. Cooperative vs Preemptive Multitasking

| | Preemptive (Threading) | Cooperative (Asyncio) |
|--|------------------------|----------------------|
| Хто перериває | ОС примусово у будь-який момент | Coroutine добровільно через `await` |
| Race conditions | Так — треба Lock/Semaphore | Ні — один потік |
| Стек | ~8 MB/потік | ~2 KB/coroutine |
| Max concurrent | ~500–1000 | ~100 000+ |
| Blocking виклик | Зупиняє 1 потік | Зупиняє **весь** Event Loop |

**Ключова небезпека asyncio:** один blocking виклик (`time.sleep`, `requests.get`) зупиняє ВСЕ — не лише одну задачу.

---

## 6. asyncio API Reference

### Основні функції

```python
# Точка входу програми
asyncio.run(main())
asyncio.run(main(), debug=True)

# Планування задач
task = asyncio.create_task(coro())
tasks = asyncio.gather(coro1(), coro2(), coro3())
results = await asyncio.gather(*coros, return_exceptions=True)

# Очікування
await asyncio.sleep(seconds)        # Відпускає Event Loop
await asyncio.wait_for(coro, timeout=5.0)  # З таймаутом

# Перевірка статусу
task.done()        # True якщо завершено
task.cancelled()   # True якщо скасовано
task.result()      # Повертає результат або кидає виняток
task.cancel()      # Надсилає CancelledError у задачу

# Поточний Event Loop
loop = asyncio.get_event_loop()

# Делегування blocking коду
result = await loop.run_in_executor(executor, sync_func, *args)
```

### async with та async for

```python
# async context manager
async with aiofiles.open("file.txt") as f:
    data = await f.read()

# async generator / iterator
async for item in async_generator():
    process(item)
```

---

## 7. Blocking vs Non-Blocking

### Таблиця замін

| Синхронний (БЛОКУЮЧИЙ) | Асинхронний (ПРАВИЛЬНИЙ) |
|------------------------|--------------------------|
| `time.sleep(n)` | `await asyncio.sleep(n)` |
| `requests.get(url)` | `await session.get(url)` (aiohttp) |
| `open(path).read()` | `await aio_file.read()` (aiofiles) |
| `psycopg2.connect(...)` | `await asyncpg.connect(...)` |
| `subprocess.run(cmd)` | `await asyncio.create_subprocess_exec(...)` |
| CPU-bound loop | `await loop.run_in_executor(process_pool, func)` |

### run_in_executor — міст між світами

```python
import asyncio
import concurrent.futures

process_pool = concurrent.futures.ProcessPoolExecutor()
thread_pool = concurrent.futures.ThreadPoolExecutor()

async def handle_request():
    loop = asyncio.get_event_loop()

    # CPU-bound → ProcessPoolExecutor (обходить GIL)
    result = await loop.run_in_executor(process_pool, heavy_computation)

    # Legacy sync I/O → ThreadPoolExecutor
    data = await loop.run_in_executor(thread_pool, legacy_db_query)

    return result, data
```

---

## 8. FastAPI & Backend Integration

### Три типи ендпоінтів у FastAPI

```python
from fastapi import FastAPI
import asyncio, time

app = FastAPI()

# ✅ async def + await: найкраще для async I/O
@app.get("/users")
async def get_users(pool):
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM users")

# ❌ async def + blocking: найгірше (блокує весь Event Loop!)
@app.get("/broken")
async def broken_endpoint():
    time.sleep(2)               # Зупиняє ВЕСЬ сервер!
    return {"status": "bad"}

# ⚠️ def (не async): FastAPI автоматично виконує в threadpool
@app.get("/legacy")
def legacy_endpoint():
    time.sleep(2)               # OK — окремий потік, loop вільний
    return {"status": "ok but limited"}
```

### Правило FastAPI:
- `async def` + тільки `await` операції → **Event Loop (оптимально)**
- `async def` + blocking виклик → **катастрофа**
- `def` (sync) → **автоматичний threadpool** (безпечно, але обмежено)

### WebSocket масштаб

```
Синхронний WSGI (Gunicorn threads):
  10 000 WebSocket з'єднань → 10 000 потоків → ~80 GB RAM
  (практично неможливо)

Asyncio ASGI (uvicorn):
  10 000 WebSocket з'єднань → 10 000 coroutine об'єктів → ~20 MB RAM
  (легко — лише пам'ять для стану)
```

---

## 9. Threading vs Multiprocessing vs Asyncio

| | Threading | Multiprocessing | Asyncio |
|--|-----------|----------------|---------|
| Модель | N потоків, 1 процес | N процесів | 1 потік, 1 процес |
| GIL | Один на всіх | Власний у кожного | Один (не обмеження) |
| Планування | Preemptive (ОС) | Preemptive (ОС) | Cooperative (await) |
| Пам'ять/unit | ~8 MB/потік | ~50 MB/процес | ~2 KB/coroutine |
| Race conditions | Так | Ні | Ні |
| CPU-bound | ❌ GIL | ✅ Реальний паралелізм | ❌ Блокує loop |
| I/O-bound | ✅ ОК | ✅ ОК | ✅ Найкраще |
| Max concurrent | ~500 | ~CPU cores | ~100 000+ |
| Ідеально для | Legacy sync бібліотеки | ML, image, math | Web, API, WebSocket |

### Рішення для combined workloads (FastAPI production)

```
HTTP request → FastAPI async endpoint
    │
    ├── DB query → asyncpg (async) → await
    ├── HTTP call → aiohttp (async) → await  
    └── CPU work → ProcessPoolExecutor → run_in_executor → await
```

---

## 10. Типові помилки та антипатерни

### Антипатерн 1: Blocking у async (найчастіша помилка)

```python
# НЕБЕЗПЕЧНО
async def endpoint():
    time.sleep(2)          # Зупиняє весь сервер!
    requests.get(url)      # Блокує Event Loop!
    psycopg2.execute(...)  # Зупиняє всі з'єднання!

# ПРАВИЛЬНО
async def endpoint():
    await asyncio.sleep(2)
    async with session.get(url) as r: ...
    async with pool.acquire() as conn: await conn.fetch(...)
```

### Антипатерн 2: Забутий await

```python
# НЕБЕЗПЕЧНО — RuntimeWarning, нічого не виконується
result = fetch_data()        # Повертає coroutine object!

# ПРАВИЛЬНО
result = await fetch_data()  # Виконує та чекає
```

### Антипатерн 3: Task без посилання (exception зникає)

```python
# НЕБЕЗПЕЧНО
asyncio.create_task(risky_op())  # Exception буде проковтнуто!

# ПРАВИЛЬНО
task = asyncio.create_task(risky_op())
try:
    await task
except Exception as e:
    logger.error(f"Task failed: {e}")
```

### Антипатерн 4: CPU-bound у async (заморожує loop)

```python
# НЕБЕЗПЕЧНО
async def process():
    result = sum(i*i for i in range(10**8))  # Блокує loop на секунди!

# ПРАВИЛЬНО
async def process():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(process_pool, heavy_sync_func)
```

### Антипатерн 5: Main завершується раніше Task

```python
# НЕБЕЗПЕЧНО
async def main():
    asyncio.create_task(background_work())
    # Event Loop зупиняється → Task знищується!

# ПРАВИЛЬНО
async def main():
    task = asyncio.create_task(background_work())
    await asyncio.sleep(0)  # Даємо Task запустись
    await task               # Явно чекаємо
```

---

## 11. Production Patterns

### Патерн 1: Connection Pool з Semaphore

```python
class ConnectionPool:
    def __init__(self, max_size: int):
        self._semaphore = asyncio.Semaphore(max_size)
    
    async def __aenter__(self):
        await self._semaphore.acquire()
        return await self._create_connection()
    
    async def __aexit__(self, *args):
        self._semaphore.release()
```

### Патерн 2: Retry з Exponential Backoff

```python
async def with_retry(coro_factory, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
```

### Патерн 3: Producer-Consumer з asyncio.Queue

```python
async def producer(queue: asyncio.Queue, items):
    for item in items:
        await queue.put(item)
    await queue.put(None)  # sentinel

async def consumer(queue: asyncio.Queue):
    while True:
        item = await queue.get()
        if item is None:
            break
        await process(item)
        queue.task_done()
```

### Патерн 4: Rate Limiter

```python
class AsyncRateLimiter:
    def __init__(self, max_calls: int, period: float = 1.0):
        self._semaphore = asyncio.Semaphore(max_calls)
        self._period = period
    
    async def __aenter__(self):
        await self._semaphore.acquire()
        asyncio.create_task(self._release_after_period())
        return self
    
    async def _release_after_period(self):
        await asyncio.sleep(self._period)
        self._semaphore.release()
    
    async def __aexit__(self, *args):
        pass
```

---

## 12. Debugging Guide

### Інструменти debugging

```bash
# 1. Debug режим через змінну середовища
PYTHONASYNCIODEBUG=1 python app.py

# 2. Verbose logging asyncio
PYTHONASYNCIODEBUG=1 python -W always app.py
```

```python
# 3. Debug режим у коді
asyncio.run(main(), debug=True)

# 4. Кастомний exception handler
def handle_exception(loop, context):
    logger.error(f"Unhandled exception: {context}")

loop = asyncio.get_event_loop()
loop.set_exception_handler(handle_exception)
```

### Що виявляє debug mode

| Проблема | Debug mode виявляє |
|----------|--------------------|
| Coroutine ніколи не awaited | `RuntimeWarning: coroutine was never awaited` |
| Blocking функція > 100ms | `Executing took X.XX seconds` |
| Exception у Task без await | Log повідомлення при GC |
| Slow callbacks | `Executing callback took X seconds` |

### Типовий stack trace аналіз

```
Task exception was never retrieved
future: <Task finished name='Task-2' coro=<risky_op() at app.py:15>
exception=ValueError('...')>
Traceback (most recent call last):
  File "app.py", line 17, in risky_op   ← Де виняток виник
    raise ValueError(...)
ValueError: ...
```

**Правило:** якщо бачиш "Task exception was never retrieved" — знайди місце де Task створювався і додай `try/except` навколо `await task`.

---

## Зв'язок з попередніми уроками

| Урок | Тема | Відношення до Asyncio |
|------|------|-----------------------|
| 32 | Threading | Preemptive vs Cooperative multitasking |
| 33 | Multiprocessing | ProcessPoolExecutor для run_in_executor |
| 34 | **Asyncio** | **Цей урок** |
| — | FastAPI | Asyncio = engine для ASGI web серверів |
