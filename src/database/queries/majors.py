"""SQL helpers for the majors table."""

from psycopg import Cursor as DBCursor


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
