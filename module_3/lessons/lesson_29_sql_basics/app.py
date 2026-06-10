from __future__ import annotations

import json
import os
import re
from pathlib import Path

import duckdb
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html


HERE = Path(__file__).resolve().parent

DATA_ROOT = HERE / "data"
ZONES_SHP = HERE / "taxi_zones" / "taxi_zones.shp"

APP_TITLE = "NYC Yellow Taxi · BI Dashboard"
PORT = 8055

MONTHS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


def discover_parquet_files() -> list[Path]:
    files = sorted(DATA_ROOT.rglob("*.parquet"))

    if not files:
        raise FileNotFoundError(
            f"No parquet files found in {DATA_ROOT}. "
            f"Expected structure: data/year=2020/month=01/*.parquet"
        )

    return files


PARQUET_FILES = discover_parquet_files()
PARQUET_GLOB = (DATA_ROOT / "**" / "*.parquet").as_posix()

print("=" * 80)
print(f"[startup] Found {len(PARQUET_FILES)} parquet files")
print(f"[startup] Data lake path: {PARQUET_GLOB}")
print("=" * 80)


con = duckdb.connect(":memory:")

con.execute(f"""
CREATE OR REPLACE VIEW trips_raw AS
SELECT
    TRY_CAST(year AS INTEGER) AS file_year,
    TRY_CAST(month AS INTEGER) AS file_month,

    tpep_pickup_datetime,
    tpep_dropoff_datetime,

    EXTRACT(year FROM tpep_pickup_datetime)::INTEGER AS pickup_year,
    EXTRACT(month FROM tpep_pickup_datetime)::INTEGER AS pickup_month_num,
    DATE_TRUNC('month', tpep_pickup_datetime) AS pickup_month,

    EXTRACT(hour FROM tpep_pickup_datetime)::INTEGER AS pickup_hour,

    passenger_count,
    trip_distance,
    total_amount,
    fare_amount,
    tip_amount,
    PULocationID,
    DOLocationID
FROM read_parquet(
    '{PARQUET_GLOB}',
    hive_partitioning = true,
    union_by_name = true
)
WHERE trip_distance > 0.1
  AND trip_distance < 100
  AND total_amount > 0
  AND tpep_pickup_datetime IS NOT NULL
  AND PULocationID IS NOT NULL
""")

con.execute("""
CREATE OR REPLACE VIEW base_trips AS
SELECT *
FROM trips_raw
WHERE file_year BETWEEN 2019 AND 2023
""")


def available_years() -> list[int]:
    rows = con.execute("""
        SELECT DISTINCT file_year
        FROM base_trips
        WHERE file_year IS NOT NULL
        ORDER BY file_year
    """).fetchall()
    return [int(r[0]) for r in rows]


def available_months(year: int | None = None) -> list[int]:
    if year:
        rows = con.execute("""
            SELECT DISTINCT file_month
            FROM base_trips
            WHERE file_year = ?
              AND file_month IS NOT NULL
            ORDER BY file_month
        """, [year]).fetchall()
    else:
        rows = con.execute("""
            SELECT DISTINCT file_month
            FROM base_trips
            WHERE file_month IS NOT NULL
            ORDER BY file_month
        """).fetchall()

    return [int(r[0]) for r in rows]


YEARS = available_years()
DEFAULT_YEAR = max(YEARS) if YEARS else 2023


def where_clause(year: int | None, month: int | None) -> str:
    clauses = []

    if year:
        clauses.append(f"file_year = {int(year)}")

    if month:
        clauses.append(f"file_month = {int(month)}")

    return "WHERE " + " AND ".join(clauses) if clauses else ""


def get_kpi(year: int | None = None, month: int | None = None) -> dict:
    row = con.execute(f"""
        SELECT
            COUNT(*) AS total_trips,
            SUM(total_amount) AS total_revenue,
            AVG(total_amount) AS avg_revenue,
            AVG(trip_distance) AS avg_distance,
            AVG(tip_amount) AS avg_tip,
            SUM(tip_amount) AS total_tips
        FROM base_trips
        {where_clause(year, month)}
    """).fetchone()

    keys = [
        "total_trips",
        "total_revenue",
        "avg_revenue",
        "avg_distance",
        "avg_tip",
        "total_tips",
    ]

    # 💥 ГОЛОВНИЙ ФІКС
    if row is None:
        return dict(zip(keys, [0, 0, 0, 0, 0, 0]))

    # 💥 DuckDB може повернути None в колонках
    clean = [x if x is not None else 0 for x in row]

    return dict(zip(keys, clean))

def get_yoy(year: int | None) -> dict:
    if not year or year - 1 not in YEARS:
        return {
            "revenue_growth": None,
            "trips_growth": None,
            "prev_year": None,
        }

    current = get_kpi(year)
    previous = get_kpi(year - 1)

    def growth(curr, prev):
        if not prev:
            return None
        return round((curr - prev) / prev * 100, 2)

    return {
        "revenue_growth": growth(current["total_revenue"], previous["total_revenue"]),
        "trips_growth": growth(current["total_trips"], previous["total_trips"]),
        "prev_year": year - 1,
    }


def get_monthly_series(year: int | None = None):
    return con.execute(f"""
        SELECT
            file_year AS year,
            file_month AS month_num,
            MAKE_DATE(file_year, file_month, 1) AS month_date,
            COUNT(*) AS trips,
            ROUND(SUM(total_amount), 0) AS revenue,
            ROUND(AVG(total_amount), 2) AS avg_fare,
            ROUND(AVG(trip_distance), 2) AS avg_distance
        FROM base_trips
        {where_clause(year, None)}
        GROUP BY 1, 2, 3
        ORDER BY 1, 2
    """).df()


def get_yearly_summary():
    return con.execute("""
        SELECT
            file_year AS year,
            COUNT(*) AS trips,
            ROUND(SUM(total_amount), 0) AS revenue,
            ROUND(AVG(total_amount), 2) AS avg_fare,
            ROUND(AVG(trip_distance), 2) AS avg_distance
        FROM base_trips
        GROUP BY 1
        ORDER BY 1
    """).df()


def get_hourly(year: int | None = None, month: int | None = None):
    return con.execute(f"""
        SELECT
            pickup_hour AS hour,
            COUNT(*) AS trips,
            ROUND(SUM(total_amount), 0) AS revenue
        FROM base_trips
        {where_clause(year, month)}
        GROUP BY 1
        ORDER BY 1
    """).df()


def get_weekday(year: int | None = None, month: int | None = None):
    return con.execute(f"""
        SELECT
            STRFTIME(tpep_pickup_datetime, '%w')::INTEGER AS weekday_num,
            STRFTIME(tpep_pickup_datetime, '%A') AS weekday,
            COUNT(*) AS trips,
            ROUND(SUM(total_amount), 0) AS revenue
        FROM base_trips
        {where_clause(year, month)}
        GROUP BY 1, 2
        ORDER BY 1
    """).df()


def get_zone_stats(year: int | None = None, month: int | None = None):
    return con.execute(f"""
        SELECT
            PULocationID AS location_id,
            COUNT(*) AS trips,
            ROUND(SUM(total_amount), 0) AS revenue,
            ROUND(AVG(total_amount), 2) AS avg_fare,
            ROUND(AVG(trip_distance), 2) AS avg_distance
        FROM base_trips
        {where_clause(year, month)}
        GROUP BY 1
    """).df()


def get_top_zones(year: int | None = None, month: int | None = None, limit: int = 15):
    stats = get_zone_stats(year, month)
    merged = stats.merge(ZONE_META, left_on="location_id", right_on="LocationID", how="left")
    merged["zone_label"] = merged["zone"].fillna("Unknown") + " · " + merged["borough"].fillna("Unknown")
    return merged.sort_values("trips", ascending=False).head(limit)


def get_business_insights(year: int | None = None, month: int | None = None) -> list[str]:
    kpi = get_kpi(year, month)
    monthly = get_monthly_series(year)
    hourly = get_hourly(year, month)
    zones = get_top_zones(year, month, limit=1)
    yoy = get_yoy(year)

    insights = []

    if not monthly.empty:
        best_month = monthly.sort_values("revenue", ascending=False).iloc[0]
        insights.append(
            f"Best revenue month: {MONTHS[int(best_month['month_num'])]} {int(best_month['year'])} "
            f"with ${int(best_month['revenue']):,}."
        )

    if not hourly.empty:
        peak_hour = hourly.sort_values("trips", ascending=False).iloc[0]
        insights.append(
            f"Peak demand hour: {int(peak_hour['hour']):02d}:00 "
            f"with {int(peak_hour['trips']):,} trips."
        )

    if not zones.empty:
        top_zone = zones.iloc[0]
        insights.append(
            f"Top pickup zone: {top_zone['zone_label']} "
            f"with {int(top_zone['trips']):,} trips."
        )

    if yoy["revenue_growth"] is not None:
        direction = "up" if yoy["revenue_growth"] >= 0 else "down"
        insights.append(
            f"Revenue is {direction} {abs(yoy['revenue_growth']):.2f}% "
            f"vs {yoy['prev_year']}."
        )

    insights.append(
        f"Average trip distance is {float(kpi['avg_distance']):.2f} miles; "
        f"average fare is ${float(kpi['avg_revenue']):.2f}."
    )

    return insights


if not ZONES_SHP.exists():
    raise FileNotFoundError(f"Taxi zone shapefile not found: {ZONES_SHP}")

GDF = (
    gpd.read_file(ZONES_SHP)[["LocationID", "zone", "borough", "geometry"]]
    .to_crs(epsg=4326)
)

GDF["geometry"] = GDF.geometry.simplify(tolerance=0.0005)
ZONE_META = GDF.drop(columns="geometry").copy()


def build_map_figure(year: int | None = None, month: int | None = None) -> go.Figure:
    stats = get_zone_stats(year, month)
    gdf = GDF.merge(stats, left_on="LocationID", right_on="location_id", how="left")

    gdf["trips"] = gdf["trips"].fillna(0)
    gdf["revenue"] = gdf["revenue"].fillna(0)
    gdf["avg_fare"] = gdf["avg_fare"].fillna(0)
    gdf["avg_distance"] = gdf["avg_distance"].fillna(0)

    fig = px.choropleth_map(
        gdf,
        geojson=json.loads(gdf.to_json()),
        locations="LocationID",
        featureidkey="properties.LocationID",
        color="trips",
        hover_name="zone",
        hover_data={
            "borough": True,
            "trips": ":,.0f",
            "revenue": ":,.0f",
            "avg_fare": ":.2f",
            "avg_distance": ":.2f",
            "LocationID": False,
        },
        center={"lat": 40.73, "lon": -73.93},
        zoom=9.5,
        map_style="carto-positron",
        color_continuous_scale="YlOrRd",
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=30, b=0),
        height=520,
        title="Pickup Demand Heatmap by Taxi Zone",
        coloraxis_colorbar=dict(title="Trips"),
    )

    return fig


def fig_yearly(df) -> go.Figure:
    fig = go.Figure()

    fig.add_bar(
        x=df["year"],
        y=df["trips"],
        name="Trips",
        marker_color="#2980b9",
        yaxis="y2",
        opacity=0.75,
    )

    fig.add_scatter(
        x=df["year"],
        y=df["revenue"],
        name="Revenue",
        mode="lines+markers",
        line=dict(color="#f39c12", width=3),
        marker=dict(size=8),
    )

    fig.update_layout(
        title="Yearly Business Overview · Trips vs Revenue",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=40, r=40, t=60, b=40),
        yaxis=dict(title="Revenue ($)", gridcolor="#eee"),
        yaxis2=dict(title="Trips", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.12),
    )

    return fig


def fig_monthly(df) -> go.Figure:
    df = df.copy()
    df["label"] = df["month_date"].astype(str).str[:7]

    fig = go.Figure()

    fig.add_bar(
        x=df["label"],
        y=df["trips"],
        name="Trips",
        marker_color="#3498db",
        opacity=0.65,
        yaxis="y2",
    )

    fig.add_scatter(
        x=df["label"],
        y=df["revenue"],
        name="Revenue",
        mode="lines+markers",
        line=dict(color="#e67e22", width=2.5),
    )

    fig.update_layout(
        title="Monthly Trend · Demand and Revenue",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=40, r=40, t=60, b=70),
        xaxis=dict(tickangle=-45),
        yaxis=dict(title="Revenue ($)", gridcolor="#eee"),
        yaxis2=dict(title="Trips", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.12),
    )

    return fig


def fig_hourly(df) -> go.Figure:
    fig = go.Figure()

    fig.add_scatter(
        x=df["hour"],
        y=df["trips"],
        mode="lines+markers",
        fill="tozeroy",
        line=dict(color="#2c3e50", width=2.5),
        marker=dict(size=5),
        name="Trips",
    )

    fig.update_layout(
        title="Hourly Demand Pattern",
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=40, r=20, t=60, b=40),
        xaxis=dict(title="Hour of Day", tickmode="linear", dtick=2),
        yaxis=dict(title="Trips", gridcolor="#eee"),
    )

    return fig


def fig_weekday(df) -> go.Figure:
    order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    df = df.copy()
    df["weekday"] = df["weekday"].astype(str)

    fig = px.bar(
        df,
        x="weekday",
        y="trips",
        category_orders={"weekday": order},
        title="Trips by Weekday",
        color_discrete_sequence=["#16a085"],
    )

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=40, r=20, t=60, b=40),
        yaxis=dict(title="Trips", gridcolor="#eee"),
        xaxis=dict(title=""),
    )

    return fig


def fig_top_zones(df) -> go.Figure:
    df = df.sort_values("trips", ascending=True)

    fig = px.bar(
        df,
        x="trips",
        y="zone_label",
        orientation="h",
        title="Top Pickup Zones",
        color="trips",
        color_continuous_scale="Blues",
    )

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=160, r=20, t=60, b=40),
        xaxis=dict(title="Trips", gridcolor="#eee"),
        yaxis=dict(title=""),
        coloraxis_showscale=False,
    )

    return fig


def money(value) -> str:
    return f"${int(value):,}"


def number(value) -> str:
    return f"{int(value):,}"


def money_float(value) -> str:
    return f"${float(value):.2f}"


def miles(value) -> str:
    return f"{float(value):.2f} mi"


CARD_STYLE = {
    "border": "none",
    "borderRadius": "14px",
    "boxShadow": "0 4px 14px rgba(0,0,0,0.08)",
    "background": "white",
}


def kpi_card(label: str, value: str, subtitle: str, color: str) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.Div(label, className="text-muted", style={
                "fontSize": "11px",
                "fontWeight": "700",
                "letterSpacing": "0.8px",
                "textTransform": "uppercase",
            }),
            html.Div(value, style={
                "fontSize": "27px",
                "fontWeight": "800",
                "color": color,
                "lineHeight": "1.1",
            }),
            html.Div(subtitle, className="text-muted", style={"fontSize": "12px"}),
        ]),
        style=CARD_STYLE,
    )


def insight_cards(insights: list[str]):
    return [
        dbc.Alert(
            insight,
            color="light",
            className="mb-2",
            style={
                "borderLeft": "5px solid #2980b9",
                "background": "white",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.05)",
                "fontSize": "14px",
            },
        )
        for insight in insights
    ]


app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title=APP_TITLE,
)

server = app.server


initial_kpi = get_kpi(DEFAULT_YEAR)
initial_yoy = get_yoy(DEFAULT_YEAR)
initial_monthly = get_monthly_series(DEFAULT_YEAR)
initial_yearly = get_yearly_summary()
initial_hourly = get_hourly(DEFAULT_YEAR)
initial_weekday = get_weekday(DEFAULT_YEAR)
initial_top_zones = get_top_zones(DEFAULT_YEAR)
initial_insights = get_business_insights(DEFAULT_YEAR)


app.layout = dbc.Container([

    dbc.Row([
        dbc.Col([
            html.H2("NYC Yellow Taxi · BI Dashboard", className="fw-bold mb-1"),
            html.Div(
                "DuckDB · Parquet Data Lake · 2019–2023 · SQL analytics without ETL",
                className="text-muted",
                style={"fontSize": "14px"},
            ),
        ], md=9),

        dbc.Col([
            html.Div("Data Lake", className="text-muted text-uppercase", style={"fontSize": "11px"}),
            html.Div(f"{len(PARQUET_FILES)} parquet files", className="fw-bold"),
            html.Div(f"{min(YEARS)}–{max(YEARS)}" if YEARS else "No years", className="text-muted"),
        ], md=3, className="text-end"),
    ], className="pt-4 pb-3 border-bottom"),

    html.Br(),

    dbc.Row([
        dbc.Col([
            html.Label("Year", className="fw-bold"),
            dcc.Dropdown(
                id="year-select",
                options=[{"label": "All years", "value": 0}] +
                        [{"label": str(y), "value": y} for y in YEARS],
                value=DEFAULT_YEAR,
                clearable=False,
            ),
        ], md=3),

        dbc.Col([
            html.Label("Month", className="fw-bold"),
            dcc.Dropdown(
                id="month-select",
                options=[{"label": "All months", "value": 0}] +
                        [{"label": MONTHS[m], "value": m} for m in range(1, 13)],
                value=0,
                clearable=False,
            ),
        ], md=3),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(kpi_card("Total Trips", number(initial_kpi["total_trips"]), "filtered trips", "#2980b9"), md=3, id="card-trips"),
        dbc.Col(kpi_card("Total Revenue", money(initial_kpi["total_revenue"]), "gross taxi revenue", "#27ae60"), md=3, id="card-revenue"),
        dbc.Col(kpi_card("Avg Fare", money_float(initial_kpi["avg_revenue"]), "mean total amount", "#8e44ad"), md=3, id="card-avg"),
        dbc.Col(kpi_card("Avg Distance", miles(initial_kpi["avg_distance"]), "mean trip distance", "#e67e22"), md=3, id="card-distance"),
    ], className="g-3 mb-4"),

    dbc.Row([
        dbc.Col([
            html.H5("Executive Insights", className="fw-bold mb-3"),
            html.Div(insight_cards(initial_insights), id="insight-panel"),
        ], md=12),
    ], className="mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            dcc.Graph(id="fig-yearly", figure=fig_yearly(initial_yearly), config={"displayModeBar": False})
        ]), style=CARD_STYLE), md=5),

        dbc.Col(dbc.Card(dbc.CardBody([
            dcc.Graph(id="fig-monthly", figure=fig_monthly(initial_monthly), config={"displayModeBar": False})
        ]), style=CARD_STYLE), md=7),
    ], className="g-3 mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            dcc.Graph(id="fig-hourly", figure=fig_hourly(initial_hourly), config={"displayModeBar": False})
        ]), style=CARD_STYLE), md=6),

        dbc.Col(dbc.Card(dbc.CardBody([
            dcc.Graph(id="fig-weekday", figure=fig_weekday(initial_weekday), config={"displayModeBar": False})
        ]), style=CARD_STYLE), md=6),
    ], className="g-3 mb-4"),

    dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            dcc.Graph(id="fig-zones", figure=fig_top_zones(initial_top_zones), config={"displayModeBar": False})
        ]), style=CARD_STYLE), md=5),

        dbc.Col(dbc.Card(dbc.CardBody([
            dcc.Graph(id="fig-map", figure=build_map_figure(DEFAULT_YEAR), config={"displayModeBar": False})
        ]), style=CARD_STYLE), md=7),
    ], className="g-3 mb-5"),

], fluid=True, style={
    "background": "#f4f6f8",
    "minHeight": "100vh",
    "paddingLeft": "28px",
    "paddingRight": "28px",
})


@app.callback(
    Output("card-trips", "children"),
    Output("card-revenue", "children"),
    Output("card-avg", "children"),
    Output("card-distance", "children"),
    Output("insight-panel", "children"),
    Output("fig-monthly", "figure"),
    Output("fig-hourly", "figure"),
    Output("fig-weekday", "figure"),
    Output("fig-zones", "figure"),
    Output("fig-map", "figure"),
    Input("year-select", "value"),
    Input("month-select", "value"),
)
def update_dashboard(year_value: int, month_value: int):
    year = year_value or None
    month = month_value or None

    kpi = get_kpi(year, month)
    insights = get_business_insights(year, month)

    monthly = get_monthly_series(year)
    hourly = get_hourly(year, month)
    weekday = get_weekday(year, month)
    top_zones = get_top_zones(year, month)

    return (
        kpi_card("Total Trips", number(kpi["total_trips"]), "filtered trips", "#2980b9"),
        kpi_card("Total Revenue", money(kpi["total_revenue"]), "gross taxi revenue", "#27ae60"),
        kpi_card("Avg Fare", money_float(kpi["avg_revenue"]), "mean total amount", "#8e44ad"),
        kpi_card("Avg Distance", miles(kpi["avg_distance"]), "mean trip distance", "#e67e22"),
        insight_cards(insights),
        fig_monthly(monthly),
        fig_hourly(hourly),
        fig_weekday(weekday),
        fig_top_zones(top_zones),
        build_map_figure(year, month),
    )


if __name__ == "__main__":
    print("=" * 80)
    print("[app] BI dashboard is running")
    print(f"[app] URL: http://127.0.0.1:{PORT}")
    print("=" * 80)
    app.run(debug=True, port=PORT)