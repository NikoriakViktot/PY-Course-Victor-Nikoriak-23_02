"""
api/neo4j_client.py — Neo4j driver singleton for the API.

Same pattern as data_dnipro_h_q — singleton driver, run_query(),
is_available() guard, and schema initialization.
"""

from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase, Driver
    from neo4j import exceptions as _neo4j_exc
    from neo4j.graph import Node, Relationship, Path
    _HAS_NEO4J = True
except ImportError:
    _HAS_NEO4J = False
    log.warning("neo4j package not installed — graph endpoints disabled")

NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://neo4j:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

_driver: "Driver | None" = None


def get_driver() -> "Driver":
    if not _HAS_NEO4J:
        raise RuntimeError("neo4j driver not installed")
    global _driver
    if _driver is None:
        if not NEO4J_PASSWORD:
            raise RuntimeError("NEO4J_PASSWORD not set")
        _driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            max_connection_pool_size=20,
            connection_timeout=10,
        )
        log.info("Neo4j driver created: %s", NEO4J_URI)
    return _driver


def close_driver() -> None:
    global _driver
    if _driver:
        _driver.close()
        _driver = None


def is_available() -> bool:
    if not _HAS_NEO4J or not NEO4J_PASSWORD:
        return False
    try:
        get_driver().verify_connectivity()
        return True
    except Exception:
        return False


def run_query(
    query: str,
    params: dict[str, Any] | None = None,
    database: str | None = None,
) -> list[dict[str, Any]]:
    driver = get_driver()
    db = database or NEO4J_DATABASE
    try:
        with driver.session(database=db) as session:
            result = session.run(query, params or {})
            return [{k: _serialize(v) for k, v in rec.items()} for rec in result]
    except _neo4j_exc.ServiceUnavailable as exc:
        raise RuntimeError(f"Neo4j unavailable: {exc}") from exc
    except _neo4j_exc.AuthError as exc:
        raise RuntimeError(f"Neo4j auth failed: {exc}") from exc


def _serialize(val: Any) -> Any:
    if not _HAS_NEO4J:
        return val
    if isinstance(val, Node):
        d: dict = {"_labels": list(val.labels), "_element_id": val.element_id}
        d.update(dict(val.items()))
        return d
    if isinstance(val, Relationship):
        d = {"_type": val.type, "_element_id": val.element_id}
        d.update(dict(val.items()))
        return d
    if isinstance(val, Path):
        return {
            "_path_nodes": [_serialize(n) for n in val.nodes],
            "_path_rels":  [_serialize(r) for r in val.relationships],
        }
    if isinstance(val, list):
        return [_serialize(i) for i in val]
    if isinstance(val, dict):
        return {k: _serialize(v) for k, v in val.items()}
    return val


_SCHEMA_STATEMENTS = [
    "CREATE CONSTRAINT zone_id IF NOT EXISTS FOR (z:Zone) REQUIRE z.zone_id IS UNIQUE",
    "CREATE INDEX zone_borough IF NOT EXISTS FOR (z:Zone) ON (z.borough)",
    "CREATE INDEX zone_name IF NOT EXISTS FOR (z:Zone) ON (z.zone_name)",
]


def initialize_schema() -> None:
    if not _HAS_NEO4J:
        return
    for stmt in _SCHEMA_STATEMENTS:
        try:
            run_query(stmt.strip())
        except Exception as exc:
            log.warning("Schema stmt failed (non-fatal): %s", exc)
