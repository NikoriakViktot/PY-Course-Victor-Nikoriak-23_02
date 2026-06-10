"""
data_loader.py — Lazy DuckDB data layer for Queue Policy Lab.

Architecture
------------
  DuckDB VIEW (lazy)  ← full 3M-row parquet, never in RAM
       ↓  SQL SAMPLE  (n rows reservoir sampling)
  pandas DataFrame    ← only n rows, fits in memory
       ↓  Simulation engine
  Policy results      ← FIFO / LIFO / RANDOM / PRIORITY comparison

Reuses the same NYC TLC 2023-01 dataset as lesson_22 Big-O Lab.

DuckDB is imported lazily inside functions — if blocked by OS DLL policy
(Windows AppControl), all functions fall back to synthetic data gracefully.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

DATA_URL = (
    "https://d37ci6vzurychx.cloudfront.net/trip-data/"
    "yellow_tripdata_2023-01.parquet"
)

_CREATE_VIEW_SQL = f"""
    CREATE OR REPLACE VIEW trips AS
    SELECT
        CAST(trip_distance  AS DOUBLE)  AS trip_distance,
        CAST(PULocationID   AS INTEGER) AS PULocationID,
        CAST(DOLocationID   AS INTEGER) AS DOLocationID
    FROM read_parquet('{DATA_URL}')
    WHERE
        trip_distance > 0.1
        AND trip_distance < 30.0
"""


def _import_duckdb() -> Any:
    """Import duckdb lazily — raises ImportError if unavailable."""
    import duckdb  # noqa: PLC0415
    return duckdb


@st.cache_resource(show_spinner=False)
def get_duckdb_connection() -> Optional[Any]:
    """
    Create a persistent DuckDB connection with a lazy VIEW.
    Returns None if duckdb is unavailable (DLL blocked / not installed).
    @st.cache_resource keeps the connection alive between Streamlit reruns.
    """
    try:
        duckdb = _import_duckdb()
    except (ImportError, OSError) as exc:
        logger.warning("DuckDB unavailable: %s — switching to synthetic mode.", exc)
        return None

    con = duckdb.connect(database=":memory:")
    try:
        con.execute("INSTALL httpfs; LOAD httpfs;")
    except Exception as exc:
        logger.debug("httpfs already present or unavailable: %s", exc)
    try:
        con.execute(_CREATE_VIEW_SQL)
    except Exception as exc:
        logger.warning("Could not create VIEW: %s", exc)
        return None
    return con


def sample_trips(con: Any, n: int) -> pd.DataFrame:
    """
    Pull exactly n rows via DuckDB reservoir sampling.
    Returns DataFrame with: trip_distance, PULocationID, DOLocationID.
    Never loads more than n rows into Python RAM.
    """
    df = con.execute(f"""
        SELECT
            trip_distance,
            PULocationID,
            DOLocationID
        FROM trips
        USING SAMPLE {n} ROWS
    """).df()
    return df.reset_index(drop=True)


def make_synthetic_trips(n: int, seed: int = 42) -> pd.DataFrame:
    """
    Fallback: generate synthetic NYC-like trips when DuckDB/internet unavailable.
    Distribution matches real NYC TLC statistics:
    - Distance: log-normal, mean ~2.8 km, most trips 0.5–10 km
    - Zones: 265 NYC taxi zones
    """
    rng = np.random.default_rng(seed)
    distances = np.clip(rng.lognormal(mean=1.0, sigma=0.7, size=n), 0.1, 30.0)
    return pd.DataFrame({
        "trip_distance": np.round(distances, 2),
        "PULocationID":  rng.integers(1, 266, size=n),
        "DOLocationID":  rng.integers(1, 266, size=n),
    })


def get_dataset_stats(con: Any) -> dict:
    """Aggregate stats via DuckDB SQL — no full DataFrame in RAM."""
    row = con.execute("""
        SELECT
            COUNT(*)                        AS total_rows,
            ROUND(AVG(trip_distance), 2)    AS avg_distance,
            ROUND(PERCENTILE_CONT(0.5)
                  WITHIN GROUP (ORDER BY trip_distance), 2) AS median_distance,
            ROUND(MAX(trip_distance), 1)    AS max_distance,
            COUNT(DISTINCT PULocationID)    AS unique_pu,
            COUNT(DISTINCT DOLocationID)    AS unique_do
        FROM trips
    """).fetchone()
    return {
        "total_rows":      int(row[0]),
        "avg_distance":    float(row[1]),
        "median_distance": float(row[2]),
        "max_distance":    float(row[3]),
        "unique_pu_zones": int(row[4]),
        "unique_do_zones": int(row[5]),
    }
