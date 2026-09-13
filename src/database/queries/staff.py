"""SQL helpers for the staff table."""

from psycopg import Cursor as DBCursor

from database.serialization import row_to_dict


def upsert_staff(
    cursor: DBCursor,
    first_name: str,
    last_name: str,
    academic_title: str | None,
    position: str | None,
    user_type: str | None,
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
        position: Employment position/rank (e.g. ``"Profesor"``, ``"Adiunkt"``); can be None.
        user_type: Informator user type (e.g. ``"employee_educational"``); can be None.
        department: Name of the unit the member belongs to (FK to ``departments``); can be None.
        email: University e-mail address, used as the natural key for upserts.
        phone: Phone number(s); can be None when unavailable.
        source_url: URL of the source business card used for provenance tracking.

    Returns:
        int: The ID of the created or existing staff record.
    """
    cursor.execute("""
        INSERT INTO staff
        (first_name, last_name, academic_title, position, user_type, department, email, phone, source_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (email)
        DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            academic_title = EXCLUDED.academic_title,
            position = EXCLUDED.position,
            user_type = EXCLUDED.user_type,
            department = EXCLUDED.department,
            phone = EXCLUDED.phone,
            source_url = EXCLUDED.source_url,
            last_updated = CURRENT_TIMESTAMP
        RETURNING id;
    """, (first_name, last_name, academic_title, position, user_type, department, email, phone, source_url))
    return cursor.fetchone()[0]


def get_staff(
    cursor: DBCursor,
    last_name: str,
    first_name: str | None = None,
    department: str | None = None,
) -> list[dict]:
    """
    Look up staff members by (case-insensitive) last name, optionally narrowed
    by first name and/or department.

    Returns every match instead of guessing one: WIiT has staff sharing the
    same first and last name , so callers must handle
    more than one row (e.g. by asking the user to disambiguate by department
    or title) rather than picking the first result.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        last_name: Family name to look up, matched case-insensitively.
        first_name: Optional case-insensitive exact filter on given name.
        department: Optional case-insensitive exact filter on unit name.

    Returns:
        list[dict]: Matching rows (id, first_name, last_name, academic_title,
            position, user_type, department, email, phone, source_url), empty
            when nothing matches.
    """
    cursor.execute("""
        SELECT id, first_name, last_name, academic_title, position, user_type,
               department, email, phone, source_url
        FROM staff
        WHERE LOWER(last_name) = LOWER(%s)
          AND (%s::text IS NULL OR LOWER(first_name) = LOWER(%s::text))
          AND (%s::text IS NULL OR LOWER(department) = LOWER(%s::text))
        ORDER BY first_name, last_name;
    """, (last_name, first_name, first_name, department, department))

    columns = ("id", "first_name", "last_name", "academic_title", "position",
               "user_type", "department", "email", "phone", "source_url")
    return [row_to_dict(columns, row) for row in cursor.fetchall()]


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
