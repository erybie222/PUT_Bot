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
    """Upsert a staff member keyed by e-mail.

    Args:
        cursor: DB cursor.
        first_name: Given name.
        last_name: Family name.
        academic_title: e.g. "dr hab. inż.", or None.
        position: Employment rank, e.g. "Profesor", or None.
        user_type: Informator user type, or None.
        department: FK to ``departments``, or None.
        email: Upsert key.
        phone: Phone number(s), or None.
        source_url: Card URL.

    Returns:
        int: The staff id.
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
    """Staff by last name, optionally narrowed.

    Args:
        cursor: DB cursor.
        last_name: Case-insensitive.
        first_name: Optional exact filter, case-insensitive.
        department: Optional exact unit filter, case-insensitive.

    Returns:
        list[dict]: All matches — WIiT has namesakes; the caller must ask
            rather than pick one.
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
    """Delete every staff member.

    Args:
        cursor: DB cursor.
    """
    cursor.execute("""
        DELETE FROM staff;
    """)
