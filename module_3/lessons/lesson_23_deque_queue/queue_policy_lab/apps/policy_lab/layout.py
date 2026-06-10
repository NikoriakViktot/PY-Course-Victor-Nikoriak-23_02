"""
apps/policy_lab/layout.py — Static layout for the Policy Analysis Lab.
"""
from __future__ import annotations

from dash import dcc, html

from domain.models import Policy, POLICY_DS


def build_layout() -> html.Div:
    return html.Div(
        id="lab-root",
        children=[
            dcc.Store(id="store-results", storage_type="memory"),

            # ── Header ──────────────────────────────────────────────────
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("📊", style={"fontSize": "1.4em"}),
                            html.Span("POLICY ANALYSIS LAB",
                                      style={"fontWeight": "700", "letterSpacing": "0.12em",
                                             "color": "#eee"}),
                        ],
                        style={"display": "flex", "alignItems": "center", "gap": "10px"},
                    ),
                    html.Div(
                        "Batch-порівняння FIFO / LIFO / RANDOM / PRIORITY на однакових даних",
                        style={"color": "#555", "fontSize": "0.8em"},
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "space-between",
                    "background": "#0d0d0d",
                    "borderBottom": "2px solid #222",
                    "padding": "12px 24px",
                    "flexWrap": "wrap",
                    "gap": "8px",
                },
            ),

            # ── Controls ────────────────────────────────────────────────
            html.Div(
                [
                    _control("Поїздок",          "sld-n-trips",   100, 2000, 500, 100),
                    _control("Arrival rate (λ)",  "sld-arrival",   0.3, 3.0,  1.0, 0.1),
                    _control("Водіїв",            "sld-drivers",   1,   20,   5,   1),
                    _control("Тіків на км",        "sld-speed",    0.5, 6.0,  2.0, 0.5),
                    html.Div(
                        [
                            html.Label("Політики:", style={"color": "#666", "fontSize": "0.72em",
                                                           "textTransform": "uppercase"}),
                            dcc.Checklist(
                                id="chk-policies",
                                options=[{"label": f" {p.value}", "value": p.value} for p in Policy],
                                value=[p.value for p in Policy],
                                inline=True,
                                style={"color": "#aaa", "fontSize": "0.82em", "gap": "10px"},
                                inputStyle={"marginRight": "4px"},
                            ),
                        ],
                        style={"display": "flex", "flexDirection": "column", "gap": "6px"},
                    ),
                    html.Div(
                        [
                            html.Button("▶ ЗАПУСТИТИ", id="btn-run-lab", n_clicks=0,
                                        className="btn btn-green",
                                        style={"padding": "8px 20px", "fontSize": "0.9em"}),
                            html.Div(id="lab-status",
                                     style={"color": "#555", "fontSize": "0.72em", "marginTop": "4px"}),
                        ],
                        style={"display": "flex", "flexDirection": "column", "alignItems": "flex-start"},
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "flex-end",
                    "gap": "24px",
                    "padding": "14px 24px",
                    "background": "#111",
                    "borderBottom": "1px solid #1e1e1e",
                    "flexWrap": "wrap",
                },
            ),

            # ── KPI cards row ────────────────────────────────────────────
            html.Div(id="kpi-cards",
                     style={"display": "flex", "gap": "10px", "padding": "14px 24px",
                            "flexWrap": "wrap", "background": "#0f0f0f"}),

            # ── Charts grid ──────────────────────────────────────────────
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(id="ch-queue",       config={"displayModeBar": False}),
                         dcc.Graph(id="ch-throughput",  config={"displayModeBar": False})],
                        style={"display": "flex", "flex": "1", "gap": "10px", "flexWrap": "wrap"},
                    ),
                    html.Div(
                        [dcc.Graph(id="ch-wait-hist",   config={"displayModeBar": False}),
                         dcc.Graph(id="ch-fairness",    config={"displayModeBar": False})],
                        style={"display": "flex", "flex": "1", "gap": "10px", "flexWrap": "wrap"},
                    ),
                    html.Div(
                        [dcc.Graph(id="ch-starvation",  config={"displayModeBar": False}),
                         dcc.Graph(id="ch-bias",        config={"displayModeBar": False})],
                        style={"display": "flex", "flex": "1", "gap": "10px", "flexWrap": "wrap"},
                    ),
                ],
                style={"padding": "0 14px 14px", "background": "#0f0f0f",
                       "display": "flex", "flexDirection": "column", "gap": "10px"},
            ),

            # ── Summary table ─────────────────────────────────────────────
            html.Div(
                [
                    html.Div("📋 Зведена таблиця метрик",
                             style={"color": "#888", "fontSize": "0.75em",
                                    "textTransform": "uppercase", "letterSpacing": "0.08em",
                                    "marginBottom": "8px"}),
                    html.Div(id="summary-table"),
                ],
                style={"padding": "14px 24px", "background": "#0f0f0f",
                       "borderTop": "1px solid #1e1e1e"},
            ),

            # ── Insights ─────────────────────────────────────────────────
            html.Div(id="insights-block",
                     style={"padding": "14px 24px", "background": "#0d0d0d",
                            "borderTop": "1px solid #1e1e1e"}),
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

def _control(label: str, sid: str, mn, mx, val, step) -> html.Div:
    return html.Div(
        [
            html.Div(
                [
                    html.Label(label, style={"color": "#666", "fontSize": "0.7em",
                                             "textTransform": "uppercase"}),
                    html.Span(id=f"{sid}-val",
                              style={"color": "#9B59B6", "fontSize": "0.8em",
                                     "marginLeft": "6px", "fontWeight": "600"}),
                ],
                style={"display": "flex", "alignItems": "baseline", "marginBottom": "4px"},
            ),
            dcc.Slider(id=sid, min=mn, max=mx, step=step, value=val,
                       marks=None, tooltip={"placement": "bottom", "always_visible": False},
                       className="dark-slider"),
        ],
        style={"flex": "1", "minWidth": "120px", "maxWidth": "180px"},
    )
