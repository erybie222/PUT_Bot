"""SQL helpers for the courses table."""

from psycopg import Cursor as DBCursor


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


def delete_courses(cursor: DBCursor) -> None:
    """
    Remove all courses.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        DELETE FROM courses;
    """)
