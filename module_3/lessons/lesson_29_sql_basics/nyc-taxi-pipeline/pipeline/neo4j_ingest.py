"""
pipeline/neo4j_ingest.py — Build Neo4j graph from PostgreSQL aggregated data.

Graph model:
    (:Zone {zone_id, zone_name, borough})
        -[:TRIP_TO {
            trips_count, avg_fare, total_revenue, avg_distance,
            weight_cost, weight_flow, weight_distance
        }]->
    (:Zone)

Weight semantics (for GDS shortest-path algorithms):
    weight_cost     = avg_fare          → minimize cost
    weight_flow     = 1 / trips_count   → penalize underused routes
    weight_distance = avg_distance      → minimize distance

Idempotent: re-running merges rather than duplicates nodes/edges.
"""

from __future__ import annotations

import logging
import os

import psycopg2
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

PG_DSN = (
    f"host={os.getenv('POSTGRES_HOST','localhost')} "
    f"port={os.getenv('POSTGRES_PORT','5432')} "
    f"dbname={os.getenv('POSTGRES_DB','nyc_taxi')} "
    f"user={os.getenv('POSTGRES_USER','taxi')} "
    f"password={os.getenv('POSTGRES_PASSWORD','')}"
)

NEO4J_URI  = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DB   = os.getenv("NEO4J_DATABASE", "neo4j")

_BATCH_SIZE = 500


# ── Schema setup ──────────────────────────────────────────────────────────────

_SCHEMA_STATEMENTS = [
    # Uniqueness constraint — required for MERGE to work correctly
    "CREATE CONSTRAINT zone_id IF NOT EXISTS FOR (z:Zone) REQUIRE z.zone_id IS UNIQUE",
    # Lookup indexes for common queries
    "CREATE INDEX zone_borough IF NOT EXISTS FOR (z:Zone) ON (z.borough)",
    "CREATE INDEX zone_name IF NOT EXISTS FOR (z:Zone) ON (z.zone_name)",
    # Relationship property index for GDS weight lookup
    "CREATE INDEX trip_to_weight_cost IF NOT EXISTS FOR ()-[r:TRIP_TO]-() ON (r.weight_cost)",
]


def _apply_schema(session) -> None:
    for stmt in _SCHEMA_STATEMENTS:
        try:
            session.run(stmt)
            log.info("Schema: %s", stmt[:70])
        except Exception as exc:
            log.warning("Schema stmt failed (non-fatal): %s — %s", stmt[:60], exc)


# ── Data fetch from Postgres ──────────────────────────────────────────────────

def _fetch_zones(pg_conn) -> list[dict]:
    with pg_conn.cursor() as cur:
        cur.execute("SELECT zone_id, zone_name, borough FROM zones ORDER BY zone_id")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetch_edges(pg_conn) -> list[dict]:
    """Aggregate trips_agg to all-time totals for graph edges."""
    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT
                pu_location_id,
                do_location_id,
                SUM(trips_count)                              AS trips_count,
                SUM(avg_fare * trips_count)
                    / NULLIF(SUM(trips_count), 0)             AS avg_fare,
                SUM(total_revenue)                            AS total_revenue,
                SUM(avg_distance * trips_count)
                    / NULLIF(SUM(trips_count), 0)             AS avg_distance
            FROM trips_agg
            WHERE trips_count > 0
            GROUP BY pu_location_id, do_location_id
        """)
        cols = [d[0] for d in cur.description]
        rows = []
        for row in cur.fetchall():
            r = dict(zip(cols, row))
            tc = r["trips_count"] or 1
            af = r["avg_fare"]    or 0.0
            ad = r["avg_distance"] or 0.0
            r["weight_cost"]     = float(af)
            r["weight_flow"]     = round(1.0 / tc, 8)
            r["weight_distance"] = float(ad)
            rows.append(r)
        log.info("Fetched %d edges from Postgres", len(rows))
    return rows


# ── Neo4j write helpers ───────────────────────────────────────────────────────

_MERGE_ZONES_CYPHER = """
UNWIND $batch AS z
MERGE (n:Zone {zone_id: z.zone_id})
SET n.zone_name = z.zone_name,
    n.borough   = z.borough
"""

_MERGE_EDGES_CYPHER = """
UNWIND $batch AS e
MATCH (pu:Zone {zone_id: e.pu_location_id})
MATCH (do:Zone {zone_id: e.do_location_id})
MERGE (pu)-[r:TRIP_TO]->(do)
SET r.trips_count     = e.trips_count,
    r.avg_fare        = e.avg_fare,
    r.total_revenue   = e.total_revenue,
    r.avg_distance    = e.avg_distance,
    r.weight_cost     = e.weight_cost,
    r.weight_flow     = e.weight_flow,
    r.weight_distance = e.weight_distance
"""


def _batched_write(session, cypher: str, rows: list[dict], label: str) -> None:
    total = 0
    for i in range(0, len(rows), _BATCH_SIZE):
        batch = rows[i : i + _BATCH_SIZE]
        session.run(cypher, batch=batch)
        total += len(batch)
        log.info("%s — written %d / %d", label, total, len(rows))


# ── GDS graph projection ──────────────────────────────────────────────────────

_GDS_PROJECT_CYPHER = """
MATCH (source:Zone)-[r:TRIP_TO]->(target:Zone)
WITH gds.graph.project(
    'taxi_graph',
    source,
    target,
    { relationshipProperties: r { .weight_cost, .weight_flow, .weight_distance, .trips_count } }
) AS g
RETURN g.graphName AS graphName, g.nodeCount AS nodeCount, g.relationshipCount AS relationshipCount
"""

_GDS_DROP_CYPHER = "CALL gds.graph.drop('taxi_graph', false) YIELD graphName"


def _project_gds_graph(session) -> None:
    try:
        session.run(_GDS_DROP_CYPHER)
        log.info("Dropped existing GDS projection 'taxi_graph'")
    except Exception:
        pass  # Does not exist yet — fine

    result = session.run(_GDS_PROJECT_CYPHER).single()
    if result:
        log.info(
            "GDS projection created: nodes=%d, rels=%d",
            result["nodeCount"],
            result["relationshipCount"],
        )


# ── Main entry point ──────────────────────────────────────────────────────────

def run() -> None:
    log.info("Connecting to Neo4j: %s", NEO4J_URI)
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    driver.verify_connectivity()

    log.info("Connecting to Postgres")
    pg_conn = psycopg2.connect(PG_DSN)

    zones = _fetch_zones(pg_conn)
    edges = _fetch_edges(pg_conn)
    pg_conn.close()

    with driver.session(database=NEO4J_DB) as session:
        _apply_schema(session)
        _batched_write(session, _MERGE_ZONES_CYPHER, zones, "Zones")
        _batched_write(session, _MERGE_EDGES_CYPHER, edges, "Edges")
        _project_gds_graph(session)

    driver.close()
    log.info("Neo4j ingest complete")


if __name__ == "__main__":
    run()
