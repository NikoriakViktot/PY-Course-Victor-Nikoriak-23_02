"""
Streamlit Dashboard — Lesson 34: asyncio
News Dashboard: async scraping demo + analytics.
"""

from __future__ import annotations

import os
import time
from datetime import date, timedelta
from typing import Any

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Inside Docker: http://fastapi-news:8000
# Outside Docker (localhost): http://localhost:8002
FASTAPI_HOST = os.environ.get("FASTAPI_HOST", "http://localhost:8002")
API_TIMEOUT = 120  # seconds — scraping can take a while

st.set_page_config(
    page_title="News Dashboard — rbc.ua",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def api(method: str, path: str, **kwargs) -> Any | None:
    """Make a synchronous HTTP request to the FastAPI backend."""
    url = f"{FASTAPI_HOST}{path}"
    try:
        resp = httpx.request(method, url, timeout=API_TIMEOUT, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        st.error(
            f"Не вдалося підключитися до FastAPI: {FASTAPI_HOST}. "
            "Перевірте, чи запущений контейнер `fastapi-news`."
        )
        return None
    except httpx.TimeoutException:
        st.error("Час очікування відповіді вичерпано. Спробуйте ще раз.")
        return None
    except httpx.HTTPStatusError as e:
        st.error(f"Помилка API: {e.response.status_code} — {e.response.text[:200]}")
        return None


def sentiment_badge(score: float) -> str:
    if score > 0:
        return f"🟢 {score:+.2f}"
    elif score < 0:
        return f"🔴 {score:+.2f}"
    else:
        return f"⚪ {score:.2f}"


def truncate(text: str, n: int = 80) -> str:
    return text if len(text) <= n else text[:n] + "…"


# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

if "scrape_result" not in st.session_state:
    st.session_state["scrape_result"] = None
if "scrape_mode" not in st.session_state:
    st.session_state["scrape_mode"] = None
if "archive_job_id" not in st.session_state:
    st.session_state["archive_job_id"] = None
if "archive_polling" not in st.session_state:
    st.session_state["archive_polling"] = False

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("📰 News Dashboard — rbc.ua")
st.caption(
    "Урок 34: asyncio · aiohttp · FastAPI · MongoDB · Streamlit  |  "
    f"API: `{FASTAPI_HOST}`"
)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_scrape, tab_news, tab_analytics, tab_archive, tab_mongo = st.tabs([
    "🚀 Async Scraping",
    "📰 Стрічка новин",
    "📊 Аналітика",
    "🗓 Архів (5 років)",
    "🗄️ MongoDB",
])

# ===========================================================================
# TAB 1: Async Scraping demo
# ===========================================================================

with tab_scrape:
    st.subheader("Демо: асинхронний vs. послідовний скрейпінг")
    st.markdown(
        """
        Натисніть **Async** — всі сторінки завантажуються **одночасно** (`asyncio.gather`).
        Натисніть **Sequential** — завантаження **по черзі**, без паралелізму.
        Діаграма Ганта покаже різницю.
        """
    )

    col_btn1, col_btn2, col_spacer = st.columns([1, 1, 4])

    with col_btn1:
        run_async = st.button("▶ Async (concurrent)", use_container_width=True, type="primary")
    with col_btn2:
        run_seq = st.button("▶ Sequential", use_container_width=True)

    if run_async or run_seq:
        mode = "async" if run_async else "sequential"
        label = "Асинхронний" if run_async else "Послідовний"

        progress_bar = st.progress(0, text=f"⏳ {label} скрейпінг запущено…")

        with st.spinner(f"Завантажую новини ({label} режим)…"):
            data = api("POST", "/api/scrape", json={"mode": mode, "pages": None})

        progress_bar.progress(100, text="Готово!")

        if data:
            st.session_state["scrape_result"] = data
            st.session_state["scrape_mode"] = mode

    result = st.session_state.get("scrape_result")

    if result:
        mode_label = "Асинхронний" if result["mode"] == "async" else "Послідовний"

        # Metrics row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Режим", mode_label)
        m2.metric("Час виконання", f"{result['total_time']:.2f} с")
        m3.metric("Нових новин збережено", result["news_saved"])
        m4.metric("Всього знайдено", result["news_total"])

        # If we have both async and sequential results in history, show speedup
        st.divider()

        # ---------------------------------------------------------------
        # Gantt chart
        # ---------------------------------------------------------------
        st.subheader("Діаграма Ганта — часова шкала запитів")

        gantt = result.get("gantt_data", [])
        if gantt:
            fig_gantt = go.Figure()

            for i, row in enumerate(gantt):
                url_short = row["url"].replace("https://www.rbc.ua", "rbc.ua")
                color = "#e74c3c" if row.get("error") else "#27ae60"
                count_label = f" ({row['count']} новин)" if row["count"] else " (0 новин)"
                error_label = f" ⚠ {row['error'][:40]}" if row.get("error") else ""

                fig_gantt.add_trace(
                    go.Bar(
                        x=[row["end"] - row["start"]],
                        y=[url_short],
                        base=[row["start"]],
                        orientation="h",
                        name=url_short,
                        marker_color=color,
                        text=f"{count_label}{error_label}",
                        textposition="inside",
                        insidetextanchor="middle",
                        hovertemplate=(
                            f"<b>{url_short}</b><br>"
                            f"Початок: {row['start']:.2f} с<br>"
                            f"Кінець: {row['end']:.2f} с<br>"
                            f"Тривалість: {row['end'] - row['start']:.2f} с<br>"
                            f"Новин: {row['count']}<br>"
                            f"Помилка: {row.get('error') or 'немає'}"
                            "<extra></extra>"
                        ),
                        showlegend=False,
                    )
                )

            fig_gantt.update_layout(
                title=f"{mode_label} скрейпінг — {result['total_time']:.2f} с загалом",
                xaxis_title="Час (секунди)",
                yaxis_title="URL",
                barmode="overlay",
                height=60 + len(gantt) * 55,
                margin=dict(l=10, r=10, t=50, b=40),
                plot_bgcolor="#0e1117",
                paper_bgcolor="#0e1117",
                font=dict(color="#fafafa"),
                xaxis=dict(
                    gridcolor="#333",
                    showgrid=True,
                ),
                yaxis=dict(
                    autorange="reversed",
                    tickfont=dict(size=11),
                ),
            )

            # Vertical line at total_time
            fig_gantt.add_vline(
                x=result["total_time"],
                line_dash="dash",
                line_color="#f39c12",
                annotation_text=f"Загалом: {result['total_time']:.2f} с",
                annotation_position="top right",
                annotation_font_color="#f39c12",
            )

            st.plotly_chart(fig_gantt, use_container_width=True)

            # Legend
            col_leg1, col_leg2 = st.columns(2)
            col_leg1.markdown("🟢 Успішно завантажено")
            col_leg2.markdown("🔴 Помилка завантаження")

        else:
            st.info("Немає даних для діаграми.")

        # ---------------------------------------------------------------
        # Table of page results
        # ---------------------------------------------------------------
        st.subheader("Результати по сторінках")
        df_gantt = pd.DataFrame(
            [
                {
                    "URL": r["url"],
                    "Початок (с)": round(r["start"], 3),
                    "Кінець (с)": round(r["end"], 3),
                    "Тривалість (с)": round(r["end"] - r["start"], 3),
                    "Новин": r["count"],
                    "Помилка": r.get("error") or "—",
                }
                for r in gantt
            ]
        )
        st.dataframe(df_gantt, use_container_width=True, hide_index=True)

    else:
        st.info(
            "Натисніть **▶ Async (concurrent)** або **▶ Sequential**, "
            "щоб запустити скрейпінг rbc.ua."
        )

# ===========================================================================
# TAB 2: News feed  (markdown cards + pagination)
# ===========================================================================

PAGE_SIZE = 20


def _sentiment_color(score: float) -> str:
    if score > 0:
        return "🟢"
    elif score < 0:
        return "🔴"
    return "⚪"


_ENTITY_ICON = {"PER": "👤", "ORG": "🏢", "LOC": "📍", "GPE": "🌍", "MISC": "🔹"}


def _format_entities(entities: list[dict]) -> str:
    if not entities:
        return ""
    parts = [
        f"{_ENTITY_ICON.get(e['label'], '🔹')} {e['text']}"
        for e in entities[:5]
    ]
    return "  |  **Сутності:** " + " · ".join(parts)


def render_news_card(article: dict) -> None:
    score = article.get("sentiment_score", 0.0)
    badge = _sentiment_color(score)
    kws = ", ".join(article.get("keywords", [])) or "—"
    pub = (article.get("pub_date") or "")[:10] or "—"
    desc = article.get("description", "").strip()
    desc_block = f"\n{desc}" if desc else ""
    ent_block = _format_entities(article.get("entities", []))
    st.markdown(
        f"""
### {article['title']}

**Категорія:** {article['category']} &nbsp;|&nbsp;
**Дата:** {pub} &nbsp;|&nbsp;
**Тональність:** {badge} `{score:+.2f}` &nbsp;|&nbsp;
**Ключові слова:** _{kws}_{ent_block}{desc_block}

[Читати статтю →]({article['url']})

---
"""
    )


with tab_news:
    st.subheader("Стрічка новин")

    # ── Filters ─────────────────────────────────────────────────────────────
    stats_for_filter = api("GET", "/api/news/stats")
    categories = ["Всі категорії"]
    if stats_for_filter and stats_for_filter.get("categories"):
        categories += [c["category"] for c in stats_for_filter["categories"]]

    cf1, cf2, cf3, cf4, cf5 = st.columns([2, 1, 1, 1, 1])
    with cf1:
        selected_cat = st.selectbox("Категорія", categories, key="news_cat")
    with cf2:
        sent_filter = st.selectbox(
            "Тональність", ["Всі", "Позитивна", "Нейтральна", "Негативна"], key="news_sent"
        )
    with cf3:
        lang_options = {"Всі мови": "", "🇺🇦 Українська": "uk", "🇷🇺 Російська": "ru"}
        lang_sel = st.selectbox("Мова", list(lang_options.keys()), key="news_lang")
    with cf4:
        search_kw = st.text_input("Пошук у заголовку", key="news_search", placeholder="ключове слово…")
    with cf5:
        st.write("")
        st.write("")
        st.button("🔄 Оновити", use_container_width=True, key="news_refresh")

    # ── Load data (fetch max 500, filter client-side for pagination) ─────────
    cat_param = "" if selected_cat == "Всі категорії" else selected_cat
    lang_param = lang_options[lang_sel]
    news_data = api("GET", "/api/news", params={"limit": 500, "category": cat_param, "lang": lang_param}) or []
    count_data = api("GET", "/api/news/count")

    total_db = count_data["count"] if count_data else 0
    st.metric("Всього новин у базі", total_db)

    # Client-side sentiment filter
    if sent_filter == "Позитивна":
        news_data = [n for n in news_data if n.get("sentiment_score", 0) > 0]
    elif sent_filter == "Негативна":
        news_data = [n for n in news_data if n.get("sentiment_score", 0) < 0]
    elif sent_filter == "Нейтральна":
        news_data = [n for n in news_data if n.get("sentiment_score", 0) == 0]

    # Client-side keyword search
    if search_kw.strip():
        q = search_kw.strip().lower()
        news_data = [n for n in news_data if q in n.get("title", "").lower()]

    if not news_data:
        st.info("🗃 Запустіть scraping на вкладці **🚀 Async Scraping**, щоб завантажити новини.")
    else:
        total_filtered = len(news_data)
        total_pages = max(1, (total_filtered + PAGE_SIZE - 1) // PAGE_SIZE)

        st.caption(f"Знайдено: **{total_filtered}** новин · сторінка")

        # Pagination control
        page = st.number_input(
            "Сторінка", min_value=1, max_value=total_pages, value=1, step=1,
            key="news_page",
            label_visibility="collapsed",
        )
        st.caption(f"{page} / {total_pages}")

        start_i = (page - 1) * PAGE_SIZE
        end_i = start_i + PAGE_SIZE
        page_items = news_data[start_i:end_i]

        for article in page_items:
            render_news_card(article)

# ===========================================================================
# TAB 3: Analytics
# ===========================================================================

with tab_analytics:
    st.subheader("Аналітика новин")

    stats = api("GET", "/api/news/stats")
    keywords_data = api("GET", "/api/news/keywords")
    count_resp = api("GET", "/api/news/count")

    if not stats or not count_resp or count_resp["count"] == 0:
        st.info("🗃 Запустіть scraping на вкладці **🚀 Async Scraping**, щоб побачити аналітику.")
    else:
        sentiment = stats.get("sentiment", {})
        total_news = count_resp["count"]
        unique_cats = len(stats.get("categories", []))
        avg_sent = sentiment.get("avg_sentiment", 0.0) or 0.0

        # Row 1: Metrics
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("📰 Всього новин", total_news)
        mc2.metric("🏷 Унікальних категорій", unique_cats)
        mc3.metric(
            "💬 Середня тональність",
            f"{avg_sent:+.3f}",
            delta=None,
        )

        st.divider()

        # Row 2: Pie + Keywords bar
        col_pie, col_kw = st.columns(2)

        with col_pie:
            st.markdown("**Розподіл за категоріями**")
            cats = stats.get("categories", [])
            if cats:
                df_cats = pd.DataFrame(cats)
                fig_pie = px.pie(
                    df_cats,
                    names="category",
                    values="count",
                    hole=0.35,
                    color_discrete_sequence=px.colors.qualitative.Plotly,
                )
                fig_pie.update_layout(
                    margin=dict(t=20, b=20, l=0, r=0),
                    height=380,
                    legend=dict(orientation="v", x=1.0, y=0.5),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Немає даних.")

        with col_kw:
            st.markdown("**Топ-20 ключових слів**")
            if keywords_data:
                df_kw = pd.DataFrame(keywords_data[:20])
                fig_kw = px.bar(
                    df_kw,
                    x="count",
                    y="keyword",
                    orientation="h",
                    color="count",
                    color_continuous_scale="Teal",
                    labels={"count": "Кількість", "keyword": "Слово"},
                )
                fig_kw.update_layout(
                    yaxis=dict(autorange="reversed"),
                    height=380,
                    margin=dict(t=20, b=20, l=0, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_kw, use_container_width=True)
            else:
                st.info("Немає даних.")

        st.divider()

        # Row 3: Timeline + Sentiment histogram
        col_time, col_sent = st.columns(2)

        with col_time:
            tl_group = st.radio(
                "Групування часової шкали", ["day", "month", "year"],
                horizontal=True, key="tl_group",
                format_func=lambda x: {"day": "День", "month": "Місяць", "year": "Рік"}[x],
            )
            timeline_data = api("GET", "/api/news/timeline", params={"group_by": tl_group})
            st.markdown("**Кількість новин і середня тональність**")
            if timeline_data:
                df_tl = pd.DataFrame(timeline_data)
                fig_tl = go.Figure()
                fig_tl.add_trace(go.Bar(
                    x=df_tl["date"], y=df_tl["count"],
                    name="Новин", marker_color="#3498db", opacity=0.7,
                    yaxis="y1",
                ))
                fig_tl.add_trace(go.Scatter(
                    x=df_tl["date"], y=df_tl["avg_sentiment"],
                    name="Середня тональність", mode="lines+markers",
                    line=dict(color="#f39c12", width=2),
                    yaxis="y2",
                ))
                fig_tl.update_layout(
                    height=320,
                    margin=dict(t=20, b=30, l=0, r=50),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(gridcolor="#333"),
                    yaxis=dict(title="Новин", gridcolor="#333"),
                    yaxis2=dict(
                        title="Тональність",
                        overlaying="y", side="right",
                        range=[-1, 1],
                        gridcolor="#333",
                        zeroline=True,
                        zerolinecolor="#555",
                    ),
                    legend=dict(orientation="h", y=1.1),
                )
                st.plotly_chart(fig_tl, use_container_width=True)
            else:
                st.info("Немає даних.")

        with col_sent:
            st.markdown("**Розподіл тональності**")
            pos = sentiment.get("positive", 0)
            neu = sentiment.get("neutral", 0)
            neg = sentiment.get("negative", 0)

            if pos + neu + neg > 0:
                df_sent = pd.DataFrame({
                    "Тональність": ["Позитивна", "Нейтральна", "Негативна"],
                    "Кількість": [pos, neu, neg],
                    "Колір": ["#27ae60", "#95a5a6", "#e74c3c"],
                })
                fig_sent = px.bar(
                    df_sent,
                    x="Тональність",
                    y="Кількість",
                    color="Тональність",
                    color_discrete_map={
                        "Позитивна": "#27ae60",
                        "Нейтральна": "#95a5a6",
                        "Негативна": "#e74c3c",
                    },
                )
                fig_sent.update_layout(
                    height=320,
                    margin=dict(t=20, b=30, l=0, r=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    xaxis=dict(gridcolor="#333"),
                    yaxis=dict(gridcolor="#333"),
                )
                st.plotly_chart(fig_sent, use_container_width=True)
            else:
                st.info("Немає даних.")

        # ── Keyword trend section ────────────────────────────────────────────
        st.divider()
        st.markdown("### Тренд ключового слова")
        st.caption(
            "Скільки разів слово зустрічалося в заголовках — по датах. "
            "Показує сплески подій та зміну тональності навколо теми."
        )

        kw_col1, kw_col2, kw_col3 = st.columns([2, 1, 1])
        with kw_col1:
            trend_kw = st.text_input(
                "Ключове слово для тренду",
                value="україн",
                key="trend_kw",
                placeholder="напр. трамп, росія, економ…",
            )
        with kw_col2:
            trend_group = st.radio(
                "Групування", ["month", "day", "year"],
                key="trend_group",
                format_func=lambda x: {"day": "День", "month": "Місяць", "year": "Рік"}[x],
                horizontal=True,
            )
        with kw_col3:
            st.write("")
            run_trend = st.button("🔍 Побудувати тренд", use_container_width=True, key="trend_btn")

        if trend_kw and run_trend:
            trend_data = api(
                "GET", "/api/news/trends",
                params={"keyword": trend_kw, "group_by": trend_group},
            )
            if trend_data:
                df_tr = pd.DataFrame(trend_data)
                total_mentions = int(df_tr["count"].sum())
                avg_sent_kw = round(df_tr["avg_sentiment"].mean(), 3)

                tc1, tc2 = st.columns(2)
                tc1.metric(f'Згадок «{trend_kw}»', total_mentions)
                tc2.metric("Середня тональність", f"{avg_sent_kw:+.3f}")

                fig_tr = go.Figure()
                fig_tr.add_trace(go.Bar(
                    x=df_tr["date"], y=df_tr["count"],
                    name="Згадок", marker_color="#9b59b6", opacity=0.75,
                    yaxis="y1",
                ))
                fig_tr.add_trace(go.Scatter(
                    x=df_tr["date"], y=df_tr["avg_sentiment"],
                    name="Тональність", mode="lines+markers",
                    line=dict(color="#f39c12", width=2),
                    yaxis="y2",
                ))
                fig_tr.add_hline(y=0, line_dash="dot", line_color="#555", yref="y2")
                fig_tr.update_layout(
                    title=f'Тренд «{trend_kw}» ({trend_group})',
                    height=360,
                    margin=dict(t=40, b=40, l=0, r=60),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(gridcolor="#333"),
                    yaxis=dict(title="Згадок", gridcolor="#333"),
                    yaxis2=dict(
                        title="Тональність", overlaying="y", side="right",
                        range=[-1, 1], gridcolor="#222",
                        zeroline=True, zerolinecolor="#555",
                    ),
                    legend=dict(orientation="h", y=1.1),
                )
                st.plotly_chart(fig_tr, use_container_width=True)
            else:
                st.warning(f"Нічого не знайдено для «{trend_kw}».")

        # ── Entity analysis section ──────────────────────────────────────────
        st.divider()
        st.markdown("### Аналіз сутностей (spaCy NER)")
        st.caption(
            "spaCy `uk_core_news_sm` автоматично виділяє: "
            "👤 Персони · 🏢 Організації · 📍 Локації · 🌍 Країни"
        )

        # Backfill button for existing articles
        reanalyze_col, _ = st.columns([2, 3])
        with reanalyze_col:
            if st.button("🔄 Додати сутності до всіх статей (backfill)", key="reanalyze_btn"):
                resp = api("POST", "/api/news/reanalyze")
                if resp:
                    n = resp.get("articles_to_process", 0)
                    if n > 0:
                        st.success(f"Запущено фоновий аналіз для {n} статей. Оновіть сторінку за ~30 с.")
                    else:
                        st.info("Всі статті вже мають сутності.")

        ent_col1, ent_col2 = st.columns([1, 2])
        with ent_col1:
            ent_type_map = {
                "Всі типи": "",
                "👤 Персони (PER)": "PER",
                "🏢 Організації (ORG)": "ORG",
                "📍 Локації (LOC)": "LOC",
                "🌍 Країни (GPE)": "GPE",
                "🔹 Інші (MISC)": "MISC",
            }
            ent_type_sel = st.selectbox(
                "Тип сутності", list(ent_type_map.keys()), key="ent_type"
            )
            ent_limit = st.slider("Топ N", 10, 50, 25, key="ent_limit")

        with ent_col2:
            entities_data = api(
                "GET", "/api/news/entities",
                params={"entity_type": ent_type_map[ent_type_sel], "limit": ent_limit},
            )
            if entities_data:
                df_ent = pd.DataFrame(entities_data)
                color_map = {
                    "PER": "#3498db", "ORG": "#e67e22",
                    "LOC": "#27ae60", "GPE": "#9b59b6", "MISC": "#95a5a6",
                }
                df_ent["color"] = df_ent["label"].map(color_map).fillna("#95a5a6")
                fig_ent = px.bar(
                    df_ent,
                    x="count", y="text",
                    orientation="h",
                    color="label",
                    color_discrete_map=color_map,
                    labels={"count": "Згадок", "text": "Сутність", "label": "Тип"},
                    title=f"Топ {ent_limit} сутностей",
                )
                fig_ent.update_layout(
                    yaxis=dict(autorange="reversed"),
                    height=max(300, ent_limit * 22),
                    margin=dict(t=40, b=20, l=0, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_ent, use_container_width=True)
            else:
                st.info(
                    "Сутності ще не завантажені. "
                    "Запустіть scraping — нові статті матимуть NER автоматично."
                )

        # Entity trend over time
        st.markdown("**Тренд конкретної сутності**")
        et_col1, et_col2, et_col3 = st.columns([2, 1, 1])
        with et_col1:
            entity_name = st.text_input(
                "Сутність", value="Зеленськ", key="ent_trend_name",
                placeholder="напр. Зеленськ, НАТО, Київ…",
            )
        with et_col2:
            entity_group = st.radio(
                "Групування", ["month", "day"],
                key="ent_trend_group",
                format_func=lambda x: {"day": "День", "month": "Місяць"}[x],
                horizontal=True,
            )
        with et_col3:
            st.write("")
            run_ent_trend = st.button("📈 Показати", use_container_width=True, key="ent_trend_btn")

        if entity_name and run_ent_trend:
            ent_trend_data = api(
                "GET", "/api/news/entity-trend",
                params={"entity": entity_name, "group_by": entity_group},
            )
            if ent_trend_data:
                df_et = pd.DataFrame(ent_trend_data)
                total_ent = int(df_et["count"].sum())
                avg_ent_sent = round(df_et["avg_sentiment"].mean(), 3)

                ec1, ec2 = st.columns(2)
                ec1.metric(f'Згадок «{entity_name}»', total_ent)
                ec2.metric("Середня тональність", f"{avg_ent_sent:+.3f}")

                fig_et = go.Figure()
                fig_et.add_trace(go.Bar(
                    x=df_et["date"], y=df_et["count"],
                    name="Згадок", marker_color="#3498db", opacity=0.75,
                    yaxis="y1",
                ))
                fig_et.add_trace(go.Scatter(
                    x=df_et["date"], y=df_et["avg_sentiment"],
                    name="Тональність", mode="lines+markers",
                    line=dict(color="#e74c3c", width=2), yaxis="y2",
                ))
                fig_et.add_hline(y=0, line_dash="dot", line_color="#555", yref="y2")
                fig_et.update_layout(
                    title=f'Сутність «{entity_name}» по {entity_group}',
                    height=340,
                    margin=dict(t=40, b=40, l=0, r=60),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(gridcolor="#333"),
                    yaxis=dict(title="Згадок", gridcolor="#333"),
                    yaxis2=dict(
                        title="Тональність", overlaying="y", side="right",
                        range=[-1, 1], gridcolor="#222",
                        zeroline=True, zerolinecolor="#555",
                    ),
                    legend=dict(orientation="h", y=1.1),
                )
                st.plotly_chart(fig_et, use_container_width=True)
            else:
                st.warning(f"Нічого не знайдено для «{entity_name}».")

# ===========================================================================
# TAB 4: Archive Scraping (multi-year)
# ===========================================================================

with tab_archive:
    st.subheader("🗓 Архівний скрейпінг rbc.ua — до 5 років")
    st.markdown(
        """
        Збирає всі новини з `rbc.ua/rus/archive/YYYY/MM/DD` за вибраний діапазон дат.
        Використовує `asyncio.Semaphore` для ввічливого паралельного завантаження.
        Прогрес зберігається в MongoDB (`scrape_jobs`), відображається в реальному часі.
        """
    )

    # ── Config ───────────────────────────────────────────────────────────────
    col_d1, col_d2, col_c1, col_c2 = st.columns([2, 2, 1, 1])
    with col_d1:
        arc_start = st.date_input(
            "Початкова дата",
            value=date.today() - timedelta(days=365 * 5),
            min_value=date(2010, 1, 1),
            max_value=date.today(),
            key="arc_start",
        )
    with col_d2:
        arc_end = st.date_input(
            "Кінцева дата",
            value=date.today(),
            min_value=date(2010, 1, 1),
            max_value=date.today(),
            key="arc_end",
        )
    with col_c1:
        arc_concurrent = st.number_input(
            "Паралельних запитів", min_value=1, max_value=30, value=10, key="arc_conc"
        )
    with col_c2:
        arc_delay = st.number_input(
            "Затримка між батчами (с)", min_value=0.0, max_value=5.0,
            value=1.0, step=0.5, key="arc_delay"
        )

    days_total = max(0, (arc_end - arc_start).days + 1)
    st.caption(
        f"Діапазон: **{arc_start}** → **{arc_end}** · **{days_total}** днів "
        f"(≈{days_total * 100:,} новин)"
    )

    # ── Start / Cancel buttons ────────────────────────────────────────────────
    col_btn_a, col_btn_b, _ = st.columns([1, 1, 3])
    with col_btn_a:
        start_archive = st.button(
            "▶ Запустити скрейпінг", type="primary",
            use_container_width=True, key="arc_start_btn",
            disabled=st.session_state["archive_polling"],
        )
    with col_btn_b:
        stop_polling = st.button(
            "⏹ Зупинити відстеження",
            use_container_width=True, key="arc_stop_btn",
            disabled=not st.session_state["archive_polling"],
        )

    if stop_polling:
        st.session_state["archive_polling"] = False
        st.rerun()

    if start_archive and arc_start <= arc_end:
        resp = api("POST", "/api/scrape/archive", json={
            "start_date": arc_start.isoformat(),
            "end_date": arc_end.isoformat(),
            "max_concurrent": int(arc_concurrent),
            "batch_size": 30,
            "batch_delay": float(arc_delay),
        })
        if resp:
            st.session_state["archive_job_id"] = resp["job_id"]
            st.session_state["archive_polling"] = True
            st.rerun()

    # ── Progress display ─────────────────────────────────────────────────────
    job_id = st.session_state.get("archive_job_id")
    if job_id:
        job = api("GET", f"/api/scrape/archive/{job_id}")
        if job:
            pct = float(job.get("progress_pct", 0))
            status = job.get("status", "unknown")

            st.progress(int(pct) / 100, text=f"Прогрес: {pct:.1f}% — статус: **{status}**")

            jc1, jc2, jc3, jc4, jc5 = st.columns(5)
            jc1.metric("Оброблено днів", f"{job['days_done']} / {job['total_days']}")
            jc2.metric("Збережено", job["articles_saved"])
            jc3.metric("Пропущено (дублі)", job["articles_skipped"])
            jc4.metric("Помилки", job["errors"])
            jc5.metric("Статус", status)

            if status == "running" and st.session_state["archive_polling"]:
                time.sleep(3)
                st.rerun()
            elif status == "done":
                st.success(
                    f"Архівний скрейпінг завершено! "
                    f"Збережено {job['articles_saved']:,} нових статей."
                )
                st.session_state["archive_polling"] = False

    # ── History of all jobs ──────────────────────────────────────────────────
    st.divider()
    st.markdown("**Усі задачі скрейпінгу**")
    jobs_list = api("GET", "/api/scrape/jobs") or []
    if not jobs_list:
        st.info("Ще не було жодного архівного скрейпінгу.")
    else:
        df_jobs = pd.DataFrame([
            {
                "job_id": j["job_id"][:8] + "…",
                "Статус": j["status"],
                "Від": j["start_date"],
                "До": j["end_date"],
                "Днів": j["total_days"],
                "Оброблено": j["days_done"],
                "Збережено": j["articles_saved"],
                "Прогрес": f"{j['progress_pct']:.1f}%",
                "Початок": (j.get("started_at") or "")[:19],
                "Кінець": (j.get("finished_at") or "")[:19],
            }
            for j in jobs_list
        ])
        st.dataframe(df_jobs, use_container_width=True, hide_index=True)

    # ── Multi-year sentiment timeline ────────────────────────────────────────
    st.divider()
    st.markdown("**Багаторічний аналіз тональності (по місяцях)**")
    mtl = api("GET", "/api/news/timeline", params={"group_by": "month"}) or []
    if not mtl:
        st.info("Недостатньо даних — запустіть архівний скрейпінг.")
    else:
        df_mtl = pd.DataFrame(mtl)
        fig_mtl = go.Figure()
        fig_mtl.add_trace(go.Bar(
            x=df_mtl["date"], y=df_mtl["count"],
            name="Новин/місяць", marker_color="#3498db", opacity=0.6, yaxis="y1",
        ))
        fig_mtl.add_trace(go.Scatter(
            x=df_mtl["date"], y=df_mtl["avg_sentiment"],
            name="Тональність (середня)", mode="lines+markers",
            line=dict(color="#e74c3c", width=2), yaxis="y2",
        ))
        fig_mtl.add_hline(y=0, line_dash="dash", line_color="#888", yref="y2")
        fig_mtl.update_layout(
            title="Тональність медіа rbc.ua по місяцях",
            xaxis_title="Місяць",
            height=420,
            margin=dict(t=40, b=40, l=0, r=60),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="#333"),
            yaxis=dict(title="Кількість новин", gridcolor="#333"),
            yaxis2=dict(
                title="Середня тональність",
                overlaying="y", side="right",
                range=[-1, 1], gridcolor="#222",
                zeroline=True, zerolinecolor="#555",
            ),
            legend=dict(orientation="h", y=1.08),
        )
        st.plotly_chart(fig_mtl, use_container_width=True)

        # Year summary table
        df_yr = df_mtl.copy()
        df_yr["year"] = df_yr["date"].str[:4]
        yearly = df_yr.groupby("year").agg(
            news_count=("count", "sum"),
            avg_sentiment=("avg_sentiment", "mean"),
        ).reset_index()
        yearly["avg_sentiment"] = yearly["avg_sentiment"].round(3)
        st.markdown("**Зведення по роках**")
        st.dataframe(yearly, use_container_width=True, hide_index=True)


# ===========================================================================
# TAB 5: MongoDB
# ===========================================================================

with tab_mongo:
    st.subheader("MongoDB — останні документи")

    col_db1, col_db2 = st.columns([3, 1])

    with col_db1:
        count_resp2 = api("GET", "/api/news/count")
        total_db = count_resp2["count"] if count_resp2 else 0
        st.metric("Документів у колекції `news`", total_db)

    with col_db2:
        st.write("")
        if st.button("🗑 Очистити всі новини", type="secondary", use_container_width=True):
            result_del = api("DELETE", "/api/news")
            if result_del is not None:
                st.success(f"Видалено {result_del.get('deleted', 0)} документів.")
                st.rerun()

    st.divider()
    st.markdown("**Останні 10 документів (raw JSON)**")

    raw_news = api("GET", "/api/news", params={"limit": 10, "skip": 0})
    if not raw_news:
        st.info("🗃 Запустіть scraping на вкладці **🚀 Async Scraping**, щоб побачити дані.")
    elif len(raw_news) == 0:
        st.warning("База даних порожня.")
    else:
        for i, doc in enumerate(raw_news, 1):
            with st.expander(f"#{i} — {truncate(doc['title'], 70)}", expanded=(i == 1)):
                st.json(doc)

    st.divider()
    st.markdown(
        """
        **Структура документа MongoDB:**
        ```json
        {
          "title":          "string",
          "url":            "string  (унікальний індекс)",
          "category":       "string",
          "description":    "string",
          "pub_date":       "datetime | null",
          "scraped_at":     "datetime (UTC)",
          "source":         "rbc.ua",
          "sentiment_score": 0.0,
          "keywords":       ["слово1", "слово2", ...],
          "word_count":     42
        }
        ```
        """
    )
