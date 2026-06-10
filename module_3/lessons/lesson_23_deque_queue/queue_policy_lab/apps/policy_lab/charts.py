"""
apps/policy_lab/charts.py — Chart builders for batch policy comparison.
"""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from domain.models import POLICY_COLORS, POLICY_LABELS, Policy

_LAYOUT = dict(
    plot_bgcolor="#111",
    paper_bgcolor="#161616",
    font=dict(color="#aaa", size=11),
    margin=dict(l=50, r=20, t=40, b=40),
    height=300,
    legend=dict(orientation="h", y=1.12, bgcolor="rgba(0,0,0,0)"),
)


def _color(p: str) -> str:
    return POLICY_COLORS.get(Policy(p), "#888")


def queue_length_chart(results: dict[str, dict]) -> go.Figure:
    """Overlay queue length time series for all policies."""
    fig = go.Figure()
    for policy, data in results.items():
        series = data.get("series", {})
        ticks = series.get("ticks", [])
        queue = series.get("queue", [])
        if not ticks:
            continue
        # Smooth with rolling mean (window=10)
        smoothed = _rolling_mean(queue, 10)
        fig.add_trace(go.Scatter(
            x=ticks, y=smoothed,
            name=policy,
            line=dict(color=_color(policy), width=2),
            hovertemplate="Тік %{x}<br>Черга: %{y:.0f}<extra>" + policy + "</extra>",
        ))
    fig.update_layout(
        title="Довжина черги в часі",
        xaxis=dict(title="Тік", gridcolor="#222"),
        yaxis=dict(title="Поїздок у черзі", gridcolor="#222"),
        **_LAYOUT,
    )
    return fig


def wait_histogram(results: dict[str, dict]) -> go.Figure:
    """Overlapping histogram of wait time distributions."""
    fig = go.Figure()
    for policy, data in results.items():
        waits = data.get("all_waits", [])
        if not waits:
            continue
        fig.add_trace(go.Histogram(
            x=waits, name=policy,
            marker_color=_color(policy),
            opacity=0.65, nbinsx=40,
            hovertemplate="Очікування: %{x}<br>Кількість: %{y}<extra>" + policy + "</extra>",
        ))
    fig.update_layout(
        barmode="overlay",
        title="Розподіл часу очікування",
        xaxis=dict(title="Тіки очікування", gridcolor="#222"),
        yaxis=dict(title="Кількість поїздок", gridcolor="#222"),
        **_LAYOUT,
    )
    return fig


def fairness_bar(results: dict[str, dict]) -> go.Figure:
    policies   = list(results.keys())
    fairnesses = [results[p]["summary"].get("fairness", 0) for p in policies]
    colors     = [_color(p) for p in policies]

    fig = go.Figure(go.Bar(
        x=policies, y=fairnesses,
        marker_color=colors,
        text=[f"{v:.3f}" for v in fairnesses],
        textposition="outside",
    ))
    fig.add_hline(y=1.0, line_dash="dash", line_color="#444",
                  annotation_text="Ідеальна рівність", annotation_position="right")
    fig.update_layout(
        title="Jain's Fairness Index (вищий = справедливіший)",
        yaxis=dict(range=[0, 1.15], title="Fairness", gridcolor="#222"),
        xaxis=dict(gridcolor="#222"),
        **_LAYOUT,
    )
    return fig


def throughput_chart(results: dict[str, dict]) -> go.Figure:
    fig = go.Figure()
    for policy, data in results.items():
        series = data.get("series", {})
        ticks = series.get("ticks", [])
        raw   = series.get("throughput", [])
        if not ticks:
            continue
        smoothed = _rolling_mean(raw, 20)
        fig.add_trace(go.Scatter(
            x=ticks, y=smoothed,
            name=policy,
            line=dict(color=_color(policy), width=2),
            hovertemplate="Тік %{x}<br>Throughput: %{y:.2f}<extra>" + policy + "</extra>",
        ))
    fig.update_layout(
        title="Пропускна здатність (ковзне 20-тіків)",
        xaxis=dict(title="Тік", gridcolor="#222"),
        yaxis=dict(title="Поїздок / тік", gridcolor="#222"),
        **_LAYOUT,
    )
    return fig


def starvation_bar(results: dict[str, dict]) -> go.Figure:
    policies = list(results.keys())
    starved  = [results[p]["summary"].get("starved", 0) for p in policies]
    colors   = ["#FF6B6B" if s > 0 else "#4ECDC4" for s in starved]

    fig = go.Figure(go.Bar(
        x=policies, y=starved,
        marker_color=colors,
        text=[str(s) for s in starved],
        textposition="outside",
    ))
    fig.update_layout(
        title="Кількість відкинутих поїздок (голодування)",
        yaxis=dict(title="Відкинуто", gridcolor="#222"),
        xaxis=dict(gridcolor="#222"),
        **_LAYOUT,
    )
    return fig


def priority_bias_scatter(priority_data: dict, fifo_data: dict) -> go.Figure:
    """Scatter: distance vs wait for PRIORITY vs FIFO."""
    fig = go.Figure()
    for policy, data, col in [
        ("PRIORITY", priority_data, _color("PRIORITY")),
        ("FIFO",     fifo_data,     _color("FIFO")),
    ]:
        waits     = data.get("all_waits", [])
        completed = data.get("completed_records", [])
        if not completed:
            continue
        import random
        sample = completed if len(completed) <= 400 else random.sample(completed, 400)
        fig.add_trace(go.Scatter(
            x=[r["distance"] for r in sample],
            y=[r["wait_ticks"] for r in sample],
            mode="markers",
            marker=dict(color=col, opacity=0.4, size=4),
            name=policy,
            hovertemplate="dist: %{x:.1f} km<br>wait: %{y} ticks<extra>" + policy + "</extra>",
        ))
    fig.update_layout(
        title="PRIORITY bias: дистанція vs очікування (PRIORITY відкидає довгі поїздки)",
        xaxis=dict(title="Дистанція (км)", gridcolor="#222"),
        yaxis=dict(title="Очікування (ticks)", gridcolor="#222"),
        **_LAYOUT,
    )
    return fig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rolling_mean(data: list[float], window: int) -> list[float]:
    result = []
    for i, v in enumerate(data):
        start = max(0, i - window + 1)
        result.append(sum(data[start:i+1]) / (i - start + 1))
    return result
