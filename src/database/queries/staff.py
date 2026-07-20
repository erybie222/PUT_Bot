"""SQL helpers for the staff table."""

from psycopg import Cursor as DBCursor


def upsert_staff(
    cursor: DBCursor,
    first_name: str,
    last_name: str,
    academic_title: str | None,
    department: str | None,
    email: str,
    phone: str | None,
    source_url: str,
) -> int:
    """
    Insert or update a staff member record and return its ID.

    Identity is the (unique) university e-mail address.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        first_name: Given name(s) of the staff member.
        last_name: Family name of the staff member.
        academic_title: Academic title prefix (e.g. ``"dr hab. inż."``); can be None.
        department: Name of the unit the member belongs to (FK to ``departments``); can be None.
        email: University e-mail address, used as the natural key for upserts.
        phone: Phone number(s); can be None when unavailable.
        source_url: URL of the source business card used for provenance tracking.

    Returns:
        int: The ID of the created or existing staff record.
    """
    cursor.execute("""
        INSERT INTO staff
        (first_name, last_name, academic_title, department, email, phone, source_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (email)
        DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            academic_title = EXCLUDED.academic_title,
            department = EXCLUDED.department,
            phone = EXCLUDED.phone,
            source_url = EXCLUDED.source_url,
            last_updated = CURRENT_TIMESTAMP
        RETURNING id;
    """, (first_name, last_name, academic_title, department, email, phone, source_url))
    return cursor.fetchone()[0]


def delete_staff(cursor: DBCursor) -> None:
    """
    Remove all staff members.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        DELETE FROM staff;
    """)
