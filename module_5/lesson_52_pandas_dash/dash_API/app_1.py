# ============================================
# 📦 ІМПОРТИ
# ============================================

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html
import os


# ============================================
# 📊 ЗАВАНТАЖЕННЯ ДАНИХ
# ============================================

BASE_DIR = os.path.dirname(__file__)
print("CWD:", os.getcwd())

DATA_PATH = os.path.join(
    BASE_DIR,
    "..",
    "data",
    "wfp_food_prices_ukr.csv"
)

df = pd.read_csv(DATA_PATH)


# ============================================
# 🔍 ПІДГОТОВКА ДАНИХ
# ============================================

print(df.columns)

# перетворимо дату
df["date"] = pd.to_datetime(df["date"], errors="coerce")


# ============================================
# 🔥 БЛОК ДЛЯ НАВЧАННЯ
# ============================================

# показуємо всі товари
print("Доступні товари:")
print(df["commodity"].unique())

# обираємо один товар
commodity = sorted(df["commodity"].dropna().unique())[0]

# фільтруємо
df = df[df["commodity"] == commodity]


# ============================================
# 📊 АГРЕГАЦІЯ
# ============================================

df_grouped = df.groupby("date")["price"].mean().reset_index()


# ============================================
# 📈 ГРАФІК
# ============================================

fig = px.line(
    df_grouped,
    x="date",
    y="price",
    title=f"📈 Ціна товару: {commodity}",
)


# ============================================
# 🌐 DASH APP
# ============================================

app_1 = Dash(__name__)

app_1.layout = html.Div(
    children=[
        html.H1("📊 Аналіз цін на продукти в Україні"),

        html.P(
            f"Зараз відображається товар: {commodity}"
        ),

        dcc.Graph(figure=fig),
    ]
)


# ============================================
# 🚀 RUN
# ============================================

if __name__ == "__main__":
    app_1.run(debug=True, port=8051)