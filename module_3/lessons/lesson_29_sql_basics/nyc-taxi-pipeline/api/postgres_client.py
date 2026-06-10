"""
api/postgres_client.py — PostgreSQL connection pool for the API.

Uses psycopg2 SimpleConnectionPool.  All callers get a connection from the
pool, execute their query, and return it.  Never leave connections open across
request boundaries.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Generator

import psycopg2
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor

log = logging.getLogger(__name__)

_pool: SimpleConnectionPool | None = None


def _dsn() -> str:
    return (
        f"host={os.getenv('POSTGRES_HOST','localhost')} "
        f"port={os.getenv('POSTGRES_PORT','5432')} "
        f"dbname={os.getenv('POSTGRES_DB','nyc_taxi')} "
        f"user={os.getenv('POSTGRES_USER','taxi')} "
        f"password={os.getenv('POSTGRES_PASSWORD','')}"
    )


def get_pool() -> SimpleConnectionPool:
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=_dsn())
        log.info("Postgres pool created")
    return _pool


def close_pool() -> None:
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None


def is_available() -> bool:
    try:
        with cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False


@contextmanager
def cursor() -> Generator[RealDictCursor, None, None]:
    """Yield a RealDictCursor, return the connection to the pool when done."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def fetchall(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    with cursor() as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]


def fetchone(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    with cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None
