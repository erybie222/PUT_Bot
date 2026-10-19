"""SQL helpers for the majors table."""

from psycopg import Cursor as DBCursor

from database.serialization import row_to_dict


def upsert_major(
    cursor: DBCursor,
    major_name: str,
    degree: str,
    study_mode: str,
    profile: str,
    faculty: str,
    is_english: bool,
) -> int:
    """Upsert a major by (name, degree, study_mode).

    Args:
        cursor: DB cursor.
        major_name: Major name, capitalised as stored.
        degree: "bachelor-of-engineering" or "masters".
        study_mode: "full-time" or "part-time".
        profile: "general-academic" or "practical".
        faculty: Faculty symbol, e.g. "WIiT".
        is_english: English-taught.

    Returns:
        int: The major's id.
    """
    cursor.execute("""
        INSERT INTO majors (name, degree, study_mode, profile, faculty, is_english)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (name, degree, study_mode)
        DO UPDATE SET
            profile = EXCLUDED.profile,
            faculty = EXCLUDED.faculty,
            is_english = EXCLUDED.is_english
        RETURNING id;
    """, (major_name, degree, study_mode, profile, faculty, is_english))
    return cursor.fetchone()[0]


def get_major_id(cursor: DBCursor, major_name: str, degree: str, study_mode: str) -> int | None:
    """Ingestion-only exact lookup of a major's id.

    Args:
        cursor: DB cursor.
        major_name: Major name, case-insensitive.
        degree: Exact degree.
        study_mode: Exact study mode.

    Returns:
        int | None: The id, or None if missing.
    """
    cursor.execute("""
        SELECT id FROM majors
        WHERE LOWER(name) = LOWER(%s) AND degree = %s AND study_mode = %s;
    """, (major_name, degree, study_mode))

    result = cursor.fetchone()
    return result[0] if result else None


def get_major(
    cursor: DBCursor,
    major_name: str | None = None,
    degree: str | None = None,
    study_mode: str | None = None,
) -> list[dict]:
    """Majors by name, or every major when no name is given.

    Args:
        cursor: DB cursor.
        major_name: Major name, case-insensitive; None lists all.
        degree: Optional degree filter.
        study_mode: Optional study-mode filter.

    Returns:
        list[dict]: All matches — a name can match several rows; the caller
            must ask rather than pick one.
    """
    cursor.execute("""
        SELECT id, name, degree, study_mode, profile, faculty, is_english
        FROM majors
        WHERE (%s::text IS NULL OR LOWER(name) = LOWER(%s::text))
          AND (%s::text IS NULL OR degree = %s::text)
          AND (%s::text IS NULL OR study_mode = %s::text)
        ORDER BY name, degree, study_mode;
    """, (major_name, major_name, degree, degree, study_mode, study_mode))

    columns = ("id", "name", "degree", "study_mode", "profile", "faculty", "is_english")
    return [row_to_dict(columns, row) for row in cursor.fetchall()]


def delete_majors(cursor: DBCursor) -> None:
    """Delete every major.

    Args:
        cursor: DB cursor.
    """
    cursor.execute("""
        DELETE FROM majors;
                   """)
