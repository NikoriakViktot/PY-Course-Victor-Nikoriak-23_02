
"""
FastAPI Concurrency Load Test
==============================
Навчальний навантажувальний тест: показує різницю між blocking та async ендпоінтами.

Запуск:
  pip install httpx aiohttp
  python load_test.py

Сервер має бути запущений:
  docker compose up --build
  (або uvicorn app.main:app --reload)

Що демонструє скрипт:
  1. /sync-broken   — 10 concurrent → CASCADE BLOCK (10s замість 2s)
  2. /async-correct — 100 concurrent → всі відповідають за ~2s
  3. /async-correct — 500 concurrent → сервер витримує без проблем
  4. Health monitor  — показує що сервер заморожений під час blocking тесту
"""
import asyncio
import statistics
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

BASE_URL = "http://localhost:8001"
TIMEOUT = 30.0  # секунд — потрібен більший timeout для blocking тестів


# ── Кольорові консольні виводи ─────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"{GREEN}  ✓ {msg}{RESET}")
def err(msg):   print(f"{RED}  ✗ {msg}{RESET}")
def warn(msg):  print(f"{YELLOW}  ⚠ {msg}{RESET}")
def info(msg):  print(f"{CYAN}  → {msg}{RESET}")
def header(msg): print(f"\n{BOLD}{msg}{RESET}")
def sep():      print("─" * 65)


# ── Структура результату ────────────────────────────────────────────────────────
@dataclass
class RequestResult:
    status_code: int
    elapsed_sec: float
    error: Optional[str] = None
    warning: str = ""

@dataclass
class BenchmarkResult:
    endpoint: str
    concurrent: int
    total_time_sec: float
    results: list = field(default_factory=list)

    @property
    def success_count(self): return sum(1 for r in self.results if r.status_code == 200)
    @property
    def error_count(self): return len(self.results) - self.success_count
    @property
    def latencies(self): return [r.elapsed_sec for r in self.results if r.status_code == 200]
    @property
    def avg_latency(self): return statistics.mean(self.latencies) if self.latencies else 0
    @property
    def p95_latency(self):
        if not self.latencies: return 0
        sorted_l = sorted(self.latencies)
        return sorted_l[int(len(sorted_l) * 0.95)]
    @property
    def throughput(self): return self.success_count / self.total_time_sec if self.total_time_sec else 0


# ── Один HTTP запит ──────────────────────────────────────────────────────────────
async def single_request(client: httpx.AsyncClient, endpoint: str, req_id: int) -> RequestResult:
    try:
        t0 = time.perf_counter()
        resp = await client.get(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
        elapsed = time.perf_counter() - t0
        warning = ""
        if resp.status_code == 200:
            try:
                data = resp.json()
                warning = data.get("warning", "")
            except Exception:
                pass
        return RequestResult(status_code=resp.status_code, elapsed_sec=elapsed, warning=warning)
    except httpx.TimeoutException:
        return RequestResult(status_code=0, elapsed_sec=TIMEOUT, error="TIMEOUT")
    except Exception as e:
        return RequestResult(status_code=0, elapsed_sec=0, error=str(e))


# ── Паралельний бенчмарк ─────────────────────────────────────────────────────────
async def benchmark(endpoint: str, concurrent: int, label: str) -> BenchmarkResult:
    info(f"Надсилаємо {concurrent} одночасних запитів до {endpoint}...")

    async with httpx.AsyncClient() as client:
        t0 = time.perf_counter()
        tasks = [single_request(client, endpoint, i) for i in range(concurrent)]
        results = await asyncio.gather(*tasks)
        total = time.perf_counter() - t0

    bench = BenchmarkResult(
        endpoint=endpoint,
        concurrent=concurrent,
        total_time_sec=total,
        results=list(results),
    )
    return bench


def print_result(bench: BenchmarkResult, expected_time: float, label: str):
    ratio = bench.total_time_sec / expected_time if expected_time else 0
    status = "✅" if ratio < 2.0 else "❌"

    print(f"\n  {BOLD}{label}{RESET}")
    print(f"    Endpoint:        {bench.endpoint}")
    print(f"    Concurrent:      {bench.concurrent} запитів")
    print(f"    Успішних:        {bench.success_count}/{bench.concurrent}")
    if bench.error_count:
        print(f"    {RED}Помилок:         {bench.error_count}{RESET}")
    print(f"    Загальний час:   {bench.total_time_sec:.2f}s  (очікувано ~{expected_time:.1f}s)")
    print(f"    Середня latency: {bench.avg_latency:.2f}s")
    print(f"    P95 latency:     {bench.p95_latency:.2f}s")
    print(f"    Throughput:      {bench.throughput:.1f} req/s")
    print(f"    Оцінка:          {status}  (коефіцієнт: {ratio:.1f}x від очікуваного)")

    # Показуємо попередження з сервера
    warnings = {r.warning for r in bench.results if r.warning}
    for w in warnings:
        warn(w)


# ── Health Monitor ─────────────────────────────────────────────────────────────
async def monitor_health_during(endpoint: str, concurrent: int, duration: float = 12.0):
    """Паралельно з основним тестом робить health-check кожну секунду."""
    header(f"🔍 Моніторинг: запити до /health під час тесту {endpoint}")
    sep()

    health_results = []

    async def health_poller():
        async with httpx.AsyncClient() as client:
            for _ in range(int(duration)):
                t0 = time.perf_counter()
                try:
                    resp = await client.get(f"{BASE_URL}/health", timeout=2.0)
                    elapsed = time.perf_counter() - t0
                    health_results.append(elapsed)
                    status = "✅ відповів" if resp.status_code == 200 else f"❌ {resp.status_code}"
                    print(f"    /health [{_+1:02d}s]: {status} за {elapsed:.3f}s")
                except Exception as e:
                    elapsed = time.perf_counter() - t0
                    health_results.append(elapsed)
                    print(f"    {RED}/health [{_+1:02d}s]: ⛔ НЕ ВІДПОВІВ! ({elapsed:.1f}s) — {e}{RESET}")
                await asyncio.sleep(1)

    async with httpx.AsyncClient() as client:
        t0 = time.perf_counter()

        # Python 3.10+: asyncio.gather() повертає Future, не coroutine
        # create_task потребує coroutine → створюємо Task для кожного запиту окремо
        request_tasks = [
            asyncio.create_task(single_request(client, endpoint, i))
            for i in range(concurrent)
        ]
        poll_task = asyncio.create_task(health_poller())

        results = await asyncio.gather(*request_tasks)
        await asyncio.sleep(0.5)
        poll_task.cancel()
        try:
            await poll_task
        except asyncio.CancelledError:
            pass
        total = time.perf_counter() - t0

    bench = BenchmarkResult(endpoint=endpoint, concurrent=concurrent, total_time_sec=total, results=list(results))

    slow_health = [t for t in health_results if t > 1.0]
    if slow_health:
        err(f"Health check затримувався {len(slow_health)} раз(и) > 1s — Event Loop був заморожений!")
    else:
        ok(f"Health check завжди відповідав < 1s — Event Loop вільний!")

    return bench


# ── ТЕСТ 1: Cascade Block ──────────────────────────────────────────────────────
async def test_cascade_block():
    header("ТЕСТ 1: Cascade Block — /sync-broken з 10 одночасними запитами")
    sep()
    print(f"""
  Сценарій: 10 клієнтів надсилають запит одночасно.
  Ендпоінт використовує time.sleep(2) всередині async def.

  Очікування (якби це було async): ~2.0s для всіх 10
  Реальність (blocking):           ~20.0s (послідовно: 2s × 10)
    """)

    bench = await monitor_health_during("/sync-broken", concurrent=10, duration=22.0)
    print_result(bench, expected_time=2.0, label="Результат /sync-broken")

    print(f"""
  {BOLD}Пояснення:{RESET}
  time.sleep(2) блокує Python thread.
  Оскільки Event Loop живе в цьому ж thread — він замерзає.
  Запит #1 займає 2s, потім Event Loop може взяти запит #2 → ще 2s...
  10 запитів × 2s = {RED}~20s замість 2s{RESET}
    """)


# ── ТЕСТ 2: Async Scales ───────────────────────────────────────────────────────
async def test_async_scales():
    header("ТЕСТ 2: Async Scales — /async-correct з різною кількістю запитів")
    sep()
    print(f"""
  Сценарій: тестуємо масштабованість async ендпоінту.
  await asyncio.sleep(2) — Event Loop вільний під час очікування.
    """)

    for n in [10, 50, 100, 500]:
        bench = await benchmark("/async-correct", concurrent=n, label=f"{n} запитів")
        ratio = bench.total_time_sec / 2.0
        verdict = f"{GREEN}✅ МАСШТАБУЄ{RESET}" if ratio < 2.5 else f"{RED}❌ ПРОБЛЕМА{RESET}"
        print(f"    {n:4d} concurrent: {bench.total_time_sec:.2f}s  ({ratio:.1f}x)  {verdict}  "
              f"throughput={bench.throughput:.0f} req/s")

    print(f"""
  {BOLD}Висновок:{RESET}
  Незалежно від кількості одночасних запитів — час завжди ~2s.
  await звільняє Event Loop → він обслуговує ВСІ запити одночасно.
    """)


# ── ТЕСТ 3: sync def vs async def ──────────────────────────────────────────────
async def test_sync_safe_vs_broken():
    header("ТЕСТ 3: Порівняння трьох варіантів з 20 concurrent запитами")
    sep()
    print()

    endpoints = [
        ("/sync-broken",   2.0, "❌ async def + time.sleep (блокуючий)"),
        ("/sync-safe",     2.0, "⚠️  def sync (FastAPI threadpool)"),
        ("/async-correct", 2.0, "✅ async def + await asyncio.sleep"),
    ]

    results_table = []
    for ep, expected, label in endpoints:
        bench = await benchmark(ep, concurrent=20, label=label)
        results_table.append((label, bench.total_time_sec, bench.throughput, bench.p95_latency))

    print(f"\n  {'Ендпоінт':<45} {'Час':>8} {'req/s':>8} {'P95':>8}")
    print(f"  {'─'*45} {'─'*8} {'─'*8} {'─'*8}")
    for label, total, throughput, p95 in results_table:
        print(f"  {label:<45} {total:>7.2f}s {throughput:>7.1f} {p95:>7.2f}s")

    print(f"""
  {BOLD}Інтерпретація:{RESET}
  ❌ sync-broken: час ~40s (20 запитів × 2s кожен послідовно)
  ⚠️  sync-safe:  час ~2-4s (threadpool ~40 потоків, але обмежено)
  ✅ async:       час ~2s (всі 20 одночасно, Event Loop вільний)
    """)


# ── ТЕСТ 4: CPU Bound Comparison ───────────────────────────────────────────────
async def test_cpu_bound():
    header("ТЕСТ 4: CPU-bound — /cpu-broken vs /cpu-fixed з 5 concurrent")
    sep()
    print()

    for ep, label in [
        ("/cpu-broken", "❌ CPU loop у Event Loop"),
        ("/cpu-fixed",  "✅ CPU loop у ProcessPool"),
    ]:
        bench = await benchmark(ep, concurrent=5, label=label)
        print(f"  {label}")
        print(f"    Час: {bench.total_time_sec:.2f}s  | avg: {bench.avg_latency:.2f}s  | "
              f"throughput: {bench.throughput:.1f} req/s")
        print()

    print(f"""
  {BOLD}Пояснення:{RESET}
  cpu-broken: математичний цикл без await = Event Loop заморожений.
  5 запитів виконуються послідовно навіть якщо надіслані одночасно.

  cpu-fixed: цикл у ProcessPoolExecutor → окремий CPU core.
  await loop.run_in_executor() = Event Loop вільний.
  5 запитів виконуються майже паралельно.
    """)


# ── ТЕСТ 5: DB Simulation ──────────────────────────────────────────────────────
async def test_db_simulation():
    header("ТЕСТ 5: DB Simulation — sync psycopg2 vs async executor з 8 запитами")
    sep()
    print()

    for ep, label in [
        ("/db-sync-broken/1",   "❌ psycopg2 sync у async def"),
        ("/db-async-correct/1", "✅ psycopg2 через run_in_executor"),
    ]:
        bench = await benchmark(ep, concurrent=8, label=label)
        print(f"  {label}")
        print(f"    Час: {bench.total_time_sec:.2f}s  | avg: {bench.avg_latency:.2f}s")
        warnings = {r.warning for r in bench.results if r.warning}
        for w in warnings:
            warn(w)
        print()

    print(f"""
  {BOLD}Production висновок:{RESET}
  Якщо використовуєш psycopg2 у FastAPI async ендпоінті без executor —
  один повільний DB запит замораює весь сервер для всіх клієнтів.
  Рішення: asyncpg або run_in_executor для legacy драйверів.
    """)


# ── Main ───────────────────────────────────────────────────────────────────────
async def main():
    print(f"\n{BOLD}{'='*65}{RESET}")
    print(f"{BOLD}  FastAPI Concurrency Load Test{RESET}")
    print(f"{BOLD}  Async vs Blocking — навчальний бенчмарк{RESET}")
    print(f"{BOLD}{'='*65}{RESET}")

    # Перевірка сервера
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/health", timeout=5.0)
            if resp.status_code != 200:
                raise ConnectionError("Сервер не відповідає")
        ok(f"Сервер доступний: {BASE_URL}")
        ok(f"Swagger UI:       {BASE_URL}/docs")
    except Exception as e:
        err(f"Сервер недоступний: {e}")
        err("Запусти: docker compose up --build")
        return

    print(f"\n  {YELLOW}УВАГА: деякі тести тривають довго (до 60s) — це навмисно.{RESET}")
    print(f"  {YELLOW}Blocking тести займають N × 2s через cascade block.{RESET}\n")

    input("  Натисни Enter щоб почати тестування...")

    await test_cascade_block()
    input("\n  Enter для наступного тесту...")

    await test_async_scales()
    input("\n  Enter для наступного тесту...")

    await test_sync_safe_vs_broken()
    input("\n  Enter для наступного тесту...")

    await test_cpu_bound()
    input("\n  Enter для наступного тесту...")

    await test_db_simulation()

    # ── Фінальне резюме ─────────────────────────────────────────────────────────
    header("📊 ФІНАЛЬНЕ РЕЗЮМЕ")
    sep()
    print(f"""
  Золоті правила FastAPI:

  1. {RED}НІКОЛИ{RESET} time.sleep() в async def → замораює сервер
  2. {RED}НІКОЛИ{RESET} requests/psycopg2/sqlite3 в async def без executor
  3. {GREEN}ЗАВЖДИ{RESET} await asyncio.sleep() замість time.sleep()
  4. {GREEN}ЗАВЖДИ{RESET} aiohttp/httpx async для HTTP запитів
  5. {GREEN}ЗАВЖДИ{RESET} asyncpg/SQLAlchemy async для DB запитів
  6. CPU-bound → ProcessPoolExecutor через run_in_executor
  7. Legacy sync → ThreadPoolExecutor через run_in_executor

  Масштаб async vs blocking:
    async def + await:   10 000+ concurrent на 1 uvicorn worker
    sync def (threadpool): ~40 concurrent (default threadpool size)
    async def + blocking:  1 concurrent (серіалізує всі запити!)
    """)
    print(f"{BOLD}{'='*65}{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())
