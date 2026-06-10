"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   Dash-застосунок: Потокова Симуляція Біржових Транзакцій                    ║
║   Урок 19 · Ітератори та Генератори · Real-World Pipeline                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║   АРХІТЕКТУРА: Event-Driven (Dash callbacks)                                 ║
║    dcc.Interval → callback → state → graph                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import os
import random
from collections import deque, defaultdict
from datetime import datetime, timedelta

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go


# ─────────────────────────────────────────────────────────────────────────────
# ДАНІ: КОМПАНІЇ ТА ЇХ ПАРАМЕТРИ
# ─────────────────────────────────────────────────────────────────────────────

COMPANIES = {
    "Нафтогаз":   {"base": 145.0, "vol": 0.018, "color": "#FF6B35"},
    "ПриватБанк": {"base":  89.0, "vol": 0.012, "color": "#4ECDC4"},
    "Розетка":    {"base": 234.0, "vol": 0.022, "color": "#A78BFA"},
    "Укрнафта":   {"base":  67.0, "vol": 0.014, "color": "#34D399"},
    "Київстар":   {"base": 312.0, "vol": 0.009, "color": "#FBBF24"},
}

DEFAULT_SELECTED = ["Нафтогаз", "Розетка", "Київстар"]

DARK_BG    = "#0F1117"
CARD_BG    = "#1A1D27"
BORDER     = "#2D3147"
TEXT_MUTED = "#8B92A5"

PLOTLY_LAYOUT = dict(
    paper_bgcolor=DARK_BG,
    plot_bgcolor=CARD_BG,
    font=dict(color="#CBD5E1", size=12),
    margin=dict(l=10, r=10, t=36, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER, borderwidth=1),
    xaxis=dict(gridcolor=BORDER, showgrid=True, zeroline=False),
    yaxis=dict(gridcolor=BORDER, showgrid=True, zeroline=False),
)


# ─────────────────────────────────────────────────────────────────────────────
# ГЕНЕРАТОР ТРАНЗАКЦІЙ
# ─────────────────────────────────────────────────────────────────────────────
# Infinite Stream Pattern: while True + yield.
# У Dash немає time.sleep() у генераторі — затримка керується dcc.Interval.

def transaction_generator(companies: dict, selected: list):
    now      = datetime.now()
    prices   = {name: cfg["base"] for name, cfg in companies.items()}
    clocks   = {name: now for name in companies}
    trade_id = 1

    while True:
        name   = random.choice(selected)
        cfg    = companies[name]
        change = random.gauss(0, cfg["vol"])

        prices[name]  *= (1 + change)
        prices[name]   = max(prices[name], 1.0)
        clocks[name]  += timedelta(seconds=2)

        yield {
            "id":         trade_id,
            "company":    name,
            "price":      round(prices[name], 2),
            "volume":     random.randint(100, 15_000),
            "change_pct": round(change * 100, 3),
            "timestamp":  clocks[name].strftime("%H:%M:%S"),
            "color":      cfg["color"],
        }

        trade_id += 1


DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "transactions.ndjson")


def file_transaction_generator(path, selected):
    """
    Infinite stream from NDJSON file, filtered to `selected` companies.

    Root cause of single-company display: the file stores all 2 000 records
    per company in sequential blocks (Нафтогаз 0-1999, ПриватБанк 2000-3999…).
    A pure line-by-line loop would emit one company for hundreds of ticks before
    reaching the next.  Fix: load once into a list, shuffle to interleave
    companies, then cycle through the shuffled list indefinitely.  The 10 K
    records (~700 KB) are small enough that a one-time load is the correct
    engineering trade-off.
    """
    # ── one-time load & shuffle ───────────────────────────────────────────────
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    random.shuffle(records)

    # ── infinite cycling stream ───────────────────────────────────────────────
    prev_prices = {}
    idx = 0
    while True:
        tx   = records[idx % len(records)]
        idx += 1

        name = tx["company"]
        if name not in selected:
            continue

        price = float(tx["price"])
        prev  = prev_prices.get(name, price)
        change_pct        = round((price - prev) / prev * 100, 3) if prev else 0.0
        prev_prices[name] = price

        color = COMPANIES[name]["color"] if name in COMPANIES else "#94A3B8"

        try:
            ts = datetime.fromisoformat(tx.get("timestamp", "")).strftime("%H:%M:%S")
        except (ValueError, TypeError):
            ts = tx.get("timestamp", "")

        yield {
            "id":         tx.get("id", 0),
            "company":    name,
            "price":      price,
            "volume":     int(tx["volume"]),
            "change_pct": change_pct,
            "timestamp":  ts,
            "color":      color,
        }


# ─────────────────────────────────────────────────────────────────────────────
# СТАН ЗАСТОСУНКУ (server-side)
# ─────────────────────────────────────────────────────────────────────────────
# Глобальний стан зберігається на сервері між callback-викликами.
# dcc.Store передає лише лічильник тіків (tick), щоб тригерити перемальовування.

def _make_state(window_size: int = 80) -> dict:
    return {
        "history":          {name: deque(maxlen=window_size) for name in COMPANIES},
        "vol_history":      {name: deque(maxlen=window_size) for name in COMPANIES},
        "time_history":     {name: deque(maxlen=window_size) for name in COMPANIES},
        "recent_trades":    deque(maxlen=12),
        "trade_counts":     defaultdict(int),
        "total_volume":     defaultdict(int),
        "last_prices":      {},
        "last_changes":     {},
        "global_ticks":     deque(maxlen=window_size),
        "aligned_prices":   {name: deque(maxlen=window_size) for name in COMPANIES},
        "session_start":    datetime.now(),
        "session_tick":     0,
        "first_real_price": {},
    }


_state            = _make_state()
_generator        = None
_current_selected = None
_current_window   = 80


# ─────────────────────────────────────────────────────────────────────────────
# ДОПОМІЖНІ ФУНКЦІЇ
# ─────────────────────────────────────────────────────────────────────────────

def moving_average(values: list, window: int) -> list:
    result = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        result.append(round(sum(values[start:i + 1]) / (i - start + 1), 2))
    return result


# ─────────────────────────────────────────────────────────────────────────────
# ПОБУДОВА ГРАФІКІВ
# ─────────────────────────────────────────────────────────────────────────────

def build_main_chart(focus: str, ma_window: int) -> go.Figure:
    fig    = go.Figure()
    prices = list(_state["history"][focus])
    times  = list(_state["time_history"][focus])
    color  = COMPANIES[focus]["color"]

    if len(prices) < 2:
        fig.update_layout(
            title=f"{focus} — очікування даних...",
            **PLOTLY_LAYOUT,
        )
        return fig

    ma = moving_average(prices, ma_window)
    r, g, b    = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    fill_color = f"rgba({r},{g},{b},0.08)"

    fig.add_trace(go.Scatter(
        x=times, y=ma, mode="lines",
        line=dict(color=color, width=1, dash="dot"),
        name=f"MA({ma_window})", opacity=0.6,
    ))
    fig.add_trace(go.Scatter(
        x=times, y=prices, mode="lines",
        fill="tonexty", fillcolor=fill_color,
        line=dict(color=color, width=2.5),
        name=focus,
    ))
    fig.add_trace(go.Scatter(
        x=[times[-1]], y=[prices[-1]], mode="markers",
        marker=dict(color=color, size=10, symbol="circle",
                    line=dict(color="white", width=2)),
        name="Остання угода", showlegend=False,
    ))
    fig.update_layout(
        title=dict(text=f"📊  {focus}  —  Ціна акції (₴)", x=0.01, font_size=14),
        **PLOTLY_LAYOUT,
    )
    return fig


def build_multi_chart(selected: list) -> go.Figure:
    fig   = go.Figure()
    times = list(_state["global_ticks"])

    if len(times) < 2:
        fig.update_layout(
            title="📉  Нормалізовані ціни — очікування даних...",
            **PLOTLY_LAYOUT,
        )
        return fig

    for name in selected:
        base = _state["first_real_price"].get(name)
        if not base:
            continue
        prices = list(_state["aligned_prices"][name])
        if len(prices) < 2:
            continue
        n    = min(len(times), len(prices))
        norm = [p / base * 100 for p in prices[:n]]
        fig.add_trace(go.Scatter(
            x=times[:n], y=norm, mode="lines",
            line=dict(color=COMPANIES[name]["color"], width=1.8),
            name=name,
        ))

    fig.update_layout(
        title=dict(text="📉  Нормалізовані ціни (база = 100)", x=0.01, font_size=13),
        **PLOTLY_LAYOUT,
    )
    fig.update_yaxes(ticksuffix=" %")
    return fig


def build_volume_chart(selected: list) -> go.Figure:
    fig = go.Figure()
    for name in selected:
        vols  = list(_state["vol_history"][name])
        times = list(_state["time_history"][name])
        if not vols:
            continue
        fig.add_trace(go.Bar(
            x=times, y=vols, name=name,
            marker_color=COMPANIES[name]["color"],
            opacity=0.75,
        ))
    fig.update_layout(
        title=dict(text="📦  Обсяг торгів (акцій/угода)", x=0.01, font_size=13),
        barmode="stack",
        **PLOTLY_LAYOUT,
    )
    return fig


def build_heatmap(selected: list) -> go.Figure:
    changes = [_state["last_changes"].get(n, 0.0) for n in selected]
    fig = go.Figure(go.Bar(
        y=selected, x=changes, orientation="h",
        marker=dict(
            color=changes,
            colorscale=[[0, "#F87171"], [0.5, "#334155"], [1, "#34D399"]],
            cmin=-2, cmax=2,
            showscale=True,
            colorbar=dict(title="Δ%", thickness=10, len=0.7),
        ),
        text=[f"{c:+.3f}%" for c in changes],
        textposition="outside",
    ))
    fig.update_layout(
        title=dict(text="🌡  Остання зміна ціни (%)", x=0.01, font_size=13),
        **PLOTLY_LAYOUT,
    )
    fig.update_xaxes(range=[-3, 3], gridcolor=BORDER)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────────────────────────────────────

_sidebar_style = {
    "width":           "280px",
    "minWidth":        "280px",
    "backgroundColor": CARD_BG,
    "borderRight":     f"1px solid {BORDER}",
    "padding":         "20px 16px",
    "overflowY":       "auto",
    "height":          "100vh",
    "position":        "sticky",
    "top":             "0",
}

_main_style = {
    "flex":            "1",
    "backgroundColor": DARK_BG,
    "padding":         "20px 24px",
    "overflowY":       "auto",
    "minHeight":       "100vh",
}

_label_style = {
    "color":      "#CBD5E1",
    "fontSize":   "0.85rem",
    "marginBottom": "6px",
    "marginTop":  "14px",
    "display":    "block",
}

_slider_style = {"marginBottom": "4px"}

_generator_note_style = {
    "background":    "linear-gradient(135deg, #1E293B 0%, #0F1117 100%)",
    "border":        f"1px solid #334155",
    "borderLeft":    "4px solid #6366F1",
    "borderRadius":  "8px",
    "padding":       "12px 16px",
    "marginTop":     "16px",
    "fontSize":      "0.82rem",
    "color":         "#94A3B8",
    "lineHeight":    "1.6",
}

_hr_style = {"borderColor": BORDER, "margin": "12px 0"}

_tab_style = {
    "backgroundColor": CARD_BG,
    "color":           TEXT_MUTED,
    "border":          f"1px solid {BORDER}",
    "borderBottom":    "none",
    "padding":         "8px 16px",
    "fontSize":        "0.9rem",
}

_tab_selected_style = {
    "backgroundColor": DARK_BG,
    "color":           "#E2E8F0",
    "border":          f"1px solid {BORDER}",
    "borderBottom":    f"2px solid #6366F1",
    "padding":         "8px 16px",
    "fontSize":        "0.9rem",
    "fontWeight":      "700",
}

_tabs_container_style = {
    "backgroundColor": DARK_BG,
    "border":          f"1px solid {BORDER}",
    "borderRadius":    "8px",
    "marginBottom":    "16px",
}

sidebar = html.Div([
    html.H3("⚙️ Панель керування",
            style={"color": "#E2E8F0", "margin": "0 0 4px 0", "fontSize": "1rem"}),
    html.Hr(style=_hr_style),

    html.Label("Компанії", style=_label_style),
    dcc.Checklist(
        id="selected-companies",
        options=[{"label": f"  {name}", "value": name} for name in COMPANIES],
        value=DEFAULT_SELECTED,
        labelStyle={"display": "block", "color": "#CBD5E1", "fontSize": "0.88rem",
                    "padding": "3px 0", "cursor": "pointer"},
        inputStyle={"marginRight": "6px", "accentColor": "#6366F1"},
    ),

    html.Hr(style=_hr_style),

    html.Label("Розмір вікна (точок)", style=_label_style),
    html.Div(dcc.Slider(id="window-size", min=20, max=300, step=10, value=80,
               marks={20: "20", 80: "80", 160: "160", 300: "300"},
               tooltip={"placement": "bottom", "always_visible": False}),
             style=_slider_style),

    html.Label("Ковзне середнє (MA)", style=_label_style),
    html.Div(dcc.Slider(id="ma-window", min=3, max=30, step=1, value=7,
               marks={3: "3", 7: "7", 15: "15", 30: "30"},
               tooltip={"placement": "bottom", "always_visible": False}),
             style=_slider_style),

    html.Label("Затримка між угодами (сек)", style=_label_style),
    html.Div(dcc.Slider(id="speed", min=0.05, max=1.5, step=0.05, value=0.25,
               marks={0.05: "0.05", 0.25: "0.25", 0.75: "0.75", 1.5: "1.5"},
               tooltip={"placement": "bottom", "always_visible": False}),
             style=_slider_style),

    html.Label("Оновлювати графіки кожні N угод", style=_label_style),
    html.Div(dcc.Slider(id="refresh-every", min=1, max=20, step=1, value=5,
               marks={1: "1", 5: "5", 10: "10", 20: "20"},
               tooltip={"placement": "bottom", "always_visible": False}),
             style=_slider_style),

    html.Hr(style=_hr_style),

    html.Label("Фокус основного графіка", style=_label_style),
    dcc.Dropdown(
        id="focus-company",
        options=[{"label": name, "value": name} for name in DEFAULT_SELECTED],
        value=DEFAULT_SELECTED[0],
        clearable=False,
        style={"backgroundColor": DARK_BG, "color": "#CBD5E1",
               "border": f"1px solid {BORDER}", "fontSize": "0.88rem"},
    ),

    html.Hr(style=_hr_style),

    dcc.Checklist(
        id="is-running",
        options=[{"label": "  ▶  Запустити стрімінг", "value": "run"}],
        value=["run"],
        labelStyle={"color": "#CBD5E1", "fontSize": "0.9rem",
                    "cursor": "pointer", "fontWeight": "600"},
        inputStyle={"marginRight": "6px", "accentColor": "#34D399"},
    ),

    html.Div([
        html.Span("🧠 ", style={"fontWeight": "bold"}),
        html.B("Як це працює:"),
        html.Br(),
        "Цей застосунок ",
        html.B("не зберігає"),
        " дані в масиві.",
        html.Br(),
        "Кожна угода генерується ",
        html.Code("transaction_generator()", style={"backgroundColor": "#0F1117",
                                                     "padding": "1px 4px",
                                                     "borderRadius": "3px"}),
        " і відразу потрапляє на графік.",
        html.Br(), html.Br(),
        "Це і є ",
        html.B("Infinite Stream Pattern"),
        " — генератор з нескінченним ",
        html.Code("while True", style={"backgroundColor": "#0F1117",
                                        "padding": "1px 4px",
                                        "borderRadius": "3px"}),
        " + ",
        html.Code("yield", style={"backgroundColor": "#0F1117",
                                   "padding": "1px 4px",
                                   "borderRadius": "3px"}),
        ".",
    ], style=_generator_note_style),

], style=_sidebar_style)

main_content = html.Div([
    html.Div([
        html.Div([
            html.H1("📈 Stock Streaming — Генераторна Симуляція",
                    style={"color": "#E2E8F0", "margin": "0", "fontSize": "1.5rem"}),
            html.P("Урок 19 · Ітератори та Генератори · Real-World Pipeline",
                   style={"color": TEXT_MUTED, "margin": "4px 0 0 0", "fontSize": "0.85rem"}),
        ]),
        html.Div(id="status-indicator",
                 style={"alignSelf": "center", "fontSize": "1rem", "fontWeight": "700"}),
    ], style={"display": "flex", "justifyContent": "space-between",
              "alignItems": "flex-start", "marginBottom": "12px"}),

    html.Hr(style=_hr_style),

    html.Div(id="metrics-row", style={"marginBottom": "16px"}),

    dcc.Tabs(
        id="main-tabs",
        children=[
            dcc.Tab(
                label="Фокус: одна компанія",
                style=_tab_style,
                selected_style=_tab_selected_style,
                children=[
                    dcc.Graph(id="main-chart",
                              config={"displayModeBar": False},
                              style={"height": "340px"}),
                ],
            ),
            dcc.Tab(
                label="Порівняння (нормалізовано)",
                style=_tab_style,
                selected_style=_tab_selected_style,
                children=[
                    dcc.Graph(id="multi-chart",
                              config={"displayModeBar": False},
                              style={"height": "340px"}),
                ],
            ),
        ],
        style={"marginBottom": "0"},
    ),

    html.Div([
        html.Div(
            dcc.Graph(id="volume-chart",
                      config={"displayModeBar": False},
                      style={"height": "280px"}),
            style={"flex": "3"},
        ),
        html.Div(
            dcc.Graph(id="heatmap",
                      config={"displayModeBar": False},
                      style={"height": "280px"}),
            style={"flex": "2"},
        ),
    ], style={"display": "flex", "gap": "12px", "marginTop": "12px",
              "marginBottom": "16px"}),

    html.Div(id="trades-tape"),

    dcc.Interval(id="interval", interval=1250, n_intervals=0, disabled=False),
    dcc.Store(id="tick-store", data=0),

], style=_main_style)

app = dash.Dash(__name__, title="Stock Streaming — Генератори Python")
app.index_string = f"""<!DOCTYPE html>
<html>
<head>
    {{%metas%}}
    <title>{{%title%}}</title>
    {{%favicon%}}
    {{%css%}}
    <style>
        body, html {{
            background-color: {DARK_BG};
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        * {{ box-sizing: border-box; }}
        ::-webkit-scrollbar {{ width: 6px; background: {DARK_BG}; }}
        ::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}
        .Select-control, .Select-menu-outer {{
            background-color: {DARK_BG} !important;
            border-color: {BORDER} !important;
            color: #CBD5E1 !important;
        }}
        .Select-value-label, .Select-option {{ color: #CBD5E1 !important; }}
        .Select-option:hover {{ background-color: {BORDER} !important; }}
        .rc-slider-track {{ background-color: #6366F1 !important; }}
        .rc-slider-handle {{
            border-color: #6366F1 !important;
            background-color: #6366F1 !important;
        }}
    </style>
</head>
<body>
    {{%app_entry%}}
    <footer>
        {{%config%}}
        {{%scripts%}}
        {{%renderer%}}
    </footer>
</body>
</html>"""

app.layout = html.Div(
    [sidebar, main_content],
    style={"display": "flex", "minHeight": "100vh", "backgroundColor": DARK_BG},
)


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────────────────────────────────────

@app.callback(
    Output("interval", "interval"),
    Output("interval", "disabled"),
    Input("speed", "value"),
    Input("refresh-every", "value"),
    Input("is-running", "value"),
)
def configure_interval(speed, refresh_every, is_running):
    disabled = not bool(is_running)
    interval = max(50, int((speed or 0.25) * (refresh_every or 5) * 1000))
    return interval, disabled


@app.callback(
    Output("focus-company", "options"),
    Output("focus-company", "value"),
    Input("selected-companies", "value"),
    State("focus-company", "value"),
)
def sync_focus_options(selected, current_focus):
    sel = selected or list(COMPANIES.keys())[:2]
    options = [{"label": name, "value": name} for name in sel]
    value   = current_focus if current_focus in sel else sel[0]
    return options, value


@app.callback(
    Output("status-indicator", "children"),
    Input("is-running", "value"),
)
def update_status(is_running):
    if is_running:
        return html.Span("🟢 Live", style={"color": "#34D399"})
    return html.Span("⏸ Пауза", style={"color": "#94A3B8"})


@app.callback(
    Output("tick-store", "data"),
    Input("interval", "n_intervals"),
    State("selected-companies", "value"),
    State("window-size", "value"),
    State("refresh-every", "value"),
    State("tick-store", "data"),
    prevent_initial_call=True,
)
def update_data(n_intervals, selected, window_size, refresh_every, tick):
    global _generator, _current_selected, _current_window, _state

    selected     = selected or list(COMPANIES.keys())[:2]
    window_size  = window_size  or 80
    refresh_every = refresh_every or 5

    if window_size != _current_window:
        _state          = _make_state(window_size)
        _current_window = window_size
        _generator      = None

    if selected != _current_selected or _generator is None:
        _generator        = file_transaction_generator(DATA_PATH, selected)
        _current_selected = selected
        _state["global_ticks"].clear()
        _state["session_start"]    = datetime.now()
        _state["session_tick"]     = 0
        _state["first_real_price"] = {}
        for name in COMPANIES:
            _state["aligned_prices"][name].clear()

    for _ in range(refresh_every):
        tx   = next(_generator)
        name = tx["company"]
        _state["history"][name].append(tx["price"])
        _state["vol_history"][name].append(tx["volume"])
        _state["time_history"][name].append(tx["timestamp"])
        _state["recent_trades"].append(tx)
        _state["trade_counts"][name]  += 1
        _state["total_volume"][name]  += tx["volume"]
        _state["last_prices"][name]    = tx["price"]
        _state["last_changes"][name]   = tx["change_pct"]
        if name not in _state["first_real_price"]:
            _state["first_real_price"][name] = tx["price"]

    _state["session_tick"] += 1
    tick_time = (
        _state["session_start"] + timedelta(seconds=_state["session_tick"])
    ).strftime("%H:%M:%S")
    _state["global_ticks"].append(tick_time)
    for name in selected:
        _state["aligned_prices"][name].append(
            _state["last_prices"].get(name, COMPANIES[name]["base"])
        )

    return (tick or 0) + 1


@app.callback(
    Output("metrics-row", "children"),
    Input("tick-store", "data"),
    State("selected-companies", "value"),
)
def update_metrics(tick, selected):
    sel = selected or list(COMPANIES.keys())[:2]
    cards = []
    for name in sel:
        price  = _state["last_prices"].get(name, COMPANIES[name]["base"])
        change = _state["last_changes"].get(name, 0.0)
        arrow  = "▲" if change >= 0 else "▼"
        delta_color = "#34D399" if change >= 0 else "#F87171"
        cards.append(html.Div([
            html.Div(name,
                     style={"color": TEXT_MUTED, "fontSize": "0.78rem",
                             "marginBottom": "4px"}),
            html.Div(f"₴ {price:,.2f}",
                     style={"color": "#E2E8F0", "fontSize": "1.35rem",
                             "fontWeight": "700", "letterSpacing": "-0.5px"}),
            html.Div(f"{arrow} {abs(change):.3f}%",
                     style={"color": delta_color, "fontSize": "0.88rem",
                             "marginTop": "2px"}),
        ], style={
            "background":    CARD_BG,
            "border":        f"1px solid {BORDER}",
            "borderRadius":  "12px",
            "padding":       "14px 18px",
            "flex":          "1",
            "minWidth":      "110px",
        }))
    return html.Div(cards, style={"display": "flex", "gap": "10px", "flexWrap": "wrap"})


@app.callback(
    Output("main-chart", "figure"),
    Input("tick-store", "data"),
    State("focus-company", "value"),
    State("ma-window", "value"),
)
def update_main_chart(tick, focus, ma_window):
    if not focus or focus not in COMPANIES:
        return go.Figure().update_layout(**PLOTLY_LAYOUT)
    return build_main_chart(focus, ma_window or 7)


@app.callback(
    Output("multi-chart", "figure"),
    Input("tick-store", "data"),
    State("selected-companies", "value"),
)
def update_multi_chart(tick, selected):
    return build_multi_chart(selected or DEFAULT_SELECTED)


@app.callback(
    Output("volume-chart", "figure"),
    Input("tick-store", "data"),
    State("selected-companies", "value"),
)
def update_volume_chart(tick, selected):
    return build_volume_chart(selected or DEFAULT_SELECTED)


@app.callback(
    Output("heatmap", "figure"),
    Input("tick-store", "data"),
    State("selected-companies", "value"),
)
def update_heatmap(tick, selected):
    return build_heatmap(selected or DEFAULT_SELECTED)


@app.callback(
    Output("trades-tape", "children"),
    Input("tick-store", "data"),
)
def update_trades(tick):
    rows = []
    for tx in reversed(list(_state["recent_trades"])):
        c     = tx["change_pct"]
        color = "#34D399" if c >= 0 else "#F87171"
        arrow = "▲" if c >= 0 else "▼"
        rows.append(html.Div([
            html.Span(tx["timestamp"],
                      style={"width": "70px", "color": TEXT_MUTED}),
            html.Span(tx["company"],
                      style={"width": "110px", "fontWeight": "700",
                              "color": "#CBD5E1"}),
            html.Span(f"₴ {tx['price']:,.2f}",
                      style={"width": "100px", "color": "#CBD5E1"}),
            html.Span(f"{arrow}{abs(c):.3f}%",
                      style={"width": "80px", "color": color}),
            html.Span(f"{tx['volume']:,} акц.",
                      style={"color": TEXT_MUTED}),
        ], style={
            "display":       "flex",
            "justifyContent": "space-between",
            "padding":        "5px 10px",
            "borderBottom":   f"1px solid {BORDER}",
            "fontSize":       "0.82rem",
        }))

    return html.Div([
        html.Div("⏱ Останні угоди",
                 style={"color": "#94A3B8", "fontSize": "0.8rem",
                         "padding": "0 10px 6px"}),
        *rows,
    ], style={
        "background":   CARD_BG,
        "border":       f"1px solid {BORDER}",
        "borderRadius": "12px",
        "padding":      "10px",
        "marginTop":    "4px",
    })


# ─────────────────────────────────────────────────────────────────────────────
# ТОЧКА ВХОДУ
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=False, port=8059)
