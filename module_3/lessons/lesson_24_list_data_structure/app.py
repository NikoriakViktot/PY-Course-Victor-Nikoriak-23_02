"""
app.py — Taxi Dispatch & Big-O Analytics Dashboard  (v2)
=========================================================
Lesson 24 · Module 3 · Python Advanced · Viktor Nikoriak

Teaching chain:
  Data Structure → Processing Cost → Aggregation → Analytics → Visualization

Run:
    cd module_3/lessons/lesson_24_list_data_structure/
    python app.py          →  http://127.0.0.1:8054/

Required (add to venv if missing):
    pip install dash dash-bootstrap-components dash-leaflet dash-extensions
                pandas geopandas duckdb plotly pyarrow shapely
"""
from __future__ import annotations

import json
import os
import time
from collections import deque

import duckdb
import geopandas as gpd
import pandas as pd
import plotly.graph_objects as go

import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash import Input, Output, State, dash_table, dcc, html

# JS function support for per-feature Leaflet styling
try:
    from dash_extensions.javascript import Namespace
    _NS = Namespace("dashExtensions", "default")
    _HAS_JS = True
except ImportError:
    _NS = None
    _HAS_JS = False

# =============================================================================
# Paths & global constants
# =============================================================================
HERE       = os.path.dirname(os.path.abspath(__file__))
ZONES_SHP  = os.path.join(HERE, "taxi_zones", "taxi_zones.shp")
DATA_URL   = (
    "https://d37ci6vzurychx.cloudfront.net/trip-data/"
    "yellow_tripdata_2023-01.parquet"
)
_DATA_DIR  = os.path.join(HERE, "data")
_LOCAL_PQ  = os.path.join(_DATA_DIR, "yellow_tripdata_2023-01.parquet")
BENCH_SIZES = [1_000, 5_000, 10_000, 25_000]

# Map metric registry:  key → (human label, palette, is_diverging)
METRICS: dict[str, tuple[str, str, bool]] = {
    "trip_count_pickup":  ("Pickup Count",           "YlOrRd",  False),
    "trip_count_dropoff": ("Dropoff Count",           "YlOrRd",  False),
    "avg_dist_pickup":    ("Avg Pickup Distance",     "Blues",   False),
    "avg_dist_dropoff":   ("Avg Dropoff Distance",    "Blues",   False),
    "net_flow":           ("Net Flow (Drop - Pick)",  "RdYlGn",  True),
    "cash_pct":           ("Cash Share %",            "Purples", False),
    "card_pct":           ("Card Share %",            "Greens",  False),
}

# =============================================================================
# Colour palettes (5-stop RGB, low → high)
# =============================================================================
_PAL: dict[str, list[tuple[int, int, int]]] = {
    "YlOrRd":  [(255,255,178),(254,204,92),(253,141,60),(240,59,32),(189,0,38)],
    "Blues":   [(247,251,255),(198,219,239),(107,174,214),(49,130,189),(8,81,156)],
    "Purples": [(252,251,253),(218,218,235),(188,189,220),(117,107,177),(63,0,125)],
    "Greens":  [(247,252,245),(199,233,192),(116,196,118),(49,163,84),(0,109,44)],
    "RdYlGn":  [(215,48,39),(252,141,89),(255,255,191),(145,207,96),(26,152,80)],
}


def _hex(t: float, palette: str) -> str:
    """Linear interpolation through a 5-stop palette. t in [0, 1]."""
    stops = _PAL[palette]
    t = max(0.0, min(1.0, t))
    pos = t * (len(stops) - 1)
    i = int(pos)
    if i >= len(stops) - 1:
        r, g, b = stops[-1]
    else:
        f = pos - i
        r0, g0, b0 = stops[i]
        r1, g1, b1 = stops[i + 1]
        r = int(r0 + (r1 - r0) * f)
        g = int(g0 + (g1 - g0) * f)
        b = int(b0 + (b1 - b0) * f)
    return f"#{r:02x}{g:02x}{b:02x}"


def _legend_strip(palette: str, vmin: float, vmax: float, label: str,
                  diverging: bool = False) -> html.Div:
    """Horizontal colour-ramp legend with 5 stop labels."""
    n = 5
    stops = [vmin + (vmax - vmin) * i / (n - 1) for i in range(n)]

    def _fmt(v: float) -> str:
        if abs(v) >= 1_000:
            return f"{v:,.0f}"
        if abs(v) < 1:
            return f"{v:.2f}"
        return f"{v:.1f}"

    if diverging:
        def norm(v): return 0.5 + v / (2 * max(abs(vmin), abs(vmax), 1e-6))
    else:
        rng = (vmax - vmin) or 1e-6
        def norm(v): return (v - vmin) / rng

    swatches = [
        html.Div([
            html.Div(style={
                "background": _hex(norm(s), palette),
                "height": "12px", "borderRadius": "2px",
            }),
            html.Small(_fmt(s), style={"fontSize": "9px", "color": "#777"}),
        ], style={"textAlign": "center", "flex": 1, "padding": "0 1px"})
        for s in stops
    ]
    return html.Div([
        html.Small(label, className="d-block text-center text-muted mb-1",
                   style={"fontSize": "11px", "fontWeight": "600"}),
        html.Div(swatches, style={"display": "flex"}),
    ])


# =============================================================================
# DuckDB — local-first parquet strategy
# =============================================================================
def _resolve_parquet() -> str:
    """
    Return a path/URL to the parquet file.

    Priority:
      1. Local cached file  (data/yellow_tripdata_2023-01.parquet)
      2. Download via urllib  (respects system proxy; avoids DuckDB httpfs blocks)
      3. Direct remote URL  (fallback — may fail behind strict firewalls)

    The local file is ~530 MB and is downloaded only once.
    """
    if os.path.exists(_LOCAL_PQ):
        print(f"[data] Using local parquet: {_LOCAL_PQ}")
        return _LOCAL_PQ

    import urllib.request
    os.makedirs(_DATA_DIR, exist_ok=True)
    tmp = _LOCAL_PQ + ".tmp"
    print(f"[data] Local parquet not found. Downloading (~530 MB) ...")
    print(f"  {DATA_URL}")
    print(f"  -> {_LOCAL_PQ}")
    print("[data] This is a one-time download. Please wait ...")
    try:
        urllib.request.urlretrieve(DATA_URL, tmp)
        os.rename(tmp, _LOCAL_PQ)
        print("[data] Download complete.")
        return _LOCAL_PQ
    except Exception as exc:
        if os.path.exists(tmp):
            os.remove(tmp)
        print(f"[data] urllib download failed: {exc}")
        print("[data] Falling back to direct DuckDB httpfs access.")
        return DATA_URL      # last resort — may fail behind firewalls


def _make_duckdb(source: str) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    if source.startswith("http"):
        try:
            con.execute("INSTALL httpfs; LOAD httpfs;")
        except Exception:
            pass
    # Normalise Windows backslashes so DuckDB parses the path correctly
    src = source.replace("\\", "/")
    con.execute(f"""
        CREATE OR REPLACE VIEW trips AS
        SELECT
            CAST(payment_type  AS INTEGER) AS payment_type,
            CAST(trip_distance AS DOUBLE)  AS trip_distance,
            CAST(PULocationID  AS INTEGER) AS PULocationID,
            CAST(DOLocationID  AS INTEGER) AS DOLocationID
        FROM read_parquet('{src}')
        WHERE payment_type IN (1, 2)
          AND trip_distance  > 0
          AND trip_distance  < 500
    """)
    return con


_PQ_SOURCE = _resolve_parquet()
_CON       = _make_duckdb(_PQ_SOURCE)


def sample_trips(n: int) -> list[dict]:
    """Pull n rows via DuckDB reservoir sampling — only n rows reach Python RAM."""
    return _CON.execute(f"""
        SELECT
            CASE payment_type WHEN 1 THEN 'Card' ELSE 'Cash' END AS payment_type,
            trip_distance, PULocationID, DOLocationID
        FROM trips USING SAMPLE {n} ROWS
    """).df().to_dict("records")


def run_analytics(top_n: int = 15, pay_filter: str = "All") -> dict:
    """
    Full-month aggregations executed entirely in DuckDB.
    Heavy SQL in the engine — only tiny result tables reach pandas.
    """
    pay_sql = {
        "All":  "",
        "Card": "AND payment_type = 1",
        "Cash": "AND payment_type = 2",
    }[pay_filter]

    # ── KPIs ──────────────────────────────────────────────────────────────────
    kpi = _CON.execute(f"""
        SELECT
            COUNT(*)                                                                AS total_trips,
            ROUND(SUM(trip_distance), 0)                                           AS total_distance,
            ROUND(AVG(trip_distance),    2)                                        AS avg_distance,
            ROUND(MEDIAN(trip_distance), 2)                                        AS median_distance,
            ROUND(MAX(trip_distance),    1)                                        AS max_distance,
            ROUND(SUM(CASE WHEN payment_type=2 THEN 1.0 ELSE 0 END)/COUNT(*)*100, 1) AS cash_pct,
            ROUND(SUM(CASE WHEN payment_type=1 THEN 1.0 ELSE 0 END)/COUNT(*)*100, 1) AS card_pct,
            COUNT(DISTINCT PULocationID)                                            AS unique_pu,
            COUNT(DISTINCT DOLocationID)                                            AS unique_do
        FROM trips WHERE 1=1 {pay_sql}
    """).fetchone()
    kpis = dict(zip(
        ["total_trips","total_distance","avg_distance","median_distance","max_distance",
         "cash_pct","card_pct","unique_pu","unique_do"],
        kpi,
    ))

    # ── Zone stats (single CTE — pickup + dropoff in one pass) ────────────────
    zone_df = _CON.execute(f"""
        WITH pu AS (
            SELECT PULocationID AS lid, COUNT(*) AS tc_pu,
                   ROUND(AVG(trip_distance), 2)                                AS ad_pu,
                   ROUND(SUM(CASE WHEN payment_type=2 THEN 1.0 ELSE 0 END)
                         / COUNT(*) * 100, 1)                                  AS cash_pct
            FROM trips WHERE 1=1 {pay_sql} GROUP BY PULocationID
        ),
        do_ AS (
            SELECT DOLocationID AS lid, COUNT(*) AS tc_do,
                   ROUND(AVG(trip_distance), 2) AS ad_do
            FROM trips WHERE 1=1 {pay_sql} GROUP BY DOLocationID
        )
        SELECT
            COALESCE(pu.lid, do_.lid)                                           AS location_id,
            COALESCE(tc_pu,    0)                                               AS trip_count_pickup,
            COALESCE(ad_pu,  0.0)                                               AS avg_dist_pickup,
            COALESCE(cash_pct, 0.0)                                             AS cash_pct,
            100.0 - COALESCE(cash_pct, 0.0)                                    AS card_pct,
            COALESCE(tc_do,    0)                                               AS trip_count_dropoff,
            COALESCE(ad_do,  0.0)                                               AS avg_dist_dropoff,
            CAST(COALESCE(tc_do, 0) AS INTEGER)
                - CAST(COALESCE(tc_pu, 0) AS INTEGER)                          AS net_flow
        FROM pu FULL OUTER JOIN do_ ON pu.lid = do_.lid
    """).df()

    # ── Distance histogram (SQL-bucketed into 1-mile intervals) ───────────────
    hist_df = _CON.execute(f"""
        SELECT FLOOR(trip_distance) AS bucket, COUNT(*) AS count
        FROM trips WHERE trip_distance <= 25 {pay_sql}
        GROUP BY bucket ORDER BY bucket
    """).df()

    # ── Distance statistics by payment type ───────────────────────────────────
    dist_pay_df = _CON.execute("""
        SELECT
            CASE payment_type WHEN 1 THEN 'Card' ELSE 'Cash' END AS payment_type,
            ROUND(AVG(trip_distance),    2) AS avg_dist,
            ROUND(MEDIAN(trip_distance), 2) AS median_dist,
            COUNT(*)                        AS n_trips
        FROM trips GROUP BY payment_type
    """).df()

    # ── Top N pickup zones ────────────────────────────────────────────────────
    top_pu_df = _CON.execute(f"""
        SELECT PULocationID AS location_id, COUNT(*) AS trip_count
        FROM trips WHERE 1=1 {pay_sql}
        GROUP BY PULocationID ORDER BY trip_count DESC LIMIT {top_n}
    """).df()

    # ── Top N dropoff zones ───────────────────────────────────────────────────
    top_do_df = _CON.execute(f"""
        SELECT DOLocationID AS location_id, COUNT(*) AS trip_count
        FROM trips WHERE 1=1 {pay_sql}
        GROUP BY DOLocationID ORDER BY trip_count DESC LIMIT {top_n}
    """).df()

    # ── OD flows (top 50 pairs) ───────────────────────────────────────────────
    od_df = _CON.execute(f"""
        SELECT PULocationID AS pu_id, DOLocationID AS do_id, COUNT(*) AS trip_count
        FROM trips WHERE 1=1 {pay_sql}
        GROUP BY PULocationID, DOLocationID ORDER BY trip_count DESC LIMIT 50
    """).df()

    # ── Dominant destination per pickup zone ──────────────────────────────────
    dom_df = _CON.execute(f"""
        WITH ranked AS (
            SELECT PULocationID, DOLocationID, COUNT(*) AS cnt,
                   ROW_NUMBER() OVER (PARTITION BY PULocationID ORDER BY COUNT(*) DESC) AS rn
            FROM trips WHERE 1=1 {pay_sql} GROUP BY PULocationID, DOLocationID
        )
        SELECT PULocationID AS pu_id, DOLocationID AS do_id, cnt AS trip_count
        FROM ranked WHERE rn = 1 ORDER BY trip_count DESC LIMIT {top_n}
    """).df()

    return {
        "kpis":      kpis,
        "zone_stats": zone_df.to_dict("records"),
        "dist_hist":  hist_df.to_dict("records"),
        "dist_pay":   dist_pay_df.to_dict("records"),
        "top_pu":     top_pu_df.to_dict("records"),
        "top_do":     top_do_df.to_dict("records"),
        "od_flows":   od_df.to_dict("records"),
        "dom_dest":   dom_df.to_dict("records"),
    }


# =============================================================================
# Taxi-zone GeoDataFrame (loaded once at startup)
# =============================================================================
_ZONES: gpd.GeoDataFrame = (
    gpd.read_file(ZONES_SHP)[["LocationID", "zone", "borough", "geometry"]]
    .to_crs(epsg=4326)
    .assign(geometry=lambda d: d.geometry.simplify(tolerance=0.0005))
)
_ZONE_LU: dict[int, dict] = {
    int(r.LocationID): {"zone": r.zone, "borough": r.borough}
    for r in _ZONES.itertuples()
}


# =============================================================================
# Data-structure implementations
# =============================================================================
class _Node:
    __slots__ = ("data", "next")
    def __init__(self, data): self.data = data; self.next = None


class LinkedQueue:
    """FIFO on a singly linked list — enqueue/dequeue both O(1)."""
    def __init__(self):
        self._head = self._tail = None

    def enqueue(self, data) -> None:
        n = _Node(data)
        if self._tail: self._tail.next = n
        else:          self._head = n
        self._tail = n

    def dequeue(self):
        if not self._head: raise IndexError
        d = self._head.data
        self._head = self._head.next
        if not self._head: self._tail = None
        return d

    def __bool__(self) -> bool: return self._head is not None


def _run_list(trips: list) -> float:
    q = list(trips); t0 = time.perf_counter()
    while q: q.pop(0)                          # O(n) — memory shift every call
    return (time.perf_counter() - t0) * 1_000


def _run_linked(trips: list) -> float:
    q = LinkedQueue()
    for t in trips: q.enqueue(t)
    t0 = time.perf_counter()
    while q: q.dequeue()                       # O(1) — pointer advance only
    return (time.perf_counter() - t0) * 1_000


def _run_deque(trips: list) -> float:
    q = deque(trips); t0 = time.perf_counter()
    while q: q.popleft()                       # O(1) — C-speed doubly linked
    return (time.perf_counter() - t0) * 1_000


def bench_all(sizes: list[int]) -> dict:
    results: dict[str, list] = {"sizes": sizes, "list": [], "linked": [], "deque": []}
    for n in sizes:
        trips = sample_trips(n)
        results["list"].append(round(_run_list(trips),   3))
        results["linked"].append(round(_run_linked(trips), 4))
        results["deque"].append(round(_run_deque(trips),  4))
    return results


# =============================================================================
# GeoJSON builder  (called each time the map metric changes)
# =============================================================================
def _fmt_metric(v: float, metric: str) -> str:
    if metric in ("trip_count_pickup", "trip_count_dropoff"):
        return f"{int(v):,}"
    if metric == "net_flow":
        return f"{int(v):+,}"
    if "pct" in metric:
        return f"{v:.1f}%"
    return f"{v:.2f} mi"


def build_geojson(zone_stats: list[dict], metric: str) -> dict:
    if not zone_stats:
        return {"type": "FeatureCollection", "features": []}

    label, palette, diverging = METRICS.get(metric, ("Value", "Blues", False))
    stats_df = pd.DataFrame(zone_stats)

    gdf = _ZONES.copy()
    if metric in stats_df.columns:
        gdf = gdf.merge(
            stats_df[["location_id", metric]],
            left_on="LocationID", right_on="location_id", how="left",
        )
        gdf[metric] = gdf[metric].fillna(0.0).astype(float)
    else:
        gdf[metric] = 0.0

    vals = gdf[metric].tolist()
    vmin, vmax = min(vals), max(vals)

    if diverging:
        abs_max = max(abs(vmin), abs(vmax), 1e-9)
        def norm(v): return 0.5 + float(v) / (2 * abs_max)
    else:
        rng = (vmax - vmin) or 1e-9
        def norm(v): return (float(v) - vmin) / rng

    gdf["fillColor"]     = gdf[metric].apply(lambda v: _hex(norm(v), palette))
    gdf["display_value"] = gdf[metric].apply(lambda v: _fmt_metric(v, metric))
    gdf["metric_label"]  = label
    gdf["location_id"]   = gdf["LocationID"].astype(int)

    raw = json.loads(
        gdf[["geometry","location_id","zone","borough",
             "fillColor","display_value","metric_label"]].to_json()
    )
    return raw


# =============================================================================
# GeoJSON options (static — set once; only .data is updated by callbacks)
# =============================================================================
if _HAS_JS:
    _GEOJSON_OPTIONS = {
        "style":         _NS("styleFeature"),
        "onEachFeature": _NS("onEachFeature"),
    }
else:
    _GEOJSON_OPTIONS = {
        "style": {"color": "#555", "weight": 1, "fillOpacity": 0.6, "opacity": 0.8}
    }

# =============================================================================
# Design tokens
# =============================================================================
_C = {"list": "#e74c3c", "linked": "#f39c12", "deque": "#27ae60"}
_CARD_STYLE = {
    "border":      "none",
    "borderRadius": "10px",
    "boxShadow":   "0 1px 6px rgba(0,0,0,0.09)",
    "background":  "#ffffff",
}
_PANEL = {"background": "#f4f5f7", "borderRadius": "12px", "padding": "18px 16px"}
_INSIGHT_STYLE = {
    "fontSize": "12px", "lineHeight": "1.6",
    "background": "#fffbea", "borderLeft": "3px solid #f39c12",
    "padding": "10px 14px", "borderRadius": "0 6px 6px 0",
    "color": "#5a4500",
}


def _insight(text: str) -> html.Div:
    return html.Div(["[insight] ", text], style=_INSIGHT_STYLE, className="mt-2")


# =============================================================================
# App
# =============================================================================
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="Big-O Analytics Lab",
    suppress_callback_exceptions=True,
)
server = app.server  # WSGI entry point


# =============================================================================
# Layout helpers
# =============================================================================
def _kpi(title: str, value_id: str, color: str = "#2c3e50") -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.P(title, className="text-muted mb-0",
                   style={"fontSize": "10px", "textTransform": "uppercase",
                          "letterSpacing": "0.7px"}),
            html.Span("—", id=value_id,
                      style={"fontSize": "22px", "fontWeight": "700", "color": color}),
        ]),
        style=_CARD_STYLE,
    )


def _section_header(text: str) -> html.P:
    return html.P(text, className="text-uppercase text-muted mb-2",
                  style={"fontSize": "10px", "letterSpacing": "1px", "fontWeight": "600"})


# =============================================================================
# Layout
# =============================================================================
app.layout = dbc.Container([

    # ── HEADER ────────────────────────────────────────────────────────────────
    dbc.Row([
        dbc.Col([
            html.H4("Taxi Dispatch Analytics  —  Big-O Lab",
                    className="mb-0 fw-bold", style={"color": "#1a1a2e"}),
            html.Small(
                "Data Structure  →  Processing Cost  →  Analytics  →  Visualization  →  Scalability",
                className="text-muted",
            ),
        ], width=9),
        dbc.Col(
            dbc.Button("Run Analysis", id="run-btn", color="primary", size="sm",
                       className="float-end mt-2"),
            width=3,
        ),
    ], className="py-3 border-bottom mb-3"),

    dbc.Row([

        # ── SIDEBAR ───────────────────────────────────────────────────────────
        dbc.Col(
            html.Div([

                _section_header("Dataset"),
                dbc.RadioItems(
                    id="mode-radio",
                    options=[
                        {"label": "Full January (SQL)",    "value": "full_january"},
                        {"label": "Sample Preview (50k)", "value": "sample_preview"},
                    ],
                    value="full_january",
                    className="mb-3",
                    labelStyle={"fontSize": "12px"},
                ),

                _section_header("Payment filter"),
                dbc.RadioItems(
                    id="payment-radio",
                    options=[
                        {"label": "All",  "value": "All"},
                        {"label": "Card", "value": "Card"},
                        {"label": "Cash", "value": "Cash"},
                    ],
                    value="All",
                    inline=True,
                    className="mb-3",
                    labelStyle={"fontSize": "12px"},
                ),

                _section_header("Queue structure (benchmark)"),
                dbc.RadioItems(
                    id="struct-radio",
                    options=[
                        {"label": html.Span("list.pop(0)  —  O(n)",
                                            style={"color": _C["list"], "fontSize": "12px"}),
                         "value": "list"},
                        {"label": html.Span("LinkedQueue  —  O(1) Py",
                                            style={"color": _C["linked"], "fontSize": "12px"}),
                         "value": "linked"},
                        {"label": html.Span("deque.popleft  —  O(1) C",
                                            style={"color": _C["deque"], "fontSize": "12px"}),
                         "value": "deque"},
                    ],
                    value="deque",
                    className="mb-3",
                ),

                _section_header("Top-N zones"),
                dcc.Slider(
                    id="topn-slider",
                    min=5, max=25, step=5, value=15,
                    marks={5: "5", 10: "10", 15: "15", 20: "20", 25: "25"},
                    tooltip={"placement": "bottom", "always_visible": False},
                    className="mb-3",
                ),

                html.Hr(className="my-2"),

                # Bottleneck panel
                dbc.Alert([
                    html.Strong("[!] list.pop(0) — O(n) bottleneck"),
                    html.Br(),
                    html.Small(
                        "Each dequeue shifts the entire backing array. "
                        "At 25k items that is ~312M pointer moves. "
                        "Total pipeline: O(n²). "
                        "The system does not scale."
                    ),
                ], color="danger", className="py-2 px-3",
                   style={"fontSize": "11px", "lineHeight": "1.5"}),

                # Complexity table
                dbc.Table([
                    html.Thead(html.Tr([
                        html.Th("Structure", style={"fontSize": "11px"}),
                        html.Th("dequeue",   style={"fontSize": "11px"}),
                        html.Th("Total",     style={"fontSize": "11px"}),
                    ])),
                    html.Tbody([
                        html.Tr([html.Td(html.Span("list",   style={"color": _C["list"],   "fontWeight":"600"})),
                                 html.Td("O(n)"),   html.Td(html.Span("O(n²)", style={"color":_C["list"],"fontWeight":"600"}))]),
                        html.Tr([html.Td(html.Span("linked", style={"color": _C["linked"], "fontWeight":"600"})),
                                 html.Td("O(1)"),   html.Td("O(n)")]),
                        html.Tr([html.Td(html.Span("deque",  style={"color": _C["deque"],  "fontWeight":"600"})),
                                 html.Td("O(1)"),   html.Td(html.Span("O(n)", style={"color":_C["deque"],"fontWeight":"600"}))]),
                    ]),
                ], bordered=False, hover=True, size="sm",
                   style={"fontSize": "11px", "marginTop": "8px"}),

            ], style=_PANEL),
            width=3,
        ),

        # ── MAIN TABS ─────────────────────────────────────────────────────────
        dbc.Col([
            dbc.Tabs([

                # ══ TAB A — PERFORMANCE ══════════════════════════════════════
                dbc.Tab(label="Performance", tab_id="tab-perf", children=[
                    html.Div(className="mt-3", children=[

                        # Metric cards
                        dbc.Row([
                            dbc.Col(_kpi("Selected Structure", "perf-struct"), width=3),
                            dbc.Col(_kpi("Queue Time",         "perf-time", "#e74c3c"), width=3),
                            dbc.Col(_kpi("Speedup vs list",    "perf-speedup", "#27ae60"), width=3),
                            dbc.Col(_kpi("Trips Processed",    "perf-trips"), width=3),
                        ], className="g-2 mb-3"),

                        # Benchmark bar display
                        html.Div(id="bench-bars", className="mb-3"),

                        # Line chart: N vs time
                        dbc.Card([
                            dbc.CardHeader(
                                html.Small("Processing Time by Dataset Size — all 3 structures",
                                           className="fw-semibold text-secondary"),
                                style={"padding": "8px 14px", "background": "#fafafa"},
                            ),
                            dbc.CardBody(
                                dcc.Graph(id="bench-line", config={"displayModeBar": False},
                                          style={"height": "280px"}),
                                className="p-1",
                            ),
                        ], style=_CARD_STYLE, className="mb-3"),

                        _insight(
                            "The line chart shows O(n²) growth for list — "
                            "curve bends upward, not linear. "
                            "deque and LinkedQueue stay linear (O(n) total), "
                            "but deque is ~10-50x faster due to C implementation."
                        ),
                    ]),
                ]),

                # ══ TAB B — ANALYTICS ════════════════════════════════════════
                dbc.Tab(label="Analytics", tab_id="tab-analytics", children=[
                    html.Div(className="mt-3", children=[

                        # KPI row (9 cards)
                        html.Div(id="kpi-row", className="mb-3"),

                        # Charts row 1: histogram + payment bar
                        dbc.Row([
                            dbc.Col(dbc.Card([
                                dbc.CardHeader(html.Small("Trip Distance Distribution",
                                               className="fw-semibold text-secondary"),
                                               style={"padding":"7px 12px","background":"#fafafa"}),
                                dbc.CardBody(dcc.Graph(id="dist-hist",
                                             config={"displayModeBar": False},
                                             style={"height":"230px"}), className="p-1"),
                            ], style=_CARD_STYLE), width=7),
                            dbc.Col(dbc.Card([
                                dbc.CardHeader(html.Small("Payment Type Distribution",
                                               className="fw-semibold text-secondary"),
                                               style={"padding":"7px 12px","background":"#fafafa"}),
                                dbc.CardBody(dcc.Graph(id="pay-pie",
                                             config={"displayModeBar": False},
                                             style={"height":"230px"}), className="p-1"),
                            ], style=_CARD_STYLE), width=5),
                        ], className="g-2 mb-3"),

                        # Charts row 2: top PU + top DO
                        dbc.Row([
                            dbc.Col(dbc.Card([
                                dbc.CardHeader(html.Small("Top Pickup Zones",
                                               className="fw-semibold text-secondary"),
                                               style={"padding":"7px 12px","background":"#fafafa"}),
                                dbc.CardBody(dcc.Graph(id="top-pu",
                                             config={"displayModeBar": False},
                                             style={"height":"260px"}), className="p-1"),
                            ], style=_CARD_STYLE), width=6),
                            dbc.Col(dbc.Card([
                                dbc.CardHeader(html.Small("Top Dropoff Zones",
                                               className="fw-semibold text-secondary"),
                                               style={"padding":"7px 12px","background":"#fafafa"}),
                                dbc.CardBody(dcc.Graph(id="top-do",
                                             config={"displayModeBar": False},
                                             style={"height":"260px"}), className="p-1"),
                            ], style=_CARD_STYLE), width=6),
                        ], className="g-2 mb-3"),

                        # Charts row 3: distance by payment
                        dbc.Row([
                            dbc.Col(dbc.Card([
                                dbc.CardHeader(html.Small("Avg & Median Distance by Payment",
                                               className="fw-semibold text-secondary"),
                                               style={"padding":"7px 12px","background":"#fafafa"}),
                                dbc.CardBody(dcc.Graph(id="dist-by-pay",
                                             config={"displayModeBar": False},
                                             style={"height":"210px"}), className="p-1"),
                            ], style=_CARD_STYLE), width=12),
                        ], className="g-2"),

                        _insight(
                            "All aggregations run in DuckDB over the full January dataset. "
                            "Only the summary tables (~KB) reach Python RAM. "
                            "This is only possible because we push heavy computation "
                            "into the engine — not into Python loops."
                        ),
                    ]),
                ]),

                # ══ TAB C — MAP ══════════════════════════════════════════════
                dbc.Tab(label="Map", tab_id="tab-map", children=[
                    html.Div(className="mt-3", children=[

                        dbc.Row([
                            dbc.Col([
                                html.Label("Map metric", className="fw-semibold",
                                           style={"fontSize": "12px"}),
                                dcc.Dropdown(
                                    id="map-metric-dd",
                                    options=[
                                        {"label": v[0], "value": k}
                                        for k, v in METRICS.items()
                                    ],
                                    value="trip_count_pickup",
                                    clearable=False,
                                    style={"fontSize": "12px"},
                                ),
                            ], width=5),
                            dbc.Col(html.Div(id="map-legend", className="mt-3"), width=7),
                        ], className="mb-2"),

                        dbc.Card([
                            dbc.CardHeader(
                                html.Small("NYC Taxi Zone Choropleth — hover for details",
                                           className="fw-semibold text-secondary"),
                                style={"padding": "7px 14px", "background": "#fafafa"},
                            ),
                            dbc.CardBody(
                                dl.Map(
                                    id="zone-map",
                                    center=[40.73, -73.95], zoom=10,
                                    style={"height": "380px", "borderRadius": "6px"},
                                    children=[
                                        dl.TileLayer(
                                            url=(
                                                "https://{s}.basemaps.cartocdn.com/"
                                                "light_all/{z}/{x}/{y}{r}.png"
                                            ),
                                            attribution=(
                                                '&copy; <a href="https://www.openstreetmap.org/copyright">'
                                                'OSM</a> &copy; <a href="https://carto.com/">CARTO</a>'
                                            ),
                                            maxZoom=19,
                                        ),
                                        dl.GeoJSON(
                                            id="geojson-layer",
                                            data={"type": "FeatureCollection", "features": []},
                                            options=_GEOJSON_OPTIONS,
                                        ),
                                    ],
                                ),
                                className="p-2",
                            ),
                        ], style=_CARD_STYLE, className="mb-2"),

                        _insight(
                            "The choropleth exists only because we first aggregated "
                            "3M+ trips efficiently in DuckDB. "
                            "Change the metric above to explore pickup density, "
                            "dropoff density, net flow, and payment geography."
                        ),
                    ]),
                ]),

                # ══ TAB D — OD FLOWS ═════════════════════════════════════════
                dbc.Tab(label="OD Flows", tab_id="tab-od", children=[
                    html.Div(className="mt-3", children=[

                        dbc.Row([
                            dbc.Col([
                                html.H6("Top Origin-Destination Pairs",
                                        className="fw-semibold mb-2",
                                        style={"fontSize": "13px"}),
                                html.Div(id="od-table"),
                            ], width=7),
                            dbc.Col([
                                html.H6("Dominant Destination per Pickup Zone",
                                        className="fw-semibold mb-2",
                                        style={"fontSize": "13px"}),
                                html.Div(id="dom-dest-table"),
                            ], width=5),
                        ], className="g-2 mb-3"),

                        dbc.Card([
                            dbc.CardHeader(
                                html.Small("Top OD Flows — trip count",
                                           className="fw-semibold text-secondary"),
                                style={"padding": "7px 12px", "background": "#fafafa"},
                            ),
                            dbc.CardBody(
                                dcc.Graph(id="od-bar", config={"displayModeBar": False},
                                          style={"height": "300px"}),
                                className="p-1",
                            ),
                        ], style=_CARD_STYLE),

                        _insight(
                            "OD analysis answers: where do trips flow? "
                            "Which pickup zone feeds the most trips to each destination? "
                            "This requires only a GROUP BY in SQL — "
                            "but the result is rich spatial intelligence."
                        ),
                    ]),
                ]),

            ], id="main-tabs", active_tab="tab-perf"),
        ], width=9),

    ], className="g-3"),

    # Stores
    dcc.Store(id="store-analytics"),
    dcc.Store(id="store-bench"),

], fluid=True,
   style={"background": "#eaecf0", "minHeight": "100vh", "paddingBottom": "40px"})


# =============================================================================
# Callback 1 — Run heavy analytics + benchmarks (button click only)
# =============================================================================
@app.callback(
    Output("store-analytics", "data"),
    Output("store-bench",     "data"),
    Input("run-btn",       "n_clicks"),
    State("payment-radio", "value"),
    State("topn-slider",   "value"),
    prevent_initial_call=True,
)
def cb_run(_clicks, pay_filter, top_n):
    global _CON, _PQ_SOURCE
    try:
        analytics = run_analytics(top_n=top_n, pay_filter=pay_filter)
        bench     = bench_all(BENCH_SIZES)
        return analytics, bench

    except Exception as first_exc:
        # If we were using the remote URL and it failed, try downloading locally
        if _PQ_SOURCE.startswith("http"):
            import urllib.request
            os.makedirs(_DATA_DIR, exist_ok=True)
            tmp = _LOCAL_PQ + ".tmp"
            try:
                print("[retry] Remote URL failed. Attempting local download ...")
                urllib.request.urlretrieve(DATA_URL, tmp)
                os.rename(tmp, _LOCAL_PQ)
                print("[retry] Download complete. Reconnecting ...")
                _PQ_SOURCE = _LOCAL_PQ
                _CON       = _make_duckdb(_PQ_SOURCE)
                analytics  = run_analytics(top_n=top_n, pay_filter=pay_filter)
                bench      = bench_all(BENCH_SIZES)
                return analytics, bench
            except Exception as retry_exc:
                if os.path.exists(tmp):
                    os.remove(tmp)
                return {"_error": f"Remote: {first_exc}\nRetry: {retry_exc}"}, None

        return {"_error": str(first_exc)}, None


# =============================================================================
# Callback 2 — Performance tab
# =============================================================================
@app.callback(
    Output("perf-struct",  "children"),
    Output("perf-time",    "children"),
    Output("perf-speedup", "children"),
    Output("perf-trips",   "children"),
    Output("bench-bars",   "children"),
    Output("bench-line",   "figure"),
    Input("store-bench",  "data"),
    Input("struct-radio", "value"),
    prevent_initial_call=True,
)
def cb_perf(bench, struct):
    empty_fig = _empty_fig("Click 'Run Analysis'")
    if not bench:
        return struct, "—", "—", "—", html.Div(), empty_fig

    t_sel  = bench[struct][-1]   # time at largest N
    t_list = bench["list"][-1]
    n_max  = bench["sizes"][-1]
    speedup = round(t_list / t_sel, 1) if t_sel > 0 else float("inf")

    # Metric cards
    t_str  = f"{t_sel:.1f}" if t_sel >= 1 else f"{t_sel:.3f}"
    sp_str = "1.0" if struct == "list" else (f"{speedup:.1f}" if speedup < 999 else ">999")

    # Animated bar display
    max_t = max(max(bench[s]) for s in ["list","linked","deque"]) or 1
    rows  = []
    for s in sorted(["list","linked","deque"], key=lambda k: -bench[k][-1]):
        t   = bench[s][-1]
        pct = t / max_t * 100
        rows.append(html.Div([
            html.Span(s, style={"fontSize": "11px", "width": "58px",
                                "display": "inline-block",
                                "color": _C[s], "fontWeight": "600"}),
            html.Div(
                html.Div(f"{t:.2f} ms", style={
                    "width": f"{pct:.1f}%", "background": _C[s],
                    "color": "white", "fontSize": "10px",
                    "padding": "2px 8px", "borderRadius": "4px",
                    "minWidth": "64px", "whiteSpace": "nowrap",
                }),
                style={"display": "inline-block",
                       "width": "calc(100% - 65px)", "verticalAlign": "middle"},
            ),
        ], className="d-flex align-items-center mb-1"))

    bars = html.Div(
        [html.Small(f"Time at N={n_max:,} (all 3 structures)",
                    className="text-muted d-block mb-2",
                    style={"fontSize": "10px"}), *rows],
        style={**_CARD_STYLE, "padding": "10px 14px"},
    )

    # Line chart
    fig = go.Figure()
    for s in ["list", "linked", "deque"]:
        fig.add_trace(go.Scatter(
            x=bench["sizes"], y=bench[s],
            mode="lines+markers",
            name={"list": "list.pop(0)  O(n)",
                  "linked": "LinkedQueue O(1)Py",
                  "deque": "deque.popleft O(1)C"}[s],
            line=dict(color=_C[s], width=2.5),
            marker=dict(size=7),
            hovertemplate=f"N=%{{x:,}}<br>time=%{{y:.3f}} ms<extra>{s}</extra>",
        ))
    fig.update_layout(
        margin=dict(l=40, r=20, t=20, b=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Queue Size (n)", gridcolor="#eee",
                   tickformat=",", tickfont=dict(size=10)),
        yaxis=dict(title="Time (ms)", gridcolor="#eee", tickfont=dict(size=10)),
        legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
    )

    return (struct.upper(), t_str, sp_str, f"{n_max:,}", bars, fig)


# =============================================================================
# Callback 3 — Analytics tab
# =============================================================================
@app.callback(
    Output("kpi-row",    "children"),
    Output("dist-hist",  "figure"),
    Output("pay-pie",    "figure"),
    Output("top-pu",     "figure"),
    Output("top-do",     "figure"),
    Output("dist-by-pay","figure"),
    Input("store-analytics", "data"),
    prevent_initial_call=True,
)
def cb_analytics(data):
    ef = _empty_fig()
    if not data:
        return html.Div(), ef, ef, ef, ef, ef

    if "_error" in data:
        err_card = dbc.Alert([
            html.Strong("Data load failed"),
            html.Br(),
            html.Code(data["_error"], style={"fontSize": "11px", "whiteSpace": "pre-wrap"}),
            html.Hr(),
            html.Small(
                "The parquet file could not be fetched. "
                "The app will attempt to download it locally on the next 'Run Analysis' click. "
                "If this persists, check your internet connection or proxy settings."
            ),
        ], color="danger")
        return err_card, ef, ef, ef, ef, ef

    k = data["kpis"]

    # KPI cards
    kpi_defs = [
        ("Total Trips",     f'{int(k["total_trips"]):,}',    "#2c3e50"),
        ("Total Distance",  f'{int(k["total_distance"]):,} mi', "#2c3e50"),
        ("Avg Distance",    f'{k["avg_distance"]} mi',       "#3498db"),
        ("Median Distance", f'{k["median_distance"]} mi',    "#3498db"),
        ("Max Distance",    f'{k["max_distance"]} mi',       "#9b59b6"),
        ("Cash Share",      f'{k["cash_pct"]}%',             "#e67e22"),
        ("Card Share",      f'{k["card_pct"]}%',             "#27ae60"),
        ("Pickup Zones",    str(int(k["unique_pu"])),         "#2c3e50"),
        ("Dropoff Zones",   str(int(k["unique_do"])),         "#2c3e50"),
    ]
    kpi_cards = dbc.Row(
        [dbc.Col(
            dbc.Card(dbc.CardBody([
                html.P(t, className="text-muted mb-0",
                       style={"fontSize": "9px", "textTransform": "uppercase",
                              "letterSpacing": "0.6px"}),
                html.Span(v, style={"fontSize": "18px", "fontWeight": "700",
                                    "color": c}),
            ]), style=_CARD_STYLE),
            width=True,
        ) for t, v, c in kpi_defs],
        className="g-2",
    )

    # Distance histogram
    hist_df = pd.DataFrame(data["dist_hist"])
    hist_fig = go.Figure()
    if not hist_df.empty:
        hist_fig.add_trace(go.Bar(
            x=hist_df["bucket"], y=hist_df["count"],
            marker_color="#3498db", opacity=0.82,
            hovertemplate="Distance: %{x:.0f}–%{x:.0f}+1 mi<br>Count: %{y:,}<extra></extra>",
        ))
        hist_fig.add_vline(x=float(k["avg_distance"]),
                           line_dash="dash", line_color="#e74c3c",
                           annotation_text="avg", annotation_font_size=10)
        hist_fig.add_vline(x=float(k["median_distance"]),
                           line_dash="dot", line_color="#27ae60",
                           annotation_text="med", annotation_font_size=10)
    hist_fig.update_layout(
        margin=dict(l=35,r=10,t=10,b=30),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Distance (mi)", gridcolor="#eee", tickfont=dict(size=10)),
        yaxis=dict(title="Trips",         gridcolor="#eee", tickfont=dict(size=10)),
        bargap=0.06,
    )

    # Payment pie
    dp = pd.DataFrame(data["dist_pay"])
    pay_fig = go.Figure()
    if not dp.empty:
        pay_fig.add_trace(go.Pie(
            labels=dp["payment_type"],
            values=dp["n_trips"],
            hole=0.45,
            marker_colors=["#27ae60", "#e67e22"],
            hovertemplate="%{label}: %{value:,} trips (%{percent})<extra></extra>",
            textinfo="label+percent",
            textfont_size=11,
        ))
    pay_fig.update_layout(
        margin=dict(l=10,r=10,t=10,b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )

    def _zone_bar(records: list[dict], metric_key: str = "trip_count",
                  color: str = "#3498db") -> go.Figure:
        rows = []
        for r in records:
            lid  = int(r["location_id"])
            name = _ZONE_LU.get(lid, {}).get("zone", str(lid))
            rows.append({"zone": name, "count": int(r[metric_key])})
        df = pd.DataFrame(rows).sort_values("count")
        fig = go.Figure(go.Bar(
            x=df["count"], y=df["zone"],
            orientation="h",
            marker_color=color,
            hovertemplate="%{y}: %{x:,}<extra></extra>",
        ))
        fig.update_layout(
            margin=dict(l=10,r=20,t=8,b=28),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(gridcolor="#eee", tickfont=dict(size=9)),
            yaxis=dict(automargin=True,  tickfont=dict(size=9)),
        )
        return fig

    pu_fig  = _zone_bar(data["top_pu"],  color="#3498db")
    do_fig  = _zone_bar(data["top_do"],  color="#e67e22")

    # Distance by payment
    dpay_fig = go.Figure()
    if not dp.empty:
        for col, cname, clr in [("avg_dist","Avg","#3498db"),("median_dist","Median","#e67e22")]:
            dpay_fig.add_trace(go.Bar(
                x=dp["payment_type"], y=dp[col],
                name=cname, marker_color=clr,
                hovertemplate=f"{cname}: %{{y:.2f}} mi<extra></extra>",
            ))
    dpay_fig.update_layout(
        margin=dict(l=40,r=10,t=10,b=30), barmode="group",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(tickfont=dict(size=11)),
        yaxis=dict(title="Distance (mi)", gridcolor="#eee"),
        legend=dict(font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
    )

    return (kpi_cards, hist_fig, pay_fig, pu_fig, do_fig, dpay_fig)


# =============================================================================
# Callback 4 — Map (reacts to new analytics OR metric change)
# =============================================================================
@app.callback(
    Output("geojson-layer", "data"),
    Output("map-legend",    "children"),
    Input("store-analytics",  "data"),
    Input("map-metric-dd",    "value"),
    prevent_initial_call=True,
)
def cb_map(data, metric):
    empty = {"type": "FeatureCollection", "features": []}
    if not data or "_error" in data:
        return empty, html.Div()

    geojson = build_geojson(data["zone_stats"], metric)

    # Legend
    label, palette, diverging = METRICS[metric]
    stats   = pd.DataFrame(data["zone_stats"])
    if metric in stats.columns:
        vals = stats[metric].dropna().astype(float)
        vmin, vmax = float(vals.min()), float(vals.max())
    else:
        vmin, vmax = 0.0, 1.0

    legend = _legend_strip(palette, vmin, vmax, label, diverging)
    return geojson, legend


# =============================================================================
# Callback 5 — OD Flows tab
# =============================================================================
@app.callback(
    Output("od-table",       "children"),
    Output("dom-dest-table", "children"),
    Output("od-bar",         "figure"),
    Input("store-analytics", "data"),
    prevent_initial_call=True,
)
def cb_od(data):
    ef = _empty_fig()
    if not data or "_error" in data:
        return html.Div(), html.Div(), ef

    total = int(data["kpis"]["total_trips"]) or 1

    # ── OD flows table ────────────────────────────────────────────────────────
    od_rows = []
    for i, r in enumerate(data["od_flows"][:15]):
        pu = _ZONE_LU.get(int(r["pu_id"]),  {}).get("zone", str(r["pu_id"]))
        do = _ZONE_LU.get(int(r["do_id"]),  {}).get("zone", str(r["do_id"]))
        od_rows.append({
            "#":    i + 1,
            "From": pu,
            "To":   do,
            "Trips": f'{int(r["trip_count"]):,}',
            "Share": f'{r["trip_count"] / total * 100:.2f}%',
        })
    od_tbl = dash_table.DataTable(
        data=od_rows,
        columns=[{"name": c, "id": c} for c in ["#","From","To","Trips","Share"]],
        style_cell={"fontSize": "11px", "padding": "4px 8px",
                    "textOverflow": "ellipsis", "maxWidth": "140px"},
        style_header={"fontWeight": "600", "background": "#f4f5f7",
                      "fontSize": "10px", "textTransform": "uppercase"},
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "background": "#f9f9f9"}
        ],
        page_size=15,
    )

    # ── Dominant destination table ────────────────────────────────────────────
    dom_rows = []
    for r in data["dom_dest"][:12]:
        pu = _ZONE_LU.get(int(r["pu_id"]), {}).get("zone", str(r["pu_id"]))
        do = _ZONE_LU.get(int(r["do_id"]), {}).get("zone", str(r["do_id"]))
        dom_rows.append({
            "Pickup Zone":  pu,
            "Top Dest.":    do,
            "Trips": f'{int(r["trip_count"]):,}',
        })
    dom_tbl = dash_table.DataTable(
        data=dom_rows,
        columns=[{"name": c, "id": c} for c in ["Pickup Zone","Top Dest.","Trips"]],
        style_cell={"fontSize": "10px", "padding": "4px 7px",
                    "textOverflow": "ellipsis", "maxWidth": "120px"},
        style_header={"fontWeight": "600", "background": "#f4f5f7",
                      "fontSize": "9px", "textTransform": "uppercase"},
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "background": "#f9f9f9"}
        ],
        page_size=12,
    )

    # ── OD bar chart (top 12) ─────────────────────────────────────────────────
    bar_rows = []
    for r in data["od_flows"][:12]:
        pu = _ZONE_LU.get(int(r["pu_id"]), {}).get("zone", str(r["pu_id"]))
        do = _ZONE_LU.get(int(r["do_id"]), {}).get("zone", str(r["do_id"]))
        bar_rows.append({"route": f"{pu[:18]} → {do[:18]}", "count": int(r["trip_count"])})
    df_bar = pd.DataFrame(bar_rows).sort_values("count")

    od_fig = go.Figure(go.Bar(
        x=df_bar["count"], y=df_bar["route"],
        orientation="h",
        marker_color="#3498db", opacity=0.85,
        hovertemplate="%{y}: %{x:,}<extra></extra>",
    ))
    od_fig.update_layout(
        margin=dict(l=10, r=20, t=10, b=30),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Trips", gridcolor="#eee", tickfont=dict(size=10)),
        yaxis=dict(automargin=True, tickfont=dict(size=9)),
    )

    return od_tbl, dom_tbl, od_fig


# =============================================================================
# Shared helper
# =============================================================================
def _empty_fig(msg: str = "No data") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        margin=dict(l=20, r=10, t=10, b=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        annotations=[dict(text=msg, showarrow=False,
                          font=dict(color="#bbb", size=12))],
    )
    return fig


# =============================================================================
# Entry point
# =============================================================================
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8054)
