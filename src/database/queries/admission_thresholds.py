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


def get_admission_threshold(
    cursor: DBCursor,
    major_name: str,
    year: int,
    round: int | None = None,
    degree: str | None = None,
    study_mode: str | None = None,
) -> list[dict]:
    """
    Look up admission threshold(s) for a major in a given recruitment year.

    An empty result means no threshold is stored for that major/year — either
    because the major wasn't offered that year, is outside WIiT's scope, or the
    year is in the future. Callers must answer "I don't know" rather than
    extrapolate (see eval/gold_set.yaml prog-edge-* cases).

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        major_name: Major name, matched case-insensitively.
        year: Recruitment year to look up.
        round: Optional exact filter on recruitment round (1 or 2).
        degree: Optional exact filter on the major's degree.
        study_mode: Optional exact filter on the major's study mode.

    Returns:
        list[dict]: Matching rows (major_name, degree, study_mode, year, round,
            min_points, capacity, source_url, last_updated), empty when nothing
            matches.
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
