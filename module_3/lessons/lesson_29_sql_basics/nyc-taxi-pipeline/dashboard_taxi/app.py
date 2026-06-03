"""
dashboard/app.py — NYC Taxi Analytics Dash dashboard.

Connects directly to PostgreSQL and the API.
All API calls include try/except — dashboard never crashes on backend failure.

Tabs:
  1. KPI Overview  — monthly metrics, revenue chart
  2. Top Routes    — bar chart of busiest origin→destination pairs
  3. Zone Heatmap  — pickup/dropoff intensity table
  4. Graph         — PageRank and betweenness centrality tables
"""

from __future__ import annotations

import os
import logging
from typing import Any

import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)

API_BASE = os.getenv("API_BASE", "http://localhost:8000/api")

_EMPTY_DF = pd.DataFrame()


# ── API helpers ────────────────────────────────────────────────────────────────

def _get(path: str, params: dict | None = None) -> Any:
    """GET from API; returns parsed JSON or safe default on any failure."""
    try:
        r = requests.get(f"{API_BASE}{path}", params=params or {}, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        log.warning("API call failed [%s]: %s", path, exc)
        return None


def _get_kpi(year=None, month=None) -> dict:
    params = {}
    if year:
        params["year"] = year
    if month:
        params["month"] = month
    result = _get("/kpi/summary", params)
    if not isinstance(result, dict):
        return {
            "total_trips": 0, "total_revenue": 0.0,
            "avg_fare": 0.0, "avg_distance": 0.0,
        }
    return result


def _get_monthly() -> pd.DataFrame:
    data = _get("/kpi/monthly")
    if not data:
        return _EMPTY_DF
    return pd.DataFrame(data)


def _get_top_routes(limit=20) -> pd.DataFrame:
    data = _get("/kpi/top-routes", {"limit": limit})
    if not data:
        return _EMPTY_DF
    return pd.DataFrame(data)


def _get_zones(year=None, month=None) -> pd.DataFrame:
    params = {}
    if year:
        params["year"] = year
    if month:
        params["month"] = month
    data = _get("/kpi/zones", params)
    if not data:
        return _EMPTY_DF
    return pd.DataFrame(data)


def _get_pagerank(limit=20) -> pd.DataFrame:
    data = _get("/graph/pagerank", {"limit": limit})
    if not data:
        return _EMPTY_DF
    return pd.DataFrame(data)


def _get_betweenness(limit=20) -> pd.DataFrame:
    data = _get("/graph/betweenness", {"limit": limit})
    if not data:
        return _EMPTY_DF
    return pd.DataFrame(data)


# ── Layout ─────────────────────────────────────────────────────────────────────

def _kpi_card(title: str, value: str, color: str = "primary") -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.H6(title, className="card-subtitle text-muted"),
            html.H3(value, className=f"text-{color} fw-bold"),
        ]),
        className="shadow-sm",
    )


def _make_layout() -> html.Div:
    return dbc.Container(fluid=True, children=[
        dbc.Row(dbc.Col(html.H2("NYC Taxi Analytics", className="my-3 text-primary"))),

        # Filters
        dbc.Row([
            dbc.Col([
                html.Label("Year"),
                dcc.Dropdown(
                    id="filter-year",
                    options=[{"label": str(y), "value": y} for y in range(2019, 2025)],
                    placeholder="All years",
                    clearable=True,
                ),
            ], width=2),
            dbc.Col([
                html.Label("Month"),
                dcc.Dropdown(
                    id="filter-month",
                    options=[{"label": str(m), "value": m} for m in range(1, 13)],
                    placeholder="All months",
                    clearable=True,
                ),
            ], width=2),
        ], className="mb-3"),

        # KPI cards
        dbc.Row(id="kpi-cards", className="mb-4 g-3"),

        # Tabs
        dbc.Tabs([
            dbc.Tab(label="Monthly Trend",  tab_id="tab-monthly"),
            dbc.Tab(label="Top Routes",     tab_id="tab-routes"),
            dbc.Tab(label="Zone Heatmap",   tab_id="tab-zones"),
            dbc.Tab(label="Graph Metrics",  tab_id="tab-graph"),
        ], id="tabs", active_tab="tab-monthly"),

        html.Div(id="tab-content", className="mt-3"),
    ])


# ── App init ───────────────────────────────────────────────────────────────────

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    suppress_callback_exceptions=True,
)
app.layout = _make_layout()


# ── Callbacks ──────────────────────────────────────────────────────────────────

@app.callback(
    Output("kpi-cards", "children"),
    Input("filter-year",  "value"),
    Input("filter-month", "value"),
)
def update_kpi(year, month):
    kpi = _get_kpi(year, month)
    return [
        dbc.Col(_kpi_card("Total Trips",    f"{kpi.get('total_trips', 0):,}"),           width=3),
        dbc.Col(_kpi_card("Total Revenue",  f"${kpi.get('total_revenue', 0):,.0f}", "success"), width=3),
        dbc.Col(_kpi_card("Avg Fare",       f"${kpi.get('avg_fare', 0):.2f}",   "info"),  width=3),
        dbc.Col(_kpi_card("Avg Distance",   f"{kpi.get('avg_distance', 0):.2f} mi", "warning"), width=3),
    ]


@app.callback(
    Output("tab-content", "children"),
    Input("tabs",         "active_tab"),
    Input("filter-year",  "value"),
    Input("filter-month", "value"),
)
def render_tab(tab, year, month):
    if tab == "tab-monthly":
        return _render_monthly()
    if tab == "tab-routes":
        return _render_routes()
    if tab == "tab-zones":
        return _render_zones(year, month)
    if tab == "tab-graph":
        return _render_graph()
    return html.Div("Select a tab")


# ── Tab renderers ──────────────────────────────────────────────────────────────

def _render_monthly() -> html.Div:
    df = _get_monthly()
    if df.empty:
        return html.Div("No monthly data available.", className="text-muted p-3")

    df["period"] = df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2)

    fig_trips = px.bar(
        df, x="period", y="total_trips",
        title="Monthly Trips",
        labels={"period": "Month", "total_trips": "Trips"},
        color_discrete_sequence=["#0d6efd"],
    )
    fig_revenue = px.line(
        df, x="period", y="total_revenue",
        title="Monthly Revenue ($)",
        labels={"period": "Month", "total_revenue": "Revenue"},
        markers=True,
    )

    return html.Div([
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_trips),   width=6),
            dbc.Col(dcc.Graph(figure=fig_revenue), width=6),
        ])
    ])


def _render_routes() -> html.Div:
    df = _get_top_routes(20)
    if df.empty:
        return html.Div("No route data available.", className="text-muted p-3")

    df["route"] = df["pu_zone_name"].fillna(df["pu_location_id"].astype(str)) + \
                  " → " + \
                  df["do_zone_name"].fillna(df["do_location_id"].astype(str))

    fig = px.bar(
        df.head(15), x="total_trips", y="route",
        orientation="h",
        title="Top 15 Routes by Trip Count",
        labels={"total_trips": "Trips", "route": ""},
        color="avg_fare",
        color_continuous_scale="Blues",
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)

    return html.Div([
        dcc.Graph(figure=fig),
        dash_table.DataTable(
            data=df.to_dict("records"),
            columns=[
                {"name": "Route",         "id": "route"},
                {"name": "Trips",         "id": "total_trips",   "type": "numeric"},
                {"name": "Avg Fare ($)",  "id": "avg_fare",      "type": "numeric"},
                {"name": "Revenue ($)",   "id": "total_revenue", "type": "numeric"},
                {"name": "Avg Dist (mi)", "id": "avg_distance",  "type": "numeric"},
            ],
            page_size=10,
            sort_action="native",
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "6px"},
            style_header={"backgroundColor": "#0d6efd", "color": "white", "fontWeight": "bold"},
        ),
    ])


def _render_zones(year, month) -> html.Div:
    df = _get_zones(year, month)
    if df.empty:
        return html.Div("No zone data available.", className="text-muted p-3")

    df["total_trips"] = df["pickup_trips"].fillna(0) + df["dropoff_trips"].fillna(0)

    fig = px.bar(
        df.head(20),
        x="zone_name", y=["pickup_trips", "dropoff_trips"],
        barmode="group",
        title="Top 20 Zones — Pickups vs Dropoffs",
        labels={"value": "Trips", "zone_name": "Zone"},
        color_discrete_map={"pickup_trips": "#0d6efd", "dropoff_trips": "#fd7e14"},
    )
    fig.update_xaxes(tickangle=45)

    return html.Div([
        dcc.Graph(figure=fig),
        dash_table.DataTable(
            data=df.to_dict("records"),
            columns=[
                {"name": "Zone",     "id": "zone_name"},
                {"name": "Borough",  "id": "borough"},
                {"name": "Pickups",  "id": "pickup_trips",  "type": "numeric"},
                {"name": "Dropoffs", "id": "dropoff_trips", "type": "numeric"},
                {"name": "Revenue",  "id": "revenue",       "type": "numeric"},
            ],
            page_size=15,
            sort_action="native",
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "6px"},
            style_header={"backgroundColor": "#0d6efd", "color": "white", "fontWeight": "bold"},
        ),
    ])


def _render_graph() -> html.Div:
    pr_df = _get_pagerank(20)
    bc_df = _get_betweenness(20)

    panels = []

    if not pr_df.empty:
        fig = px.bar(
            pr_df, x="pagerank_score", y="zone_name",
            orientation="h",
            title="PageRank — Most Central Zones",
            color="borough",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
        panels.append(dbc.Col(dcc.Graph(figure=fig), width=6))
    else:
        panels.append(dbc.Col(html.Div("PageRank data unavailable (Neo4j offline?)", className="text-muted p-3"), width=6))

    if not bc_df.empty:
        fig2 = px.bar(
            bc_df, x="betweenness_score", y="zone_name",
            orientation="h",
            title="Betweenness — Bridge Zones",
            color="borough",
        )
        fig2.update_layout(yaxis={"categoryorder": "total ascending"}, height=450)
        panels.append(dbc.Col(dcc.Graph(figure=fig2), width=6))
    else:
        panels.append(dbc.Col(html.Div("Betweenness data unavailable (Neo4j offline?)", className="text-muted p-3"), width=6))

    return html.Div([dbc.Row(panels)])


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
