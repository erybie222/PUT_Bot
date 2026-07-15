"""Database connection utilities built on a process-wide psycopg3 connection pool."""

from collections.abc import Iterator
from contextlib import contextmanager

from psycopg import Connection
from psycopg_pool import ConnectionPool

from src.config import DatabaseSettings

# Single pool shared by the whole process; created lazily on first use.
_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """
    Return the process-wide connection pool, creating it on first use.

    Args:
        None.

    Returns:
        ConnectionPool: Open psycopg3 pool configured from environment settings.

    Raises:
        psycopg.OperationalError: Raised when the pool cannot reach the database.
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
    """
    Borrow a PostgreSQL connection from the pool for the duration of the context.

    The connection is returned to the pool on exit instead of being closed,
    so repeated calls (e.g. from bot tools) reuse existing connections.
    On a clean exit the transaction is committed; on an exception it is
    rolled back — both handled by the pool.

    Args:
        None.

    Returns:
        Iterator[Connection]: Pooled psycopg3 connection yielded for the context body.

    Raises:
        psycopg.Error: Raised when acquiring a connection from the pool fails.
    """
    with get_pool().connection() as conn:
        yield conn


def close_pool() -> None:
    """
    Close the process-wide pool and all its connections.

    Call once on application shutdown; afterwards a new pool is created
    on the next ``get_db_connection()`` call.

    Args:
        None.

    Returns:
        None: This function performs connection cleanup side effects only.
    """
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None