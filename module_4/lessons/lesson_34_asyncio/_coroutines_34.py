"""
Допоміжні корутини для Уроку 34 — Asyncio
==========================================
Цей файл вирішує проблему Windows + Jupyter:
  RuntimeError: asyncio.run() cannot be called from a running event loop

Jupyter вже запускає власний Event Loop. asyncio.run() не може запустити
вкладений loop. Рішення: nest_asyncio або await безпосередньо в клітинці.

Використання в notebook:
  from _coroutines_34 import run, *

  # Замість asyncio.run(main()):
  await main()           # ← просто await, без asyncio.run()
  # або:
  run(main())            # ← run() з nest_asyncio підтримкою
"""
import asyncio
import time
from typing import Any, Coroutine

# ── Jupyter-сумісний runner ──────────────────────────────────────────────────
def run(coro: Coroutine) -> Any:
    """
    Запускає корутину у будь-якому середовищі:
    - Jupyter (запущений loop) → nest_asyncio або get_event_loop().run_until_complete
    - Звичайний Python script → asyncio.run()
    """
    try:
        loop = asyncio.get_running_loop()
        # Ми всередині запущеного loop (Jupyter) → використовуємо nest_asyncio
        try:
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        except ImportError:
            # Fallback: повертаємо coroutine — треба await у клітинці
            print("Встанови nest_asyncio: pip install nest_asyncio")
            print("Або використовуй 'await' замість 'run()'")
            return coro
    except RuntimeError:
        # Немає запущеного loop (звичайний Python) → asyncio.run()
        return asyncio.run(coro)


# ── Урок: Coroutine Lifecycle ─────────────────────────────────────────────────

async def fetch_data_demo():
    """Базова корутина для демонстрації lifecycle."""
    print("Starting...")
    await asyncio.sleep(1)
    print("Finished")
    return "data"


async def lifecycle_demo():
    """Демонстрація трьох способів запуску корутини."""
    print("=== Правильний запуск coroutine ===")
    await fetch_data_demo()
    print()

    print("=== create_task: планує без blocking ===")
    task = asyncio.create_task(fetch_data_demo())
    print(f"Task створено, done={task.done()}")
    await task
    print(f"Task завершено, done={task.done()}")


# ── Урок: Blocking vs Non-Blocking ───────────────────────────────────────────

async def background_task_broken():
    """⛔ НЕПРАВИЛЬНО: time.sleep блокує Event Loop."""
    print("[TASK] Started (blocking!)")
    time.sleep(3)
    print("[TASK] Finished")


async def background_task_correct():
    """✅ ПРАВИЛЬНО: await asyncio.sleep звільняє Event Loop."""
    print("[TASK] Started (async!)")
    await asyncio.sleep(3)
    print("[TASK] Finished")


async def health_ping(n: int = 6):
    """Пінгує кожні 0.5с — показує чи Event Loop вільний."""
    for i in range(n):
        print(f"  [PING] Ping #{i + 1}!")
        await asyncio.sleep(0.5)


async def blocking_demo():
    """Показує cascade block від time.sleep."""
    print("З time.sleep (BLOCKING):")
    print("Очікуємо... [TASK] blocked весь Event Loop")
    await asyncio.gather(background_task_broken(), health_ping(4))


async def nonblocking_demo():
    """Показує кооперативне виконання через await."""
    print("З await asyncio.sleep (CORRECT):")
    await asyncio.gather(background_task_correct(), health_ping(6))


# ── Урок: asyncio.gather ─────────────────────────────────────────────────────

async def simulate_db_query(query_id: int, delay: float):
    """Симуляція DB запиту з затримкою."""
    print(f"  DB Query {query_id}: починаємо...")
    await asyncio.sleep(delay)
    result = f"data_from_query_{query_id}"
    print(f"  DB Query {query_id}: завершено за {delay}s")
    return result


async def sequential_queries():
    """Послідовні DB запити."""
    start = time.perf_counter()
    r1 = await simulate_db_query(1, 1.0)
    r2 = await simulate_db_query(2, 0.8)
    r3 = await simulate_db_query(3, 0.6)
    elapsed = time.perf_counter() - start
    print(f"Послідовно: {elapsed:.2f}s")
    return [r1, r2, r3]


async def concurrent_queries():
    """Конкурентні DB запити через gather."""
    start = time.perf_counter()
    results = await asyncio.gather(
        simulate_db_query(1, 1.0),
        simulate_db_query(2, 0.8),
        simulate_db_query(3, 0.6),
    )
    elapsed = time.perf_counter() - start
    print(f"Gather: {elapsed:.2f}s (очікували ~1.0s)")
    return results


async def gather_demo():
    print("=== Послідовне виконання ===")
    await sequential_queries()
    print()
    print("=== asyncio.gather (concurrent) ===")
    await concurrent_queries()


# ── Урок: Task + Exception Handling ─────────────────────────────────────────

async def risky_operation(op_id: int):
    """Операція яка може впасти."""
    await asyncio.sleep(0.1)
    if op_id == 2:
        raise RuntimeError(f"Operation {op_id} failed!")
    return f"result_{op_id}"


async def safe_gather_demo():
    """Правильна обробка виняток у Tasks."""
    print("=== Обробка виняток у Tasks ===")
    tasks = [asyncio.create_task(risky_operation(i)) for i in range(4)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"  Task {i}: ПОМИЛКА — {result}")
        else:
            print(f"  Task {i}: {result}")


# ── Урок: Async Context Manager ──────────────────────────────────────────────

class FakeConnectionPool:
    """Симуляція DB connection pool через asyncio.Semaphore."""

    def __init__(self, max_size: int = 3):
        self.max_size = max_size
        self._semaphore = asyncio.Semaphore(max_size)
        self._counter = 0

    async def __aenter__(self):
        await self._semaphore.acquire()
        self._counter += 1
        conn_id = self._counter
        used = self.max_size - self._semaphore._value
        print(f"  [POOL] З'єднання #{conn_id} відкрито (зайнято: {used}/{self.max_size})")
        return conn_id

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._semaphore.release()
        print(f"  [POOL] З'єднання повернено в pool")
        return False


async def db_query_with_pool(pool: FakeConnectionPool, user_id: int):
    async with pool as conn:
        await asyncio.sleep(0.3)
        return {"conn": conn, "user_id": user_id}


async def connection_pool_demo():
    """Демонстрація connection pool з Semaphore."""
    pool = FakeConnectionPool(max_size=2)
    print("Pool max=2, надсилаємо 5 запитів одночасно:")
    results = await asyncio.gather(*[db_query_with_pool(pool, i) for i in range(5)])
    print(f"Всі {len(results)} запитів завершені!")


# ── run_in_executor ───────────────────────────────────────────────────────────

import concurrent.futures

_process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=2)


def heavy_sync_math(n: int = 3_000_000) -> int:
    """CPU-bound синхронна функція."""
    return sum(i * i for i in range(n))


async def cpu_broken_demo():
    """⛔ CPU-bound у Event Loop — заморожує все."""
    print("[MATH] CPU loop у Event Loop (BLOCKING)...")
    t0 = time.perf_counter()
    result = sum(i * i for i in range(3_000_000))
    print(f"[MATH] Done: {time.perf_counter()-t0:.2f}s — Event Loop був заморожений!")
    return result


async def cpu_fixed_demo():
    """✅ CPU-bound в ProcessPoolExecutor — loop вільний."""
    print("[MATH] CPU loop у ProcessPool (CORRECT)...")
    t0 = time.perf_counter()
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(_process_pool, heavy_sync_math, 3_000_000)
    print(f"[MATH] Done: {time.perf_counter()-t0:.2f}s — Event Loop був вільним!")
    return result
