"""
apps/policy_lab/callbacks.py — Callbacks for the Policy Analysis Lab.
"""
from __future__ import annotations

import plotly.graph_objects as go
from dash import Input, Output, State, html, no_update, dash_table, callback_context

from apps.policy_lab.charts import (
    fairness_bar, priority_bias_scatter, queue_length_chart,
    starvation_bar, throughput_chart, wait_histogram,
)
from domain import dispatcher_engine as engine
from domain.models import POLICY_COLORS, POLICY_BEHAVIOR, Policy
from services import metrics_service, trip_service


def register_callbacks(app) -> None:

    # =========================================================================
    # Slider display
    # =========================================================================

    @app.callback(
        [Output(f"sld-{k}-val", "children") for k in ["n-trips", "arrival", "drivers", "speed"]],
        [Input(f"sld-{k}", "value")         for k in ["n-trips", "arrival", "drivers", "speed"]],
    )
    def show_slider_vals(n, arr, drv, spd):
        return str(n), str(arr), str(drv), str(spd)

    # =========================================================================
    # Run batch simulation → store results
    # =========================================================================

    @app.callback(
        Output("store-results", "data"),
        Output("lab-status",    "children"),
        Input("btn-run-lab",    "n_clicks"),
        [
            State("sld-n-trips",  "value"),
            State("sld-arrival",  "value"),
            State("sld-drivers",  "value"),
            State("sld-speed",    "value"),
            State("chk-policies", "value"),
        ],
        prevent_initial_call=True,
    )
    def run_batch(n_clicks, n_trips, arrival, drivers, speed, selected_policies):
        if not selected_policies:
            return no_update, "⚠️ Виберіть хоча б одну політику"

        trips, is_real = trip_service.load_trips(int(n_trips))
        source = "NYC TLC 2023-01" if is_real else "синтетичні дані"

        results: dict[str, dict] = {}
        for pv in selected_policies:
            state = engine.init_state(
                trips                = trips,
                policy               = pv,
                arrival_rate         = float(arrival),
                num_drivers          = int(drivers),
                process_ticks_per_km = float(speed),
            )
            state = engine.run_to_completion(state)

            results[pv] = {
                "summary":          metrics_service.batch_summary(state),
                "series":           metrics_service.chart_series(state),
                "all_waits":        state.get("all_waits", []),
                "completed_records": state.get("completed", []),
            }

        status = f"✅ Виконано · {n_trips} поїздок · {source} · {len(selected_policies)} політик"
        return results, status

    # =========================================================================
    # Update all charts + KPI cards from stored results
    # =========================================================================

    @app.callback(
        [
            Output("kpi-cards",      "children"),
            Output("ch-queue",       "figure"),
            Output("ch-throughput",  "figure"),
            Output("ch-wait-hist",   "figure"),
            Output("ch-fairness",    "figure"),
            Output("ch-starvation",  "figure"),
            Output("ch-bias",        "figure"),
            Output("summary-table",  "children"),
            Output("insights-block", "children"),
        ],
        Input("store-results", "data"),
        prevent_initial_call=False,
    )
    def update_all(results):
        if not results:
            empty_fig = go.Figure()
            empty_fig.update_layout(
                plot_bgcolor="#111", paper_bgcolor="#161616",
                font=dict(color="#555"), height=300,
                xaxis=dict(visible=False), yaxis=dict(visible=False),
                annotations=[dict(text="Натисніть ▶ ЗАПУСТИТИ", showarrow=False,
                                  font=dict(color="#444", size=14), x=0.5, y=0.5)],
            )
            placeholder = html.Div("Натисніть ▶ ЗАПУСТИТИ",
                                   style={"color": "#444", "padding": "20px"})
            return (
                placeholder,
                empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
                placeholder, placeholder,
            )

        kpis_row    = _build_kpi_cards(results)
        q_fig       = queue_length_chart(results)
        t_fig       = throughput_chart(results)
        wh_fig      = wait_histogram(results)
        fair_fig    = fairness_bar(results)
        starv_fig   = starvation_bar(results)
        bias_fig    = (
            priority_bias_scatter(results["PRIORITY"], results["FIFO"])
            if "PRIORITY" in results and "FIFO" in results
            else go.Figure()
        )
        table       = _build_summary_table(results)
        insights    = _build_insights(results)

        return (kpis_row, q_fig, t_fig, wh_fig, fair_fig,
                starv_fig, bias_fig, table, insights)


# ---------------------------------------------------------------------------
# Private: KPI cards
# ---------------------------------------------------------------------------

def _build_kpi_cards(results: dict) -> html.Div:
    cards = []
    for policy, data in results.items():
        s     = data["summary"]
        color = POLICY_COLORS.get(Policy(policy), "#888")
        cards.append(
            html.Div(
                [
                    html.Div(policy, style={"color": color, "fontWeight": "700",
                                            "fontSize": "0.9em", "marginBottom": "6px",
                                            "borderBottom": f"1px solid {color}33",
                                            "paddingBottom": "4px"}),
                    html.Div(POLICY_BEHAVIOR.get(Policy(policy), ""),
                             style={"color": "#555", "fontSize": "0.68em",
                                    "marginBottom": "8px", "lineHeight": "1.3"}),
                    *[
                        html.Div(
                            [html.Span(v, style={"color": color, "fontWeight": "600",
                                                  "fontSize": "1.15em"}),
                             html.Span(f" {k}", style={"color": "#555", "fontSize": "0.7em"})],
                            style={"marginBottom": "2px"},
                        )
                        for k, v in [
                            ("виконано",  str(s.get("completed", 0))),
                            ("голод.",    str(s.get("starved", 0))),
                            ("avg wait",  f"{s.get('avg_wait', 0):.1f}t"),
                            ("fairness",  f"{s.get('fairness', 0):.3f}"),
                            ("p95 wait",  f"{s.get('p95_wait', 0):.0f}t"),
                        ]
                    ],
                ],
                style={
                    "flex": "1",
                    "minWidth": "180px",
                    "background": "#161616",
                    "border": f"1px solid {color}44",
                    "borderTop": f"3px solid {color}",
                    "borderRadius": "4px",
                    "padding": "12px 14px",
                },
            )
        )
    return html.Div(cards, style={"display": "flex", "gap": "10px", "flexWrap": "wrap"})


# ---------------------------------------------------------------------------
# Private: Summary table
# ---------------------------------------------------------------------------

def _build_summary_table(results: dict) -> html.Div:
    rows = []
    for policy, data in results.items():
        s = data["summary"]
        rows.append({
            "Політика":          policy,
            "Виконано":          s.get("completed", 0),
            "Голодування":       s.get("starved", 0),
            "Avg Wait (ticks)":  s.get("avg_wait", 0),
            "P95 Wait":          s.get("p95_wait", 0),
            "Max Wait":          s.get("max_wait", 0),
            "Fairness":          s.get("fairness", 0),
            "Throughput/тік":    s.get("throughput", 0),
            "Max Queue":         s.get("max_queue", 0),
        })

    return dash_table.DataTable(
        data=rows,
        columns=[{"name": c, "id": c} for c in rows[0].keys()] if rows else [],
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": "#1a1a1a", "color": "#888",
                      "fontWeight": "600", "fontSize": "0.72em",
                      "textTransform": "uppercase", "letterSpacing": "0.06em",
                      "border": "1px solid #2a2a2a"},
        style_cell={"backgroundColor": "#161616", "color": "#ccc",
                    "fontSize": "0.82em", "border": "1px solid #222",
                    "textAlign": "center", "padding": "8px 10px"},
        style_data_conditional=[
            {"if": {"filter_query": "{Голодування} > 0", "column_id": "Голодування"},
             "color": "#FF6B6B", "fontWeight": "700"},
            {"if": {"filter_query": "{Fairness} > 0.6"},
             "color": "#4ECDC4"},
        ],
    )


# ---------------------------------------------------------------------------
# Private: Insights
# ---------------------------------------------------------------------------

def _build_insights(results: dict) -> html.Div:
    summaries = {p: d["summary"] for p, d in results.items()}
    fairest   = max(summaries, key=lambda p: summaries[p].get("fairness", 0))
    fastest   = max(summaries, key=lambda p: summaries[p].get("completed", 0))
    worst_star = max(summaries, key=lambda p: summaries[p].get("starved", 0))

    def block(title: str, body: str, color: str) -> html.Div:
        return html.Div(
            [
                html.Div(title, style={"color": color, "fontWeight": "700",
                                       "fontSize": "0.82em", "marginBottom": "4px"}),
                html.Div(body, style={"color": "#777", "fontSize": "0.78em",
                                      "lineHeight": "1.5"}),
            ],
            style={"flex": "1", "minWidth": "200px",
                   "background": "#161616", "borderLeft": f"3px solid {color}",
                   "padding": "10px 14px", "borderRadius": "0 4px 4px 0"},
        )

    insight_msg = (
        f"Найсправедливіша: {fairest} (Jain's index = {summaries[fairest].get('fairness', 0):.3f})  |  "
        f"Найбільший throughput: {fastest} ({summaries[fastest].get('completed', 0)} поїздок)  |  "
        f"Найбільше голодування: {worst_star} ({summaries[worst_star].get('starved', 0)} відкинуто)"
    )

    return html.Div(
        [
            html.Div("💡 Архітектурні висновки",
                     style={"color": "#888", "fontSize": "0.75em",
                            "textTransform": "uppercase", "letterSpacing": "0.08em",
                            "marginBottom": "12px"}),
            html.Div(
                [
                    block("🟢 FIFO — collections.deque",
                          "popleft() гарантує хронологічний порядок. Жодна поїздка "
                          "не пропускається. Ідеальний вибір для справедливого диспетчера.",
                          "#4ECDC4"),
                    block("🔴 LIFO — list.pop()",
                          "Новий виклик завжди першим. Старі запити тонуть на дні стека "
                          "і ніколи не обслуговуються → starvation. Катастрофа для сервісу.",
                          "#FF6B6B"),
                    block("🟡 RANDOM — list[random]",
                          "Жоден клієнт не може передбачити час очікування. "
                          "Дисперсія висока. Ніяких гарантій. Нестабільний відгук.",
                          "#FFB347"),
                    block("🟣 PRIORITY — heapq",
                          "Мінімальне середнє очікування, але короткі поїздки субсидують "
                          "довгі. Priority starvation — довгі поїздки можуть ніколи не виїхати.",
                          "#9B59B6"),
                ],
                style={"display": "flex", "gap": "10px", "flexWrap": "wrap", "marginBottom": "10px"},
            ),
            html.Div(
                insight_msg,
                style={"background": "#111", "borderRadius": "4px",
                       "padding": "10px 14px", "color": "#888",
                       "fontSize": "0.78em", "border": "1px solid #222"},
            ),
            html.Div(
                "📐 Ключова думка: структура даних — це контракт виконання. "
                "Обираючи deque замість list, ви обираєте хто отримає право бути обслуженим першим.",
                style={"marginTop": "10px", "color": "#4ECDC4",
                       "fontSize": "0.82em", "fontStyle": "italic"},
            ),
        ],
    )
