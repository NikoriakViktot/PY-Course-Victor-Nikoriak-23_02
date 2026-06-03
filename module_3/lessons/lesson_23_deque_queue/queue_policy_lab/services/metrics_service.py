"""
services/metrics_service.py — Compute summary metrics from SimState.

All functions accept the serialized state dict and return plain values.
"""
from __future__ import annotations

import statistics
from typing import Any


def live_kpis(state: dict) -> dict:
    """Return current KPI values for the live metrics panel."""
    all_waits = state.get("all_waits", [])
    history   = state.get("metrics_history", [])

    avg_wait = round(sum(all_waits) / max(1, len(all_waits)), 1)
    fairness = _jains(all_waits)

    # Throughput: avg completed per tick over last 20 ticks
    recent = history[-20:]
    throughput = round(sum(r["throughput"] for r in recent) / max(1, len(recent)), 2)

    return {
        "tick":            state.get("tick", 0),
        "queue_length":    len(state.get("queue", [])),
        "total_completed": state.get("total_completed", 0),
        "total_starved":   state.get("total_starved", 0),
        "avg_wait":        avg_wait,
        "fairness":        round(fairness, 3),
        "throughput":      throughput,
        "active_drivers":  sum(1 for d in state.get("drivers", []) if d["status"] == "busy"),
    }


def batch_summary(state: dict) -> dict:
    """Full summary for Policy Lab batch comparison."""
    all_waits = state.get("all_waits", [])
    history   = state.get("metrics_history", [])
    n = len(all_waits)

    if n == 0:
        return {"policy": state.get("policy"), "completed": 0}

    total_ticks = state.get("tick", 1)
    max_q = max((r["queue_length"] for r in history), default=0)
    avg_q = round(sum(r["queue_length"] for r in history) / max(1, len(history)), 1)

    return {
        "policy":        state.get("policy"),
        "completed":     n,
        "starved":       state.get("total_starved", 0),
        "avg_wait":      round(sum(all_waits) / n, 1),
        "median_wait":   round(sorted(all_waits)[n // 2], 1),
        "p95_wait":      round(sorted(all_waits)[int(n * 0.95)], 1),
        "max_wait":      int(max(all_waits)),
        "fairness":      round(_jains(all_waits), 3),
        "throughput":    round(n / max(1, total_ticks), 3),
        "max_queue":     max_q,
        "avg_queue":     avg_q,
    }


def chart_series(state: dict) -> dict:
    """Extract chart-ready series from metrics_history."""
    h = state.get("metrics_history", [])
    if not h:
        return {"ticks": [], "queue": [], "throughput": [], "wait": [], "starved": []}
    return {
        "ticks":      [r["tick"] for r in h],
        "queue":      [r["queue_length"] for r in h],
        "throughput": [r["throughput"] for r in h],
        "wait":       [r["avg_wait"] for r in h],
        "starved":    [r["starved_total"] for r in h],
        "fairness":   [r["fairness"] for r in h],
    }


def _jains(waits: list[float]) -> float:
    n = len(waits)
    if n == 0:
        return 1.0
    s1 = sum(waits)
    s2 = sum(x * x for x in waits)
    return (s1 * s1) / (n * s2) if s2 > 0 else 1.0
