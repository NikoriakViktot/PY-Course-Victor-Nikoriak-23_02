"""
app.py — Taxi Big-O Lab  (Production Refactor)
================================================
Data layer:  DuckDB VIEW (lazy, 3M rows never in RAM)
Sample layer: pandas (only n rows in memory)
Algo layer:  pure Python loops (Big-O demonstration)
SQL layer:   DuckDB queries on full VIEW (performance comparison)

Run:  streamlit run app.py
"""
from __future__ import annotations

import math
import time

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from algorithms import (
    ALL_ALGO_LABELS,
    ALGO_META,
    MAX_N_QUADRATIC,
    binary_search,
    build_hash_index,
    estimate_algo_memory_gb,
    estimate_memory_bytes,
    hash_index_lookup,
    linear_scan,
    nested_loop,
    nested_optimized_set,
    pandas_filter_count,
    prepare_sorted_distances,
)
from data_loader import (
    dataset_summary,
    duckdb_count_on_view,
    estimate_load_gb,
    get_dataset_stats,
    get_duckdb_connection,
    load_full_dataset,
    sample_from_view,
)
from metrics import (
    MemoryGuardError,
    TimedResult,
    estimate_dataframe_gb,
    get_memory_usage_gb,
    time_measure,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Taxi Big-O Lab",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATASET_SIZES        = [1_000, 5_000, 10_000, 50_000, 100_000]
CHART_SIZES          = [500, 1_000, 3_000, 5_000, 10_000, 25_000, 50_000]
PAYMENT_LOOKUP_TARGET = "Cash"
BINARY_DEFAULT_THRESHOLD = 3.0


# ===========================================================================
# SECTION 1 — Header
# ===========================================================================

def render_header() -> None:
    st.title("🚕 Taxi Big-O Lab")
    st.markdown(
        """
        Інтерактивна демонстрація **алгоритмічної складності (Big-O)**
        на реальних даних NYC TLC Yellow Taxi 2023 (~3 млн рядків).

        > **Архітектура:**  DuckDB VIEW (lazy) → SQL SAMPLE → pandas (n рядків)
        > → Python loop (Big-O demo)
        """
    )


# ===========================================================================
# SECTION 2 — Data Connection & Stats
# ===========================================================================

_FALLBACK_STATS: dict = {
    "total_rows": 3_000_000,
    "cash_count": 0,
    "card_count": 0,
    "avg_distance": 0.0,
    "max_distance": 0.0,
    "unique_pu_zones": 0,
    "unique_do_zones": 0,
}


def render_data_section(con) -> dict:
    """
    Show dataset statistics via SQL aggregation.
    The FULL dataset stays in DuckDB — never touches Python RAM.

    Returns _FALLBACK_STATS on network error so the rest of the app can run.
    """
    with st.expander("📊 Датасет NYC TLC 2023-01 (статистика через DuckDB)", expanded=False):
        with st.spinner("Отримуємо статистику через DuckDB SQL…"):
            try:
                stats = get_dataset_stats(con)
            except Exception as exc:
                st.error(
                    "🌐 **Не вдалося отримати статистику з remote parquet.**\n\n"
                    f"`{type(exc).__name__}: {exc}`\n\n"
                    "Перевір інтернет-з'єднання. Алгоритмічний розділ залишається "
                    "доступним — дані будуть завантажені при першому SAMPLE-запиті."
                )
                return _FALLBACK_STATS

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Рядків у VIEW",  f"{stats['total_rows']:,}")
        c2.metric("Cash поїздок",   f"{stats['cash_count']:,}")
        c3.metric("Card поїздок",   f"{stats['card_count']:,}")
        c4.metric("Сер. дистанція", f"{stats['avg_distance']:.2f} км")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Макс. дистанція", f"{stats['max_distance']:.1f} км")
        c6.metric("Зон pickup",      stats["unique_pu_zones"])
        c7.metric("Зон dropoff",     stats["unique_do_zones"])
        c8.metric("Джерело",         "NYC TLC 2023-01")

        st.info(
            "💡 **Ці числа отримані без завантаження 3M рядків в RAM.** "
            "DuckDB виконав `SELECT COUNT(*), AVG(…)` безпосередньо над parquet-файлом "
            "через колонкове читання + predicate pushdown."
        )
    return stats


# ===========================================================================
# SECTION 3 — Sidebar Controls
# ===========================================================================

def render_sidebar_controls(
    total_n: int,
) -> tuple[int, str, float, bool, float]:
    """
    Returns
    -------
    n               : int    — sample size (rows to load into pandas)
    algo_label      : str    — selected algorithm label
    threshold       : float  — binary-search distance threshold
    full_mode       : bool   — True = load ALL rows into pandas RAM
    memory_limit_gb : float  — user-set RAM hard limit (GB)
    """
    with st.sidebar:
        st.header("⚙️ Параметри")

        # ── Dataset mode toggle ────────────────────────────────────────────
        st.markdown("**Режим датасету**")
        full_mode = st.toggle(
            "🗄️ Full dataset mode",
            value=False,
            help=(
                "Sample mode: лише n рядків у RAM (безпечно).\n"
                "Full mode: ВСІ ~3M рядків у pandas RAM — потрібно ≥2 GB RAM."
            ),
        )
        if full_mode:
            st.warning(
                "⚠️ Full dataset mode завантажує **всі ~3M рядків** у RAM. "
                "Переконайся, що пам'яті достатньо."
            )

        st.divider()

        # ── Sample size (only relevant in sample mode) ─────────────────────
        if not full_mode:
            st.markdown("**Розмір вибірки (n)**")
            available = [s for s in DATASET_SIZES if s <= total_n]
            n = st.select_slider(
                "n",
                options=available,
                value=available[min(2, len(available) - 1)],
                label_visibility="collapsed",
            )
            st.caption(
                f"Завантажується {n:,} рядків з ~{total_n:,} у VIEW  \n"
                f"(решта {total_n - n:,} залишаються в DuckDB)"
            )
        else:
            n = total_n
            est_gb = estimate_load_gb(total_n)
            st.info(f"📦 Повний датасет: ~{total_n:,} рядків · ≈{est_gb:.1f} GB RAM")

        st.divider()

        # ── Memory limit slider ────────────────────────────────────────────
        st.markdown("**RAM ліміт (GB)**")
        memory_limit_gb = st.slider(
            "RAM limit GB",
            min_value=1,
            max_value=16,
            value=8,
            step=1,
            label_visibility="collapsed",
            help="Жорстке обмеження оперативної пам'яті. "
                 "При перевищенні операцію буде скасовано.",
        )
        current_gb = get_memory_usage_gb()
        pct = current_gb / memory_limit_gb * 100
        color = "🟢" if pct < 60 else ("🟡" if pct < 85 else "🔴")
        st.caption(
            f"{color} Поточне використання: **{current_gb:.2f} GB** / "
            f"{memory_limit_gb} GB  ({pct:.0f}%)"
        )

        st.divider()

        # ── Algorithm selector ─────────────────────────────────────────────
        st.markdown("**Алгоритм**")
        algo_label = st.selectbox("algo", ALL_ALGO_LABELS, label_visibility="collapsed")

        threshold = BINARY_DEFAULT_THRESHOLD
        if "binary" in algo_label.lower():
            st.divider()
            st.markdown("**Поріг дистанції**")
            threshold = st.slider(
                "trip_distance >", min_value=0.1, max_value=20.0,
                value=BINARY_DEFAULT_THRESHOLD, step=0.1,
            )

        st.divider()
        mode_label = "FULL (~3M рядків)" if full_mode else f"{n:,} рядків"
        st.markdown(
            "**Шари архітектури**\n\n"
            "```\n"
            "DuckDB VIEW  ← 3M рядків (lazy)\n"
            "     ↓ SQL SAMPLE\n"
            f"pandas df    ← {mode_label}\n"
            "     ↓ Python loops\n"
            "Algorithm    ← Big-O demo\n"
            "```"
        )

    return n, algo_label, threshold, full_mode, float(memory_limit_gb)


# ===========================================================================
# SECTION 4 — Algorithm Runner
# ===========================================================================

def render_result_card(
    result: TimedResult, algo_key: str, n: int, extra_info: str = ""
) -> None:
    meta = ALGO_META[algo_key]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Складність",   meta.notation)
    c2.metric("n (рядків)",   f"{n:,}")
    c3.metric("Результат",    f"{result.value:,}")
    c4.metric("Час",          f"{result.elapsed_ms:.3f} мс")
    if result.op_count:
        st.caption(f"Операцій: **{result.op_count:,}**")
    if extra_info:
        st.info(extra_info)
    with st.expander("📖 Пояснення"):
        st.markdown(meta.long_desc)


def run_algorithm(algo_label: str, df: pd.DataFrame, threshold: float) -> None:
    algo_key = next(k for k, m in ALGO_META.items() if m.label == algo_label)
    meta = ALGO_META[algo_key]
    n = len(df)

    if n > meta.safe_max_n:
        st.warning(f"⚠️ n={n:,} > безпечного порогу {meta.safe_max_n:,} для {meta.notation}")

    if algo_key == "linear":
        result = time_measure(linear_scan, df, PAYMENT_LOOKUP_TARGET)
        render_result_card(result, algo_key, n,
            f"Перевірено кожен з {result.op_count:,} рядків по черзі (Python `for` loop).")

    elif algo_key == "hash":
        build = time_measure(build_hash_index, df)
        index = build.value
        lookup = time_measure(hash_index_lookup, index, PAYMENT_LOOKUP_TARGET)
        render_result_card(lookup, algo_key, n,
            f"Побудова індексу (O(n)): {build.elapsed_ms:.2f} мс.  "
            f"Пошук (O(1)): {lookup.elapsed_ms:.4f} мс.")
        col1, col2 = st.columns(2)
        col1.metric("🔨 Build O(n)", f"{build.elapsed_ms:.2f} мс")
        col2.metric("🔍 Lookup O(1)", f"{lookup.elapsed_ms:.4f} мс")

    elif algo_key == "binary":
        sort_r = time_measure(prepare_sorted_distances, df)
        sorted_d = sort_r.value
        search  = time_measure(binary_search, sorted_d, threshold)
        count, steps = search.value, search.op_count
        max_steps = math.ceil(math.log2(n)) if n > 1 else 1
        render_result_card(
            TimedResult(value=count, elapsed_ms=search.elapsed_ms, op_count=steps),
            algo_key, n,
            f"Дистанція > {threshold} км: **{count:,}** поїздок.  "
            f"Максимум кроків: log₂({n:,}) ≈ **{max_steps}** (замість {n:,}!).  "
            f"Сортування: {sort_r.elapsed_ms:.2f} мс."
        )

    elif algo_key == "quadratic":
        actual_n = min(n, MAX_N_QUADRATIC)
        if actual_n < n:
            st.warning(
                f"🔴 O(n²) обмежено до **{actual_n:,}** рядків. "
                f"{actual_n:,}² = {actual_n**2:,} операцій!")
        r = time_measure(nested_loop, df, actual_n)
        match_count, ops = r.value, r.op_count
        render_result_card(
            TimedResult(value=match_count, elapsed_ms=r.elapsed_ms, op_count=ops),
            algo_key, actual_n,
            f"Знайдено {match_count:,} пар. Виконано {ops:,} = {actual_n:,}² порівнянь."
        )


# ===========================================================================
# SECTION 5 — Educational Block
# ===========================================================================

# ── Code snippets for each algorithm ────────────────────────────────────────

_CODE_LINEAR = """\
def linear_scan(df, target="Cash"):
    count = 0
    ops   = 0
    values = df['payment_type'].tolist()

    for val in values:      # ← O(n): один прохід по n елементах
        ops   += 1          #   кожен елемент = 1 порівняння
        if val == target:
            count += 1

    return count, ops

# ┌──────────────────────────────────────────────────────────┐
# │  n =  10,000  →  10,000 порівнянь                       │
# │  n =  50,000  →  50,000 порівнянь  (×5)                 │
# │  n = 100,000  → 100,000 порівнянь  (×10)                │
# └──────────────────────────────────────────────────────────┘
"""

_CODE_HASH = """\
# КРОК 1: O(n) — будуємо хеш-таблицю ОДИН РАЗ
def build_hash_index(df):
    index = {}
    for i, val in enumerate(df['payment_type']):
        if val not in index:
            index[val] = []
        index[val].append(i)       # dict: hash(key) → адреса → список індексів
    return index

# КРОК 2: O(1) — пошук за будь-яким ключем
def hash_index_lookup(index, key="Cash"):
    return len(index.get(key, []))
    # ↑ hash("Cash") → адреса комірки → значення
    # 1 операція незалежно від розміру index!

# ┌──────────────────────────────────────────────────────────┐
# │  Build:  n=100,000  → 100,000 операцій (ОДИН РАЗ)       │
# │  Lookup: n=1        →       1 операція (ЗАВЖДИ!)         │
# │  Lookup: n=100,000  →       1 операція (ЗАВЖДИ!)         │
# └──────────────────────────────────────────────────────────┘
"""

_CODE_BINARY = """\
import bisect

# КРОК 1: O(n log n) — сортуємо ОДИН РАЗ
def prepare_sorted_distances(df):
    distances = df['trip_distance'].tolist()
    distances.sort()                 # Timsort: O(n log n)
    return distances

# КРОК 2: O(log n) — бінарний пошук
def binary_search(sorted_distances, threshold=3.0):
    # bisect_right: позиція ПІСЛЯ всіх елементів ≤ threshold
    idx   = bisect.bisect_right(sorted_distances, threshold)
    count = len(sorted_distances) - idx
    return count, ceil(log2(len(sorted_distances)))

# ┌────────────────────────────────────────────────────────────┐
# │  Принцип: кожен крок відкидає ПОЛОВИНУ простору пошуку    │
# │  n =   1,000 → max  10 кроків  (log₂ 1,000  ≈ 10)        │
# │  n = 100,000 → max  17 кроків  (log₂ 100,000 ≈ 17)       │
# │  n = 3,000,000 → max 22 кроки  (log₂ 3M     ≈ 22)        │
# └────────────────────────────────────────────────────────────┘
"""

_CODE_QUADRATIC = """\
def nested_loop(df, max_n=3000):
    actual_n = min(len(df), max_n)
    pickup   = df['PULocationID'].iloc[:actual_n].tolist()
    dropoff  = df['DOLocationID'].iloc[:actual_n].tolist()

    match_count = 0
    ops = 0

    for i in range(actual_n):        # ← зовнішній цикл: n ітерацій
        for j in range(actual_n):    # ← внутрішній цикл: n ітерацій КОЖЕН РАЗ
            ops += 1                 #   разом: n × n = n² порівнянь!
            if i != j and pickup[i] == dropoff[j]:
                match_count += 1

    return match_count, ops

# ┌──────────────────────────────────────────────────────────────┐
# │  n =   500  →       250,000 операцій                        │
# │  n = 1,000  →     1,000,000 операцій  (×4 відносно n=500)   │
# │  n = 2,000  →     4,000,000 операцій  (×16 відносно n=500!) │
# │  n = 3,000  →     9,000,000 операцій  (×36!)                │
# └──────────────────────────────────────────────────────────────┘
"""

# ── Before/After: O(n²) антипатерн → O(n) виправлення ────────────────────

_CODE_ANTIPATTERN_SLOW = """\
# ❌ АНТИПАТЕРН: O(n × m) — list 'in' всередині циклу
def find_cash_trips_SLOW(pickup_zones, cash_zone_list):
    result = []
    for zone in pickup_zones:          # O(n) — зовнішній цикл
        if zone in cash_zone_list:     # O(m) — ЛІНІЙНИЙ пошук по списку!
            result.append(zone)        # Разом: O(n × m)
    return result

# Якщо n=10,000 і m=10,000:
# → 10,000 × 10,000 = 100,000,000 порівнянь 💥
"""

_CODE_ANTIPATTERN_FAST = """\
# ✅ ВИПРАВЛЕННЯ: O(n + m) — конвертуємо список у set
def find_cash_trips_FAST(pickup_zones, cash_zone_list):
    cash_set = set(cash_zone_list)     # O(m) — будуємо хеш-таблицю ОДИН РАЗ
    result = []
    for zone in pickup_zones:          # O(n) — зовнішній цикл
        if zone in cash_set:           # O(1) — хеш-пошук!
            result.append(zone)        # Разом: O(n + m)
    return result

# Якщо n=10,000 і m=10,000:
# → 10,000 + 10,000 = 20,000 операцій ✅
# Прискорення: 100,000,000 / 20,000 = 5,000x 🚀
"""

_CODE_DEDUP_SLOW = """\
# ❌ АНТИПАТЕРН: O(n²) — вкладені цикли для пошуку дублікатів
def has_duplicate_SLOW(data):
    n = len(data)
    for i in range(n):               # O(n)
        for j in range(i + 1, n):    # O(n) для кожного i
            if data[i] == data[j]:   # → O(n²) загалом
                return True
    return False
"""

_CODE_DEDUP_FAST = """\
# ✅ ВИПРАВЛЕННЯ: O(n) — хеш-множина (set)
def has_duplicate_FAST(data):
    seen = set()               # хеш-таблиця: O(1) для кожної операції
    for item in data:          # O(n) — один прохід
        if item in seen:       # O(1) — хеш → адреса → перевірка
            return True
        seen.add(item)         # O(1) — хеш → адреса → вставка
    return False               # n ітерацій × O(1) = O(n) 🚀
"""


def _benchmark_antipattern(data_a: list, data_b: list) -> tuple[float, float, int, int]:
    """Run both slow (O(n×m)) and fast (O(n+m)) implementations and return timings."""

    # ── Slow: O(n × m) ────────────────────────────────────────────────────
    def slow(zones_a, zones_b):
        result = []
        for z in zones_a:
            if z in zones_b:      # O(m) list scan
                result.append(z)
        return len(result)

    # ── Fast: O(n + m) ────────────────────────────────────────────────────
    def fast(zones_a, zones_b):
        s = set(zones_b)          # O(m) once
        return sum(1 for z in zones_a if z in s)  # O(n) × O(1)

    start = time.perf_counter()
    count_slow = slow(data_a, data_b)
    t_slow = (time.perf_counter() - start) * 1_000

    start = time.perf_counter()
    count_fast = fast(data_a, data_b)
    t_fast = (time.perf_counter() - start) * 1_000

    return t_slow, t_fast, count_slow, count_fast


def render_educational_section(df: pd.DataFrame, algo_key: str, n: int) -> None:
    """
    6-вкладковий навчальний блок:
      🔬 Реалізації   — кілька реалізацій одного алгоритму
      ❌ Антипатерни  — типові помилки + виправлення
      ✅ Патерни      — правильні шаблони
      📊 Операції     — формула + таблиця зростання + живий вимір
      💾 Памʼять      — оцінка RAM + порівняння структур даних
      ⚙️ Під капотом  — Python internals (dynamic array, hash table, bisect)
    """
    st.subheader("📚 Big-O: Глибокий Аналіз")

    meta = ALGO_META[algo_key]

    tab_impl, tab_anti, tab_good, tab_ops, tab_mem, tab_hood = st.tabs([
        "🔬 Реалізації",
        "❌ Антипатерни",
        "✅ Патерни",
        "📊 Операції",
        "💾 Памʼять",
        "⚙️ Під капотом",
    ])

    # =========================================================================
    # Вкладка 1: 🔬 Реалізації
    # =========================================================================
    with tab_impl:
        st.markdown(
            f"### {meta.badge} `{meta.notation}` — {meta.label}\n\n"
            f"{meta.long_desc}"
        )
        st.divider()
        st.markdown(
            f"**📌 Формула:** `{meta.formula}`\n\n"
            f"{meta.formula_explanation}"
        )
        st.divider()
        st.markdown("#### Кілька реалізацій одного алгоритму")
        st.caption(
            "Всі варіанти мають однакову Big-O складність, але різняться "
            "читабельністю, використанням памʼяті та реальним часом."
        )

        for impl in meta.implementations:
            badge = "✅" if impl.is_recommended else "⚠️"
            with st.expander(f"{badge} **{impl.name}** — `{impl.complexity}`", expanded=True):
                st.markdown(impl.description)
                st.code(impl.code, language="python")

    # =========================================================================
    # Вкладка 2: ❌ Антипатерни
    # =========================================================================
    with tab_anti:
        st.markdown(
            f"### ❌ Антипатерни — як НЕ треба писати `{meta.notation}` код\n\n"
            "Антипатерн — це код, який **виглядає нешкідливо**, але "
            "приховує дорогу операцію або неправильну складність."
        )

        for i, ap in enumerate(meta.anti_patterns, 1):
            st.divider()
            st.markdown(f"#### Антипатерн {i}: {ap.title}")

            col_bad, col_good = st.columns(2)
            with col_bad:
                st.markdown("**❌ НЕПРАВИЛЬНО**")
                st.code(ap.bad_code, language="python")
                st.error(ap.why_bad)

            with col_good:
                st.markdown("**✅ ВИПРАВЛЕННЯ**")
                st.code(ap.fix_code, language="python")
                st.success(ap.why_good)

        st.divider()

        # Живий бенчмарк: O(n×m) list vs O(n+m) set
        st.markdown("#### 🏃 Живий бенчмарк: list vs set у циклі")
        bench_n = min(n, 8_000)
        zones_a = df["PULocationID"].tolist()[:bench_n]
        zones_b = df["DOLocationID"].tolist()[:bench_n]

        if st.button(f"▶ Запустити: O(n×m) list vs O(n+m) set  (n={bench_n:,})"):
            with st.spinner("Запускаємо обидві версії…"):
                t_slow, t_fast, cnt_slow, cnt_fast = _benchmark_antipattern(
                    zones_a, zones_b
                )
            speedup = t_slow / t_fast if t_fast > 0 else 0

            c1, c2, c3 = st.columns(3)
            c1.metric("❌ O(n×m) list", f"{t_slow:.1f} мс",
                      f"{bench_n * bench_n:,} порівнянь")
            c2.metric("✅ O(n+m) set", f"{t_fast:.2f} мс",
                      f"{bench_n * 2:,} операцій")
            c3.metric("🚀 Прискорення", f"{speedup:.0f}×")

            fig = go.Figure(go.Bar(
                x=["❌ list  O(n×m)", "✅ set  O(n+m)"],
                y=[t_slow, t_fast],
                marker_color=["#ef4444", "#10b981"],
                text=[f"{t_slow:.1f} мс", f"{t_fast:.3f} мс"],
                textposition="outside",
            ))
            fig.update_layout(
                title=f"list vs set при n={bench_n:,}",
                yaxis_title="мс (менше = краще)",
                template="plotly_dark", height=300,
            )
            st.plotly_chart(fig, width='stretch')
            st.success(
                f"**{speedup:.0f}×** прискорення лише від заміни `list` на `set`. "
                f"Операцій: {bench_n**2:,} → {bench_n*2:,}"
            )

    # =========================================================================
    # Вкладка 3: ✅ Патерни
    # =========================================================================
    with tab_good:
        st.markdown(
            f"### ✅ Правильні патерни для `{meta.notation}`\n\n"
            "Ці шаблони гарантують оптимальну складність і читабельність."
        )

        for gp in meta.good_patterns:
            with st.expander(
                f"✅ **{gp.title}** — `{gp.complexity}`", expanded=True
            ):
                st.markdown(gp.description)
                st.code(gp.code, language="python")

        st.divider()
        st.markdown("#### 📋 Загальна таблиця: коли що використовувати")
        st.markdown(
            """
            | Задача | Структура | Складність |
            |---|---|---|
            | Перебір усіх елементів | `for val in list` | O(n) |
            | Перевірка наявності | `val in set` | O(1) |
            | Підрахунок частот | `Counter(data)` | O(n) build, O(1) query |
            | Lookup за ключем | `dict[key]` | O(1) |
            | Range query на sorted | `bisect.bisect_right` | O(log n) |
            | Дублікати | `seen = set()` | O(n) |
            | Унікальні значення | `set(data)` | O(n) |
            | Картезіанський добуток | nested loops | O(n²) — уникати! |

            **Золоте правило:** якщо всередині циклу є `in list` або `list.index()` →
            замінити на `set` або `dict`.
            """
        )

        st.divider()
        st.markdown("#### while vs for — коли що використовувати")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**`for` — рекомендовано для більшості випадків**")
            st.code(
                "# ✅ for: читабельно, Pythonic\n"
                "for val in data:           # step = 1, auto\n"
                "    process(val)\n\n"
                "# ✅ for з enumerate:\n"
                "for i, val in enumerate(data):\n"
                "    print(i, val)",
                language="python",
            )
            st.success(
                "for loop: автоматичний крок, менше помилок з індексами, "
                "читабельніше. Python оптимізує for loop на рівні байт-коду."
            )
        with col2:
            st.markdown("**`while` — коли потрібен нестандартний крок або умова**")
            st.code(
                "# ✅ while: нестандартний крок\n"
                "i = 0\n"
                "while i < len(data):\n"
                "    process(data[i])\n"
                "    i += 2           # крок = 2\n\n"
                "# ✅ while: не відомо скільки ітерацій\n"
                "while not queue.empty():\n"
                "    item = queue.get()\n"
                "    process(item)",
                language="python",
            )
            st.warning(
                "while потребує явного оновлення i. Ризик нескінченного циклу "
                "або off-by-one помилки. Використовуй лише коли for не підходить."
            )

    # =========================================================================
    # Вкладка 4: 📊 Операції
    # =========================================================================
    with tab_ops:
        st.markdown("### 📊 Аналіз кількості операцій")

        # Формула і пояснення
        st.markdown(
            f"**Формула для `{meta.notation}`:** `{meta.formula}`\n\n"
            f"**Пояснення:**\n{meta.formula_explanation}"
        )
        st.divider()

        # Таблиця зростання операцій для поточного алгоритму
        st.markdown("#### Скільки операцій при різних n?")
        rows_ops = []
        for _n in [100, 1_000, 5_000, 10_000, 50_000, 100_000, 1_000_000]:
            log_n = math.ceil(math.log2(_n)) if _n > 1 else 1
            ops_by_key = {
                "linear":    f"{_n:,}",
                "hash":      f"{_n:,} (build) + 1 (lookup)",
                "binary":    f"~{log_n}",
                "quadratic": f"{_n**2:,}" if _n <= 5_000 else "♾ (cap=3000)",
            }
            rows_ops.append({
                "n": f"{_n:,}",
                f"Операцій ({meta.notation})": ops_by_key[algo_key],
                "O(1)": "1",
                "O(log n)": f"~{log_n}",
                "O(n)": f"{_n:,}",
                "O(n²)": f"{_n**2:,}" if _n <= 5_000 else "♾",
            })
        st.dataframe(pd.DataFrame(rows_ops).set_index("n"), width="stretch")
        st.caption(
            "♾ — понад 10¹⁰ операцій: неможливо виконати за розумний час. "
            "Виділена колонка — поточний алгоритм."
        )

        st.divider()
        st.markdown("#### Три правила Big-O аналізу")

        with st.expander("1️⃣ Найгірший сценарій (Worst-Case)", expanded=True):
            st.markdown(
                "Big-O завжди оцінює **найгірші умови** роботи алгоритму.\n\n"
                "Лінійний пошук може знайти елемент на першій ітерації (O(1) lucky case), "
                "але **ми проектуємо систему** під сценарій «елемент відсутній» → n кроків."
            )
            st.code(
                "for i, item in enumerate(data):\n"
                "    if item == target:\n"
                "        return i      # Best case: O(1) — перший елемент\n"
                "return None           # Worst case: O(n) — не знайдено\n"
                "# Big-O = O(n)  (проектуємо під worst case!)",
                language="python",
            )

        with st.expander("2️⃣ Ігнорування констант", expanded=True):
            st.markdown(
                "Два проходи по списку — це `2n` операцій. Big-O: **O(n)**.\n\n"
                "Константа `2` відкидається — при великих n вона несуттєва:\n"
                "- n=1,000,000: `2n` = 2,000,000 vs `n` = 1,000,000 → різниця у 2×\n"
                "- Але `n²` = 1,000,000,000,000 → **у мільйон разів більше!**\n\n"
                "Клас зростання (`n`, `n²`, `log n`) важливіший за константу."
            )
            st.code(
                "# 2n операцій → O(n)\n"
                "for item in data: maximum = max(maximum, item)  # n ops\n"
                "for item in data: minimum = min(minimum, item)  # n ops\n"
                "# Big-O: O(n) — не O(2n)",
                language="python",
            )

        with st.expander("3️⃣ Вищий порядок поглинає нижчі", expanded=True):
            st.markdown(
                "Якщо в коді є блок O(n) і блок O(n²) — загальна складність **O(n²)**.\n\n"
                "`T(n) = 3n² + 4n + 5` → **O(n²)**\n\n"
                "При n=1,000,000: `3n²` = 3×10¹², `4n` = 4×10⁶ → різниця у мільйон разів. "
                "Доданок `4n` **незначний**."
            )
            st.code(
                "def mixed(data):\n"
                "    total = sum(data)               # O(n)  — поглинається\n"
                "    for i in range(len(data)):      # ┐\n"
                "        for j in range(len(data)):  # ┘ O(n²) — домінує\n"
                "            pairs.append((i, j))\n"
                "# Загальна: O(n + n²) = O(n²)",
                language="python",
            )

        st.divider()
        st.markdown("#### 📐 Живий вимір: O(n) vs O(n²) при різних n")
        if st.button("▶ Виміряти O(n) та O(n²) (4 розміри)"):
            sizes_test = [500, 1_000, 2_000, 3_000]
            t_lin, t_quad, t_opt = [], [], []
            progress = st.progress(0.0)
            for step, sz in enumerate(sizes_test):
                sample_df = df.head(sz) if sz <= len(df) else df
                t_lin.append(time_measure(linear_scan, sample_df, "Cash").elapsed_ms)
                t_quad.append(time_measure(nested_loop, sample_df, sz).elapsed_ms)
                t_opt.append(time_measure(nested_optimized_set, sample_df, sz).elapsed_ms)
                progress.progress((step + 1) / len(sizes_test))
            progress.empty()

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=sizes_test, y=t_lin, name="O(n) Linear",
                mode="lines+markers", line=dict(color="#f59e0b", width=2)))
            fig.add_trace(go.Scatter(x=sizes_test, y=t_quad, name="O(n²) Nested",
                mode="lines+markers", line=dict(color="#ef4444", width=2)))
            fig.add_trace(go.Scatter(x=sizes_test, y=t_opt, name="O(n) Set (оптимізовано)",
                mode="lines+markers", line=dict(color="#10b981", width=2,
                dash="dash")))
            fig.update_layout(title="Реальний час: O(n) vs O(n²) vs O(n) set",
                xaxis_title="n (рядків)", yaxis_title="Час (мс)",
                template="plotly_dark", height=380)
            st.plotly_chart(fig, width='stretch')

            result_rows = []
            for sz, tl, tq, to in zip(sizes_test, t_lin, t_quad, t_opt):
                result_rows.append({
                    "n": f"{sz:,}",
                    "O(n) лін. мс": f"{tl:.2f}",
                    "O(n²) мс": f"{tq:.2f}",
                    "O(n) set мс": f"{to:.3f}",
                    "O(n²)/O(n)": f"{tq/tl:.0f}×" if tl > 0 else "—",
                })
            st.dataframe(pd.DataFrame(result_rows).set_index("n"), width='stretch')

    # =========================================================================
    # Вкладка 5: 💾 Памʼять
    # =========================================================================
    with tab_mem:
        st.markdown("### 💾 Використання памʼяті")

        if meta.memory_info:
            mi = meta.memory_info
            st.markdown(f"**Формула:** `{mi.formula}`")
            st.markdown(mi.explanation)
            st.divider()

            # Таблиця breakdown
            st.markdown("#### Розбивка по компонентах (байт/елемент)")
            bd_rows = [{"Компонент": k, "Байт/елемент": v}
                       for k, v in mi.breakdown.items()]
            total_per_elem = sum(mi.breakdown.values())
            bd_rows.append({"Компонент": "**РАЗОМ**", "Байт/елемент": total_per_elem})
            st.dataframe(pd.DataFrame(bd_rows).set_index("Компонент"), width="stretch")

        st.divider()

        # Графік RAM при різних n для поточного алгоритму
        st.markdown("#### Скільки RAM потрібно при різних n?")
        mem_sizes = [1_000, 5_000, 10_000, 50_000, 100_000, 500_000]
        mem_rows = []
        for _n in mem_sizes:
            breakdown = estimate_memory_bytes(algo_key, _n)
            total_mb = breakdown.get("Разом", sum(breakdown.values())) / 1_048_576
            mem_rows.append({"n": f"{_n:,}", "RAM (МБ)": f"{total_mb:.1f}"})
        st.dataframe(pd.DataFrame(mem_rows).set_index("n"), width="stretch")

        st.divider()

        # Порівняння структур даних
        st.markdown("#### Порівняння: list vs dict vs set (памʼять і швидкість)")
        st.markdown(
            """
            | Структура | Памʼять (n ел.) | Lookup | Append | Ітерація |
            |---|---|---|---|---|
            | `list` | n × **8 байт** | O(n) | O(1) amorт. | O(n) |
            | `dict` | n × **~240 байт** | **O(1)** | O(1) amorт. | O(n) |
            | `set` | n × **~196 байт** | **O(1)** | O(1) amorт. | O(n) |
            | `numpy array` | n × **8 байт** | O(n) | O(n) (resize) | O(n) vectorized |

            **Висновок:**
            - `list` — найкомпактніший, але O(n) lookup.
            - `dict` — у 30× важчий за list, але O(1) lookup.
            - `set` — як dict без values (~20% легший), O(1) membership.
            - Trade-off: **памʼять ↔ швидкість**. Обирай залежно від задачі.
            """
        )

        st.divider()
        st.markdown("#### 🔬 list.append() — O(1) амортизовано, але коли O(n)?")
        st.markdown(
            "list у Python — **dynamic array** (динамічний масив). "
            "Коли поточна ємність (`capacity`) вичерпана, відбувається **resize**:"
        )
        st.code(
            "# Послідовність capacity при resize:\n"
            "# 0 → 4 → 8 → 16 → 25 → 35 → 46 → 58 → 72 → 88 → 106...\n"
            "# (не подвоюється — CPython використовує формулу: cap = cap + cap//8 + 6)\n\n"
            "# При resize:\n"
            "# 1. Виділяється новий блок памʼяті (більший)\n"
            "# 2. Всі n елементів КОПІЮЮТЬСЯ → O(n) one-time cost\n"
            "# 3. Старий блок звільняється\n\n"
            "# Амортизований аналіз:\n"
            "# resize відбувається log₂(n) разів за n append()\n"
            "# Сумарна вартість копіювань: n + n/2 + n/4 + ... = 2n\n"
            "# Тому: n append() = O(2n) = O(n) total → O(1) per append",
            language="python",
        )
        st.info(
            "**append() — O(n) тільки при resize**. "
            "Але в середньому (амортизовано) — O(1). "
            "Якщо розмір відомий заперед — використовуй `[None] * n` → "
            "ніколи не ресайзиться."
        )

    # =========================================================================
    # Вкладка 6: ⚙️ Під капотом
    # =========================================================================
    with tab_hood:
        st.markdown(
            f"### ⚙️ Що відбувається під капотом Python для `{meta.notation}`"
        )

        if meta.internals_explanation:
            st.markdown(meta.internals_explanation)

        st.divider()
        st.markdown("#### 🏗️ DuckDB vs Pandas — архітектурний шар")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**❌ Pandas-first (неефективно на великих даних)**")
            st.code(
                "# Завантажуємо ВСІ 3M рядків у RAM\n"
                "df = pd.read_parquet(url)       # ~500 MB RAM\n\n"
                "# Фільтруємо в Python\n"
                "cash = df[df.payment_type=='Cash']  # читає КОЖЕН рядок\n\n"
                "# Вибірка по вже завантаженому\n"
                "sample = df.sample(n=10_000)\n",
                language="python",
            )
            st.error("3M рядків × 10 колонок = ~500 MB RAM просто на завантаження.")

        with col2:
            st.markdown("**✅ DuckDB-first (lazy, ефективно)**")
            st.code(
                "# VIEW = 0 байт у RAM (lazy!)\n"
                "con.execute(\"\"\"\n"
                "  CREATE VIEW trips AS\n"
                "  SELECT ... FROM read_parquet('url')\n"
                "\"\"\")  # нічого не завантажується!\n\n"
                "# Тільки n рядків у памʼять\n"
                "df = con.execute(\n"
                "  f'SELECT * FROM trips USING SAMPLE {n} ROWS'\n"
                ").df()\n",
                language="python",
            )
            st.success("3M рядків у VIEW, але в RAM — лише n=10,000 рядків.")

        st.divider()
        st.markdown(
            """
            #### Чому DuckDB швидше за Pandas на великих даних?

            | | Pandas | DuckDB |
            |---|---|---|
            | **Зберігання** | Row-oriented | **Column-oriented** |
            | **Читання parquet** | Всі колонки | **Тільки потрібні** |
            | **Виконання** | Python + NumPy (1 потік) | **SIMD AVX2 + multi-thread** |
            | **WHERE фільтр** | Після завантаження | **Pushdown на рівні файлу** |
            | **RAM при 3M рядків** | ~500 MB | **~0 MB (lazy VIEW)** |

            **Column pruning** — `SELECT payment_type FROM trips` → DuckDB читає
            ТІЛЬКИ колонку `payment_type` з parquet, ігноруючи `trip_distance`, `PU/DOLocationID`.

            **Predicate pushdown** — `WHERE payment_type = 2` застосовується на рівні
            parquet row-groups (блоки по ~122K рядків). Блоки без значення `2` пропускаються
            **без читання з диску**.

            **SIMD AVX2** — порівнює 8 int32 за **одну CPU-інструкцію** (256-bit register).
            Python loop: 1 порівняння за ~50 нс. AVX2: 8 порівнянь за ~1 нс → **400× швидше**.
            """
        )


# ===========================================================================
# SECTION 6 — SQL vs Pandas Comparison (DuckDB on VIEW vs pandas on sample)
# ===========================================================================

def render_sql_vs_pandas(df: pd.DataFrame, con) -> None:
    st.subheader("⚡ DuckDB на VIEW (3M рядків) vs Pandas на вибірці")
    st.markdown(
        """
        Ключова демонстрація: DuckDB запитує **повний parquet** через VIEW,
        Pandas фільтрує **маленьку вибірку** (n рядків).
        Хто виграє — і чому?
        """
    )

    col_run, _ = st.columns([1, 3])
    if not col_run.button("▶ Запустити порівняння"):
        return

    sample_n = len(df)

    # ── Pandas on sample ──────────────────────────────────────────────────
    p_start = time.perf_counter()
    pandas_count = int((df["payment_type"] == PAYMENT_LOOKUP_TARGET).sum())
    pandas_ms = (time.perf_counter() - p_start) * 1_000

    # ── DuckDB SQL on full VIEW ───────────────────────────────────────────
    d_start = time.perf_counter()
    sql_count = duckdb_count_on_view(con, payment_code=2)
    sql_ms = (time.perf_counter() - d_start) * 1_000

    # ── Display ───────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)

    c1.metric(
        f"🐼 Pandas  (n={sample_n:,} рядків)",
        f"{pandas_ms:.3f} мс",
        f"Cash: {pandas_count:,}  (вибірка)",
    )
    c2.metric(
        "🦆 DuckDB SQL (повний VIEW ~3M рядків)",
        f"{sql_ms:.1f} мс",
        f"Cash: {sql_count:,}  (весь датасет)",
    )

    ratio_note = ""
    if sql_ms < pandas_ms:
        ratio = pandas_ms / sql_ms
        c3.metric("🏆 Переможець", "DuckDB", f"{ratio:.1f}× швидше")
        ratio_note = (
            f"DuckDB обробив **{sql_count:,}** рядків "
            f"за {sql_ms:.1f} мс — швидше ніж Pandas фільтрував {sample_n:,}. "
            "Причина: columnar reading + SIMD + predicate pushdown."
        )
    else:
        ratio = sql_ms / pandas_ms
        c3.metric("🏆 Переможець", "Pandas", f"{ratio:.1f}× швидше")
        ratio_note = (
            f"На малих вибірках (n={sample_n:,}) Pandas швидше — "
            "DuckDB має overhead на query compilation. "
            "**Збільш n до 100,000+** щоб побачити перелом."
        )

    if ratio_note:
        st.info(ratio_note)

    with st.expander("📖 Що відбувається під капотом?"):
        st.markdown(
            f"""
            **Pandas (вибірка {sample_n:,} рядків):**
            1. DataFrame вже в RAM → NumPy boolean mask → підрахунок
            2. O(n) операцій на малому n → швидко

            **DuckDB SQL (VIEW ≈ 3M рядків):**
            1. Компілює SQL → execution plan
            2. `payment_type = 2` → pushdown на parquet row-groups
            3. Читає ТІЛЬКИ `payment_type` колонку (column pruning)
            4. AVX2 SIMD: порівнює 8 int32 за одну CPU-інструкцію
            5. Multi-thread: ділить row-groups між потоками

            **Перелом:** при n > ~50,000–100,000 DuckDB стає швидшим
            навіть на `SELECT COUNT(*)`, незважаючи на більший обсяг даних.
            """
        )


# ===========================================================================
# SECTION 7 — Scaling Chart (samples from DuckDB at each size)
# ===========================================================================

def render_scaling_chart(con) -> None:
    st.subheader("📈 Scaling Chart — реальне зростання часу при різних n")

    col_run, col_log, _ = st.columns([1, 1, 4])
    run_clicked = col_run.button("▶ Запустити Scaling Analysis")
    use_log     = col_log.checkbox("Log scale (Y)", value=True)

    if not run_clicked:
        return

    # Pre-fetch a large sample once (avoids N DuckDB calls)
    max_chart_n = max(CHART_SIZES)
    with st.spinner(f"Завантажуємо {max_chart_n:,} рядків з DuckDB…"):
        base_df = sample_from_view(con, max_chart_n)

    sizes = [s for s in CHART_SIZES if s <= len(base_df)]

    timings: dict[str, list[float]] = {
        "O(n)": [], "O(1)": [], "O(log n)": [], "O(n²)": []
    }

    progress = st.progress(0.0)
    status   = st.empty()

    for step, sz in enumerate(sizes):
        status.text(f"Вимірюємо n={sz:,}…")
        # Subsample from the in-memory base (no extra DuckDB round-trip)
        df_s = base_df.sample(n=sz, random_state=42).reset_index(drop=True)

        # O(n) — linear scan
        t = time_measure(linear_scan, df_s, "Cash")
        timings["O(n)"].append(t.elapsed_ms)

        # O(1) — build index, measure only the lookup
        build_r  = time_measure(build_hash_index, df_s)
        lookup_r = time_measure(hash_index_lookup, build_r.value, "Cash")
        timings["O(1)"].append(max(lookup_r.elapsed_ms, 0.0001))

        # O(log n) — sort once, measure only the search
        sort_r   = time_measure(prepare_sorted_distances, df_s)
        search_r = time_measure(binary_search, sort_r.value, 3.0)
        timings["O(log n)"].append(max(search_r.elapsed_ms, 0.0001))

        # O(n²) — capped at 1,000
        quad_n = min(sz, 1_000)
        quad_r = time_measure(nested_loop, df_s, quad_n)
        timings["O(n²)"].append(quad_r.elapsed_ms)

        progress.progress((step + 1) / len(sizes))

    status.empty()
    progress.empty()

    # ── Plotly chart ─────────────────────────────────────────────────────
    fig = go.Figure()
    style = {
        "O(n)":    "#f59e0b",
        "O(1)":    "#10b981",
        "O(log n)": "#3b82f6",
        "O(n²)":   "#ef4444",
    }
    for algo, color in style.items():
        fig.add_trace(go.Scatter(
            x=sizes, y=timings[algo], name=algo,
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=6),
            hovertemplate=f"<b>{algo}</b><br>n=%{{x:,}}<br>%{{y:.4f}} мс<extra></extra>",
        ))

    fig.update_layout(
        title="Час виконання алгоритмів залежно від розміру вибірки",
        xaxis_title="n (рядків у вибірці)",
        yaxis_title="Час виконання (мс)",
        yaxis_type="log" if use_log else "linear",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="plotly_dark",
        height=480,
    )
    st.plotly_chart(fig, width='stretch')

    st.caption(
        f"O(n²) обмежено до {1_000:,} рядків у графіку.  "
        "Data: один раз завантажено з DuckDB VIEW, потім субсемплінг у пам'яті."
    )

    # Operations table
    with st.expander("📊 Таблиця: операцій при різних n"):
        rows = []
        for _n in [100, 1_000, 10_000, 100_000, 1_000_000]:
            ln = math.ceil(math.log2(_n)) if _n > 1 else 1
            rows.append({
                "n": f"{_n:,}",
                "O(1)": "1",
                f"O(log n) ≈log₂": f"~{ln}",
                "O(n)": f"{_n:,}",
                "O(n log n)": f"{_n * ln:,}",
                "O(n²)": f"{_n**2:,}" if _n <= 10_000 else "♾",
            })
        st.dataframe(pd.DataFrame(rows).set_index("n"), width='stretch')


# ===========================================================================
# SECTION 8 — Memory Status & Safety Helpers
# ===========================================================================

def render_memory_status(limit_gb: float) -> None:
    """Inline RAM gauge — shown just before a heavy operation."""
    current_gb = get_memory_usage_gb()
    pct = current_gb / limit_gb * 100
    color = "🟢" if pct < 60 else ("🟡" if pct < 85 else "🔴")
    st.caption(
        f"{color} **RAM:** {current_gb:.2f} GB / {limit_gb:.0f} GB  "
        f"({pct:.0f}% використано)"
    )


def _pre_flight_check(
    n: int,
    algo_key: str,
    full_mode: bool,
    limit_gb: float,
) -> bool:
    """
    Show a pre-flight RAM warning before executing a heavy operation.

    Returns True if execution should proceed, False if the user cancelled.
    Raises MemoryGuardError if the projection already exceeds the limit.
    """
    current_gb  = get_memory_usage_gb()
    df_est_gb   = estimate_dataframe_gb(n)
    algo_est_gb = estimate_algo_memory_gb(algo_key, n)
    total_est   = current_gb + df_est_gb + algo_est_gb

    if total_est > limit_gb:
        raise MemoryGuardError(
            current_gb=total_est,
            limit_gb=limit_gb,
            context=f"pre_flight_check for {algo_key} n={n:,}",
            delta_gb=df_est_gb + algo_est_gb,
        )

    # Soft warning when usage would be > 70 % of limit
    if total_est > limit_gb * 0.70:
        st.warning(
            f"⚠️ **Pre-flight:** очікуване використання RAM після операції "
            f"**{total_est:.2f} GB** (~{total_est / limit_gb * 100:.0f}% від ліміту {limit_gb:.0f} GB).  \n"
            f"DataFrame: +{df_est_gb:.3f} GB · алгоритм: +{algo_est_gb:.3f} GB · "
            f"зараз: {current_gb:.2f} GB"
        )

    if full_mode:
        full_est = estimate_load_gb(n)
        st.info(
            f"📦 **Full dataset mode:** ~{n:,} рядків  \n"
            f"Очікуване зростання RAM: **+{full_est:.2f} GB**  \n"
            f"Загальний прогноз: {current_gb + full_est:.2f} GB"
        )

    return True


def _render_memory_error(exc: MemoryGuardError) -> None:
    """Rich error card for a MemoryGuardError — shown instead of a traceback."""
    st.error(
        f"🔴 **Перевищено RAM ліміт**\n\n"
        f"Поточне/очікуване: **{exc.current_gb:.2f} GB** > "
        f"ліміт **{exc.limit_gb:.1f} GB**  \n"
        f"Де сталось: `{exc.context}`  \n"
        f"Зростання під час операції: **{exc.delta_gb:+.2f} GB**"
    )
    st.markdown(
        "**Що зробити:**\n"
        "- 🔽 Зменш **n** у боковій панелі\n"
        "- 🔽 Вимкни **Full dataset mode** → перейди на Sample mode\n"
        "- 🔼 Збільш **RAM ліміт** (якщо пам'яті фізично вистачає)\n"
        "- ♻️ Перезапусти застосунок (`streamlit run app.py`) для очищення пам'яті"
    )


# ===========================================================================
# MAIN
# ===========================================================================

def main() -> None:
    render_header()
    st.divider()

    # ── DuckDB lazy connection (VIEW registered, zero data loaded) ──────────
    with st.spinner("🦆 Підключення до DuckDB та реєстрація VIEW…"):
        try:
            con = get_duckdb_connection()
        except Exception as exc:
            st.error(f"❌ DuckDB connection failed: {exc}")
            st.stop()

    # ── Dataset statistics via SQL aggregation (no RAM) ────────────────────
    stats = render_data_section(con)
    total_n = stats.get("total_rows", 3_000_000)
    st.success(
        f"✅ DuckDB VIEW активний · ~{total_n:,} рядків доступно · 0 байт у Python RAM"
    )

    # ── Sidebar controls (now returns 5 values) ────────────────────────────
    n, algo_label, threshold, full_mode, memory_limit_gb = render_sidebar_controls(
        total_n
    )

    algo_key = next(k for k, m in ALGO_META.items() if m.label == algo_label)

    # ── Load data — sample mode or full dataset mode ───────────────────────
    df: pd.DataFrame | None = None
    try:
        if full_mode:
            # Warn about O(n²) danger before even trying
            if algo_key == "quadratic":
                st.error(
                    "🔴 **Full dataset mode + O(n²) заборонено.**  \n"
                    f"~{total_n:,}² = неможливо виконати.  \n"
                    "Вимкни Full dataset mode або вибери інший алгоритм."
                )
                st.stop()

            with st.spinner(f"Завантажуємо ВСІ ~{total_n:,} рядків у RAM…"):
                df = load_full_dataset(con, limit_gb=memory_limit_gb)

            actual_n = len(df)
            st.success(
                f"✅ Повний датасет завантажено: **{actual_n:,} рядків** у RAM  \n"
                f"RAM після завантаження: **{get_memory_usage_gb():.2f} GB** "
                f"/ {memory_limit_gb:.0f} GB ліміт"
            )
        else:
            with st.spinner(f"SQL SAMPLE {n:,} рядків з DuckDB VIEW…"):
                df = sample_from_view(con, n)

    except MemoryGuardError as exc:
        _render_memory_error(exc)
        st.stop()
    except Exception as exc:
        err_str = str(exc)
        if "HTTP" in err_str or "HTTPException" in type(exc).__name__:
            st.error(
                "🌐 **Не вдалося завантажити дані — помилка мережі.**\n\n"
                f"`{type(exc).__name__}: {exc}`\n\n"
                "**Що перевірити:**\n"
                "- Інтернет-з'єднання активне?\n"
                "- CDN `d37ci6vzurychx.cloudfront.net` доступний?\n"
                "- Спробуй перезапустити застосунок через кілька хвилин."
            )
        else:
            st.error(f"❌ Помилка завантаження даних: {exc}")
        st.stop()

    actual_n = len(df)

    # ── Algorithm Experiment ───────────────────────────────────────────────
    st.divider()
    st.header("🧪 Експеримент")

    mode_badge = "🗄️ FULL" if full_mode else "🔬 Sample"
    col_info, col_mem, col_run = st.columns([4, 2, 1])
    col_info.markdown(
        f"**Алгоритм:** `{algo_label}`  |  "
        f"**n:** `{actual_n:,}` рядків ({mode_badge})  |  "
        f"**VIEW:** ~{total_n:,} рядків (DuckDB)"
    )
    with col_mem:
        render_memory_status(memory_limit_gb)

    if col_run.button("▶ Run Experiment", type="primary"):
        try:
            _pre_flight_check(actual_n, algo_key, full_mode, memory_limit_gb)
            with st.spinner("Виконуємо алгоритм…"):
                run_algorithm(algo_label, df, threshold)
        except MemoryGuardError as exc:
            _render_memory_error(exc)
    else:
        st.info("← Вибери алгоритм і n у боковій панелі, потім натисни **Run Experiment**.")

    # ── Educational Section ────────────────────────────────────────────────
    st.divider()
    render_educational_section(df, algo_key, actual_n)

    # ── SQL vs Pandas ──────────────────────────────────────────────────────
    st.divider()
    render_sql_vs_pandas(df, con)

    # ── Scaling Chart ──────────────────────────────────────────────────────
    st.divider()
    render_scaling_chart(con)

    # ── Footer ─────────────────────────────────────────────────────────────
    st.divider()
    st.caption(
        "📚 Module 3 · Lesson 22 · Big-O Notation · Viktor Nikoriak  |  "
        "Data: NYC TLC Yellow Taxi 2023-01  |  "
        "Architecture: DuckDB lazy VIEW → SQL SAMPLE → pandas"
    )


if __name__ == "__main__":
    main()
