"""SQL helpers for the faculties table."""

from psycopg import Cursor as DBCursor

from database.serialization import row_to_dict


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


def get_faculties(cursor: DBCursor) -> list[dict]:
    """
    List every faculty currently supported by the project.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.

    Returns:
        list[dict]: All rows (symbol, name), ordered by name.
    """
    cursor.execute("""
        SELECT symbol, name FROM faculties ORDER BY name;
    """)

    columns = ("symbol", "name")
    return [row_to_dict(columns, row) for row in cursor.fetchall()]
