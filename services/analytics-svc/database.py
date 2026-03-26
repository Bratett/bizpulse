import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor

from config import settings

_pool = None


def get_connection():
    """Get a database connection using the read-only role (thread-safe)."""
    global _pool
    if _pool is None or _pool.closed:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            dsn=settings.database_url,
        )
    conn = _pool.getconn()
    conn.set_session(readonly=True, autocommit=True)
    return conn


def release_connection(conn):
    """Return a connection to the pool."""
    global _pool
    if _pool and not _pool.closed:
        _pool.putconn(conn)


def query(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a read-only query and return results as dicts."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]
    finally:
        release_connection(conn)
