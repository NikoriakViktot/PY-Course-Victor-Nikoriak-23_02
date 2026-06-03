# ============================================
# 📦 ІМПОРТИ
# ============================================

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
from pathlib import Path


# ============================================
# 📊 ЗАВАНТАЖЕННЯ ДАНИХ
# ============================================

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "data" / "wfp_food_prices_ukr.csv"

df = pd.read_csv(DATA_PATH)

df["date"] = pd.to_datetime(df["date"], errors="coerce")

# список товарів
commodities = df["commodity"].dropna().unique()


# ============================================
# 🌐 DASH APP
# ============================================

app_2 = Dash(__name__)

app_2.layout = html.Div([

    html.H1("📊 Інтерактивний аналіз цін"),

    html.P("Оберіть товар:"),

    # ----------------------------------------
    # 🔥 DROPDOWN (це новий елемент!)
    # ----------------------------------------
    dcc.Dropdown(
        options=[{"label": c, "value": c} for c in commodities],
        value=commodities[0],  # дефолт
        id="commodity-dropdown"
    ),

    # графік
    dcc.Graph(id="price-graph")
])


# ============================================
# 🔁 CALLBACK (СЕРЦЕ DASH)
# ============================================

@app_2.callback(
    Output("price-graph", "figure"),
    Input("commodity-dropdown", "value")
)
def update_graph(selected_commodity):

    # ----------------------------------------
    # 🧠 ТЕПЕР ДАНІ ЗАЛЕЖАТЬ ВІД UI
    # ----------------------------------------

    filtered_df = df[df["commodity"] == selected_commodity]

    df_grouped = (
        filtered_df
        .groupby("date")["price"]
        .mean()
        .reset_index()
    )

    fig = px.line(
        df_grouped,
        x="date",
        y="price",
        title=f"📈 {selected_commodity}"
    )

    return fig


# ============================================
# 🚀 RUN
# ============================================

if __name__ == "__main__":
    app_2.run(debug=True, port=8052)