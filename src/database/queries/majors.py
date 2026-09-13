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
    """
    Create a new major record and return its ID.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        major_name: Normalized major name (e.g. ``"informatyka"``).
        degree: Degree of the major. (bachelor-of-engineering/masters)
        study_mode: Study mode of the major. (full-time/part-time)
        profile: Profile name of the major (general-academic / practical),
        faculty: Symbol of the faculty for the major. (e.g. WIiT ),
        is_english: Whether the major conducted in english.

    Returns:
        int: The ID of the created or existing major.
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
    """
    Get a major's ID.

   Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        major_name: Normalized major name (e.g. : ``"informatyka"``).
        degree: Degree of the major. (bachelor-of-engineering/masters)
        study_mode: Study mode of the major. (full-time/part-time)

    Returns:
        int | None: The ID of the  major, or None when it does not exist.
    """
    cursor.execute("""
        SELECT id FROM majors
        WHERE LOWER(name) = LOWER(%s) AND degree = %s AND study_mode = %s;
    """, (major_name, degree, study_mode))

    result = cursor.fetchone()
    return result[0] if result else None


def get_major(
    cursor: DBCursor,
    major_name: str,
    degree: str | None = None,
    study_mode: str | None = None,
) -> list[dict]:
    """
    Look up majors by (case-insensitive) name, optionally narrowed by degree/study mode.

    Returns every matching row instead of guessing one: majors are unique by
    (name, degree, study_mode), so a name-only lookup can legitimately return
    more than one row and the caller must handle that (e.g. by asking the user
    to disambiguate) rather than picking the first result.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        major_name: Major name to look up, matched case-insensitively.
        degree: Optional exact filter on degree (bachelor-of-engineering/masters).
        study_mode: Optional exact filter on study mode (full-time/part-time).

    Returns:
        list[dict]: Matching rows (id, name, degree, study_mode, profile,
            faculty, is_english), empty when nothing matches.
    """
    cursor.execute("""
        SELECT id, name, degree, study_mode, profile, faculty, is_english
        FROM majors
        WHERE LOWER(name) = LOWER(%s)
          AND (%s::text IS NULL OR degree = %s::text)
          AND (%s::text IS NULL OR study_mode = %s::text)
        ORDER BY name, degree, study_mode;
    """, (major_name, degree, degree, study_mode, study_mode))

    columns = ("id", "name", "degree", "study_mode", "profile", "faculty", "is_english")
    return [row_to_dict(columns, row) for row in cursor.fetchall()]


def delete_majors(cursor: DBCursor) -> None:
    """
        Remove all majors.

        Args:
            cursor: Open PostgreSQL cursor used to execute SQL statements.

        Returns:
            None: This function performs database side effects only.
        """
    cursor.execute("""
        DELETE FROM majors;
                   """)
