"""Database connection utilities."""

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg2
from psycopg2.extensions import connection as DBConnection

from src.config import DatabaseSettings


@contextmanager
def get_db_connection() -> Iterator[DBConnection]:
    """
    Create a PostgreSQL connection wrapped in a context manager.

    Args:
        None.

    Returns:
        Iterator[DBConnection]: Open psycopg2 connection yielded for the context body.

    Raises:
        psycopg2.Error: Raised when establishing the database connection fails.
    """
    conn: DBConnection | None = None
    try:
        db_settings = DatabaseSettings()
        conn = psycopg2.connect(**db_settings.to_dict())
        yield conn
    except psycopg2.Error as exc:
        print(f"Database connection error: {exc}")
        raise
    finally:
        if conn:
            conn.close()