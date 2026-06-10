"""
infrastructure/data_loader.py — Lazy DuckDB connection and sampling.

DuckDB is imported lazily inside functions to handle Windows DLL
Application Control blocks gracefully. Returns None on failure.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

DATA_URL = (
    "https://d37ci6vzurychx.cloudfront.net/trip-data/"
    "yellow_tripdata_2023-01.parquet"
)

_CREATE_VIEW_SQL = f"""
    CREATE OR REPLACE VIEW trips AS
    SELECT
        CAST(trip_distance AS DOUBLE)  AS trip_distance,
        CAST(PULocationID  AS INTEGER) AS PULocationID,
        CAST(DOLocationID  AS INTEGER) AS DOLocationID
    FROM read_parquet('{DATA_URL}')
    WHERE trip_distance > 0.1 AND trip_distance < 30.0
"""

_FAILED = object()          # sentinel: "tried and failed — don't retry"
_connection: Any = None    # None = not tried yet; _FAILED = failed; else = live connection


def get_connection() -> Optional[Any]:
    """
    Return a cached DuckDB connection, or None if unavailable.
    Failure is cached too — DLL errors are never retried.
    """
    global _connection
    if _connection is _FAILED:
        return None
    if _connection is not None:
        return _connection
    try:
        import duckdb
        con = duckdb.connect(":memory:")
        try:
            con.execute("INSTALL httpfs; LOAD httpfs;")
        except Exception:
            pass
        con.execute(_CREATE_VIEW_SQL)
        _connection = con
        logger.info("DuckDB connected — lazy VIEW registered.")
        return con
    except (ImportError, OSError, Exception) as exc:
        logger.warning("DuckDB unavailable: %s", exc)
        _connection = _FAILED
        return None


def sample_trips(n: int) -> Optional[list[dict]]:
    """
    Sample n trips from the remote parquet via DuckDB.
    Returns list of dicts or None if DuckDB is unavailable.
    """
    con = get_connection()
    if con is None:
        return None
    try:
        rows = con.execute(f"""
            SELECT trip_distance, PULocationID, DOLocationID
            FROM trips USING SAMPLE {n} ROWS
        """).fetchall()
        return [
            {"trip_distance": r[0], "PULocationID": r[1], "DOLocationID": r[2]}
            for r in rows
        ]
    except Exception as exc:
        logger.warning("DuckDB sample failed: %s", exc)
        return None


def get_dataset_stats() -> Optional[dict]:
    """Run SQL aggregation over the full VIEW — no full DataFrame in RAM."""
    con = get_connection()
    if con is None:
        return None
    try:
        row = con.execute("""
            SELECT
                COUNT(*)                     AS total_rows,
                ROUND(AVG(trip_distance), 2) AS avg_dist,
                ROUND(MAX(trip_distance), 1) AS max_dist,
                COUNT(DISTINCT PULocationID) AS unique_pu
            FROM trips
        """).fetchone()
        return {
            "total_rows": int(row[0]),
            "avg_dist":   float(row[1]),
            "max_dist":   float(row[2]),
            "unique_pu":  int(row[3]),
        }
    except Exception:
        return None
