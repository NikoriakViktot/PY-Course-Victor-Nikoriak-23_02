"""
data_loader.py — завантаження та фільтрація каталогу товарів.

Чому окремий файл:
  app.py відповідає за UI.
  Цей файл відповідає за дані.
  Вони не змішуються.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

# Шлях до CSV — на рівень вище від цієї папки
DATA_PATH = Path(__file__).parent.parent / "data" / "amazon_ecommerce_1M.csv"

# Тільки потрібні для каталогу колонки.
# 1M рядків × 20 колонок → 1M рядків × 13 колонок = менше пам'яті.
CATALOG_COLS = [
    "product_id",
    "category",
    "subcategory",
    "brand",
    "price",
    "discount",
    "final_price",
    "rating",
    "review_count",
    "stock",
    "seller_rating",
    "delivery_status",
    "is_returned",
]


@st.cache_data(show_spinner=False)
def load_catalog() -> pd.DataFrame:
    """
    Читає CSV один раз, потім Streamlit тримає результат у кеші.
    Наступні перезавантаження сторінки — миттєві.

    Не завантажуємо всі 1M рядків у пам'ять без потреби:
    usecols зчитує тільки вказані колонки вже під час парсингу CSV.
    """
    df = pd.read_csv(DATA_PATH, usecols=CATALOG_COLS)
    # Округлюємо числа для чистішого відображення
    df["final_price"] = df["final_price"].round(0).astype(int)
    df["price"]       = df["price"].round(0).astype(int)
    df["discount"]    = df["discount"].round(1)
    df["rating"]      = df["rating"].round(1)
    return df


def apply_filters(
    df: pd.DataFrame,
    categories: list[str],
    brands: list[str],
    price_range: tuple[int, int],
    min_rating: float,
    delivery: str,
) -> pd.DataFrame:
    """
    Повертає відфільтрований датафрейм.
    Всі фільтри накладаються через булеву маску —
    один прохід по даних замість багатьох окремих .query() викликів.
    """
    mask = pd.Series(True, index=df.index)

    if categories:
        mask &= df["category"].isin(categories)

    if brands:
        mask &= df["brand"].isin(brands)

    mask &= df["final_price"].between(price_range[0], price_range[1])
    mask &= df["rating"] >= min_rating

    if delivery != "Всі":
        mask &= df["delivery_status"] == delivery

    return df[mask].reset_index(drop=True)


def top_brands(df: pd.DataFrame, n: int = 20) -> list[str]:
    """Топ-N брендів за кількістю записів — для розумного списку фільтру."""
    return df["brand"].value_counts().head(n).index.tolist()
