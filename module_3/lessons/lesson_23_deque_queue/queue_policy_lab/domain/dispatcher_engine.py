"""
domain/dispatcher_engine.py — Tick-based state machine for taxi dispatch.

All functions are PURE: they receive a state dict and return a NEW state dict.
No mutation. No global state. Dash-Store-safe.

Step pipeline for each tick (called by advance_one_tick):
  1. release_completed  — free drivers whose trips ended
  2. enqueue_arrivals   — push new trips into the buffer
  3. drop_starved       — remove trips waiting too long
  4. assign_drivers     — match free drivers to queue via policy
  5. record_metrics     — append TickMetrics snapshot

Educational note:
  The only difference between FIFO / LIFO / RANDOM / PRIORITY is in step 4
  (assign_drivers → policies.dequeue). Everything else is identical.
  This makes the data-structure → behavior link explicit and measurable.
"""
from __future__ import annotations

import copy
import math
import random as _rand
from typing import Any

from domain import policies as pol
from domain.models import Policy


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

METRICS_HISTORY_LIMIT = 600   # keep last N ticks in metrics_history
COMPLETED_DISPLAY_LIMIT = 60  # keep last N in completed list (UI)
RECENT_ARRIVALS_LIMIT = 10    # incoming feed size


# ---------------------------------------------------------------------------
# State initialiser
# ---------------------------------------------------------------------------

def init_state(
    trips: list[dict],
    policy: str,
    arrival_rate: float,
    num_drivers: int,
    process_ticks_per_km: float,
    max_wait_ticks: int = 120,
    seed: int = 42,
) -> dict:
    """
    Build a fresh, fully initialised simulation state dict.
    Returns a JSON-serializable dict — safe to store in dcc.Store.
    """
    schedule = _build_arrival_schedule(trips, arrival_rate, seed)
    drivers = [
        {
            "driver_id":  i,
            "status":     "idle",
            "trip_id":    None,
            "distance":   None,
            "start_tick": None,
            "free_at":    None,
        }
        for i in range(num_drivers)
    ]
    return {
        "running":          False,
        "tick":             0,
        "policy":           policy,
        "params": {
            "arrival_rate":         arrival_rate,
            "num_drivers":          num_drivers,
            "process_ticks_per_km": process_ticks_per_km,
            "max_wait_ticks":       max_wait_ticks,
        },
        "trips":            trips,
        "arrival_schedule": schedule,
        "queue":            [],
        "drivers":          drivers,
        "completed":        [],
        "recent_arrivals":  [],
        "metrics_history":  [],
        "total_starved":    0,
        "total_completed":  0,
        "all_waits":        [],
    }


# ---------------------------------------------------------------------------
# Step 1 — Release completed drivers
# ---------------------------------------------------------------------------

def release_completed(state: dict) -> dict:
    """
    Free any driver whose trip has finished (free_at <= current tick).
    Returns new state with updated drivers list.
    """
    t = state["tick"]
    drivers = []
    for d in state["drivers"]:
        if d["status"] == "busy" and d["free_at"] is not None and d["free_at"] <= t:
            drivers.append({
                **d,
                "status":     "idle",
                "trip_id":    None,
                "distance":   None,
                "start_tick": None,
                "free_at":    None,
            })
        else:
            drivers.append(d)
    return {**state, "drivers": drivers}


# ---------------------------------------------------------------------------
# Step 2 — Enqueue arrivals
# ---------------------------------------------------------------------------

def enqueue_arrivals(state: dict) -> dict:
    """
    Pull trips scheduled for the current tick and push them into the queue.
    Updates recent_arrivals feed for the Incoming Calls panel.
    """
    t = state["tick"]
    arrivals_indices: list[int] = state["arrival_schedule"].get(str(t), [])

    if not arrivals_indices:
        return state

    queue = list(state["queue"])
    new_arrivals: list[dict] = []

    for idx in arrivals_indices:
        trip = state["trips"][idx]
        item: dict = {
            "trip_id":      trip["trip_id"],
            "distance":     trip["distance"],
            "arrival_tick": t,
            "pu_zone":      trip["pu_zone"],
            "do_zone":      trip["do_zone"],
        }
        pol.enqueue(queue, item, state["policy"])
        new_arrivals.append(item)

    recent = (new_arrivals + state["recent_arrivals"])[:RECENT_ARRIVALS_LIMIT]
    return {**state, "queue": queue, "recent_arrivals": recent}


# ---------------------------------------------------------------------------
# Step 3 — Drop starved trips
# ---------------------------------------------------------------------------

def drop_starved(state: dict) -> dict:
    """
    Remove trips that have waited longer than max_wait_ticks.
    Records the count in total_starved.

    Educational note:
      In LIFO mode, the BOTTOM of the list (oldest items) is never served —
      they silently accumulate here until they exceed max_wait and are dropped.
      This is *starvation* made explicit and measurable.
    """
    t = state["tick"]
    max_wait: int = state["params"]["max_wait_ticks"]
    dropped = 0
    surviving = []
    for item in state["queue"]:
        if (t - item["arrival_tick"]) > max_wait:
            dropped += 1
        else:
            surviving.append(item)
    if dropped == 0:
        return state
    return {**state, "queue": surviving, "total_starved": state["total_starved"] + dropped}


# ---------------------------------------------------------------------------
# Step 4 — Assign drivers
# ---------------------------------------------------------------------------

def assign_drivers(state: dict) -> dict:
    """
    Match idle drivers to queued trips using the selected policy.

    This is the ONLY step where policy matters.
    The single call to pol.dequeue() is what makes FIFO/LIFO/RANDOM/PRIORITY
    produce completely different system behavior.
    """
    t = state["tick"]
    speed = state["params"]["process_ticks_per_km"]
    policy = state["policy"]

    queue = list(state["queue"])
    drivers = list(state["drivers"])
    completed = list(state["completed"])
    all_waits = list(state["all_waits"])
    total_completed = state["total_completed"]

    for i, driver in enumerate(drivers):
        if driver["status"] != "idle" or not queue:
            continue

        trip = pol.dequeue(queue, policy)   # ← THE policy decision point
        if trip is None:
            break

        duration = max(1, round(trip["distance"] * speed))
        drivers[i] = {
            **driver,
            "status":     "busy",
            "trip_id":    trip["trip_id"],
            "distance":   trip["distance"],
            "start_tick": t,
            "free_at":    t + duration,
        }

        wait = t - trip["arrival_tick"]
        completed.append({
            "trip_id":         trip["trip_id"],
            "distance":        trip["distance"],
            "wait_ticks":      wait,
            "arrival_tick":    trip["arrival_tick"],
            "completion_tick": t,
        })
        all_waits.append(float(wait))
        total_completed += 1

    completed = completed[-COMPLETED_DISPLAY_LIMIT:]

    return {
        **state,
        "queue":           queue,
        "drivers":         drivers,
        "completed":       completed,
        "all_waits":       all_waits,
        "total_completed": total_completed,
    }


# ---------------------------------------------------------------------------
# Step 5 — Record metrics
# ---------------------------------------------------------------------------

def record_metrics(state: dict) -> dict:
    """
    Append a TickMetrics snapshot to metrics_history.
    Computes Jain's Fairness Index from all_waits.
    """
    t = state["tick"]
    all_waits = state["all_waits"]
    completed_this_tick = sum(
        1 for c in state["completed"] if c["completion_tick"] == t
    )

    avg_wait = (sum(all_waits) / len(all_waits)) if all_waits else 0.0
    fairness = _jains_fairness(all_waits)
    active_drivers = sum(1 for d in state["drivers"] if d["status"] == "busy")

    snap = {
        "tick":           t,
        "queue_length":   len(state["queue"]),
        "throughput":     completed_this_tick,
        "avg_wait":       round(avg_wait, 1),
        "starved_total":  state["total_starved"],
        "fairness":       round(fairness, 3),
        "active_drivers": active_drivers,
    }
    history = (state["metrics_history"] + [snap])[-METRICS_HISTORY_LIMIT:]
    return {**state, "metrics_history": history}


# ---------------------------------------------------------------------------
# Master step — advance_one_tick
# ---------------------------------------------------------------------------

def advance_one_tick(state: dict) -> dict:
    """
    Advance the simulation by exactly one tick.
    Composes all 5 steps in order. Returns a new state dict.

    This is the function called by the Dash interval callback:
        new_state = advance_one_tick(current_state)

    Each step is independently testable and inspectable.
    """
    state = {**state, "tick": state["tick"] + 1}
    state = release_completed(state)
    state = enqueue_arrivals(state)
    state = drop_starved(state)
    state = assign_drivers(state)
    state = record_metrics(state)
    return state


def inject_burst(state: dict, n: int = 8) -> dict:
    """
    Manually inject n synthetic trips into the queue.
    Used by the 'Burst' button in the live dispatcher UI.
    """
    t = state["tick"]
    queue = list(state["queue"])
    policy = state["policy"]

    for i in range(n):
        distance = round(_rand.uniform(0.5, 15.0), 1)
        item = {
            "trip_id":      -(i + 1 + t * 100),   # negative IDs = synthetic burst
            "distance":     distance,
            "arrival_tick": t,
            "pu_zone":      _rand.randint(1, 265),
            "do_zone":      _rand.randint(1, 265),
        }
        pol.enqueue(queue, item, policy)

    return {**state, "queue": queue}


# ---------------------------------------------------------------------------
# Batch runner (for Policy Lab — runs to completion)
# ---------------------------------------------------------------------------

def run_to_completion(state: dict) -> dict:
    """
    Run simulation until all scheduled trips are processed.
    Used by Policy Lab for batch comparison (not live dispatcher).
    """
    last_tick = max((int(k) for k in state["arrival_schedule"]), default=0)
    drain_limit = last_tick + state["params"]["max_wait_ticks"]

    while True:
        state = advance_one_tick(state)
        if state["tick"] > drain_limit:
            break
        if state["tick"] > last_tick and len(state["queue"]) == 0:
            break

    return state


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _build_arrival_schedule(
    trips: list[dict],
    arrival_rate: float,
    seed: int,
) -> dict[str, list[int]]:
    """
    Assign each trip to an arrival tick using a Poisson process.
    Returns {str(tick): [trip_index, ...]} — string keys for JSON compatibility.
    """
    rng = _rand.Random(seed)
    schedule: dict[str, list[int]] = {}
    tick = 0
    for idx, _ in enumerate(trips):
        gap = max(1, round(rng.expovariate(arrival_rate)))
        tick += gap
        key = str(tick)
        schedule.setdefault(key, []).append(idx)
    return schedule


def _jains_fairness(waits: list[float]) -> float:
    """
    Jain's Fairness Index: F = (Σxᵢ)² / (n · Σxᵢ²)
    Range [0, 1]. 1.0 = perfect equality, 0.0 = extreme inequality.
    """
    n = len(waits)
    if n == 0:
        return 1.0
    s1 = sum(waits)
    s2 = sum(x * x for x in waits)
    return (s1 * s1) / (n * s2) if s2 > 0 else 1.0
