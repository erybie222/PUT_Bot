"""SQL helpers for the admission_thresholds table."""

from psycopg import Cursor as DBCursor

from database.serialization import row_to_dict


def upsert_threshold(
    cursor: DBCursor,
    major_id: int,
    year: int,
    points: float,
    capacity: int,
    source_url: str,
) -> None:
    """Upsert a round-1 threshold.

    Args:
        cursor: DB cursor.
        major_id: FK to ``majors``; must already exist.
        year: Recruitment year.
        points: Minimum points.
        capacity: Number of places.
        source_url: Provenance (``"PDF: <path>"``).
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


def get_admission_threshold(
    cursor: DBCursor,
    major_name: str,
    year: int,
    round: int | None = None,
    degree: str | None = None,
    study_mode: str | None = None,
) -> list[dict]:
    """Thresholds for a major in one year.

    Args:
        cursor: DB cursor.
        major_name: Major name, case-insensitive.
        year: Recruitment year.
        round: Optional round filter (1 or 2).
        degree: Optional degree filter.
        study_mode: Optional study-mode filter.

    Returns:
        list[dict]: Matching rows; ``[]`` if none stored.
    """
    cursor.execute("""
        SELECT m.name, m.degree, m.study_mode, t.year, t.round,
               t.min_points, t.capacity, t.source_url, t.last_updated
        FROM admission_thresholds t
        JOIN majors m ON m.id = t.major_id
        WHERE LOWER(m.name) = LOWER(%s)
          AND t.year = %s
          AND (%s::int IS NULL OR t.round = %s::int)
          AND (%s::text IS NULL OR m.degree = %s::text)
          AND (%s::text IS NULL OR m.study_mode = %s::text)
        ORDER BY t.round;
    """, (major_name, year, round, round, degree, degree, study_mode, study_mode))

    columns = ("major_name", "degree", "study_mode", "year", "round",
               "min_points", "capacity", "source_url", "last_updated")
    return [row_to_dict(columns, row) for row in cursor.fetchall()]


def delete_admission_thresholds(cursor: DBCursor) -> None:
    """Delete every threshold.

    Args:
        cursor: DB cursor.
    """
    cursor.execute("""
        DELETE FROM admission_thresholds;
                   """)
