"""
simulation.py — Tick-based Queue Policy Simulation Engine.

Architecture
------------
  TripRequest  ← immutable data record per incoming taxi trip
  PolicyEngine ← single-policy simulator (FIFO/LIFO/RANDOM/PRIORITY)
  run_all_policies() ← runs all 4 policies on identical input, returns dict

Key design principle:
  Each policy uses a DIFFERENT data structure:
    FIFO     → collections.deque   (popleft O(1))
    LIFO     → list                (pop      O(1))
    RANDOM   → list                (random swap + pop O(1))
    PRIORITY → heapq               (heappop O(log n))

This makes the data structure choice visible and measurable.
"""
from __future__ import annotations

import heapq
import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Policy definitions
# ---------------------------------------------------------------------------

class Policy(str, Enum):
    FIFO     = "FIFO"
    LIFO     = "LIFO"
    RANDOM   = "RANDOM"
    PRIORITY = "PRIORITY"


POLICY_COLORS = {
    Policy.FIFO:     "#4ECDC4",
    Policy.LIFO:     "#FF6B6B",
    Policy.RANDOM:   "#FFB347",
    Policy.PRIORITY: "#9B59B6",
}

POLICY_LABELS = {
    Policy.FIFO:     "🟢 FIFO (deque)",
    Policy.LIFO:     "🔴 LIFO (list)",
    Policy.RANDOM:   "🟡 RANDOM (list)",
    Policy.PRIORITY: "🟣 PRIORITY (heapq)",
}

POLICY_DESCRIPTIONS = {
    Policy.FIFO:     "Справедливість: обслуговуємо в порядку надходження",
    Policy.LIFO:     "Переривання: найновіший запит обслуговується першим",
    Policy.RANDOM:   "Хаос: випадковий вибір — ніхто не захищений",
    Policy.PRIORITY: "Оптимізація: найкоротші поїздки першими (ризик голодування)",
}


# ---------------------------------------------------------------------------
# Data records
# ---------------------------------------------------------------------------

@dataclass(order=True)
class TripRequest:
    """Immutable record for one incoming taxi trip."""
    priority:     float = field(compare=True)   # heapq key (lower = served first)
    arrival_tick: int   = field(compare=False)
    trip_id:      int   = field(compare=False)
    distance:     float = field(compare=False)
    pu_zone:      int   = field(compare=False)
    do_zone:      int   = field(compare=False)


@dataclass
class CompletedTrip:
    trip_id:         int
    distance:        float
    arrival_tick:    int
    completion_tick: int

    @property
    def wait_ticks(self) -> int:
        return self.completion_tick - self.arrival_tick


@dataclass
class TickSnapshot:
    tick:            int
    queue_length:    int
    completed:       int
    arrivals:        int
    starved_total:   int   # Cumulative trips dropped due to starvation
    active_drivers:  int


# ---------------------------------------------------------------------------
# Simulation engine
# ---------------------------------------------------------------------------

class PolicyEngine:
    """
    Tick-based dispatcher simulation for a single execution policy.

    Each tick:
      1. Free drivers whose trips have completed.
      2. Admit new trip arrivals (Poisson process).
      3. Drop trips that have waited longer than MAX_WAIT_TICKS (starvation).
      4. Assign free drivers to waiting trips via the chosen policy.
      5. Record a TickSnapshot.
    """

    MAX_WAIT_TICKS: int = 150

    def __init__(
        self,
        policy:               Policy,
        trips_df:             pd.DataFrame,
        arrival_rate:         float,   # avg trips per tick (Poisson lambda)
        num_drivers:          int,
        process_ticks_per_km: float,   # ticks to complete 1 km
        seed:                 int = 42,
    ) -> None:
        self.policy               = policy
        self.trips_df             = trips_df.reset_index(drop=True)
        self.arrival_rate         = arrival_rate
        self.num_drivers          = num_drivers
        self.process_ticks_per_km = process_ticks_per_km
        self._rng                 = random.Random(seed)

        # Internal queue structures — one per policy
        self._fifo_queue:  deque[TripRequest] = deque()
        self._stack:       list[TripRequest]  = []   # LIFO & RANDOM share list
        self._heap:        list[TripRequest]  = []   # PRIORITY

        # Driver state: list of ticks when each busy driver becomes free
        self._driver_free_at: list[int] = []

        # Results
        self.snapshots:        list[TickSnapshot]  = []
        self.completed_trips:  list[CompletedTrip] = []
        self._starved_count:   int = 0
        self._current_tick:    int = 0

        # Pre-compute Poisson arrival schedule once (reproducible)
        self._arrival_schedule: dict[int, list[int]] = self._build_schedule()

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------

    def _build_schedule(self) -> dict[int, list[int]]:
        """
        Assign each trip in trips_df to an arrival tick using a Poisson process.
        Inter-arrival time ~ Exponential(1/arrival_rate).
        Returns {tick: [trip_index, ...], ...}
        """
        schedule: dict[int, list[int]] = {}
        tick = 0
        n = len(self.trips_df)
        for idx in range(n):
            # Draw inter-arrival gap: Exponential(lambda=arrival_rate)
            gap = max(1, round(self._rng.expovariate(self.arrival_rate)))
            tick += gap
            schedule.setdefault(tick, []).append(idx)
        return schedule

    # ------------------------------------------------------------------
    # Queue operations — data structure dispatching
    # ------------------------------------------------------------------

    def _enqueue(self, trip: TripRequest) -> None:
        if self.policy == Policy.FIFO:
            self._fifo_queue.append(trip)       # deque.append  O(1)
        elif self.policy == Policy.LIFO:
            self._stack.append(trip)            # list.append   O(1)
        elif self.policy == Policy.RANDOM:
            self._stack.append(trip)            # list.append   O(1)
        else:  # PRIORITY
            heapq.heappush(self._heap, trip)    # heapq push    O(log n)

    def _dequeue(self) -> Optional[TripRequest]:
        if self.policy == Policy.FIFO:
            return self._fifo_queue.popleft() if self._fifo_queue else None  # O(1)
        elif self.policy == Policy.LIFO:
            return self._stack.pop() if self._stack else None                # O(1)
        elif self.policy == Policy.RANDOM:
            if not self._stack:
                return None
            # Swap random element to end, pop: O(1) amortized
            i = self._rng.randint(0, len(self._stack) - 1)
            self._stack[i], self._stack[-1] = self._stack[-1], self._stack[i]
            return self._stack.pop()
        else:  # PRIORITY
            return heapq.heappop(self._heap) if self._heap else None         # O(log n)

    def _queue_length(self) -> int:
        if self.policy == Policy.FIFO:
            return len(self._fifo_queue)
        elif self.policy == Policy.PRIORITY:
            return len(self._heap)
        else:
            return len(self._stack)

    def _drop_starved(self) -> int:
        """Remove trips from FIFO queue that have waited too long."""
        if self.policy != Policy.FIFO:
            return 0
        dropped = 0
        while (
            self._fifo_queue
            and (self._current_tick - self._fifo_queue[0].arrival_tick) > self.MAX_WAIT_TICKS
        ):
            self._fifo_queue.popleft()
            dropped += 1
        return dropped

    # ------------------------------------------------------------------
    # Core tick
    # ------------------------------------------------------------------

    def tick(self) -> bool:
        """
        Advance simulation by one tick.
        Returns True while simulation should continue.
        """
        self._current_tick += 1
        t = self._current_tick

        # 1. Release drivers whose trips completed this tick
        self._driver_free_at = [ft for ft in self._driver_free_at if ft > t]
        free_drivers = self.num_drivers - len(self._driver_free_at)

        # 2. Admit arrivals
        arrivals = self._arrival_schedule.get(t, [])
        for idx in arrivals:
            row = self.trips_df.iloc[idx]
            trip = TripRequest(
                priority     = float(row["trip_distance"]),  # short trip = low priority value
                arrival_tick = t,
                trip_id      = int(idx),
                distance     = float(row["trip_distance"]),
                pu_zone      = int(row["PULocationID"]),
                do_zone      = int(row["DOLocationID"]),
            )
            self._enqueue(trip)

        # 3. Starvation: drop long-waiting trips from FIFO front
        self._starved_count += self._drop_starved()

        # 4. Dispatch free drivers
        completed_this_tick = 0
        while free_drivers > 0 and self._queue_length() > 0:
            trip = self._dequeue()
            if trip is None:
                break
            duration = max(1, round(trip.distance * self.process_ticks_per_km))
            self._driver_free_at.append(t + duration)
            self.completed_trips.append(CompletedTrip(
                trip_id         = trip.trip_id,
                distance        = trip.distance,
                arrival_tick    = trip.arrival_tick,
                completion_tick = t,
            ))
            completed_this_tick += 1
            free_drivers -= 1

        # 5. Record snapshot
        self.snapshots.append(TickSnapshot(
            tick           = t,
            queue_length   = self._queue_length(),
            completed      = completed_this_tick,
            arrivals       = len(arrivals),
            starved_total  = self._starved_count,
            active_drivers = self.num_drivers - free_drivers,
        ))

        # Stop when all scheduled arrivals have passed and queue is drained
        last_arrival_tick = max(self._arrival_schedule.keys(), default=0)
        return t < last_arrival_tick + self.MAX_WAIT_TICKS and (
            t <= last_arrival_tick or self._queue_length() > 0
        )

    def run(self) -> PolicyEngine:
        """Run to completion. Returns self for chaining."""
        while self.tick():
            pass
        return self

    # ------------------------------------------------------------------
    # Result accessors
    # ------------------------------------------------------------------

    def snapshots_df(self) -> pd.DataFrame:
        return pd.DataFrame([
            {
                "tick":          s.tick,
                "queue_length":  s.queue_length,
                "completed":     s.completed,
                "arrivals":      s.arrivals,
                "starved_total": s.starved_total,
                "active_drivers":s.active_drivers,
            }
            for s in self.snapshots
        ])

    def completed_df(self) -> pd.DataFrame:
        if not self.completed_trips:
            return pd.DataFrame(columns=["trip_id", "distance", "wait_ticks",
                                          "arrival_tick", "completion_tick"])
        return pd.DataFrame([
            {
                "trip_id":         c.trip_id,
                "distance":        c.distance,
                "wait_ticks":      c.wait_ticks,
                "arrival_tick":    c.arrival_tick,
                "completion_tick": c.completion_tick,
            }
            for c in self.completed_trips
        ])

    def summary(self) -> dict:
        """Aggregate metrics for comparison table."""
        cdf = self.completed_df()
        sdf = self.snapshots_df()

        if cdf.empty:
            return {"policy": self.policy.value}

        wait = cdf["wait_ticks"]
        total_ticks = int(sdf["tick"].max()) if not sdf.empty else 1
        max_q = int(sdf["queue_length"].max()) if not sdf.empty else 0
        avg_q = round(float(sdf["queue_length"].mean()), 1) if not sdf.empty else 0.0

        # Fairness index: Jain's fairness = (Σwᵢ)² / (n · Σwᵢ²), range [0,1]
        n = len(wait)
        sum_w  = float(wait.sum())
        sum_w2 = float((wait ** 2).sum())
        jains  = (sum_w ** 2) / (n * sum_w2) if sum_w2 > 0 else 1.0

        return {
            "policy":           self.policy.value,
            "completed":        n,
            "starved":          self._starved_count,
            "avg_wait":         round(float(wait.mean()), 1),
            "median_wait":      round(float(wait.median()), 1),
            "p95_wait":         round(float(wait.quantile(0.95)), 1),
            "max_wait":         int(wait.max()),
            "fairness":         round(jains, 3),
            "throughput_tpt":   round(n / total_ticks, 3),
            "max_queue":        max_q,
            "avg_queue":        avg_q,
        }


# ---------------------------------------------------------------------------
# Multi-policy runner
# ---------------------------------------------------------------------------

def run_all_policies(
    trips_df:             pd.DataFrame,
    arrival_rate:         float,
    num_drivers:          int,
    process_ticks_per_km: float,
    seed:                 int = 42,
) -> dict[Policy, PolicyEngine]:
    """
    Run all 4 policies on the SAME input dataset.
    Returns dict of completed PolicyEngine instances.
    """
    return {
        policy: PolicyEngine(
            policy               = policy,
            trips_df             = trips_df,
            arrival_rate         = arrival_rate,
            num_drivers          = num_drivers,
            process_ticks_per_km = process_ticks_per_km,
            seed                 = seed,
        ).run()
        for policy in Policy
    }
