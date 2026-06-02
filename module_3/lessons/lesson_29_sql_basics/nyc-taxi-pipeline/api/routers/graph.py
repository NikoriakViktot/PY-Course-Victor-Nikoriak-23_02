"""
api/routers/graph.py — Graph algorithm endpoints backed by Neo4j GDS.

All endpoints degrade gracefully if Neo4j is unavailable.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from fastapi import APIRouter, Query, HTTPException

from api import neo4j_client as neo4j

router = APIRouter(prefix="/graph", tags=["graph"])

_WEIGHT_MAP = {
    "cost":     "weight_cost",
    "flow":     "weight_flow",
    "distance": "weight_distance",
}


class WeightMode(str, Enum):
    cost     = "cost"
    flow     = "flow"
    distance = "distance"


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health")
def graph_health() -> dict[str, Any]:
    return {"neo4j_available": neo4j.is_available()}


# ── Dijkstra ──────────────────────────────────────────────────────────────────

@router.get("/shortest-path")
def shortest_path(
    source: int    = Query(..., description="Pickup zone ID"),
    target: int    = Query(..., description="Dropoff zone ID"),
    mode:   WeightMode = Query(WeightMode.cost, description="cost | flow | distance"),
) -> dict[str, Any]:
    """
    Dijkstra shortest path between two zones.

    Modes:
      cost     — minimizes avg_fare
      flow     — minimizes 1/trips_count (least congested)
      distance — minimizes avg_distance
    """
    if not neo4j.is_available():
        return {"error": "graph_unavailable", "path": [], "total_cost": None}

    weight_prop = _WEIGHT_MAP[mode.value]

    cypher = """
    MATCH (src:Zone {zone_id: $source})
    MATCH (tgt:Zone {zone_id: $target})
    CALL gds.shortestPath.dijkstra.stream('taxi_graph', {
        sourceNode: id(src),
        targetNode: id(tgt),
        relationshipWeightProperty: $weight
    })
    YIELD totalCost, nodeIds, costs
    RETURN
        totalCost,
        [n IN gds.util.asNodes(nodeIds) | n.zone_id]   AS zone_ids,
        [n IN gds.util.asNodes(nodeIds) | n.zone_name] AS zone_names,
        costs
    LIMIT 1
    """

    try:
        rows = neo4j.run_query(cypher, {"source": source, "target": target, "weight": weight_prop})
    except RuntimeError as exc:
        return {"error": str(exc), "path": [], "total_cost": None}

    if not rows:
        return {"source": source, "target": target, "mode": mode, "path": [], "total_cost": None}

    r = rows[0]
    path = [
        {"zone_id": zid, "zone_name": zname, "leg_cost": round(cost, 4)}
        for zid, zname, cost in zip(
            r.get("zone_ids", []),
            r.get("zone_names", []),
            r.get("costs", []),
        )
    ]
    return {
        "source":     source,
        "target":     target,
        "mode":       mode,
        "total_cost": round(float(r.get("totalCost") or 0), 4),
        "path":       path,
    }


# ── PageRank ──────────────────────────────────────────────────────────────────

@router.get("/pagerank")
def pagerank(
    limit: int = Query(20, ge=1, le=263),
) -> list[dict[str, Any]]:
    """Top N zones by PageRank (weighted by trips_count)."""
    if not neo4j.is_available():
        return []

    cypher = """
    CALL gds.pageRank.stream('taxi_graph', {
        maxIterations: 20,
        dampingFactor: 0.85,
        relationshipWeightProperty: 'trips_count'
    })
    YIELD nodeId, score
    WITH gds.util.asNode(nodeId) AS zone, score
    RETURN
        zone.zone_id   AS zone_id,
        zone.zone_name AS zone_name,
        zone.borough   AS borough,
        round(score, 6) AS pagerank_score
    ORDER BY pagerank_score DESC
    LIMIT $limit
    """

    try:
        return neo4j.run_query(cypher, {"limit": limit})
    except RuntimeError:
        return []


# ── Betweenness Centrality ────────────────────────────────────────────────────

@router.get("/betweenness")
def betweenness(
    limit: int = Query(20, ge=1, le=263),
) -> list[dict[str, Any]]:
    """Top N bridge zones by betweenness centrality."""
    if not neo4j.is_available():
        return []

    cypher = """
    CALL gds.betweenness.stream('taxi_graph')
    YIELD nodeId, score
    WITH gds.util.asNode(nodeId) AS zone, score
    RETURN
        zone.zone_id   AS zone_id,
        zone.zone_name AS zone_name,
        zone.borough   AS borough,
        round(score, 2) AS betweenness_score
    ORDER BY betweenness_score DESC
    LIMIT $limit
    """

    try:
        return neo4j.run_query(cypher, {"limit": limit})
    except RuntimeError:
        return []


# ── Zone neighbors ────────────────────────────────────────────────────────────

@router.get("/neighbors/{zone_id}")
def zone_neighbors(
    zone_id: int,
    direction: str = Query("out", regex="^(out|in|both)$"),
    top_n:    int  = Query(10, ge=1, le=50),
) -> list[dict[str, Any]]:
    """Direct neighbors of a zone, ranked by trips_count."""
    if not neo4j.is_available():
        return []

    if direction == "out":
        match = "MATCH (z:Zone {zone_id: $zid})-[r:TRIP_TO]->(n:Zone)"
    elif direction == "in":
        match = "MATCH (n:Zone)-[r:TRIP_TO]->(z:Zone {zone_id: $zid})"
    else:
        match = "MATCH (z:Zone {zone_id: $zid})-[r:TRIP_TO]-(n:Zone)"

    cypher = f"""
    {match}
    RETURN
        n.zone_id       AS zone_id,
        n.zone_name     AS zone_name,
        n.borough       AS borough,
        r.trips_count   AS trips_count,
        round(r.avg_fare, 2)      AS avg_fare,
        round(r.avg_distance, 2)  AS avg_distance
    ORDER BY r.trips_count DESC
    LIMIT $top_n
    """

    try:
        return neo4j.run_query(cypher, {"zid": zone_id, "top_n": top_n})
    except RuntimeError:
        return []
