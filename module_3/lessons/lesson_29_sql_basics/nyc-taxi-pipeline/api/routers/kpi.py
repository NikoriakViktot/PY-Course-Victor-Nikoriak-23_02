"""
api/routers/kpi.py — KPI and analytics endpoints backed by PostgreSQL.

Critical fix:
  get_kpi() ALWAYS returns a dict with safe defaults.
  No endpoint ever returns None or raises on missing data.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, HTTPException

from api import postgres_client as pg

router = APIRouter(prefix="/kpi", tags=["kpi"])

_KPI_DEFAULT: dict[str, Any] = {
    "total_trips":   0,
    "total_revenue": 0.0,
    "avg_fare":      0.0,
    "avg_distance":  0.0,
    "year":          None,
    "month":         None,
}


# ── KPI ───────────────────────────────────────────────────────────────────────

@router.get("/summary")
def get_kpi(
    year:  int | None = Query(None, description="Filter by year"),
    month: int | None = Query(None, description="Filter by month (1–12)"),
) -> dict[str, Any]:
    """
    Return aggregated KPI metrics.

    Always returns a valid dict — never None, never raises on missing data.
    """
    if not pg.is_available():
        return {**_KPI_DEFAULT, "error": "database_unavailable"}

    try:
        if year and month:
            row = pg.fetchone(
                """
                SELECT year, month, total_trips, total_revenue, avg_fare, avg_distance
                FROM monthly_summary
                WHERE year = %s AND month = %s
                """,
                (year, month),
            )
        elif year:
            row = pg.fetchone(
                """
                SELECT
                    year,
                    NULL::INT                                  AS month,
                    SUM(total_trips)                           AS total_trips,
                    SUM(total_revenue)                         AS total_revenue,
                    SUM(avg_fare * total_trips)
                        / NULLIF(SUM(total_trips), 0)          AS avg_fare,
                    SUM(avg_distance * total_trips)
                        / NULLIF(SUM(total_trips), 0)          AS avg_distance
                FROM monthly_summary
                WHERE year = %s
                GROUP BY year
                """,
                (year,),
            )
        else:
            row = pg.fetchone(
                """
                SELECT
                    NULL::INT                                  AS year,
                    NULL::INT                                  AS month,
                    SUM(total_trips)                           AS total_trips,
                    SUM(total_revenue)                         AS total_revenue,
                    SUM(avg_fare * total_trips)
                        / NULLIF(SUM(total_trips), 0)          AS avg_fare,
                    SUM(avg_distance * total_trips)
                        / NULLIF(SUM(total_trips), 0)          AS avg_distance
                FROM monthly_summary
                """
            )

        if row is None:
            return {**_KPI_DEFAULT, "year": year, "month": month}

        return {
            "year":          row.get("year"),
            "month":         row.get("month"),
            "total_trips":   int(row.get("total_trips")   or 0),
            "total_revenue": float(row.get("total_revenue") or 0.0),
            "avg_fare":      round(float(row.get("avg_fare")      or 0.0), 2),
            "avg_distance":  round(float(row.get("avg_distance")  or 0.0), 2),
        }

    except Exception as exc:
        return {**_KPI_DEFAULT, "year": year, "month": month, "error": str(exc)}


# ── Monthly time series ───────────────────────────────────────────────────────

@router.get("/monthly")
def get_monthly_series(
    year: int | None = Query(None),
) -> list[dict[str, Any]]:
    """Monthly KPI time series, optionally filtered by year."""
    if not pg.is_available():
        return []
    try:
        if year:
            rows = pg.fetchall(
                "SELECT * FROM monthly_summary WHERE year = %s ORDER BY year, month",
                (year,),
            )
        else:
            rows = pg.fetchall(
                "SELECT * FROM monthly_summary ORDER BY year, month"
            )
        return [_safe_monthly(r) for r in rows]
    except Exception:
        return []


def _safe_monthly(r: dict) -> dict[str, Any]:
    return {
        "year":          int(r.get("year")  or 0),
        "month":         int(r.get("month") or 0),
        "total_trips":   int(r.get("total_trips")   or 0),
        "total_revenue": float(r.get("total_revenue") or 0.0),
        "avg_fare":      round(float(r.get("avg_fare")     or 0.0), 2),
        "avg_distance":  round(float(r.get("avg_distance") or 0.0), 2),
    }


# ── Top routes ────────────────────────────────────────────────────────────────

@router.get("/top-routes")
def get_top_routes(
    limit: int = Query(20, ge=1, le=100),
) -> list[dict[str, Any]]:
    """Top N routes by total trip count (all time)."""
    if not pg.is_available():
        return []
    try:
        return pg.fetchall(
            """
            SELECT
                tr.pu_location_id,
                pu.zone_name  AS pu_zone_name,
                pu.borough    AS pu_borough,
                tr.do_location_id,
                dz.zone_name  AS do_zone_name,
                dz.borough    AS do_borough,
                tr.total_trips,
                round(tr.avg_fare::numeric, 2)      AS avg_fare,
                round(tr.total_revenue::numeric, 2) AS total_revenue,
                round(tr.avg_distance::numeric, 2)  AS avg_distance
            FROM top_routes tr
            LEFT JOIN zones pu ON pu.zone_id = tr.pu_location_id
            LEFT JOIN zones dz ON dz.zone_id = tr.do_location_id
            ORDER BY tr.total_trips DESC
            LIMIT %s
            """,
            (limit,),
        )
    except Exception:
        return []


# ── Zone heatmap ──────────────────────────────────────────────────────────────

@router.get("/zones")
def get_zone_summary(
    year:  int | None = Query(None),
    month: int | None = Query(None),
) -> list[dict[str, Any]]:
    """Zone-level pickup/dropoff totals for heatmap rendering."""
    if not pg.is_available():
        return []
    try:
        conditions = []
        params: list = []
        if year:
            conditions.append("zs.year = %s")
            params.append(year)
        if month:
            conditions.append("zs.month = %s")
            params.append(month)

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

        return pg.fetchall(
            f"""
            SELECT
                zs.zone_id,
                z.zone_name,
                z.borough,
                SUM(zs.pickup_trips)  AS pickup_trips,
                SUM(zs.dropoff_trips) AS dropoff_trips,
                SUM(zs.revenue)       AS revenue
            FROM zone_summary zs
            LEFT JOIN zones z ON z.zone_id = zs.zone_id
            {where}
            GROUP BY zs.zone_id, z.zone_name, z.borough
            ORDER BY pickup_trips DESC
            """,
            tuple(params),
        )
    except Exception:
        return []
