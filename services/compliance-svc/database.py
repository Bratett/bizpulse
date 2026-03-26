import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor

from config import settings

_pool = None


def get_pool():
    """Get or create the connection pool (read-write)."""
    global _pool
    if _pool is None or _pool.closed:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=settings.database_url,
        )
    return _pool


def get_connection():
    """Get a read-write database connection from the pool."""
    return get_pool().getconn()


def release_connection(conn):
    """Return a connection to the pool."""
    pool = get_pool()
    if pool and not pool.closed:
        pool.putconn(conn)


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a read query and return results as dicts."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    finally:
        release_connection(conn)


def execute_in_transaction(operations: list[tuple[str, tuple]]) -> None:
    """Execute multiple SQL statements in a single transaction.

    Each operation is a (sql, params) tuple. All succeed or all fail.
    Used for compute and filing operations that must be atomic.
    """
    conn = get_connection()
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            for sql, params in operations:
                cur.execute(sql, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.autocommit = True
        release_connection(conn)


def query_single(sql: str, params: tuple = ()) -> dict | None:
    """Execute a query and return the first row, or None."""
    results = query(sql, params)
    return results[0] if results else None
