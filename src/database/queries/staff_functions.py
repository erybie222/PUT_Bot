"""SQL helpers for the staff_functions table."""

from psycopg import Cursor as DBCursor


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
