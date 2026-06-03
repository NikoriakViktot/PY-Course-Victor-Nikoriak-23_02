"""
app.py — Queue Policy Lab: Data Structures as Execution Policies
================================================================
Демонструє, як вибір структури даних (deque/list/heapq) визначає
поведінку реальної системи диспетчеризації таксі.

FIFO    → deque.popleft()       → справедливість
LIFO    → list.pop()            → переривання + голодування
RANDOM  → list + random swap    → нестабільність
PRIORITY → heapq.heappop()      → оптимізація + bias

Джерело даних: NYC TLC Yellow Taxi 2023-01 (реальні поїздки)
Запуск: streamlit run app.py
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from data_loader import (
    get_duckdb_connection,
    get_dataset_stats,
    make_synthetic_trips,
    sample_trips,
)
from simulation import (
    Policy,
    PolicyEngine,
    POLICY_COLORS,
    POLICY_DESCRIPTIONS,
    POLICY_LABELS,
    run_all_policies,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Queue Policy Lab",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _color(p: Policy) -> str:
    return POLICY_COLORS[p]


def _delta_arrow(val: float, better: str = "low") -> str:
    """Return markdown arrow for metric delta display."""
    return "↓" if better == "low" else "↑"


# ---------------------------------------------------------------------------
# Section 1: Header
# ---------------------------------------------------------------------------

def render_header() -> None:
    st.title("🚕 Queue Policy Lab")
    st.markdown(
        """
        **Дата-структури як політики виконання** — інтерактивна симуляція
        на реальних даних NYC TLC Yellow Taxi 2023.

        Кожна з 4 черг отримує **однаковий потік поїздок** і обробляє їх
        відповідно до своєї структури даних. Результати вимірюємо і порівнюємо.

        | Політика | Структура | Поведінка |
        |----------|-----------|-----------|
        | 🟢 FIFO  | `deque.popleft()` | Справедливість — перший прийшов, перший обслужений |
        | 🔴 LIFO  | `list.pop()`      | Переривання — найновіший запит завжди першим |
        | 🟡 RANDOM | `list` + random  | Хаос — ніхто не захищений від довгого очікування |
        | 🟣 PRIORITY | `heapq.heappop()` | Оптимізація — короткі поїздки першими |
        """
    )
    st.divider()


# ---------------------------------------------------------------------------
# Section 2: Data loading
# ---------------------------------------------------------------------------

def load_data(n_trips: int) -> tuple[pd.DataFrame, bool]:
    """
    Try DuckDB → remote parquet. Falls back to synthetic data if unavailable.
    Returns (df, is_real_data).
    """
    con = get_duckdb_connection()
    if con is not None:
        try:
            df = sample_trips(con, n_trips)
            return df, True
        except Exception as exc:
            st.warning(
                f"🌐 **Remote parquet недоступний** (`{type(exc).__name__}`).  \n"
                "Використовуємо синтетичні дані з розподілом, близьким до NYC TLC."
            )
    return make_synthetic_trips(n_trips), False


def render_data_section(n_trips: int) -> pd.DataFrame:
    with st.expander("📊 Датасет NYC TLC 2023-01", expanded=False):
        with st.spinner("Підключення до DuckDB VIEW…"):
            con = get_duckdb_connection()
            if con is not None:
                try:
                    stats = get_dataset_stats(con)
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Рядків у VIEW",    f"{stats['total_rows']:,}")
                    c2.metric("Сер. дистанція",   f"{stats['avg_distance']:.2f} км")
                    c3.metric("Медіана",          f"{stats['median_distance']:.2f} км")
                    c4.metric("Макс. дистанція",  f"{stats['max_distance']:.1f} км")
                    c5.metric("Зон pickup",       stats["unique_pu_zones"])
                    st.info(
                        "💡 Статистика через DuckDB SQL-агрегацію — "
                        "жоден рядок з 3M не завантажено в Python RAM."
                    )
                except Exception:
                    st.warning("Статистика недоступна — offline-режим.")
            else:
                st.warning("🔌 DuckDB недоступний (DLL заблокований OS). Режим: синтетичні дані.")

        with st.spinner(f"Завантажуємо {n_trips:,} поїздок для симуляції…"):
            df, is_real = load_data(n_trips)

        source_label = "🟢 NYC TLC 2023-01 (real)" if is_real else "🟡 Synthetic (offline)"
        st.caption(f"Джерело: {source_label} · {len(df):,} рядків · "
                   f"Дистанція: {df['trip_distance'].min():.1f}–{df['trip_distance'].max():.1f} км")

        fig = px.histogram(
            df, x="trip_distance", nbins=60,
            title="Розподіл дистанцій поїздок",
            labels={"trip_distance": "Дистанція (км)", "count": "Кількість"},
            color_discrete_sequence=["#4ECDC4"],
        )
        fig.update_layout(height=250, margin=dict(t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    return df


# ---------------------------------------------------------------------------
# Section 3: Sidebar
# ---------------------------------------------------------------------------

def render_sidebar() -> dict:
    with st.sidebar:
        st.header("⚙️ Параметри симуляції")
        st.divider()

        st.subheader("📦 Дані")
        n_trips = st.select_slider(
            "Кількість поїздок",
            options=[200, 500, 1_000, 2_000, 5_000],
            value=1_000,
            help="Розмір датасету для симуляції. Більше = довша симуляція.",
        )

        st.divider()
        st.subheader("🚕 Параметри системи")

        num_drivers = st.slider(
            "Кількість водіїв", min_value=1, max_value=20, value=5,
            help="Кількість одночасно працюючих таксі.",
        )
        arrival_rate = st.slider(
            "Інтенсивність надходження (λ)",
            min_value=0.2, max_value=3.0, value=1.0, step=0.1,
            help="Середня кількість нових поїздок за тік (Poisson lambda). "
                 "λ > обробка = черга зростає.",
        )
        process_speed = st.slider(
            "Тіки на км (швидкість обробки)",
            min_value=0.5, max_value=5.0, value=2.0, step=0.5,
            help="Скільки тіків займає 1 км поїздки. Менше = швидший сервіс.",
        )

        st.divider()
        st.subheader("🎯 Політики")
        selected_policies = st.multiselect(
            "Порівнювати:",
            options=[p.value for p in Policy],
            default=[p.value for p in Policy],
            help="Вибеpіть які політики запустити.",
        )

        st.divider()
        st.caption(
            "**Навантаження системи:**  \n"
            f"λ = {arrival_rate:.1f} trip/tick  \n"
            f"μ = {num_drivers / max(0.1, process_speed * 2.5):.2f} trip/tick (est.)  \n"
        )
        utilization = arrival_rate / max(0.01, num_drivers / max(0.1, process_speed * 2.5))
        color = "🔴" if utilization > 1.2 else "🟡" if utilization > 0.8 else "🟢"
        st.caption(f"ρ = {min(utilization, 9.99):.2f} {color}  \n"
                   "_ρ > 1 → черга необмежено зростатиме_")

        run = st.button("▶ Запустити симуляцію", use_container_width=True, type="primary")

    return {
        "n_trips":        n_trips,
        "num_drivers":    num_drivers,
        "arrival_rate":   arrival_rate,
        "process_speed":  process_speed,
        "policies":       [Policy(p) for p in selected_policies],
        "run":            run,
    }


# ---------------------------------------------------------------------------
# Section 4: Run simulation
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def cached_simulation(
    trips_hash: int,
    arrival_rate: float,
    num_drivers: int,
    process_speed: float,
    policy_values: tuple[str, ...],
) -> dict[str, dict]:
    """
    Cache simulation results by parameter hash.
    Converts PolicyEngine results to serialisable dicts for Streamlit cache.
    """
    import hashlib, json
    from data_loader import make_synthetic_trips

    # Regenerate trips from hash (we pass n_trips encoded in hash)
    n_trips = trips_hash
    df = make_synthetic_trips(n_trips)

    results = {}
    for pv in policy_values:
        policy = Policy(pv)
        engine = PolicyEngine(
            policy=policy,
            trips_df=df,
            arrival_rate=arrival_rate,
            num_drivers=num_drivers,
            process_ticks_per_km=process_speed,
        ).run()
        results[pv] = {
            "summary":      engine.summary(),
            "snapshots":    engine.snapshots_df().to_dict("list"),
            "completed":    engine.completed_df().to_dict("list"),
        }
    return results


def run_simulation(
    trips_df:      pd.DataFrame,
    arrival_rate:  float,
    num_drivers:   int,
    process_speed: float,
    policies:      list[Policy],
) -> dict[Policy, dict]:
    """Run simulation for selected policies, show progress."""
    results: dict[Policy, dict] = {}
    progress = st.progress(0, text="Запускаємо симуляцію…")

    for i, policy in enumerate(policies):
        progress.progress((i) / len(policies), text=f"Симуляція: {POLICY_LABELS[policy]}")
        engine = PolicyEngine(
            policy               = policy,
            trips_df             = trips_df,
            arrival_rate         = arrival_rate,
            num_drivers          = num_drivers,
            process_ticks_per_km = process_speed,
        ).run()
        results[policy] = {
            "summary":   engine.summary(),
            "snapshots": engine.snapshots_df(),
            "completed": engine.completed_df(),
        }
        progress.progress((i + 1) / len(policies), text=f"✓ {POLICY_LABELS[policy]}")

    progress.empty()
    return results


# ---------------------------------------------------------------------------
# Section 5: Charts
# ---------------------------------------------------------------------------

def render_kpi_cards(results: dict[Policy, dict]) -> None:
    st.subheader("📊 Ключові показники")
    cols = st.columns(len(results))
    for col, (policy, data) in zip(cols, results.items()):
        s = data["summary"]
        color = _color(policy)
        with col:
            st.markdown(
                f"""
                <div style="border-left: 4px solid {color}; padding: 10px 14px;
                             border-radius: 6px; background: #1e1e1e; margin-bottom: 8px;">
                  <div style="font-size:1.1em; font-weight:600; color:{color}">
                    {POLICY_LABELS[policy]}
                  </div>
                  <div style="color:#aaa; font-size:0.8em; margin-bottom:8px">
                    {POLICY_DESCRIPTIONS[policy]}
                  </div>
                  <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px">
                    <div><span style="color:#888">Виконано</span><br>
                      <b style="font-size:1.3em">{s.get('completed',0):,}</b></div>
                    <div><span style="color:#888">Голодування</span><br>
                      <b style="font-size:1.3em; color:{'#FF6B6B' if s.get('starved',0) > 0 else '#4ECDC4'}">
                        {s.get('starved',0):,}</b></div>
                    <div><span style="color:#888">Сер. очікування</span><br>
                      <b>{s.get('avg_wait','—')} ticks</b></div>
                    <div><span style="color:#888">Справедливість</span><br>
                      <b>{s.get('fairness','—')}</b></div>
                    <div><span style="color:#888">P95 очікування</span><br>
                      <b>{s.get('p95_wait','—')} ticks</b></div>
                    <div><span style="color:#888">Макс. черга</span><br>
                      <b>{s.get('max_queue','—')}</b></div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_queue_length_chart(results: dict[Policy, dict]) -> None:
    st.subheader("📈 Довжина черги в часі")
    st.caption(
        "LIFO та RANDOM накопичують старі запити — черга зростає хаотично.  "
        "FIFO стабільно дренується. PRIORITY оптимізує throughput, але може "
        "залишати довгі поїздки чекати."
    )

    fig = go.Figure()
    for policy, data in results.items():
        sdf: pd.DataFrame = data["snapshots"]
        if sdf.empty:
            continue
        # Smoothed line (rolling mean over 10 ticks)
        smoothed = sdf["queue_length"].rolling(10, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=sdf["tick"],
            y=smoothed,
            name=POLICY_LABELS[policy],
            line=dict(color=_color(policy), width=2),
            hovertemplate="Тік %{x}<br>Черга: %{y:.0f}<extra></extra>",
        ))

    fig.update_layout(
        xaxis_title="Тік симуляції",
        yaxis_title="Кількість поїздок у черзі",
        legend=dict(orientation="h", y=1.1),
        height=350,
        margin=dict(t=20, b=40),
        plot_bgcolor="#1e1e1e",
        paper_bgcolor="#1e1e1e",
        font_color="#ccc",
        xaxis=dict(gridcolor="#333"),
        yaxis=dict(gridcolor="#333"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_wait_time_charts(results: dict[Policy, dict]) -> None:
    st.subheader("⏱ Розподіл часу очікування")

    col1, col2 = st.columns(2)

    # ── Histogram overlay ──────────────────────────────────────────────────
    with col1:
        st.caption("Гістограма: порівняння розподілів")
        fig = go.Figure()
        for policy, data in results.items():
            cdf: pd.DataFrame = data["completed"]
            if cdf.empty or "wait_ticks" not in cdf.columns:
                continue
            fig.add_trace(go.Histogram(
                x=cdf["wait_ticks"],
                name=POLICY_LABELS[policy],
                marker_color=_color(policy),
                opacity=0.65,
                nbinsx=40,
                hovertemplate="Очікування: %{x} ticks<br>Кількість: %{y}<extra></extra>",
            ))
        fig.update_layout(
            barmode="overlay",
            xaxis_title="Тіки очікування",
            yaxis_title="Кількість поїздок",
            height=320,
            margin=dict(t=10, b=40),
            legend=dict(orientation="h", y=1.05),
            plot_bgcolor="#1e1e1e",
            paper_bgcolor="#1e1e1e",
            font_color="#ccc",
            xaxis=dict(gridcolor="#333"),
            yaxis=dict(gridcolor="#333"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Box plot ──────────────────────────────────────────────────────────
    with col2:
        st.caption("Box plot: медіана, IQR, хвости, викиди")
        frames = []
        for policy, data in results.items():
            cdf: pd.DataFrame = data["completed"]
            if cdf.empty or "wait_ticks" not in cdf.columns:
                continue
            tmp = cdf[["wait_ticks"]].copy()
            tmp["policy"] = POLICY_LABELS[policy]
            frames.append(tmp)

        if frames:
            all_waits = pd.concat(frames, ignore_index=True)
            fig2 = px.box(
                all_waits, x="policy", y="wait_ticks",
                color="policy",
                color_discrete_map={POLICY_LABELS[p]: _color(p) for p in results},
                points=False,
            )
            fig2.update_layout(
                xaxis_title="",
                yaxis_title="Тіки очікування",
                showlegend=False,
                height=320,
                margin=dict(t=10, b=40),
                plot_bgcolor="#1e1e1e",
                paper_bgcolor="#1e1e1e",
                font_color="#ccc",
                xaxis=dict(gridcolor="#333", tickangle=-20),
                yaxis=dict(gridcolor="#333"),
            )
            st.plotly_chart(fig2, use_container_width=True)


def render_fairness_chart(results: dict[Policy, dict]) -> None:
    st.subheader("⚖️ Індекс справедливості та голодування")
    st.caption(
        "**Fairness (Jain's index):** 1.0 = ідеальна рівність, 0.0 = крайня нерівність.  \n"
        "**Starved trips:** поїздки, що чекали понад ліміт і були відкинуті."
    )

    col1, col2 = st.columns(2)

    with col1:
        policies   = [POLICY_LABELS[p] for p in results]
        fairnesses = [results[p]["summary"].get("fairness", 0) for p in results]
        colors     = [_color(p) for p in results]

        fig = go.Figure(go.Bar(
            x=policies,
            y=fairnesses,
            marker_color=colors,
            text=[f"{v:.3f}" for v in fairnesses],
            textposition="outside",
            hovertemplate="%{x}<br>Fairness: %{y:.3f}<extra></extra>",
        ))
        fig.add_hline(y=1.0, line_dash="dash", line_color="#666",
                      annotation_text="Ідеальна рівність", annotation_position="right")
        fig.update_layout(
            yaxis=dict(range=[0, 1.15], title="Jain's Fairness Index"),
            xaxis_title="",
            height=300,
            margin=dict(t=10, b=40),
            plot_bgcolor="#1e1e1e",
            paper_bgcolor="#1e1e1e",
            font_color="#ccc",
            xaxis=dict(gridcolor="#333", tickangle=-15),
            yaxis_gridcolor="#333",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        starved = [results[p]["summary"].get("starved", 0) for p in results]

        fig2 = go.Figure(go.Bar(
            x=policies,
            y=starved,
            marker_color=["#FF6B6B" if s > 0 else "#4ECDC4" for s in starved],
            text=[str(s) for s in starved],
            textposition="outside",
            hovertemplate="%{x}<br>Голодування: %{y}<extra></extra>",
        ))
        fig2.update_layout(
            yaxis_title="Кількість відкинутих поїздок",
            xaxis_title="",
            height=300,
            margin=dict(t=10, b=40),
            plot_bgcolor="#1e1e1e",
            paper_bgcolor="#1e1e1e",
            font_color="#ccc",
            xaxis=dict(gridcolor="#333", tickangle=-15),
            yaxis_gridcolor="#333",
        )
        st.plotly_chart(fig2, use_container_width=True)


def render_priority_bias(results: dict[Policy, dict]) -> None:
    """Show how PRIORITY biases towards short trips."""
    if Policy.PRIORITY not in results:
        return

    st.subheader("🔬 Аналіз bias: PRIORITY vs FIFO")
    st.caption(
        "PRIORITY обслуговує короткі поїздки першими → більший throughput, "
        "але довгі поїздки можуть чекати набагато довше (bias / starvation risk)."
    )

    col1, col2 = st.columns(2)

    for col, policy in zip([col1, col2], [Policy.PRIORITY, Policy.FIFO]):
        if policy not in results:
            continue
        cdf: pd.DataFrame = results[policy]["completed"]
        if cdf.empty or "distance" not in cdf.columns:
            continue

        # Scatter: distance vs wait_ticks
        fig = px.scatter(
            cdf.sample(min(500, len(cdf)), random_state=42),
            x="distance", y="wait_ticks",
            opacity=0.5,
            color_discrete_sequence=[_color(policy)],
            title=f"{POLICY_LABELS[policy]}",
            labels={"distance": "Дистанція (км)", "wait_ticks": "Очікування (ticks)"},
        )
        fig.update_layout(
            height=280,
            margin=dict(t=40, b=30),
            plot_bgcolor="#1e1e1e",
            paper_bgcolor="#1e1e1e",
            font_color="#ccc",
            xaxis=dict(gridcolor="#333"),
            yaxis=dict(gridcolor="#333"),
        )
        col.plotly_chart(fig, use_container_width=True)

    # Correlation analysis
    priority_cdf: pd.DataFrame = results[Policy.PRIORITY]["completed"]
    if not priority_cdf.empty and "distance" in priority_cdf.columns:
        corr = priority_cdf["distance"].corr(priority_cdf["wait_ticks"])
        st.info(
            f"📐 **Кореляція дистанція ↔ очікування (PRIORITY):** `r = {corr:.3f}`  \n"
            "Позитивна кореляція підтверджує: довші поїздки чекають довше при PRIORITY."
        )


def render_throughput_chart(results: dict[Policy, dict]) -> None:
    st.subheader("🚀 Пропускна здатність у часі (ковзне сер.)")
    st.caption("Кількість виконаних поїздок за останні 20 тіків.")

    fig = go.Figure()
    for policy, data in results.items():
        sdf: pd.DataFrame = data["snapshots"]
        if sdf.empty:
            continue
        throughput = sdf["completed"].rolling(20, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=sdf["tick"],
            y=throughput,
            name=POLICY_LABELS[policy],
            line=dict(color=_color(policy), width=2),
            hovertemplate="Тік %{x}<br>Throughput: %{y:.2f}<extra></extra>",
        ))

    fig.update_layout(
        xaxis_title="Тік симуляції",
        yaxis_title="Поїздок / тік (ковзне сер.)",
        legend=dict(orientation="h", y=1.1),
        height=300,
        margin=dict(t=20, b=40),
        plot_bgcolor="#1e1e1e",
        paper_bgcolor="#1e1e1e",
        font_color="#ccc",
        xaxis=dict(gridcolor="#333"),
        yaxis=dict(gridcolor="#333"),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_summary_table(results: dict[Policy, dict]) -> None:
    st.subheader("📋 Зведена таблиця метрик")

    rows = []
    for policy, data in results.items():
        s = data["summary"]
        rows.append({
            "Політика":        POLICY_LABELS[policy],
            "Виконано":        s.get("completed", 0),
            "Голодування":     s.get("starved", 0),
            "Сер. очікування": s.get("avg_wait", "—"),
            "Медіана":         s.get("median_wait", "—"),
            "P95 очікування":  s.get("p95_wait", "—"),
            "Макс. очікування":s.get("max_wait", "—"),
            "Справедливість":  s.get("fairness", "—"),
            "Throughput/тік":  s.get("throughput_tpt", "—"),
            "Макс. черга":     s.get("max_queue", "—"),
        })

    df_table = pd.DataFrame(rows)
    st.dataframe(df_table, use_container_width=True, hide_index=True)


def render_insights(results: dict[Policy, dict]) -> None:
    st.subheader("💡 Архітектурні висновки")

    summaries = {p: d["summary"] for p, d in results.items()}

    # Find best/worst
    if len(summaries) >= 2:
        fairest = max(summaries, key=lambda p: summaries[p].get("fairness", 0))
        most_throughput = max(summaries, key=lambda p: summaries[p].get("completed", 0))
        most_starved = max(summaries, key=lambda p: summaries[p].get("starved", 0))

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"""
**🟢 FIFO — `collections.deque`**
- `append()` + `popleft()` — обидві операції **O(1)**
- Гарантує **хронологічну справедливість** — жоден запит не буде пропущений
- Ідеальний для: HTTP-серверів, черг завдань, спулінгу принтера
- Слабкість: не відрізняє пріоритетні запити від звичайних

**🔴 LIFO — `list`**
- `append()` + `pop()` — обидві **O(1)**, але поведінка деструктивна
- Нові запити завжди першими → **старі запити ніколи не обслуговуються** (starvation)
- Застосування у системах: call stack, DFS-обхід, Undo/Redo
- **Ніколи** не використовуйте LIFO для диспетчеризації замовлень!
                """
            )

        with col2:
            st.markdown(
                f"""
**🟡 RANDOM — `list` + random swap**
- Випадковий вибір → **нестабільний час відгуку**, висока дисперсія
- Жоден клієнт не може передбачити, коли буде обслужений
- Використовується: рандомізовані алгоритми, load balancing (деякі варіанти)
- На практиці гірший за FIFO у більшості метрик

**🟣 PRIORITY — `heapq`**
- `heappush` / `heappop` — **O(log n)**
- Короткі поїздки першими → **вищий throughput**, але довгі поїздки чекають
- Ризик **priority starvation** для низькопріоритетних запитів
- Застосування: планувальник завдань ОС, A*, Dijkstra
                """
            )

        st.success(
            f"**Найсправедливіша:** {POLICY_LABELS[fairest]}  \n"
            f"**Найбільший throughput:** {POLICY_LABELS[most_throughput]}  \n"
            f"**Найбільше голодування:** {POLICY_LABELS.get(most_starved, '—')}"
        )

    st.info(
        "📐 **Ключова думка:**  \n"
        "Структури даних — це **не просто контейнери**. Це **контракти виконання**.  \n"
        "Обираючи `deque` замість `list`, ви не просто обираєте клас — "
        "ви обираєте **яке замовлення має право бути обслуженим першим**."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    render_header()
    params = render_sidebar()

    # Data loading happens always (for expander)
    trips_df = render_data_section(params["n_trips"])

    if not params["run"]:
        st.info(
            "👈 Налаштуйте параметри у бічній панелі та натисніть **▶ Запустити симуляцію**."
        )
        st.markdown(
            """
            ### Що відбувається під капотом?

            ```
            NYC TLC trips (DuckDB SAMPLE)
                    ↓
            Scheduler (arrival_rate, Poisson)
                    ↓
            ┌───────────────────────────────┐
            │  FIFO     → deque.popleft()   │
            │  LIFO     → list.pop()        │
            │  RANDOM   → list[random]      │
            │  PRIORITY → heapq.heappop()   │
            └───────────────────────────────┘
                    ↓
            Metrics: queue_length, wait_time,
                     fairness, starvation
            ```

            Кожна з 4 черг отримує **однаковий потік поїздок** і обробляє їх
            за своєю структурою. Різниця — виключно у вибраній структурі даних.
            """
        )
        return

    if not params["policies"]:
        st.warning("Виберіть хоча б одну політику в бічній панелі.")
        return

    with st.spinner("Запускаємо симуляцію…"):
        results = run_simulation(
            trips_df     = trips_df,
            arrival_rate = params["arrival_rate"],
            num_drivers  = params["num_drivers"],
            process_speed= params["process_speed"],
            policies     = params["policies"],
        )

    st.success(
        f"✅ Симуляція завершена · "
        f"{len(params['policies'])} політик · "
        f"{params['n_trips']:,} поїздок"
    )
    st.divider()

    render_kpi_cards(results)
    st.divider()

    render_queue_length_chart(results)
    render_throughput_chart(results)
    st.divider()

    render_wait_time_charts(results)
    st.divider()

    render_fairness_chart(results)
    st.divider()

    if Policy.PRIORITY in results and Policy.FIFO in results:
        render_priority_bias(results)
        st.divider()

    render_summary_table(results)
    st.divider()

    render_insights(results)


if __name__ == "__main__":
    main()
