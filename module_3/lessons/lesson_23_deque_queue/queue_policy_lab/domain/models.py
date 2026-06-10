"""
domain/models.py — Immutable domain model.

All types are plain dicts at runtime (JSON-serializable for dcc.Store).
TypedDicts are provided for static analysis only.
"""
from __future__ import annotations

from enum import Enum
from typing import TypedDict, Optional


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------

class Policy(str, Enum):
    FIFO     = "FIFO"
    LIFO     = "LIFO"
    RANDOM   = "RANDOM"
    PRIORITY = "PRIORITY"


POLICY_COLORS: dict[Policy, str] = {
    Policy.FIFO:     "#4ECDC4",
    Policy.LIFO:     "#FF6B6B",
    Policy.RANDOM:   "#FFB347",
    Policy.PRIORITY: "#9B59B6",
}

POLICY_LABELS: dict[Policy, str] = {
    Policy.FIFO:     "FIFO",
    Policy.LIFO:     "LIFO",
    Policy.RANDOM:   "RANDOM",
    Policy.PRIORITY: "PRIORITY",
}

POLICY_DS: dict[Policy, str] = {
    Policy.FIFO:     "collections.deque  →  popleft() O(1)",
    Policy.LIFO:     "list (stack)        →  pop()     O(1)",
    Policy.RANDOM:   "list (shuffle)      →  pop()     O(1)",
    Policy.PRIORITY: "heapq (min-heap)    →  heappop() O(log n)",
}

POLICY_BEHAVIOR: dict[Policy, str] = {
    Policy.FIFO:     "Справедливість — черга обслуговується в порядку надходження",
    Policy.LIFO:     "Переривання — найновіший запит завжди першим (старі голодують)",
    Policy.RANDOM:   "Хаос — випадковий вибір (нестабільний час відгуку)",
    Policy.PRIORITY: "Оптимізація — короткі поїздки першими (bias проти довгих)",
}


# ---------------------------------------------------------------------------
# TypedDicts (for IDE hints; runtime uses plain dicts)
# ---------------------------------------------------------------------------

class TripRecord(TypedDict):
    """One row from the trips dataset."""
    trip_id:  int
    distance: float
    pu_zone:  int
    do_zone:  int


class QueueItem(TypedDict):
    """Trip waiting in the queue."""
    trip_id:      int
    distance:     float
    arrival_tick: int
    pu_zone:      int
    do_zone:      int


class DriverState(TypedDict):
    """Single driver state."""
    driver_id:  int
    status:     str          # "idle" | "busy"
    trip_id:    Optional[int]
    distance:   Optional[float]
    start_tick: Optional[int]
    free_at:    Optional[int]


class CompletedRecord(TypedDict):
    """Completed trip record."""
    trip_id:         int
    distance:        float
    wait_ticks:      int
    arrival_tick:    int
    completion_tick: int


class TickMetrics(TypedDict):
    tick:          int
    queue_length:  int
    throughput:    int      # completed this tick
    avg_wait:      float
    starved_total: int
    fairness:      float
    active_drivers:int


class SimParams(TypedDict):
    arrival_rate:         float
    num_drivers:          int
    process_ticks_per_km: float
    max_wait_ticks:       int


class SimState(TypedDict):
    """Full serializable simulation state — stored in dcc.Store."""
    running:          bool
    tick:             int
    policy:           str               # Policy.value
    params:           SimParams
    trips:            list[TripRecord]
    arrival_schedule: dict[str, list[int]]  # str(tick) -> [trip_idx]
    queue:            list[QueueItem]
    drivers:          list[DriverState]
    completed:        list[CompletedRecord]
    recent_arrivals:  list[QueueItem]   # feed for "incoming" panel
    metrics_history:  list[TickMetrics]
    total_starved:    int
    total_completed:  int
    all_waits:        list[float]
