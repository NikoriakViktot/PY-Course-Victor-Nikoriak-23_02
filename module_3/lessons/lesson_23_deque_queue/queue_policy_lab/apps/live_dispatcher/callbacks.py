"""
apps/live_dispatcher/callbacks.py — All Dash callbacks for the live dispatcher.

Architecture:
  1. control_simulation()  — master state machine (interval + buttons)
  2. update_panels()       — renders 4 operational panels from state
  3. update_charts()       — renders 4 live charts from state
  4. update_slider_vals()  — display slider values + policy hint
  5. update_interval()     — enable/disable the tick interval
  6. update_status_bar()   — bottom status line
"""
from __future__ import annotations

import plotly.graph_objects as go
from dash import Input, Output, State, callback_context, html, no_update

from apps.live_dispatcher import components as comp
from domain import dispatcher_engine as engine
from domain.models import POLICY_COLORS, POLICY_BEHAVIOR, Policy
from services import metrics_service, trip_service


TICK_INTERVAL_MS = 400


def register_callbacks(app) -> None:

    # =========================================================================
    # 1. Master state machine
    # =========================================================================

    @app.callback(
        Output("store-sim", "data"),
        [
            Input("interval-tick",  "n_intervals"),
            Input("btn-start",      "n_clicks"),
            Input("btn-pause",      "n_clicks"),
            Input("btn-reset",      "n_clicks"),
            Input("btn-step",       "n_clicks"),
            Input("btn-burst",      "n_clicks"),
            Input("drp-policy",     "value"),
        ],
        [
            State("store-sim",   "data"),
            State("sld-arrival", "value"),
            State("sld-drivers", "value"),
            State("sld-speed",   "value"),
            State("sld-trips",   "value"),
        ],
        prevent_initial_call=True,
    )
    def control_simulation(
        n_ivl, n_start, n_pause, n_reset, n_step, n_burst, policy,
        state, arrival, drivers, speed, n_trips,
    ):
        ctx = callback_context
        if not ctx.triggered:
            return no_update

        triggered = ctx.triggered[0]["prop_id"].split(".")[0]

        # ── Reset or first load ─────────────────────────────────────────
        if triggered == "btn-reset" or state is None:
            trips, _ = trip_service.load_trips(int(n_trips or 300))
            return engine.init_state(
                trips                = trips,
                policy               = policy or "FIFO",
                arrival_rate         = float(arrival or 1.0),
                num_drivers          = int(drivers or 5),
                process_ticks_per_km = float(speed or 2.0),
            )

        state = dict(state)

        # ── Start ───────────────────────────────────────────────────────
        if triggered == "btn-start":
            state["running"] = True
            state["policy"]  = policy
            state["params"]["arrival_rate"]         = float(arrival)
            state["params"]["num_drivers"]          = int(drivers)
            state["params"]["process_ticks_per_km"] = float(speed)
            # Rebuild drivers list if count changed
            current_count = len(state.get("drivers", []))
            if int(drivers) != current_count:
                state["drivers"] = _rebuild_drivers(int(drivers), state["tick"])
            return state

        # ── Pause ───────────────────────────────────────────────────────
        if triggered == "btn-pause":
            state["running"] = False
            return state

        # ── Step ────────────────────────────────────────────────────────
        if triggered == "btn-step":
            state["policy"] = policy
            return engine.advance_one_tick(state)

        # ── Burst — inject synthetic traffic spike ───────────────────────
        if triggered == "btn-burst":
            return engine.inject_burst(state, n=10)

        # ── Policy hot-swap ─────────────────────────────────────────────
        if triggered == "drp-policy":
            state["policy"] = policy
            return state

        # ── Interval tick ────────────────────────────────────────────────
        if triggered == "interval-tick":
            if not state.get("running"):
                return no_update
            state["policy"] = policy
            state["params"]["arrival_rate"]         = float(arrival)
            state["params"]["num_drivers"]          = int(drivers)
            state["params"]["process_ticks_per_km"] = float(speed)
            # Resize drivers if slider changed mid-simulation
            current_count = len(state.get("drivers", []))
            if int(drivers) != current_count:
                state["drivers"] = _rebuild_drivers(int(drivers), state["tick"])
            return engine.advance_one_tick(state)

        return no_update

    # =========================================================================
    # 2. Four operational panels
    # =========================================================================

    @app.callback(
        [
            Output("panel-incoming",  "children"),
            Output("panel-queue",     "children"),
            Output("panel-drivers",   "children"),
            Output("panel-completed", "children"),
        ],
        Input("store-sim", "data"),
        prevent_initial_call=False,
    )
    def update_panels(state):
        if state is None:
            empty = html.Div("Натисніть ↺ RESET для ініціалізації",
                             style={"color": "#444", "padding": "12px", "fontSize": "0.82em"})
            return empty, empty, empty, empty

        policy = state.get("policy", "FIFO")
        tick   = state.get("tick", 0)
        color  = POLICY_COLORS.get(Policy(policy), "#888")

        incoming = comp.panel(
            "📞 Вхідні виклики",
            comp.incoming_panel(state.get("recent_arrivals", []), tick),
            accent=color,
        )
        queue = comp.panel(
            f"📦 Буфер черги [{policy}] — {len(state.get('queue', []))} в черзі",
            comp.queue_panel(state.get("queue", []), policy, tick),
            accent=color,
        )
        drivers = comp.panel(
            f"🚗 Водії ({sum(1 for d in state.get('drivers', []) if d['status']=='busy')}/{len(state.get('drivers', []))} зайняті)",
            comp.drivers_panel(state.get("drivers", []), tick),
            accent="#4ECDC4",
        )
        completed = comp.panel(
            f"✅ Завершено ({state.get('total_completed', 0)} всього)",
            comp.completed_panel(state.get("completed", [])),
            accent="#9B59B6",
        )
        return incoming, queue, drivers, completed

    # =========================================================================
    # 3. KPI strip
    # =========================================================================

    @app.callback(
        Output("panel-kpis", "children"),
        Input("store-sim", "data"),
        prevent_initial_call=False,
    )
    def update_kpis(state):
        if state is None:
            return html.Div()
        kpis   = metrics_service.live_kpis(state)
        policy = state.get("policy", "FIFO")
        return comp.kpi_strip(kpis, policy)

    # =========================================================================
    # 4. Live charts
    # =========================================================================

    @app.callback(
        [
            Output("chart-queue",      "figure"),
            Output("chart-throughput", "figure"),
            Output("chart-wait",       "figure"),
            Output("chart-starved",    "figure"),
        ],
        Input("store-sim", "data"),
        prevent_initial_call=False,
    )
    def update_charts(state):
        if state is None:
            return _empty_fig("Черга"), _empty_fig("Throughput"), _empty_fig("Очікування"), _empty_fig("Голодування")

        policy = state.get("policy", "FIFO")
        color  = POLICY_COLORS.get(Policy(policy), "#888")
        series = metrics_service.chart_series(state)

        q_fig = _line_fig(series["ticks"], series["queue"],      "Довжина черги",    color,   "Тіки", "Поїздок у черзі")
        t_fig = _line_fig(series["ticks"], series["throughput"], "Throughput",       "#9B59B6","Тіки", "Завершено/тік")
        w_fig = _line_fig(series["ticks"], series["wait"],       "Сер. очікування",  "#FFB347","Тіки", "Тіки очікування")
        s_fig = _line_fig(series["ticks"], series["starved"],    "Голодування (кум.)", "#FF6B6B","Тіки", "Відкинуто")

        return q_fig, t_fig, w_fig, s_fig

    # =========================================================================
    # 5. Slider value display + policy hint
    # =========================================================================

    @app.callback(
        [
            Output("sld-arrival-val", "children"),
            Output("sld-drivers-val", "children"),
            Output("sld-speed-val",   "children"),
            Output("sld-trips-val",   "children"),
            Output("policy-hint",     "children"),
        ],
        [
            Input("sld-arrival", "value"),
            Input("sld-drivers", "value"),
            Input("sld-speed",   "value"),
            Input("sld-trips",   "value"),
            Input("drp-policy",  "value"),
        ],
    )
    def update_slider_vals(arrival, drivers, speed, trips, policy):
        hint = POLICY_BEHAVIOR.get(Policy(policy), "") if policy else ""
        return (
            str(arrival),
            str(drivers),
            str(speed),
            str(trips),
            hint,
        )

    # =========================================================================
    # 6. Enable/disable interval
    # =========================================================================

    @app.callback(
        Output("interval-tick", "disabled"),
        Input("store-sim", "data"),
        prevent_initial_call=False,
    )
    def update_interval(state):
        if state is None:
            return True
        return not state.get("running", False)

    # =========================================================================
    # 7. Status bar
    # =========================================================================

    @app.callback(
        Output("status-bar", "children"),
        Input("store-sim", "data"),
        prevent_initial_call=False,
    )
    def update_status(state):
        if state is None:
            return "🔴 Не ініціалізовано — натисніть ↺ RESET"
        t = state.get("tick", 0)
        n = len(state.get("trips", []))
        p = state.get("policy", "?")
        running = state.get("running", False)
        dot = "🟢" if running else "⏸"
        schedule_end = max((int(k) for k in state.get("arrival_schedule", {"0": []})), default=0)
        return f"{dot} Тік {t} / ~{schedule_end} · Політика: {p} · Поїздок: {n} · {POLICY_BEHAVIOR.get(Policy(p), '')}"


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _hex_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _line_fig(
    x: list, y: list, title: str, color: str,
    xlab: str = "Тік", ylab: str = "",
) -> go.Figure:
    fig = go.Figure()
    if x:
        # Show last 300 ticks for performance
        x, y = x[-300:], y[-300:]
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode="lines",
            line=dict(color=color, width=1.5),
            fill="tozeroy",
            fillcolor=_hex_rgba(color, 0.09),
            hovertemplate=f"{xlab}: %{{x}}<br>{ylab}: %{{y}}<extra></extra>",
        ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=11, color="#888"), x=0.02, y=0.95),
        xaxis=dict(title=None, color="#444", gridcolor="#1e1e1e", showgrid=True),
        yaxis=dict(title=None, color="#444", gridcolor="#1e1e1e", showgrid=True),
        margin=dict(l=36, r=10, t=28, b=28),
        height=180,
        plot_bgcolor="#111",
        paper_bgcolor="#0f0f0f",
        font=dict(color="#666", size=10),
        showlegend=False,
    )
    return fig


def _empty_fig(title: str) -> go.Figure:
    return _line_fig([], [], title, "#333")


def _rebuild_drivers(count: int, tick: int) -> list[dict]:
    """Create a fresh driver list when count changes mid-simulation."""
    return [
        {"driver_id": i, "status": "idle",
         "trip_id": None, "distance": None,
         "start_tick": None, "free_at": None}
        for i in range(count)
    ]
