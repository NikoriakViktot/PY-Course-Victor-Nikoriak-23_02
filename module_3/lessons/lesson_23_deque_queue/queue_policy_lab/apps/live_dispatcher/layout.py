"""
apps/live_dispatcher/layout.py — Static layout tree for the live dispatcher.
"""
from __future__ import annotations

from dash import dcc, html

from domain.models import Policy, POLICY_COLORS, POLICY_DS, POLICY_BEHAVIOR


def build_layout() -> html.Div:
    return html.Div(
        id="app-root",
        children=[

            # ── Hidden stores ────────────────────────────────────────────
            dcc.Store(id="store-sim", storage_type="memory"),
            dcc.Interval(id="interval-tick", interval=400, n_intervals=0, disabled=True),

            # ── Header bar ───────────────────────────────────────────────
            html.Div(
                id="header",
                children=[
                    html.Div(
                        [
                            html.Span("🚕", style={"fontSize": "1.4em"}),
                            html.Span(
                                "LIVE DISPATCH ROOM",
                                style={"fontWeight": "700", "letterSpacing": "0.12em",
                                       "fontSize": "1em", "color": "#eee"},
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center", "gap": "10px"},
                    ),
                    # Policy selector
                    html.Div(
                        [
                            html.Label("Політика:", style={"color": "#666", "fontSize": "0.75em"}),
                            dcc.Dropdown(
                                id="drp-policy",
                                options=[
                                    {"label": f"{p.value} — {POLICY_DS[p]}", "value": p.value}
                                    for p in Policy
                                ],
                                value="FIFO",
                                clearable=False,
                                style={"width": "360px", "fontSize": "0.82em"},
                                className="dark-dropdown",
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center", "gap": "8px"},
                    ),
                    # Control buttons
                    html.Div(
                        [
                            html.Button("▶ START",  id="btn-start",  n_clicks=0, className="btn btn-green"),
                            html.Button("⏸ PAUSE",  id="btn-pause",  n_clicks=0, className="btn btn-yellow"),
                            html.Button("↺ RESET",  id="btn-reset",  n_clicks=0, className="btn btn-red"),
                            html.Button("→ STEP",   id="btn-step",   n_clicks=0, className="btn btn-blue"),
                            html.Button("💥 BURST",  id="btn-burst",  n_clicks=0, className="btn btn-purple"),
                        ],
                        style={"display": "flex", "gap": "6px"},
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "background": "#0d0d0d",
                    "borderBottom": "2px solid #222",
                    "padding": "10px 20px",
                    "flexWrap": "wrap",
                    "gap": "10px",
                },
            ),

            # ── Controls strip ───────────────────────────────────────────
            html.Div(
                id="controls-strip",
                children=[
                    _slider_group("Надходжень/тік (λ)", "sld-arrival", 0.3, 5.0, 1.0, 0.1),
                    _slider_group("Водіїв",              "sld-drivers",  1,  25,   5, 1),
                    _slider_group("Тіків на км",          "sld-speed",   0.5, 6.0, 2.0, 0.5),
                    _slider_group("К-сть поїздок",        "sld-trips",   100, 2000, 300, 50),
                    html.Div(
                        id="policy-hint",
                        style={"color": "#888", "fontSize": "0.72em",
                               "maxWidth": "260px", "lineHeight": "1.4"},
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "flex-end",
                    "gap": "20px",
                    "background": "#111",
                    "borderBottom": "1px solid #1e1e1e",
                    "padding": "10px 20px",
                    "flexWrap": "wrap",
                },
            ),

            # ── 4-panel dispatch row ─────────────────────────────────────
            html.Div(
                id="dispatch-row",
                children=[
                    html.Div(id="panel-incoming",  className="dispatch-panel"),
                    html.Div(id="panel-queue",     className="dispatch-panel"),
                    html.Div(id="panel-drivers",   className="dispatch-panel"),
                    html.Div(id="panel-completed", className="dispatch-panel"),
                ],
                style={
                    "display": "flex",
                    "gap": "10px",
                    "padding": "10px 20px",
                    "background": "#0f0f0f",
                },
            ),

            # ── KPI strip ────────────────────────────────────────────────
            html.Div(id="panel-kpis"),

            # ── Live charts ──────────────────────────────────────────────
            html.Div(
                id="charts-row",
                children=[
                    dcc.Graph(id="chart-queue",      config={"displayModeBar": False}, style={"flex": "1"}),
                    dcc.Graph(id="chart-throughput", config={"displayModeBar": False}, style={"flex": "1"}),
                    dcc.Graph(id="chart-wait",       config={"displayModeBar": False}, style={"flex": "1"}),
                    dcc.Graph(id="chart-starved",    config={"displayModeBar": False}, style={"flex": "1"}),
                ],
                style={
                    "display": "flex",
                    "gap": "8px",
                    "padding": "0 20px 14px",
                    "background": "#0f0f0f",
                },
            ),

            # ── Status bar ───────────────────────────────────────────────
            html.Div(id="status-bar", style={
                "background": "#080808",
                "borderTop": "1px solid #1a1a1a",
                "padding": "5px 20px",
                "color": "#444",
                "fontSize": "0.7em",
            }),
        ],
        style={
            "fontFamily": "'JetBrains Mono', 'Courier New', monospace",
            "background": "#0f0f0f",
            "minHeight": "100vh",
            "color": "#ccc",
        },
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slider_group(label: str, slider_id: str,
                   mn: float, mx: float, val: float, step: float) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Label(label, style={"color": "#666", "fontSize": "0.7em",
                                             "textTransform": "uppercase"}),
                    html.Span(id=f"{slider_id}-val",
                              style={"color": "#4ECDC4", "fontSize": "0.8em",
                                     "marginLeft": "6px", "fontWeight": "600"}),
                ],
                style={"display": "flex", "alignItems": "baseline", "marginBottom": "4px"},
            ),
            dcc.Slider(
                id=slider_id,
                min=mn, max=mx, step=step, value=val,
                marks=None,
                tooltip={"placement": "bottom", "always_visible": False},
                className="dark-slider",
            ),
        ],
        style={"flex": "1", "minWidth": "120px", "maxWidth": "200px"},
    )
