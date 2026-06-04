"""
FastAPI Concurrency Demo
========================
6 ендпоінтів, що наочно показують:
  - як blocking код ВБИВАЄ async сервер
  - як правильний async витримує тисячі запитів
  - як run_in_executor рятує від CPU-bound пастки
"""
import asyncio
import concurrent.futures
import os
import time

from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI(
    title="Asyncio vs Blocking Demo",
    description="Навчальний приклад: порівняння синхронних та асинхронних ендпоінтів",
    version="1.0.0",
)

# ProcessPool для CPU-bound задач (ініціалізуємо один раз)
_process_pool = concurrent.futures.ProcessPoolExecutor(max_workers=os.cpu_count())


# ── Pydantic Response Models ───────────────────────────────────────────────────

class ResponseModel(BaseModel):
    endpoint: str
    message: str
    worker_pid: int
    simulated_delay_sec: float
    server_time_sec: float
    warning: str = ""


# ── Допоміжні функції ──────────────────────────────────────────────────────────

def _cpu_intensive_work(n: int = 4_000_000) -> int:
    """Синхронна CPU-bound функція — викликається з ProcessPool."""
    return sum(i * i for i in range(n))


def _sync_db_query(user_id: int) -> dict:
    """Симуляція синхронного DB driver (psycopg2 / sqlite3)."""
    time.sleep(1.5)  # Блокуючий network call до PostgreSQL
    return {"id": user_id, "name": f"User_{user_id}"}


# ── Endpoint 1: Health Check ───────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    """Завжди відповідає миттєво. Використовуй щоб перевірити чи Event Loop живий."""
    return {"status": "ok", "pid": os.getpid()}


# ── Endpoint 2: BROKEN — async def + time.sleep ───────────────────────────────

@app.get("/sync-broken", response_model=ResponseModel, tags=["❌ Blocking"])
async def sync_broken(request: Request):
    """
    НАЙНЕБЕЗПЕЧНІШИЙ ендпоінт.
    async def + time.sleep() = Event Loop заморожений для ВСІХ користувачів.

    Тест: надішли 10 одночасних запитів → 1 запит займає 2s, але сервер
    заблокований, тому 2-й запит чекає 2s, 3-й — 4s... разом ~20s!
    """
    t0 = time.perf_counter()
    # ⛔ ПОМИЛКА: блокує весь Event Loop, всі інші клієнти чекають
    time.sleep(2)
    elapsed = time.perf_counter() - t0

    return ResponseModel(
        endpoint="/sync-broken",
        message="Відповідь отримана, але сервер був заморожений!",
        worker_pid=os.getpid(),
        simulated_delay_sec=2.0,
        server_time_sec=round(elapsed, 3),
        warning="⛔ time.sleep() заморозив Event Loop для ВСІХ з'єднань!",
    )


# ── Endpoint 3: SAFE SYNC — def (threadpool) ──────────────────────────────────

@app.get("/sync-safe", response_model=ResponseModel, tags=["⚠️ Safe but Limited"])
def sync_safe(request: Request):
    """
    FastAPI детектує def (не async def) → автоматично виконує в threadpool.
    Event Loop не блокується, але масштаб обмежений кількістю потоків (~40).
    """
    t0 = time.perf_counter()
    time.sleep(2)  # OK — виконується у окремому потоці, не в Event Loop
    elapsed = time.perf_counter() - t0

    return ResponseModel(
        endpoint="/sync-safe",
        message="Виконано у threadpool, Event Loop вільний.",
        worker_pid=os.getpid(),
        simulated_delay_sec=2.0,
        server_time_sec=round(elapsed, 3),
        warning="⚠️ Масштаб обмежений: max ~40 одночасних запитів (розмір threadpool)",
    )


# ── Endpoint 4: CORRECT — async def + await asyncio.sleep ─────────────────────

@app.get("/async-correct", response_model=ResponseModel, tags=["✅ Correct Async"])
async def async_correct(request: Request):
    """
    ПРАВИЛЬНИЙ асинхронний ендпоінт.
    await asyncio.sleep() звільняє Event Loop — сервер обробляє тисячі одночасно.

    Тест: надішли 1000 одночасних запитів → всі відповідають за ~2s!
    """
    t0 = time.perf_counter()
    # ✅ await звільняє Event Loop — інші запити виконуються під час очікування
    await asyncio.sleep(2)
    elapsed = time.perf_counter() - t0

    return ResponseModel(
        endpoint="/async-correct",
        message="Event Loop вільний під час очікування — масштаб необмежений!",
        worker_pid=os.getpid(),
        simulated_delay_sec=2.0,
        server_time_sec=round(elapsed, 3),
        warning="",
    )


# ── Endpoint 5: CPU BROKEN — async def + CPU loop ─────────────────────────────

@app.get("/cpu-broken", response_model=ResponseModel, tags=["❌ Blocking"])
async def cpu_broken(request: Request):
    """
    CPU-bound задача безпосередньо в Event Loop.
    Математичний цикл ніколи не звільняє контроль → Event Loop заморожений.
    """
    t0 = time.perf_counter()
    # ⛔ CPU loop без await — Event Loop не отримує контроль
    result = sum(i * i for i in range(3_000_000))
    elapsed = time.perf_counter() - t0

    return ResponseModel(
        endpoint="/cpu-broken",
        message=f"Рахунок завершено: {result}",
        worker_pid=os.getpid(),
        simulated_delay_sec=0,
        server_time_sec=round(elapsed, 3),
        warning="⛔ CPU-цикл заморозив Event Loop на весь час обчислення!",
    )


# ── Endpoint 6: CPU FIXED — run_in_executor ───────────────────────────────────

@app.get("/cpu-fixed", response_model=ResponseModel, tags=["✅ Correct Async"])
async def cpu_fixed(request: Request):
    """
    CPU-bound задача делегована в ProcessPoolExecutor.
    Event Loop вільний під час обчислення у окремому процесі.
    """
    t0 = time.perf_counter()
    loop = asyncio.get_event_loop()
    # ✅ Відправляємо в окремий процес, await звільняє Event Loop
    result = await loop.run_in_executor(_process_pool, _cpu_intensive_work, 4_000_000)
    elapsed = time.perf_counter() - t0

    return ResponseModel(
        endpoint="/cpu-fixed",
        message=f"CPU робота виконана в окремому процесі: result={result}",
        worker_pid=os.getpid(),
        simulated_delay_sec=0,
        server_time_sec=round(elapsed, 3),
        warning="",
    )


# ── Endpoint 7: DB Simulation ─────────────────────────────────────────────────

@app.get("/db-sync-broken/{user_id}", response_model=ResponseModel, tags=["❌ Blocking"])
async def db_sync_broken(user_id: int):
    """
    Симуляція async def + psycopg2 (синхронний DB driver).
    Найчастіша реальна помилка в FastAPI проєктах.
    """
    t0 = time.perf_counter()
    # ⛔ Sync DB query в async def = Event Loop заморожений!
    user = _sync_db_query(user_id)
    elapsed = time.perf_counter() - t0

    return ResponseModel(
        endpoint=f"/db-sync-broken/{user_id}",
        message=f"User: {user}",
        worker_pid=os.getpid(),
        simulated_delay_sec=1.5,
        server_time_sec=round(elapsed, 3),
        warning="⛔ psycopg2/sqlite3 синхронний виклик блокує Event Loop!",
    )


@app.get("/db-async-correct/{user_id}", response_model=ResponseModel, tags=["✅ Correct Async"])
async def db_async_correct(user_id: int):
    """
    Симуляція async def + asyncpg (асинхронний DB driver).
    run_in_executor для legacy синхронних драйверів.
    """
    t0 = time.perf_counter()
    loop = asyncio.get_event_loop()
    # ✅ Threadpool для legacy sync DB (або asyncpg для справжнього async)
    user = await loop.run_in_executor(None, _sync_db_query, user_id)
    elapsed = time.perf_counter() - t0

    return ResponseModel(
        endpoint=f"/db-async-correct/{user_id}",
        message=f"User: {user} (via threadpool executor)",
        worker_pid=os.getpid(),
        simulated_delay_sec=1.5,
        server_time_sec=round(elapsed, 3),
        warning="",
    )
