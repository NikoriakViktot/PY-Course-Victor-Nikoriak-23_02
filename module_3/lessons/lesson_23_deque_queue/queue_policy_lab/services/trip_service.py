"""
services/trip_service.py — Facade for trip data loading.

Tries DuckDB → synthetic fallback. Returns clean list[dict] format
ready for dispatcher_engine.init_state().
"""
from __future__ import annotations

from infrastructure import data_loader, synthetic_data


def load_trips(n: int, seed: int = 42) -> tuple[list[dict], bool]:
    """
    Load n trip records.

    Returns (trips, is_real) where:
      trips   — list of {trip_id, distance, pu_zone, do_zone}
      is_real — True if from DuckDB, False if synthetic
    """
    raw = data_loader.sample_trips(n)
    if raw:
        trips = [
            {
                "trip_id":  i,
                "distance": row["trip_distance"],
                "pu_zone":  row["PULocationID"],
                "do_zone":  row["DOLocationID"],
            }
            for i, row in enumerate(raw)
        ]
        return trips, True

    return synthetic_data.make_trips(n, seed=seed), False


def get_stats() -> dict | None:
    """Return dataset-level stats from DuckDB, or None if unavailable."""
    return data_loader.get_dataset_stats()
