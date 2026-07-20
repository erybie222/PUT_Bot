"""SQL helpers for the office_hours table."""

from psycopg import Cursor as DBCursor


def delete_office_hours_by_id(cursor: DBCursor, staff_id: int) -> None:
    """
    Remove all office hours of one staff member.

    Used before re-inserting the currently published set, so office hours
    removed at the source disappear from the database as well.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        staff_id: Foreign key pointing to the ``staff`` table.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        DELETE FROM office_hours
        WHERE staff_id = %s;
    """, (staff_id,))


def insert_office_hour(
    cursor: DBCursor,
    staff_id: int,
    day_of_week: str,
    start_time: str,
    end_time: str,
    location: str | None,
    comment: str | None,
    source_url: str,
) -> None:
    """
    Insert a single weekly office-hours slot for a staff member.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        staff_id: Foreign key pointing to the ``staff`` table.
        day_of_week: Polish weekday name (e.g. ``"poniedziałek"``).
        start_time: Slot start in ``HH:MM`` format.
        end_time: Slot end in ``HH:MM`` format.
        location: Building/room or ``"online"``; can be None when unavailable.
        source_url: URL of the source business card used for provenance tracking.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        INSERT INTO office_hours
        (staff_id, day_of_week, start_time, end_time, location, comment ,source_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (staff_id, day_of_week, start_time) DO NOTHING;
    """, (staff_id, day_of_week, start_time, end_time, location,comment, source_url))


def delete_office_hours(cursor: DBCursor) -> None:
    """
    Remove all office hours.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        DELETE FROM office_hours;
    """)
