"""
infrastructure/synthetic_data.py — NYC TLC-like synthetic trip generator.

Used as fallback when DuckDB / remote parquet is unavailable.
Distance distribution matches real NYC TLC 2023-01 statistics.
"""
from __future__ import annotations

import random
from typing import Optional


def make_trips(n: int, seed: int = 42) -> list[dict]:
    """
    Generate n synthetic taxi trips with realistic NYC-like statistics.

    Distance: log-normal(μ=1.0, σ=0.7) clipped to [0.1, 30.0] km
    Zones:    uniform over 265 NYC taxi zones
    """
    rng = random.Random(seed)
    trips = []
    for i in range(n):
        # Log-normal: most trips 0.5–8 km, tail to 30 km
        u1 = rng.gauss(0, 1)
        u2 = rng.gauss(0, 1)
        raw = 1.0 + 0.7 * u1
        dist = round(min(30.0, max(0.1, pow(2.718281828, raw))), 2)
        trips.append({
            "trip_id":  i,
            "distance": dist,
            "pu_zone":  rng.randint(1, 265),
            "do_zone":  rng.randint(1, 265),
        })
    return trips
