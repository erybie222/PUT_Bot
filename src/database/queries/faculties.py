"""SQL helpers for the faculties table."""

from psycopg import Cursor as DBCursor

from database.serialization import row_to_dict


def initialize_lookups(cursor: DBCursor) -> None:
    """Insert the WIiT faculty row (idempotent).

    Args:
        cursor: DB cursor.
    """
    cursor.execute("""
        INSERT INTO faculties (symbol, name)
        VALUES ('WIiT', 'Wydział Informatyki i Telekomunikacji')
        ON CONFLICT (symbol) DO NOTHING;
    """)


def get_faculties(cursor: DBCursor) -> list[dict]:
    """List every faculty, ordered by name.

    Args:
        cursor: DB cursor.

    Returns:
        list[dict]: Rows ``(symbol, name)``.
    """
    cursor.execute("""
        SELECT symbol, name FROM faculties ORDER BY name;
    """)

    columns = ("symbol", "name")
    return [row_to_dict(columns, row) for row in cursor.fetchall()]
