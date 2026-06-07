"""
pipeline/etl.py — NYC Taxi ETL: Parquet → DuckDB aggregation → PostgreSQL.

Data flow:
  Parquet (Data Lake)
      ↓  DuckDB (in-process, zero-copy reads)
  Aggregated DataFrames
      ↓  psycopg2 COPY (bulk upsert)
  PostgreSQL (aggregated tables ONLY)

Design decisions:
- DuckDB reads parquet directly — no pandas intermediate for raw scan.
- All aggregation happens inside DuckDB before touching Postgres.
- Upsert via INSERT … ON CONFLICT DO UPDATE so re-runs are idempotent.
- Zone metadata is seeded from the TLC zone CSV on first run.
"""

from __future__ import annotations

import logging
import os
from io import StringIO
from pathlib import Path

import duckdb
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

# ── Config ────────────────────────────────────────────────────────────────────

PG_DSN = (
    f"host={os.getenv('POSTGRES_HOST','localhost')} "
    f"port={os.getenv('POSTGRES_PORT','5432')} "
    f"dbname={os.getenv('POSTGRES_DB','nyc_taxi')} "
    f"user={os.getenv('POSTGRES_USER','taxi')} "
    f"password={os.getenv('POSTGRES_PASSWORD','')}"
)
PARQUET_GLOB = os.getenv("PARQUET_GLOB", "data/**/*.parquet")

# NYC TLC zone CSV — download once and place in data/taxi_zones.csv
ZONE_CSV = Path("data/taxi_zones.csv")


# ── DuckDB aggregation queries ────────────────────────────────────────────────

_AGG_QUERY = """
SELECT
    YEAR(tpep_pickup_datetime)   AS year,
    MONTH(tpep_pickup_datetime)  AS month,
    PULocationID                 AS pu_location_id,
    DOLocationID                 AS do_location_id,
    COUNT(*)                     AS trips_count,
    AVG(fare_amount)             AS avg_fare,
    SUM(total_amount)            AS total_revenue,
    AVG(trip_distance)           AS avg_distance
FROM read_parquet('{glob}', hive_partitioning=true)
WHERE fare_amount  > 0
  AND trip_distance > 0
  AND total_amount  > 0
  AND PULocationID  IS NOT NULL
  AND DOLocationID  IS NOT NULL
  AND tpep_pickup_datetime IS NOT NULL
GROUP BY 1, 2, 3, 4
"""

_MONTHLY_QUERY = """
SELECT
    year,
    month,
    SUM(trips_count)                      AS total_trips,
    SUM(total_revenue)                    AS total_revenue,
    SUM(avg_fare * trips_count)
        / NULLIF(SUM(trips_count), 0)     AS avg_fare,
    SUM(avg_distance * trips_count)
        / NULLIF(SUM(trips_count), 0)     AS avg_distance
FROM ({agg}) t
GROUP BY year, month
"""

_ZONE_SUMMARY_QUERY = """
SELECT
    pu_location_id AS zone_id,
    year,
    month,
    SUM(trips_count)   AS pickup_trips,
    0                  AS dropoff_trips,
    SUM(total_revenue) AS revenue
FROM ({agg}) t
GROUP BY pu_location_id, year, month

UNION ALL

SELECT
    do_location_id AS zone_id,
    year,
    month,
    0                  AS pickup_trips,
    SUM(trips_count)   AS dropoff_trips,
    0                  AS revenue
FROM ({agg}) t
GROUP BY do_location_id, year, month
"""


# ── Aggregation ───────────────────────────────────────────────────────────────

def aggregate(glob: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Run all three aggregation queries via DuckDB.
    Returns (trips_agg_df, monthly_df, zone_summary_df).
    """
    log.info("DuckDB scanning: %s", glob)
    con = duckdb.connect()

    agg_sql = _AGG_QUERY.format(glob=glob)

    trips_df = con.execute(agg_sql).df()
    log.info("trips_agg rows: %d", len(trips_df))

    monthly_df = con.execute(_MONTHLY_QUERY.format(agg=agg_sql)).df()
    log.info("monthly_summary rows: %d", len(monthly_df))

    zone_df = con.execute(_ZONE_SUMMARY_QUERY.format(agg=agg_sql)).df()
    # Consolidate pickup + dropoff per zone/month
    zone_df = (
        zone_df
        .groupby(["zone_id", "year", "month"], as_index=False)
        .agg(pickup_trips=("pickup_trips", "sum"),
             dropoff_trips=("dropoff_trips", "sum"),
             revenue=("revenue", "sum"))
    )
    log.info("zone_summary rows: %d", len(zone_df))

    con.close()
    return trips_df, monthly_df, zone_df


# ── Postgres helpers ──────────────────────────────────────────────────────────

def _upsert(cur, table: str, df: pd.DataFrame, pk_cols: list[str]) -> None:
    """Generic upsert: INSERT … ON CONFLICT (pk_cols) DO UPDATE SET …"""
    if df.empty:
        log.warning("Skipping empty dataframe for %s", table)
        return

    cols = list(df.columns)
    update_cols = [c for c in cols if c not in pk_cols]

    update_clause = ", ".join(
        f"{c} = EXCLUDED.{c}" for c in update_cols
    )
    conflict_clause = ", ".join(pk_cols)

    sql = (
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES %s "
        f"ON CONFLICT ({conflict_clause}) DO UPDATE SET {update_clause}"
    )

    rows = [tuple(row) for row in df.itertuples(index=False)]
    execute_values(cur, sql, rows, page_size=2000)
    log.info("Upserted %d rows into %s", len(rows), table)


def seed_zones(cur, csv_path: Path) -> None:
    """Load zone reference data from TLC CSV if zones table is empty."""
    cur.execute("SELECT COUNT(*) FROM zones")
    if cur.fetchone()[0] > 0:
        log.info("zones table already seeded — skipping")
        return

    if not csv_path.exists():
        log.warning(
            "Zone CSV not found at %s — zones table will be empty. "
            "Download from: https://d37ci6vzurychx.cloudfront.net/"
            "misc/taxi+_zone_lookup.csv",
            csv_path,
        )
        return

    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    col_map = {c.lower(): c for c in df.columns}
    df = df.rename(columns={
        col_map.get("locationid", "LocationID"): "zone_id",
        col_map.get("zone",       "zone"):       "zone_name",
        col_map.get("borough",    "borough"):    "borough",
    })[["zone_id", "zone_name", "borough"]]
    df = df.dropna()

    execute_values(
        cur,
        "INSERT INTO zones (zone_id, zone_name, borough) VALUES %s "
        "ON CONFLICT (zone_id) DO NOTHING",
        [tuple(r) for r in df.itertuples(index=False)],
    )
    log.info("Seeded %d zones", len(df))


def refresh_materialized_view(cur) -> None:
    # CONCURRENTLY requires a prior population; plain REFRESH always works
    cur.execute("REFRESH MATERIALIZED VIEW top_routes")
    log.info("Refreshed materialized view top_routes")


# ── Main entry point ──────────────────────────────────────────────────────────

def run(glob: str = PARQUET_GLOB) -> None:
    trips_df, monthly_df, zone_df = aggregate(glob)

    log.info("Connecting to Postgres: %s", PG_DSN.split("password")[0])
    conn = psycopg2.connect(PG_DSN)
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            seed_zones(cur, ZONE_CSV)

            # Filter to valid zones only (FK constraint)
            cur.execute("SELECT zone_id FROM zones")
            valid_zones = {r[0] for r in cur.fetchall()}

            if valid_zones:
                trips_df = trips_df[
                    trips_df["pu_location_id"].isin(valid_zones)
                    & trips_df["do_location_id"].isin(valid_zones)
                ]
                zone_df = zone_df[zone_df["zone_id"].isin(valid_zones)]

            _upsert(cur, "trips_agg",      trips_df,  ["year", "month", "pu_location_id", "do_location_id"])
            _upsert(cur, "monthly_summary", monthly_df, ["year", "month"])
            _upsert(cur, "zone_summary",    zone_df,    ["zone_id", "year", "month"])

            try:
                refresh_materialized_view(cur)
            except Exception as exc:
                log.warning("Could not refresh top_routes view: %s", exc)

        conn.commit()
        log.info("ETL complete — all tables updated")

    except Exception:
        conn.rollback()
        log.exception("ETL failed — transaction rolled back")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    run()
