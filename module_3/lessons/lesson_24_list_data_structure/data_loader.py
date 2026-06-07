"""
data_loader.py — Lazy DuckDB data layer for Taxi Big-O Lab.

Architecture
------------
  DuckDB VIEW (lazy)  ← full 3M-row parquet, never in RAM
       ↓  SQL SAMPLE  (or SELECT * for full-mode)
  pandas DataFrame    ← only n rows, fits in memory
       ↓  Python loops
  Algorithm results   ← Big-O demonstration

Key principle: Data size ≠ Data loaded.
You can work with 3M rows while holding only 10k in memory.

Memory safety
-------------
  estimate_load_gb(n)          → pre-flight RAM estimate
  load_full_dataset(con, lim)  → full load with hard memory guard
"""
from __future__ import annotations

import logging

import duckdb
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

DATA_URL = (
    "https://d37ci6vzurychx.cloudfront.net/trip-data/"
    "yellow_tripdata_2023-01.parquet"
)

# Payment code → label (kept in SQL layer, mapped after sampling)
_PAYMENT_SQL = "CASE payment_type WHEN 1 THEN 'Card' ELSE 'Cash' END"

_CREATE_VIEW_SQL = f"""
    CREATE OR REPLACE VIEW trips AS
    SELECT
        CAST(payment_type  AS INTEGER) AS payment_type,
        CAST(trip_distance AS DOUBLE)  AS trip_distance,
        CAST(PULocationID  AS INTEGER) AS PULocationID,
        CAST(DOLocationID  AS INTEGER) AS DOLocationID
    FROM read_parquet('{DATA_URL}')
    WHERE
        payment_type IN (1, 2)
        AND trip_distance > 0
        AND trip_distance < 500
"""


# ---------------------------------------------------------------------------
# Connection — @st.cache_resource persists across reruns (one per session)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_duckdb_connection() -> duckdb.DuckDBPyConnection:
    """
    Create a persistent in-memory DuckDB connection with a lazy VIEW over
    the remote parquet.

    The VIEW is LAZY: it defines *how* to read the data, but does NOT
    execute any query or allocate any memory until you actually run SQL.

    Why @st.cache_resource?
    -----------------------
    Unlike @st.cache_data (for serialisable values), @st.cache_resource
    keeps the live Python object (the connection) between reruns without
    pickling it. Perfect for database connections.
    """
    con = duckdb.connect(database=":memory:")

    # Install httpfs extension — enables reading remote parquet over HTTPS
    try:
        con.execute("INSTALL httpfs; LOAD httpfs;")
    except Exception as exc:
        logger.debug("httpfs already present: %s", exc)

    # Register the lazy VIEW — zero data loaded here
    con.execute(_CREATE_VIEW_SQL)
    logger.info("DuckDB VIEW 'trips' registered (lazy, no data loaded yet).")
    return con


# ---------------------------------------------------------------------------
# Sampling — small pandas slice, not a full load
# ---------------------------------------------------------------------------

def sample_from_view(con: duckdb.DuckDBPyConnection, n: int) -> pd.DataFrame:
    """
    Pull exactly *n* rows from the DuckDB VIEW using reservoir sampling.

    Why SQL SAMPLE instead of pandas.sample()?
    -------------------------------------------
    pandas.sample(n) requires the FULL DataFrame to exist in RAM first.
    DuckDB SAMPLE reads only what is needed to return n rows,
    leveraging parquet column pruning and predicate pushdown.

    The returned DataFrame is small (n rows × 4 cols) — safe for RAM.
    """
    df = con.execute(f"""
        SELECT
            {_PAYMENT_SQL}      AS payment_type,
            trip_distance,
            PULocationID,
            DOLocationID
        FROM trips
        USING SAMPLE {n} ROWS
    """).df()
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Dataset statistics — SQL aggregation, no full pandas load
# ---------------------------------------------------------------------------

def get_dataset_stats(con: duckdb.DuckDBPyConnection) -> dict:
    """
    Compute dataset-level statistics entirely in DuckDB.

    DuckDB reads only the required columns from parquet (column pruning),
    aggregates in its vectorised execution engine, and returns a single row.
    No 3M-row DataFrame ever touches Python RAM.
    """
    row = con.execute("""
        SELECT
            COUNT(*)                                       AS total_rows,
            SUM(CASE WHEN payment_type = 2 THEN 1 ELSE 0 END) AS cash_count,
            SUM(CASE WHEN payment_type = 1 THEN 1 ELSE 0 END) AS card_count,
            ROUND(AVG(trip_distance), 2)                   AS avg_distance,
            ROUND(MAX(trip_distance), 1)                   AS max_distance,
            COUNT(DISTINCT PULocationID)                   AS unique_pu,
            COUNT(DISTINCT DOLocationID)                   AS unique_do
        FROM trips
    """).fetchone()

    return {
        "total_rows":     int(row[0]),
        "cash_count":     int(row[1]),
        "card_count":     int(row[2]),
        "avg_distance":   float(row[3]),
        "max_distance":   float(row[4]),
        "unique_pu_zones": int(row[5]),
        "unique_do_zones": int(row[6]),
    }


# ---------------------------------------------------------------------------
# SQL COUNT on the full VIEW — the real DuckDB power demo
# ---------------------------------------------------------------------------

def duckdb_count_on_view(
    con: duckdb.DuckDBPyConnection,
    payment_code: int = 2,     # 2 = Cash
) -> int:
    """
    COUNT matching rows in the FULL VIEW (potentially 3M+ rows) using SQL.

    This is fundamentally different from pandas filtering on a sample:
    - DuckDB reads only the payment_type column (column pruning)
    - Applies the WHERE predicate at the parquet page level
    - Uses AVX2 SIMD vectorised execution
    - Returns a single integer — never materialises a DataFrame

    Complexity: O(n) scan, but with vectorised C execution and
    parquet-level optimisations that make the constant factor ~100× smaller
    than a Python loop.
    """
    return con.execute(
        f"SELECT COUNT(*) FROM trips WHERE payment_type = {payment_code}"
    ).fetchone()[0]


# ---------------------------------------------------------------------------
# Utility: summary stats on a sampled pandas DataFrame
# ---------------------------------------------------------------------------

def dataset_summary(df: pd.DataFrame) -> dict:
    """Basic stats on a small sampled DataFrame (for the result card)."""
    return {
        "total_rows":      len(df),
        "cash_count":      int((df["payment_type"] == "Cash").sum()),
        "card_count":      int((df["payment_type"] == "Card").sum()),
        "avg_distance_km": round(float(df["trip_distance"].mean()), 2),
        "max_distance_km": round(float(df["trip_distance"].max()), 2),
        "unique_pu_zones": int(df["PULocationID"].nunique()),
        "unique_do_zones": int(df["DOLocationID"].nunique()),
    }


# ---------------------------------------------------------------------------
# Memory estimation and full-dataset loading
# ---------------------------------------------------------------------------

#: Approximate bytes per pandas row for our 4-column schema:
#:   payment_type (object/str ~50B) + trip_distance (float64 8B)
#:   + PULocationID (int32 4B) + DOLocationID (int32 4B) + pandas overhead
_BYTES_PER_ROW: int = 120


def estimate_load_gb(n_rows: int) -> float:
    """
    Pre-flight RAM estimate: how many GB will *n_rows* occupy as a DataFrame?

    Uses a conservative per-row estimate that includes pandas object overhead.
    Actual usage may vary ±30% depending on string interning.
    """
    return n_rows * _BYTES_PER_ROW / (1_024 ** 3)


def load_full_dataset(
    con: duckdb.DuckDBPyConnection,
    limit_gb: float = 8.0,
) -> pd.DataFrame:
    """
    Load ALL rows from the trips VIEW into pandas RAM.

    Safety
    ------
    1. Pre-flight: estimates projected RAM (current + expected delta).
       Raises MemoryGuardError *before* fetching if projection exceeds limit.
    2. Post-load: checks actual RSS after materialisation.
       Raises MemoryGuardError if limit is breached.

    This function should ONLY be called when the user explicitly enables
    "Full dataset mode" in the UI and accepts the memory risk.
    """
    from metrics import MemoryGuardError, check_memory, get_memory_usage_gb

    # ── Step 1: count rows via SQL (no data loaded) ────────────────────────
    row_count = con.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    estimated_gb = estimate_load_gb(row_count)
    current_gb   = get_memory_usage_gb()
    projected_gb = current_gb + estimated_gb

    if projected_gb > limit_gb:
        raise MemoryGuardError(
            current_gb=projected_gb,
            limit_gb=limit_gb,
            context="pre-flight for load_full_dataset",
            delta_gb=estimated_gb,
        )

    # ── Step 2: materialise all rows ──────────────────────────────────────
    df = con.execute(f"""
        SELECT
            {_PAYMENT_SQL}      AS payment_type,
            trip_distance,
            PULocationID,
            DOLocationID
        FROM trips
    """).df()

    # ── Step 3: post-load RAM check ────────────────────────────────────────
    check_memory(limit_gb, "load_full_dataset (post-materialisation)")

    return df.reset_index(drop=True)
