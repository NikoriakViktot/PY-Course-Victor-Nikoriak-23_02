"""
FastAPI Concurrency — Streamlit Visual Demo
============================================
Візуально показує різницю між blocking та async ендпоінтами
у реальному часі через Gantt-chart запитів.

Запуск:
  pip install streamlit httpx plotly
  streamlit run streamlit_demo.py

Сервер (окремий термінал):
  docker compose up --build
"""
import asyncio
import concurrent.futures
import statistics
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

import os

import httpx
import plotly.graph_objects as go
import streamlit as st

# ── Конфігурація ────────────────────────────────────────────────────────────────
# Всередині Docker: FASTAPI_HOST=http://fastapi-demo:8000
# Локально:        FASTAPI_HOST=http://localhost:8001  (або не задано)
DEFAULT_HOST = os.environ.get("FASTAPI_HOST", "http://localhost:8001")
# URL що відкривається у браузері (localhost навіть коли Streamlit в Docker)
BROWSER_HOST = os.environ.get("BROWSER_HOST", "http://localhost:8001")

ENDPOINTS = {
    "✅ async-correct":     "/async-correct",
    "❌ sync-broken":       "/sync-broken",
    "⚠️  sync-safe (def)":  "/sync-safe",
    "❌ cpu-broken":        "/cpu-broken",
    "✅ cpu-fixed":         "/cpu-fixed",
    "❌ db-sync-broken":    "/db-sync-broken/1",
    "✅ db-async-correct":  "/db-async-correct/1",
}

COLORS = {
    "/async-correct":    "#2ecc71",   # зелений
    "/sync-broken":      "#e74c3c",   # червоний
    "/sync-safe":        "#f39c12",   # помаранчевий
    "/cpu-broken":       "#c0392b",   # темно-червоний
    "/cpu-fixed":        "#27ae60",   # темно-зелений
    "/db-sync-broken/1": "#e74c3c",
    "/db-async-correct/1": "#2ecc71",
}

# ── Код та пояснення для кожного ендпоінту ──────────────────────────────────────
ENDPOINT_INFO = {
    "/async-correct": {
        "color": "#2ecc71",
        "verdict": "✅ ПРАВИЛЬНО — async + await",
        "why": (
            "`await asyncio.sleep(2)` призупиняє лише цю корутину. "
            "Event Loop за цей час обслуговує всіх інших клієнтів. "
            "100 запитів = ~2s (не 200s!)."
        ),
        "code": """\
@app.get("/async-correct")
async def async_correct():
    # await передає контроль Event Loop на 2s.
    # За цей час він обслуговує ВСІХ інших клієнтів.
    await asyncio.sleep(2)          # ← НЕ блокує потік
    return {
        "endpoint": "async-correct",
        "message": "Non-blocking: Event Loop вільний"
    }""",
    },
    "/sync-broken": {
        "color": "#e74c3c",
        "verdict": "❌ НЕБЕЗПЕЧНО — async def + time.sleep()",
        "why": (
            "`time.sleep(2)` блокує **весь** Python thread. "
            "Event Loop заморожений — не може обробити жоден інший запит. "
            "10 запитів займуть 10×2 = **20s** замість 2s!"
        ),
        "code": """\
@app.get("/sync-broken")
async def sync_broken():
    # ❌ ПОМИЛКА: time.sleep() блокує весь Python thread!
    # Event Loop заморожений — НЕ може обробляти ЖОДЕН інший запит.
    time.sleep(2)       # ← вбиває весь сервер на 2s!
    return {
        "endpoint": "sync-broken",
        "warning": "BLOCKING in async def — cascade block!"
    }""",
    },
    "/sync-safe": {
        "color": "#f39c12",
        "verdict": "⚠️ ДОПУСТИМО — sync def → ThreadPoolExecutor",
        "why": (
            "FastAPI виявляє `def` (без `async`) і автоматично відправляє у ThreadPoolExecutor. "
            "Event Loop вільний, але масштаб обмежений ~40 потоками. "
            "Добре для legacy коду, не ідеально для high load."
        ),
        "code": """\
@app.get("/sync-safe")
def sync_safe():          # ← УВАГА: звичайна def, не async def!
    # FastAPI виявляє 'def' → запускає в окремому потоці (ThreadPoolExecutor).
    # Event Loop НЕ блокується.
    # Але: масштаб обмежений кількістю потоків (~40 за замовч.).
    time.sleep(2)
    return {
        "endpoint": "sync-safe",
        "message": "ThreadPoolExecutor — safe but limited scale"
    }""",
    },
    "/cpu-broken": {
        "color": "#c0392b",
        "verdict": "❌ НЕБЕЗПЕЧНО — CPU цикл без await у async def",
        "why": (
            "CPU-цикл без жодного `await` — Event Loop ніколи не отримує контроль. "
            "Весь сервер заморожений поки цикл виконується. "
            "Asyncio не допомагає для CPU-bound задач без `run_in_executor`."
        ),
        "code": """\
@app.get("/cpu-broken")
async def cpu_broken():
    # ❌ ПОМИЛКА: CPU-цикл без await — Event Loop заморожений!
    # Жоден await ніколи не виконається поки цей цикл не завершиться.
    total = 0
    for i in range(5_000_000):   # ~1-2s CPU роботи
        total += i * i            # ← нуль await → сервер мертвий
    return {"endpoint": "cpu-broken", "result": total}""",
    },
    "/cpu-fixed": {
        "color": "#27ae60",
        "verdict": "✅ ПРАВИЛЬНО — CPU у ProcessPoolExecutor",
        "why": (
            "`run_in_executor(ProcessPoolExecutor)` переносить CPU роботу в окремий **процес** "
            "(обходить GIL). Event Loop залишається вільним. "
            "Єдине правильне рішення для CPU-bound задач в asyncio."
        ),
        "code": """\
_process_pool = ProcessPoolExecutor(max_workers=os.cpu_count())

def _heavy_cpu_work():
    return sum(i * i for i in range(5_000_000))

@app.get("/cpu-fixed")
async def cpu_fixed():
    loop = asyncio.get_event_loop()
    # run_in_executor переносить блокуючий виклик в окремий процес.
    # await чекає результату — але Event Loop при цьому ВІЛЬНИЙ!
    result = await loop.run_in_executor(_process_pool, _heavy_cpu_work)
    return {"endpoint": "cpu-fixed", "result": result}""",
    },
    "/db-sync-broken/1": {
        "color": "#e74c3c",
        "verdict": "❌ НЕБЕЗПЕЧНО — синхронний DB драйвер у async def",
        "why": (
            "Синхронні DB драйвери (psycopg2, SQLAlchemy sync, sqlite3) "
            "роблять блокуючі мережеві виклики. "
            "В `async def` — вбивають Event Loop на час кожного SQL запиту."
        ),
        "code": """\
@app.get("/db-sync-broken/{user_id}")
async def db_sync_broken(user_id: int):
    # Симуляція синхронного DB драйвера (psycopg2):
    # conn = psycopg2.connect(...)   ← блокуючий TCP handshake
    # cursor.execute("SELECT ...")   ← блокуючий мережевий запит
    time.sleep(1)   # ← Event Loop заморожений під час кожного DB запиту!
    return {
        "user_id": user_id,
        "warning": "Sync DB in async def = cascade block"
    }""",
    },
    "/db-async-correct/1": {
        "color": "#2ecc71",
        "verdict": "✅ ПРАВИЛЬНО — asyncpg або run_in_executor",
        "why": (
            "Варіант 1: asyncpg — нативний async PostgreSQL драйвер. "
            "Варіант 2: `run_in_executor` для legacy sync бібліотек. "
            "В обох випадках Event Loop вільний під час I/O."
        ),
        "code": """\
@app.get("/db-async-correct/{user_id}")
async def db_async_correct(user_id: int):
    # Варіант 1 (рекомендований): asyncpg — нативний async
    # async with pool.acquire() as conn:
    #     row = await conn.fetchrow("SELECT * FROM users WHERE id=$1", user_id)

    # Варіант 2: run_in_executor для legacy sync бібліотек
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,                          # ThreadPoolExecutor (default)
        lambda: {"id": user_id}        # sync функція у потоці
    )
    return {"user_id": user_id, "message": "Async DB — Event Loop вільний"}""",
    },
}

ENDPOINT_TIMEOUT = 40.0  # секунди


# ── Структура результату ────────────────────────────────────────────────────────
@dataclass
class ReqResult:
    req_id: int
    endpoint: str
    status_code: int
    start_abs: float    # абсолютний час start (для Gantt)
    end_abs: float
    error: Optional[str] = None

    @property
    def elapsed(self): return self.end_abs - self.start_abs


# ── HTTP запит (синхронний) ─────────────────────────────────────────────────────
def make_request(host: str, endpoint: str, req_id: int, t_origin: float) -> ReqResult:
    """Один HTTP GET. Виконується у потоці ThreadPoolExecutor."""
    start = time.perf_counter()
    try:
        with httpx.Client(timeout=ENDPOINT_TIMEOUT) as client:
            resp = client.get(host + endpoint)
        return ReqResult(
            req_id=req_id,
            endpoint=endpoint,
            status_code=resp.status_code,
            start_abs=start - t_origin,
            end_abs=time.perf_counter() - t_origin,
        )
    except Exception as e:
        end = time.perf_counter()
        return ReqResult(
            req_id=req_id, endpoint=endpoint, status_code=0,
            start_abs=start - t_origin,
            end_abs=end - t_origin,
            error=str(e)[:60],
        )


# ── Concurrent benchmark ─────────────────────────────────────────────────────────
def run_benchmark(host: str, endpoint: str, n: int) -> list[ReqResult]:
    """Надсилає n запитів одночасно через ThreadPoolExecutor."""
    t_origin = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as pool:
        futures = [pool.submit(make_request, host, endpoint, i, t_origin) for i in range(n)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    results.sort(key=lambda r: r.req_id)
    return results


# ── Health Monitor ───────────────────────────────────────────────────────────────
class HealthMonitor:
    """Постійно пінгує /health в окремому потоці."""

    def __init__(self, host: str):
        self.host = host
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.history: list[dict] = []   # {"t": float, "ok": bool, "ms": float}
        self._lock = threading.Lock()

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            t0 = time.perf_counter()
            try:
                with httpx.Client(timeout=1.5) as c:
                    r = c.get(self.host + "/health")
                    ok = r.status_code == 200
            except Exception:
                ok = False
            ms = (time.perf_counter() - t0) * 1000
            with self._lock:
                self.history.append({"t": time.perf_counter(), "ok": ok, "ms": ms})
                if len(self.history) > 60:
                    self.history.pop(0)
            time.sleep(0.8)

    def get_history(self) -> list[dict]:
        with self._lock:
            return list(self.history)

    @property
    def last_status(self) -> tuple[bool, float]:
        with self._lock:
            if not self.history:
                return False, 0.0
            last = self.history[-1]
            return last["ok"], last["ms"]


# ── Gantt Chart ──────────────────────────────────────────────────────────────────
def build_gantt(results: list[ReqResult], title: str) -> go.Figure:
    if not results:
        return go.Figure()

    color = COLORS.get(results[0].endpoint, "#3498db")
    error_color = "#e74c3c"
    total_time = max(r.end_abs for r in results)

    fig = go.Figure()

    for r in results:
        c = error_color if r.error else color
        label = f"Req #{r.req_id+1}"
        hover = (
            f"<b>{label}</b><br>"
            f"Start: {r.start_abs:.3f}s<br>"
            f"End: {r.end_abs:.3f}s<br>"
            f"Duration: {r.elapsed:.3f}s<br>"
            f"Status: {r.status_code if not r.error else r.error}"
        )
        fig.add_trace(go.Bar(
            name=label,
            y=[label],
            x=[r.elapsed],
            base=[r.start_abs],
            orientation="h",
            marker_color=c,
            marker_line_width=1,
            marker_line_color="white",
            hovertemplate=hover + "<extra></extra>",
            showlegend=False,
        ))

    # Вертикальна лінія: очікуваний async час (~2s)
    fig.add_vline(x=2.0, line_dash="dash", line_color="gray", line_width=1,
                  annotation_text="async baseline (2s)", annotation_position="top right")

    fig.update_layout(
        title=dict(text=title, font_size=16),
        xaxis=dict(title="Час (секунди)", range=[0, max(total_time + 0.5, 3.5)]),
        yaxis=dict(title="Запит", autorange="reversed"),
        height=max(300, len(results) * 26 + 100),
        margin=dict(l=80, r=20, t=50, b=40),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#1a1d24",
        font_color="white",
        bargap=0.15,
        barmode="overlay",
    )
    return fig


def build_summary_bar(all_results: dict[str, list[ReqResult]]) -> go.Figure:
    """Стовпчиковий графік: середній час відповіді по ендпоінтах."""
    labels, avgs, colors_list, totals = [], [], [], []
    for label, results in all_results.items():
        if not results:
            continue
        ep = results[0].endpoint
        avgs.append(statistics.mean(r.elapsed for r in results))
        totals.append(max(r.end_abs for r in results))
        labels.append(label.split(" ", 1)[-1])   # прибираємо емоджі
        colors_list.append(COLORS.get(ep, "#3498db"))

    fig = go.Figure(go.Bar(
        x=labels, y=avgs,
        marker_color=colors_list,
        text=[f"{v:.2f}s" for v in avgs],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Avg latency: %{y:.3f}s<extra></extra>",
    ))
    fig.update_layout(
        title="Порівняння: середній час відповіді (менше = краще)",
        yaxis_title="Avg latency (s)",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#1a1d24",
        font_color="white",
        height=350,
        margin=dict(l=20, r=20, t=50, b=60),
    )
    fig.add_hline(y=2.0, line_dash="dot", line_color="gray",
                  annotation_text="baseline delay", annotation_position="right")
    return fig


def build_health_chart(history: list[dict]) -> go.Figure:
    if not history:
        return go.Figure()
    t0 = history[0]["t"]
    ts = [h["t"] - t0 for h in history]
    ms = [h["ms"] for h in history]
    ok = [h["ok"] for h in history]
    colors_list = ["#2ecc71" if o else "#e74c3c" for o in ok]

    fig = go.Figure(go.Bar(x=ts, y=ms, marker_color=colors_list, name="health ping"))
    fig.add_hline(y=200, line_dash="dash", line_color="orange",
                  annotation_text="200ms threshold")
    fig.update_layout(
        title="Health Monitor: /health response time (зелений=OK, червоний=frozen)",
        xaxis_title="Час (s)",
        yaxis_title="Response time (ms)",
        paper_bgcolor="#0e1117",
        plot_bgcolor="#1a1d24",
        font_color="white",
        height=220,
        showlegend=False,
        margin=dict(l=60, r=20, t=45, b=40),
    )
    return fig


# ── Streamlit App ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="FastAPI Concurrency Demo",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .big-metric { font-size: 2rem; font-weight: bold; text-align: center; }
    .frozen { color: #e74c3c; }
    .alive  { color: #2ecc71; }
    .warn   { color: #f39c12; }
    .info-box {
        background: #1a1d24; border-left: 4px solid #3498db;
        padding: 0.8rem 1rem; border-radius: 4px; margin: 0.5rem 0;
    }
    .danger-box {
        background: #2d1515; border-left: 4px solid #e74c3c;
        padding: 0.8rem 1rem; border-radius: 4px; margin: 0.5rem 0;
    }
    .success-box {
        background: #152d1a; border-left: 4px solid #2ecc71;
        padding: 0.8rem 1rem; border-radius: 4px; margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Налаштування")
    host = st.text_input("FastAPI host", value=DEFAULT_HOST)

    st.divider()
    st.subheader("🧪 Тест")
    endpoint_label = st.selectbox("Ендпоінт", list(ENDPOINTS.keys()), index=0)
    n_concurrent = st.slider("Одночасних запитів", 1, 200, 20)
    endpoint_path = ENDPOINTS[endpoint_label]

    st.divider()
    st.subheader("📊 Порівняння")
    compare_n = st.slider("N запитів для кожного", 5, 50, 10)

    st.divider()
    st.caption("🔗 Внутрішній: " + host)
    st.markdown(f"📖 **[Swagger UI →]({BROWSER_HOST}/docs)**")
    st.markdown(f"🔗 **[Health →]({BROWSER_HOST}/health)**")

# ── Health Monitor init ──────────────────────────────────────────────────────────
if "health_monitor" not in st.session_state:
    st.session_state.health_monitor = HealthMonitor(host)
    st.session_state.health_monitor.start()

if "all_results" not in st.session_state:
    st.session_state.all_results = {}

monitor = st.session_state.health_monitor

# ── Header ───────────────────────────────────────────────────────────────────────
st.title("⚡ FastAPI Concurrency — Live Demo")
st.caption("Навчальний інструмент: Async vs Blocking ендпоінти в реальному часі")

# ── Top Status Bar ───────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    is_ok, ping_ms = monitor.last_status
    status_color = "🟢" if is_ok else "🔴"
    st.metric("Сервер", f"{status_color} {'OK' if is_ok else 'FROZEN'}", f"{ping_ms:.0f}ms")

with col2:
    history = monitor.get_history()
    if history:
        recent = history[-10:]
        ok_rate = sum(1 for h in recent if h["ok"]) / len(recent) * 100
        st.metric("Health rate (останні 10)", f"{ok_rate:.0f}%",
                  delta=f"{ok_rate-100:.0f}%" if ok_rate < 100 else None)
    else:
        st.metric("Health rate", "—")

with col3:
    st.metric("Вибраний ендпоінт", endpoint_path)

with col4:
    st.metric("Concurrent запитів", n_concurrent)

st.divider()

# ── Tabs ─────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 Одиночний тест",
    "📊 Порівняння всіх",
    "🔍 Health Monitor",
    "📚 Пояснення",
])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1: Single Test
# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader(f"Тест: `{endpoint_path}` × {n_concurrent} concurrent")

    # Попередження для blocking ендпоінтів
    if "broken" in endpoint_path:
        st.markdown(
            f'<div class="danger-box">⛔ <b>Увага:</b> <code>{endpoint_path}</code> — '
            f'blocking ендпоінт. {n_concurrent} запитів займуть ~<b>{n_concurrent * 2}s</b> '
            f'(cascade block). Health monitor покаже server frozen.</div>',
            unsafe_allow_html=True,
        )
    elif "correct" in endpoint_path or "fixed" in endpoint_path:
        st.markdown(
            f'<div class="success-box">✅ <code>{endpoint_path}</code> — '
            f'async ендпоінт. {n_concurrent} запитів займуть ~<b>2s</b> незалежно від n.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="info-box">⚠️ <code>{endpoint_path}</code> — '
            f'sync def (threadpool). Масштаб обмежений ~40 потоками.</div>',
            unsafe_allow_html=True,
        )

    # ── Код ендпоінту ────────────────────────────────────────────────────────────
    ep_key = endpoint_path if endpoint_path in ENDPOINT_INFO else endpoint_path.rsplit("/", 1)[0] + "/1"
    info = ENDPOINT_INFO.get(ep_key) or ENDPOINT_INFO.get(endpoint_path, {})
    if info:
        with st.expander(f"📖 Код FastAPI ендпоінту: `{endpoint_path}`", expanded=True):
            c_left, c_right = st.columns([3, 2])
            with c_left:
                st.code(info["code"], language="python")
            with c_right:
                verdict_color = info["color"]
                st.markdown(
                    f'<div style="border-left:4px solid {verdict_color};padding:0.7rem 1rem;'
                    f'background:#1a1d24;border-radius:4px;margin-bottom:0.5rem;">'
                    f'<b>{info["verdict"]}</b></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(info["why"])

    run_btn = st.button("▶  Запустити тест", type="primary", use_container_width=True)

    if run_btn:
        progress = st.progress(0, text="Надсилаємо запити...")
        status_ph = st.empty()

        # Запускаємо в окремому потоці щоб не блокувати Streamlit UI
        result_holder = {}

        def _run():
            result_holder["results"] = run_benchmark(host, endpoint_path, n_concurrent)

        t = threading.Thread(target=_run)
        t0_wall = time.time()
        t.start()

        while t.is_alive():
            elapsed = time.time() - t0_wall
            expected = 2.5 if ("correct" in endpoint_path or "fixed" in endpoint_path) else n_concurrent * 2.1
            pct = max(0, min(int(elapsed / expected * 100), 95))
            progress.progress(pct, text=f"⏳ Виконується... {elapsed:.1f}s")
            time.sleep(0.3)

        t.join()
        progress.progress(100, text="✅ Завершено!")

        results = result_holder["results"]
        st.session_state.all_results[endpoint_label] = results

        total_time = max(r.end_abs for r in results)
        ok_count = sum(1 for r in results if r.status_code == 200)
        avg_lat = statistics.mean(r.elapsed for r in results)
        p95_lat = sorted(r.elapsed for r in results)[int(len(results) * 0.95)]

        # Метрики
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Загальний час", f"{total_time:.2f}s",
                   delta=f"{total_time-2:.2f}s vs async baseline",
                   delta_color="inverse")
        mc2.metric("Успішних", f"{ok_count}/{n_concurrent}")
        mc3.metric("Avg latency", f"{avg_lat:.2f}s")
        mc4.metric("P95 latency", f"{p95_lat:.2f}s")

        # Висновок
        if total_time > n_concurrent * 1.5 and "broken" in endpoint_path:
            st.error(
                f"❌ **Cascade Block підтверджено!** {n_concurrent} запитів × ~2s = **{total_time:.1f}s** "
                f"(замість ~2s якби це був async). Сервер обслуговував їх ПОСЛІДОВНО."
            )
        elif total_time < 3.5:
            st.success(
                f"✅ **Async працює!** {n_concurrent} запитів виконані за **{total_time:.2f}s** "
                f"(майже як один запит). Event Loop обслуговував їх ОДНОЧАСНО."
            )
        else:
            st.warning(f"⚠️ Час: {total_time:.2f}s для {n_concurrent} запитів")

        # Gantt chart
        fig = build_gantt(
            results,
            f"Gantt: {n_concurrent} одночасних запитів → {endpoint_path}  (total: {total_time:.2f}s)"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Таблиця
        with st.expander("📋 Детальні результати"):
            for r in results[:30]:
                icon = "✅" if r.status_code == 200 else "❌"
                st.text(f"{icon} Req #{r.req_id+1:3d}  start={r.start_abs:.3f}s  "
                        f"end={r.end_abs:.3f}s  elapsed={r.elapsed:.3f}s  "
                        f"status={r.status_code if not r.error else r.error}")
            if len(results) > 30:
                st.caption(f"... ще {len(results)-30} запитів")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2: Compare All
# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader(f"Порівняння всіх ендпоінтів × {compare_n} concurrent")

    compare_selection = st.multiselect(
        "Оберіть ендпоінти для порівняння:",
        list(ENDPOINTS.keys()),
        default=[
            "✅ async-correct",
            "❌ sync-broken",
            "⚠️  sync-safe (def)",
        ],
    )

    compare_btn = st.button("▶  Запустити порівняння", type="primary", use_container_width=True)

    if compare_btn and compare_selection:
        compare_results = {}
        progress_bar = st.progress(0, "Порівняння...")

        for idx, label in enumerate(compare_selection):
            ep = ENDPOINTS[label]
            pct_start = int(idx / len(compare_selection) * 100)
            progress_bar.progress(pct_start, text=f"Тестуємо {ep}...")
            compare_results[label] = run_benchmark(host, ep, compare_n)
            progress_bar.progress(pct_start + int(1/len(compare_selection)*90))

        progress_bar.progress(100, "✅ Готово!")
        st.session_state.all_results.update(compare_results)

        # Summary bar chart
        st.plotly_chart(build_summary_bar(compare_results), use_container_width=True)

        # Підсумкова таблиця
        st.subheader("📊 Результати")
        cols = st.columns(len(compare_results))
        for col, (label, results) in zip(cols, compare_results.items()):
            total = max(r.end_abs for r in results)
            avg = statistics.mean(r.elapsed for r in results)
            ok = sum(1 for r in results if r.status_code == 200)
            throughput = ok / total if total else 0
            ep = results[0].endpoint

            is_blocking = "broken" in ep
            col.metric(
                label=label.split(" ", 1)[-1],
                value=f"{total:.2f}s",
                delta=f"{avg:.2f}s avg | {throughput:.1f} req/s",
                delta_color="inverse" if is_blocking else "normal",
            )

        # Gantt для кожного
        for label, results in compare_results.items():
            with st.expander(f"Gantt: {label}", expanded=False):
                total = max(r.end_abs for r in results)
                fig = build_gantt(results, f"{label} — {compare_n} concurrent ({total:.2f}s)")
                st.plotly_chart(fig, use_container_width=True)

    elif st.session_state.all_results:
        st.plotly_chart(build_summary_bar(st.session_state.all_results), use_container_width=True)
    else:
        st.info("Натисни 'Запустити порівняння' щоб побачити результати.")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3: Health Monitor
# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("🔍 Live Health Monitor — /health")
    st.caption("Пінгує сервер кожні 0.8с. Показує чи Event Loop живий під час тестів.")

    col_a, col_b = st.columns([2, 1])
    with col_a:
        history_chart_ph = st.empty()
    with col_b:
        st.markdown("**Легенда:**")
        st.markdown("🟢 Зелений = сервер відповів < 200ms")
        st.markdown("🔴 Червоний = сервер не відповів (Event Loop frozen)")
        st.markdown("---")
        st.markdown("**Що спостерігати:**")
        st.markdown("1. Запусти `/sync-broken` тест з Tab 1")
        st.markdown("2. Повернись сюди — побачиш червоні стовпці")
        st.markdown("3. Запусти `/async-correct` — все зелене")

    refresh_ph = st.empty()
    auto_refresh = st.toggle("🔄 Авто-оновлення (кожні 2s)", value=False)

    if auto_refresh:
        history = monitor.get_history()
        history_chart_ph.plotly_chart(build_health_chart(history), use_container_width=True)
        time.sleep(2)
        st.rerun()
    else:
        if st.button("🔄 Оновити графік"):
            history = monitor.get_history()
            history_chart_ph.plotly_chart(build_health_chart(history), use_container_width=True)

    history = monitor.get_history()
    if history:
        history_chart_ph.plotly_chart(build_health_chart(history), use_container_width=True)
        slow = sum(1 for h in history if h["ms"] > 200)
        failed = sum(1 for h in history if not h["ok"])
        if failed > 0:
            st.error(f"⛔ {failed} health ping(s) не отримали відповідь — сервер був заморожений!")
        elif slow > 0:
            st.warning(f"⚠️ {slow} health ping(s) відповіли > 200ms — Event Loop завантажений")
        else:
            st.success("✅ Сервер завжди відповідав < 200ms — Event Loop вільний")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 4: Explanation
# ════════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("📚 Пояснення: код кожного ендпоінту та чому так")

    st.markdown("""
### Як читати Gantt-чарт

| Вигляд | Що означає |
|--------|-----------|
| Всі рядки рівні, закінчуються одночасно | ✅ Async — Event Loop паралельно |
| Рядки йдуть сходинками один за одним | ❌ Cascade block — сервер послідовний |
| Частина коротка, частина довга | ⚠️ Threadpool — обмежено N потоками |
""")

    st.markdown("---")
    st.subheader("Код та аналіз кожного ендпоінту")

    for ep_path, info in ENDPOINT_INFO.items():
        display_path = ep_path.replace("/1", "/{id}")
        with st.expander(f"{info['verdict']}  →  `{display_path}`", expanded=False):
            col_code, col_explain = st.columns([3, 2])
            with col_code:
                st.code(info["code"], language="python")
            with col_explain:
                st.markdown(
                    f'<div style="border-left:4px solid {info["color"]};padding:0.7rem 1rem;'
                    f'background:#1a1d24;border-radius:4px;margin-bottom:1rem;">'
                    f'<b>{info["verdict"]}</b></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(info["why"])

    st.markdown("---")
    st.markdown("""
### Cascade Block — математика

```
/sync-broken × 10 concurrent:
  Запит #1:  [████████] 2s  → відповів
  Запит #2:       [████████] 2s  → сервер зміг взяти ТІЛЬКИ ПІСЛЯ #1
  Запит #3:            [████████] 2s
  ...
  Запит #10:                              [████████] 2s
  TOTAL: 20s  (не 2s як очікувалось!)
```

### Async — Event Loop

```
/async-correct × 10 concurrent:
  Запит #1:  [████████] 2s  ←┐
  Запит #2:  [████████] 2s  ← Event Loop обробляє всі одночасно
  Запит #3:  [████████] 2s  ←┘  (await передає контроль між ними)
  ...
  Запит #10: [████████] 2s
  TOTAL: ~2s  (всі завершились майже одночасно!)
```

### Золоте правило

> `await asyncio.sleep(2)` → Event Loop: "я чекаю, обслугови інших"
>
> `time.sleep(2)` → OS: "заморожуй весь Python thread на 2s"
>
> **Будь-який blocking виклик в `async def` без `await` = `time.sleep()`**
""")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("FastAPI Concurrency Demo · Урок 34 — Asyncio · Module 4")
st.caption(f"Internal API: {host}  |  Browser: {BROWSER_HOST}  |  Swagger UI: {BROWSER_HOST}/docs")
