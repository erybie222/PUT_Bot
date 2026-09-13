"""SQL helpers for the office_hours table."""

from psycopg import Cursor as DBCursor

from database.serialization import row_to_dict


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


def get_office_hour(
    cursor: DBCursor,
    staff_id: int,
    day_of_week: str | None = None,
) -> list[dict]:
    """
    Look up weekly office-hours slots for one staff member.

    An empty list means the person currently has no published slots — distinct
    from the person not existing at all (that's an empty get_staff() result).
    Callers must not conflate the two (see eval/gold_set.yaml
    konsultacje-edge-brak-opublikowanych).

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        staff_id: Foreign key pointing to the ``staff`` table (resolved
            beforehand through get_staff).
        day_of_week: Optional case-insensitive exact filter on Polish weekday
            name (e.g. ``"poniedziałek"``).

    Returns:
        list[dict]: Matching rows (day_of_week, start_time, end_time, location,
            comment, source_url, last_updated), ordered Monday..Sunday then by
            start time; empty when nothing matches.
    """
    cursor.execute("""
        SELECT day_of_week, start_time, end_time, location, comment,
               source_url, last_updated
        FROM office_hours
        WHERE staff_id = %s
          AND (%s::text IS NULL OR LOWER(day_of_week) = LOWER(%s::text))
        ORDER BY
            CASE day_of_week
                WHEN 'poniedziałek' THEN 1
                WHEN 'wtorek' THEN 2
                WHEN 'środa' THEN 3
                WHEN 'czwartek' THEN 4
                WHEN 'piątek' THEN 5
                WHEN 'sobota' THEN 6
                WHEN 'niedziela' THEN 7
                ELSE 8
            END,
            start_time;
    """, (staff_id, day_of_week, day_of_week))

    columns = ("day_of_week", "start_time", "end_time", "location", "comment",
               "source_url", "last_updated")
    return [row_to_dict(columns, row) for row in cursor.fetchall()]


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
