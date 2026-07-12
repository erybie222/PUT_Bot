"""SQL helper functions for data insertion and upserts."""

from psycopg2.extensions import cursor as DBCursor


def initialize_lookups(cursor: DBCursor) -> None:
    """
    Ensure base lookup records required by the project are present.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        INSERT INTO faculties (acronym, name)
        VALUES ('WIiT', 'Wydział Informatyki i Telekomunikacji')
        ON CONFLICT (acronym) DO NOTHING;
    """)

def get_or_create_major(cursor: DBCursor, major_name: str) -> int | None:
    """
    Get a major ID by name, creating the major if it does not exist.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        major_name: Normalized major name (for example: ``"informatyka"``).

    Returns:
        int | None: Existing or newly created major ID, or None when it cannot be resolved.
    """
    cursor.execute("""
        INSERT INTO majors (name, degree, study_mode, faculty)
        VALUES (%s, 1, 'full-time', 'WIiT')
        ON CONFLICT (name, degree, study_mode) DO NOTHING;
    """, (major_name,))

    cursor.execute("""
        SELECT id FROM majors
        WHERE name = %s AND degree = 1 AND study_mode = 'full-time';
    """, (major_name,))

    result = cursor.fetchone()
    return result[0] if result else None

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

def upsert_course(
    cursor: DBCursor,
    code: str,
    major_id: int,
    semester: int,
    name: str,
    is_obligatory: bool,
    is_english: bool,
    ects: int,
    w: int,
    c: int,
    l: int,
    p: int,
    form: str,
    source_url: str | None,
) -> None:
    """
    Insert or update a course row from the ECTS catalog.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        code: Unique course code used as a primary key.
        major_id: Foreign key pointing to the ``majors`` table.
        semester: Semester number in range 1..8.
        name: Human-readable course name.
        is_obligatory: Flag indicating obligatory vs elective status.
        is_english: Flag indicating whether the course is taught in English.
        ects: Number of ECTS points assigned to the course.
        w: Number of lecture hours.
        c: Number of exercise hours.
        l: Number of laboratory hours.
        p: Number of project hours.
        form: Assessment type label (for example: exam/pass).
        source_url: URL to course source document; can be None when unavailable.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        INSERT INTO courses 
        (course_code, major_id, semester, name, is_obligatory, is_english, ects, 
         hours_lecture, hours_classes, hours_lab, hours_project, assessment_type, source_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (course_code) 
        DO UPDATE SET 
            semester = EXCLUDED.semester,
            name = EXCLUDED.name,
            is_obligatory = EXCLUDED.is_obligatory,
            is_english = EXCLUDED.is_english,
            ects = EXCLUDED.ects,
            hours_lecture = EXCLUDED.hours_lecture,
            hours_classes = EXCLUDED.hours_classes,
            hours_lab = EXCLUDED.hours_lab,
            hours_project = EXCLUDED.hours_project,
            assessment_type = EXCLUDED.assessment_type,
            source_url = EXCLUDED.source_url,
            last_updated = CURRENT_TIMESTAMP;
    """, (code, major_id, semester, name, is_obligatory, is_english, ects, w, c, l, p, form, source_url))