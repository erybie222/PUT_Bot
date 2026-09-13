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
    """
    Insert a single function (administrative role) held by a staff member.

    A function is an appointed role (e.g. ``"Dyrektor instytutu"``) within a
    unit — distinct from ``staff.position`` (employment rank) and from
    ``staff.department`` (where the person works).

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        staff_id: Foreign key pointing to the ``staff`` table.
        function_name: Role name (e.g. ``"Kierownik zakładu"``).
        department_name: Unit the role is held in (e.g. ``"Instytut Informatyki"``);
            stored as plain text — the role's unit may lie outside WIiT, so it is
            not constrained by a foreign key. Can be None when unavailable.
        source_url: URL of the source business card used for provenance tracking.

    Returns:
        None: This function performs database side effects only.
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
    """
    Look up administrative functions, joined with the holder's staff record.

    Supports both directions of the lookup: "who holds function X in unit Y"
    (via function_name / department_name) and "what functions does person Z
    hold" (via staff_id, resolved beforehand through get_staff).

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        staff_id: Optional exact filter on the holder (FK to ``staff``).
        function_name: Optional case-insensitive exact filter on function name
            (e.g. ``"Dyrektor instytutu"``).
        department_name: Optional case-insensitive exact filter on the unit the
            function is held in.

    Returns:
        list[dict]: Matching rows (function_name, department_name, source_url,
            last_updated, staff_id, first_name, last_name, academic_title,
            position, email), empty when nothing matches.
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
    """
    Remove all staff functions.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        DELETE FROM staff_functions;
    """)
