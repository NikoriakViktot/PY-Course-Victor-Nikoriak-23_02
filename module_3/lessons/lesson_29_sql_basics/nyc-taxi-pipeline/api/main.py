"""
api/main.py — FastAPI application entry point.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import neo4j_client, postgres_client
from api.routers import kpi, graph

log = logging.getLogger(__name__)

app = FastAPI(
    title="NYC Taxi Analytics API",
    description="Aggregated trip analytics backed by PostgreSQL + Neo4j GDS",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(kpi.router,   prefix="/api")
app.include_router(graph.router, prefix="/api")


@app.on_event("startup")
async def startup() -> None:
    log.info("Initializing Neo4j schema")
    try:
        neo4j_client.initialize_schema()
    except Exception as exc:
        log.warning("Neo4j schema init failed (non-fatal): %s", exc)


@app.on_event("shutdown")
async def shutdown() -> None:
    neo4j_client.close_driver()
    postgres_client.close_pool()


@app.get("/health")
def health() -> dict:
    return {
        "status":    "ok",
        "postgres":  postgres_client.is_available(),
        "neo4j":     neo4j_client.is_available(),
    }
