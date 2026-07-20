"""SQL helpers for the faculties table."""

from psycopg import Cursor as DBCursor


def initialize_lookups(cursor: DBCursor) -> None:
    """
    Ensure base lookup records required by the project are present.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        INSERT INTO faculties (symbol, name)
        VALUES ('WIiT', 'Wydział Informatyki i Telekomunikacji')
        ON CONFLICT (symbol) DO NOTHING;
    """)
