"""SQL helpers for the office_hours table."""

from psycopg import Cursor as DBCursor

from database.serialization import row_to_dict


def delete_office_hours_by_id(cursor: DBCursor, staff_id: int) -> None:
    """Delete one person's slots before re-inserting the published set.

    Args:
        cursor: DB cursor.
        staff_id: FK to ``staff``.
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
    """Insert one weekly slot.

    Args:
        cursor: DB cursor.
        staff_id: FK to ``staff``.
        day_of_week: Polish weekday name.
        start_time: ``HH:MM``.
        end_time: ``HH:MM``.
        location: Room or "online", or None.
        comment: Per-slot note, or None.
        source_url: Card URL.
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
    """Weekly slots of one person, Monday first.

    Args:
        cursor: DB cursor.
        staff_id: Id from ``get_staff``.
        day_of_week: Optional Polish weekday filter.

    Returns:
        list[dict]: Slots; ``[]`` means none published, not "no such person".
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
    """Delete every slot.

    Args:
        cursor: DB cursor.
    """
    cursor.execute("""
        DELETE FROM office_hours;
    """)
