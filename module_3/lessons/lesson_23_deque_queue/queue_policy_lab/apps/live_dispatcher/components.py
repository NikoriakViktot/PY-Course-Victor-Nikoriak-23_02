"""
apps/live_dispatcher/components.py — Reusable UI building blocks.

All functions return Dash component trees (no side effects).
"""
from __future__ import annotations

from dash import html

from domain.models import POLICY_COLORS, POLICY_DS, POLICY_BEHAVIOR, Policy


# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------

def wait_color(wait_ticks: int) -> str:
    if wait_ticks < 10:
        return "#4ECDC4"
    if wait_ticks < 30:
        return "#FFB347"
    if wait_ticks < 60:
        return "#FF8C42"
    return "#FF6B6B"


def status_color(status: str) -> str:
    return "#4ECDC4" if status == "busy" else "#555"


# ---------------------------------------------------------------------------
# Policy badge
# ---------------------------------------------------------------------------

def policy_badge(policy: str) -> html.Span:
    color = POLICY_COLORS.get(Policy(policy), "#888")
    return html.Span(
        policy,
        style={
            "background": color,
            "color": "#0d0d0d",
            "padding": "2px 10px",
            "borderRadius": "12px",
            "fontWeight": "700",
            "fontSize": "0.85em",
        },
    )


# ---------------------------------------------------------------------------
# Incoming arrivals feed
# ---------------------------------------------------------------------------

def incoming_panel(arrivals: list[dict], current_tick: int) -> html.Div:
    if not arrivals:
        return html.Div(
            "Очікуємо виклики…",
            style={"color": "#555", "padding": "10px", "fontStyle": "italic"},
        )
    items = []
    for trip in arrivals[:10]:
        age = current_tick - trip.get("arrival_tick", current_tick)
        items.append(
            html.Div(
                [
                    html.Span(f"#{abs(trip['trip_id'])}", style={"color": "#888", "fontSize": "0.75em", "minWidth": "40px"}),
                    html.Span(f" {trip['distance']:.1f} km", style={"color": "#eee", "fontWeight": "600"}),
                    html.Span(f" z{trip.get('pu_zone', '?')}→z{trip.get('do_zone', '?')}", style={"color": "#777", "fontSize": "0.75em"}),
                    html.Span(f" t+{age}", style={"color": "#555", "fontSize": "0.7em", "marginLeft": "auto"}),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "4px",
                    "padding": "5px 8px",
                    "borderLeft": "3px solid #4ECDC4",
                    "marginBottom": "3px",
                    "background": "#1a1a1a",
                    "borderRadius": "0 4px 4px 0",
                    "fontSize": "0.82em",
                },
            )
        )
    return html.Div(items)


# ---------------------------------------------------------------------------
# Queue buffer panel
# ---------------------------------------------------------------------------

def queue_panel(queue_items: list[dict], policy: str, current_tick: int) -> html.Div:
    from domain.policies import queue_display_order
    ordered = queue_display_order(queue_items, policy)

    if not ordered:
        return html.Div(
            "Черга порожня",
            style={"color": "#555", "padding": "10px", "fontStyle": "italic"},
        )

    # Show max 25 items; indicate overflow
    visible = ordered[:25]
    overflow = len(ordered) - 25

    rows = []
    for i, item in enumerate(visible):
        wait = current_tick - item.get("arrival_tick", current_tick)
        col = wait_color(wait)
        is_next = i == 0

        rows.append(
            html.Div(
                [
                    html.Span(
                        "▶ NEXT" if is_next else f"{i+1:2d}.",
                        style={"color": col if is_next else "#444",
                               "fontSize": "0.7em",
                               "minWidth": "46px",
                               "fontWeight": "700" if is_next else "400"},
                    ),
                    html.Span(
                        f"{item['distance']:.1f} km",
                        style={"color": "#ddd", "fontWeight": "600", "minWidth": "56px"},
                    ),
                    html.Span(
                        f"z{item.get('pu_zone', '?')}",
                        style={"color": "#666", "fontSize": "0.72em", "minWidth": "36px"},
                    ),
                    html.Span(
                        f"⏳ {wait}t",
                        style={"color": col, "fontSize": "0.75em",
                               "marginLeft": "auto", "fontWeight": "600" if wait > 30 else "400"},
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "4px",
                    "padding": "4px 8px",
                    "borderLeft": f"3px solid {col}",
                    "marginBottom": "2px",
                    "background": "#1c1c1c" if not is_next else "#1f2b2b",
                    "borderRadius": "0 4px 4px 0",
                    "fontSize": "0.82em",
                },
            )
        )

    if overflow > 0:
        rows.append(
            html.Div(
                f"… ще {overflow} поїздок у черзі",
                style={"color": "#555", "fontSize": "0.75em", "padding": "4px 8px"},
            )
        )

    return html.Div(rows)


# ---------------------------------------------------------------------------
# Drivers panel
# ---------------------------------------------------------------------------

def drivers_panel(drivers: list[dict], current_tick: int) -> html.Div:
    rows = []
    for d in drivers:
        busy = d["status"] == "busy"
        remaining = max(0, (d.get("free_at") or 0) - current_tick) if busy else 0
        icon = "🚗" if busy else "💤"
        trip_info = f"{d['distance']:.1f}km  -{remaining}t" if busy else "вільний"
        bar_width = f"{min(100, remaining * 8)}%" if busy else "0%"

        rows.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(icon, style={"fontSize": "1.1em"}),
                            html.Span(
                                f" D{d['driver_id']+1}",
                                style={"color": "#aaa", "fontSize": "0.8em", "marginLeft": "4px"},
                            ),
                            html.Span(
                                trip_info,
                                style={
                                    "color": "#4ECDC4" if busy else "#444",
                                    "fontSize": "0.78em",
                                    "marginLeft": "auto",
                                },
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center"},
                    ),
                    html.Div(
                        style={
                            "height": "3px",
                            "background": "#333",
                            "borderRadius": "2px",
                            "marginTop": "3px",
                            "overflow": "hidden",
                        },
                        children=html.Div(
                            style={
                                "height": "100%",
                                "width": bar_width,
                                "background": "#4ECDC4",
                                "borderRadius": "2px",
                                "transition": "width 0.3s ease",
                            }
                        ),
                    ),
                ],
                style={
                    "padding": "5px 8px",
                    "marginBottom": "3px",
                    "background": "#1c1c1c",
                    "borderRadius": "4px",
                    "borderLeft": f"3px solid {'#4ECDC4' if busy else '#333'}",
                },
            )
        )
    return html.Div(rows)


# ---------------------------------------------------------------------------
# Completed trips panel
# ---------------------------------------------------------------------------

def completed_panel(completed: list[dict]) -> html.Div:
    recent = list(reversed(completed))[:12]
    if not recent:
        return html.Div(
            "Немає завершених поїздок",
            style={"color": "#555", "padding": "10px", "fontStyle": "italic"},
        )
    rows = []
    for trip in recent:
        col = wait_color(trip["wait_ticks"])
        rows.append(
            html.Div(
                [
                    html.Span("✓", style={"color": "#4ECDC4", "fontSize": "0.8em", "minWidth": "16px"}),
                    html.Span(f"{trip['distance']:.1f} km", style={"color": "#ddd", "fontWeight": "600", "fontSize": "0.82em"}),
                    html.Span(f"⏳{trip['wait_ticks']}t", style={"color": col, "fontSize": "0.75em", "marginLeft": "auto"}),
                ],
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "4px",
                    "padding": "4px 8px",
                    "borderLeft": f"3px solid {col}",
                    "marginBottom": "2px",
                    "background": "#1a1a1a",
                    "borderRadius": "0 4px 4px 0",
                    "fontSize": "0.82em",
                },
            )
        )
    return html.Div(rows)


# ---------------------------------------------------------------------------
# KPI strip
# ---------------------------------------------------------------------------

def kpi_strip(kpis: dict, policy: str) -> html.Div:
    color = POLICY_COLORS.get(Policy(policy), "#888")

    def kpi(label: str, value: str, highlight: bool = False) -> html.Div:
        return html.Div(
            [
                html.Div(label, style={"color": "#666", "fontSize": "0.7em", "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                html.Div(value, style={"color": color if highlight else "#eee", "fontSize": "1.3em", "fontWeight": "700", "lineHeight": "1.2"}),
            ],
            style={"textAlign": "center", "padding": "0 12px"},
        )

    return html.Div(
        [
            kpi("Тік",         str(kpis.get("tick", 0))),
            html.Div(style={"width": "1px", "background": "#333", "margin": "0 4px"}),
            kpi("Черга",       str(kpis.get("queue_length", 0)),    True),
            kpi("Виконано",    str(kpis.get("total_completed", 0))),
            kpi("Голодування", str(kpis.get("total_starved", 0)),   kpis.get("total_starved", 0) > 0),
            html.Div(style={"width": "1px", "background": "#333", "margin": "0 4px"}),
            kpi("Сер. чека",   f"{kpis.get('avg_wait', 0):.1f}t"),
            kpi("Fairness",    f"{kpis.get('fairness', 0):.3f}",    True),
            kpi("Throughput",  f"{kpis.get('throughput', 0):.1f}/t"),
            kpi("Водіїв",      f"{kpis.get('active_drivers', 0)}"),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "background": "#111",
            "borderTop": f"2px solid {color}",
            "borderBottom": "1px solid #222",
            "padding": "10px 16px",
            "flexWrap": "wrap",
            "gap": "4px",
        },
    )


# ---------------------------------------------------------------------------
# Panel wrapper
# ---------------------------------------------------------------------------

def panel(title: str, content: html.Div, accent: str = "#4ECDC4") -> html.Div:
    return html.Div(
        [
            html.Div(
                title,
                style={
                    "color": accent,
                    "fontSize": "0.7em",
                    "fontWeight": "700",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.08em",
                    "padding": "6px 10px 4px",
                    "borderBottom": f"1px solid {accent}22",
                    "background": "#0f0f0f",
                },
            ),
            html.Div(
                content,
                style={"padding": "6px", "overflowY": "auto", "maxHeight": "320px"},
            ),
        ],
        style={
            "background": "#161616",
            "border": "1px solid #2a2a2a",
            "borderRadius": "6px",
            "overflow": "hidden",
            "flex": "1",
            "minWidth": "0",
        },
    )
