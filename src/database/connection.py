"""Process-wide psycopg3 connection pool."""

from collections.abc import Iterator
from contextlib import contextmanager
from psycopg import Connection
from psycopg_pool import ConnectionPool
from config import DatabaseSettings

_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Return the shared pool, creating it on first use.

    Returns:
        ConnectionPool: Open pool configured from ``.env``.
    """
    global _pool
    pool = _pool
    if pool is None:
        db_settings = DatabaseSettings()
        pool = ConnectionPool(
            kwargs=db_settings.to_dict(),
            min_size=1,
            max_size=10,
            open=True,
        )
        _pool = pool
    return pool


@contextmanager
def get_db_connection() -> Iterator[Connection]:
    """Borrow a pooled connection; commits on clean exit, rolls back on exception.

    Returns:
        Iterator[Connection]: The borrowed connection.
    """
    with get_pool().connection() as conn:
        yield conn


def close_pool() -> None:
    """Close the pool on shutdown; the next ``get_db_connection()`` opens a new one."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None