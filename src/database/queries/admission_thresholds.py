"""SQL helpers for the admission_thresholds table."""

from psycopg import Cursor as DBCursor


def upsert_threshold(
    cursor: DBCursor,
    major_id: int,
    year: int,
    points: float,
    capacity: int,
    source_url: str,
) -> None:
    """
    Insert or update a single admission threshold record.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        major_id: Foreign key pointing to the ``majors`` table.
        year: Admission year for the threshold record.
        points: Minimum admission points for the given year/round.
        capacity: Number of available places for the given year/round.
        source_url: Source reference used for provenance tracking.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        INSERT INTO admission_thresholds
        (major_id, year, round, min_points, capacity, source_url)
        VALUES (%s, %s, 1, %s, %s, %s)
        ON CONFLICT (major_id, year, round)
        DO UPDATE SET
            min_points = EXCLUDED.min_points,
            capacity = EXCLUDED.capacity,
            last_updated = CURRENT_TIMESTAMP;
    """, (major_id, year, points, capacity, source_url))


def delete_admission_thresholds(cursor: DBCursor) -> None:
    """
        Remove all admission thresholds.

        Args:
            cursor: Open PostgreSQL cursor used to execute SQL statements.

        Returns:
            None: This function performs database side effects only.
        """
    cursor.execute("""
        DELETE FROM admission_thresholds;
                   """)
