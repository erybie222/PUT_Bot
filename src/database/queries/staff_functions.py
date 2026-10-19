"""SQL helpers for the staff_functions table."""

from psycopg import Cursor as DBCursor

from database.serialization import row_to_dict


def insert_staff_function(
    cursor: DBCursor,
    staff_id: int,
    function_name: str,
    department_name: str | None,
    source_url: str,
) -> None:
    """Insert an appointed role (e.g. "Dyrektor instytutu").

    Args:
        cursor: DB cursor.
        staff_id: FK to ``staff``.
        function_name: Role name.
        department_name: Unit as plain text (may lie outside WIiT, so no FK), or None.
        source_url: Card URL.
    """
    cursor.execute("""
        INSERT INTO staff_functions
        (staff_id, function_name, department_name, source_url)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (staff_id, function_name, department_name) DO NOTHING;
    """, (staff_id, function_name, department_name, source_url))


def get_staff_function(
    cursor: DBCursor,
    staff_id: int | None = None,
    function_name: str | None = None,
    department_name: str | None = None,
) -> list[dict]:
    """Functions joined with their holder.

    Args:
        cursor: DB cursor.
        staff_id: Optional holder filter.
        function_name: Optional exact filter, case-insensitive.
        department_name: Optional exact unit filter, case-insensitive.

    Returns:
        list[dict]: Matching rows; ``[]`` if none.
    """
    cursor.execute("""
        SELECT sf.function_name, sf.department_name, sf.source_url, sf.last_updated,
               s.id, s.first_name, s.last_name, s.academic_title, s.position, s.email
        FROM staff_functions sf
        JOIN staff s ON s.id = sf.staff_id
        WHERE (%s::int IS NULL OR sf.staff_id = %s::int)
          AND (%s::text IS NULL OR LOWER(sf.function_name) = LOWER(%s::text))
          AND (%s::text IS NULL OR LOWER(sf.department_name) = LOWER(%s::text))
        ORDER BY s.last_name, s.first_name;
    """, (
        staff_id, staff_id,
        function_name, function_name,
        department_name, department_name,
    ))

    columns = ("function_name", "department_name", "source_url", "last_updated",
               "staff_id", "first_name", "last_name", "academic_title", "position", "email")
    return [row_to_dict(columns, row) for row in cursor.fetchall()]


def delete_staff_functions(cursor: DBCursor) -> None:
    """Delete every staff function.

    Args:
        cursor: DB cursor.
    """
    cursor.execute("""
        DELETE FROM staff_functions;
    """)
