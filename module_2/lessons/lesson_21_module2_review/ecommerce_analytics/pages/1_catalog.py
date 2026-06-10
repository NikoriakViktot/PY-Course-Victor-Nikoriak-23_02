
"""
app.py — ShopHub: каталог товарів

Проста сторінка для перегляду товарів з фільтрацією та базовою аналітикою.

"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

# Додаємо поточну папку до шляху — щоб знайти data_loader.py
sys.path.insert(0, str(Path(__file__).parent))

from core.data_loader import load_catalog, apply_filters, top_brands
# ─────────────────────────────────────────────────────────────────────────────
# НАЛАШТУВАННЯ СТОРІНКИ
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="ShopHub — Каталог товарів",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Мінімальний CSS: трохи збільшуємо шрифт у таблиці і прибираємо зайві відступи
st.markdown(
    """
    <style>
    thead tr th { font-size: 13px !important; }
    tbody tr td { font-size: 13px !important; }
    .block-container { padding-top: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# ЗАВАНТАЖЕННЯ ДАНИХ
# 1M рядків читається один раз і кешується.
# Всі наступні взаємодії користувача — без повторного читання файлу.
# ─────────────────────────────────────────────────────────────────────────────

with st.spinner("Завантажуємо каталог товарів…"):
    df = load_catalog()

# ─────────────────────────────────────────────────────────────────────────────
# ШАПКА МАГАЗИНУ
# ─────────────────────────────────────────────────────────────────────────────

st.title("🛒 ShopHub")
st.markdown(
    "Знаходьте найкращі товари за вигідними цінами. "
    f"У каталозі **{len(df):,}** пропозицій."
)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# БОКОВА ПАНЕЛЬ — ФІЛЬТРИ
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("🔍 Фільтри")

    # --- Категорія ---
    all_categories = sorted(df["category"].unique())
    selected_categories = st.multiselect(
        "Категорія",
        options=all_categories,
        default=all_categories,
    )

    # --- Бренд ---
    # Щоб список брендів не був надто довгим — показуємо топ-20 за популярністю.
    # Фільтруємо бренди за вже обраними категоріями для кращого UX.
    cat_subset = df[df["category"].isin(selected_categories)] if selected_categories else df
    popular = top_brands(cat_subset, n=20)
    selected_brands = st.multiselect(
        "Бренд (топ-20)",
        options=popular,
        default=[],
        help="Порожньо = всі бренди",
    )

    st.markdown("---")

    # --- Ціна ---
    price_min = int(df["final_price"].min())
    price_max = int(df["final_price"].max())
    price_range = st.slider(
        "Ціна (₹)",
        min_value=price_min,
        max_value=price_max,
        value=(price_min, 30_000),
        step=500,
        format="₹%d",
    )

    # --- Рейтинг ---
    min_rating = st.slider(
        "Мінімальний рейтинг ⭐",
        min_value=1.0,
        max_value=5.0,
        value=3.0,
        step=0.1,
    )

    # --- Статус доставки ---
    statuses = ["Всі"] + sorted(df["delivery_status"].dropna().unique().tolist())
    selected_delivery = st.selectbox("Статус доставки", statuses)

    st.markdown("---")
    st.caption(f"Датасет: **{len(df):,}** рядків")
    st.caption(
        "⚡ 1M рядків обробляємо ефективно: "
        "читаємо тільки потрібні колонки, "
        "кешуємо після першого завантаження, "
        "відображаємо відфільтровану вибірку."
    )

# ─────────────────────────────────────────────────────────────────────────────
# ФІЛЬТРАЦІЯ
# ─────────────────────────────────────────────────────────────────────────────

filtered = apply_filters(
    df,
    categories=selected_categories,
    brands=selected_brands,
    price_range=price_range,
    min_rating=min_rating,
    delivery=selected_delivery,
)

# ─────────────────────────────────────────────────────────────────────────────
# KPI — 4 ключові показники
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("📊 Загальна статистика")

k1, k2, k3, k4 = st.columns(4)

if len(filtered) == 0:
    for col in [k1, k2, k3, k4]:
        col.metric("—", "—")
else:
    k1.metric(
        "Знайдено пропозицій",
        f"{len(filtered):,}",
        help="Кількість записів після застосування фільтрів",
    )
    k2.metric(
        "Середня ціна",
        f"₹{filtered['final_price'].mean():,.0f}",
    )
    k3.metric(
        "Середній рейтинг",
        f"{filtered['rating'].mean():.2f} ⭐",
    )
    k4.metric(
        "Частка повернень",
        f"{filtered['is_returned'].mean():.1%}",
        help="Скільки % товарів з цієї вибірки були повернені",
    )

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# КАТАЛОГ ТОВАРІВ
# Відображаємо максимум 150 рядків — показувати 1M рядків у браузері
# неможливо: це зависить вкладку. 150 — достатньо для перегляду.
# ─────────────────────────────────────────────────────────────────────────────

DISPLAY_LIMIT = 150

st.subheader("📦 Каталог товарів")

if len(filtered) == 0:
    st.warning("⚠️ Товарів не знайдено. Спробуйте змінити фільтри.")
else:
    st.caption(
        f"Показуємо **{min(DISPLAY_LIMIT, len(filtered))}** "
        f"з **{len(filtered):,}** знайдених пропозицій."
    )

    # Вибираємо потрібні колонки і перейменовуємо на українські назви
    catalog_view = (
        filtered
        .head(DISPLAY_LIMIT)
        [[
            "product_id", "brand", "category", "subcategory",
            "final_price", "discount", "rating", "review_count",
            "stock", "seller_rating", "delivery_status",
        ]]
        .rename(columns={
            "product_id":     "Артикул",
            "brand":          "Бренд",
            "category":       "Категорія",
            "subcategory":    "Підкатегорія",
            "final_price":    "Ціна (₹)",
            "discount":       "Знижка (%)",
            "rating":         "Рейтинг ⭐",
            "review_count":   "Відгуки",
            "stock":          "Залишок",
            "seller_rating":  "Рейтинг продавця",
            "delivery_status":"Статус доставки",
        })
    )

    # column_config: задаємо формат кожного стовпця
    st.dataframe(
        catalog_view,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ціна (₹)":           st.column_config.NumberColumn(format="₹%d"),
            "Знижка (%)":         st.column_config.NumberColumn(format="%.1f%%"),
            "Рейтинг ⭐":         st.column_config.NumberColumn(format="%.1f ⭐", min_value=1, max_value=5),
            "Рейтинг продавця":   st.column_config.NumberColumn(format="%.1f"),
            "Відгуки":            st.column_config.NumberColumn(format="%d"),
            "Залишок":            st.column_config.NumberColumn(format="%d шт."),
        },
    )

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# АНАЛІТИКА КАТАЛОГУ — 3 графіки
# Використовуємо агрегації, а не сирі дані.
# Групуємо → малюємо: замість 1M точок — 5–10 значень.
# ─────────────────────────────────────────────────────────────────────────────

st.subheader("📈 Аналітика каталогу")

if len(filtered) == 0:
    st.info("Немає даних для побудови графіків.")
else:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Кількість пропозицій за категоріями**")
        by_category = (
            filtered["category"]
            .value_counts()
            .rename_axis("Категорія")
            .rename("Кількість")
        )
        st.bar_chart(by_category, color="#4A90D9")

    with col2:
        st.markdown("**Середня ціна за категоріями (₹)**")
        avg_price = (
            filtered
            .groupby("category")["final_price"]
            .mean()
            .round(0)
            .sort_values(ascending=False)
            .rename_axis("Категорія")
            .rename("Середня ціна (₹)")
        )
        st.bar_chart(avg_price, color="#F5A623")

    st.markdown("**Топ-10 брендів за кількістю пропозицій**")
    top10 = (
        filtered["brand"]
        .value_counts()
        .head(10)
        .rename_axis("Бренд")
        .rename("Кількість")
    )
    st.bar_chart(top10, color="#7ED321")

    # Бонусна таблиця: середній рейтинг і ціна по категоріях
    st.markdown("**Порівняння категорій: рейтинг та ціна**")
    category_summary = (
        filtered
        .groupby("category")
        .agg(
            пропозицій=("product_id", "count"),
            середня_ціна=("final_price", "mean"),
            середній_рейтинг=("rating", "mean"),
            частка_повернень=("is_returned", "mean"),
        )
        .round(2)
        .sort_values("середній_рейтинг", ascending=False)
        .rename(columns={
            "пропозицій":       "Пропозицій",
            "середня_ціна":     "Середня ціна (₹)",
            "середній_рейтинг": "Рейтинг ⭐",
            "частка_повернень": "Повернення",
        })
    )
    st.dataframe(
        category_summary,
        use_container_width=True,
        column_config={
            "Середня ціна (₹)": st.column_config.NumberColumn(format="₹%.0f"),
            "Рейтинг ⭐":       st.column_config.NumberColumn(format="%.2f ⭐"),
            "Повернення":       st.column_config.NumberColumn(format="%.1%"),
        },
    )

# ─────────────────────────────────────────────────────────────────────────────
# ПІДВАЛ
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "ShopHub · Навчальний проєкт · "
    "Дані: Amazon India E-commerce Dataset · "
    "Побудовано на Streamlit"
)
