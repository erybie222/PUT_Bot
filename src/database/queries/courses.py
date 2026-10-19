"""SQL helpers for the courses table."""

from psycopg import Cursor as DBCursor

from database.serialization import row_to_dict


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
    """Upsert a course by its code.

    Args:
        cursor: DB cursor.
        code: Course code (PK).
        major_id: FK to ``majors``.
        semester: Semester 1..8.
        name: Course name.
        is_obligatory: Obligatory vs elective.
        is_english: Taught in English.
        ects: ECTS points.
        w: Lecture hours.
        c: Classes hours.
        l: Lab hours.
        p: Project hours.
        form: ``assessment_type`` ("Egzamin" / "Zaliczenie z ocena").
        source_url: Course-card URL, or None.
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


def get_course(
    cursor: DBCursor,
    major_name: str,
    course_name: str | None = None,
    semester: int | None = None,
    is_obligatory: bool | None = None,
    is_english: bool | None = None,
) -> list[dict]:
    """Courses of a major, optionally filtered.

    Args:
        cursor: DB cursor.
        major_name: Major name, case-insensitive.
        course_name: Optional ILIKE substring.
        semester: Optional semester filter.
        is_obligatory: Optional obligatory/elective filter.
        is_english: Optional English-taught filter.

    Returns:
        list[dict]: Matching rows; ``[]`` if none.
    """
    course_pattern = f"%{course_name}%" if course_name is not None else None

    cursor.execute("""
        SELECT c.course_code, c.name, c.semester, c.is_obligatory, c.is_english,
               c.ects, c.hours_lecture, c.hours_classes, c.hours_lab, c.hours_project,
               c.assessment_type, c.source_url, c.last_updated
        FROM courses c
        JOIN majors m ON m.id = c.major_id
        WHERE LOWER(m.name) = LOWER(%s)
          AND (%s::text IS NULL OR c.name ILIKE %s::text)
          AND (%s::int IS NULL OR c.semester = %s::int)
          AND (%s::boolean IS NULL OR c.is_obligatory = %s::boolean)
          AND (%s::boolean IS NULL OR c.is_english = %s::boolean)
        ORDER BY c.semester, c.name;
    """, (
        major_name,
        course_pattern, course_pattern,
        semester, semester,
        is_obligatory, is_obligatory,
        is_english, is_english,
    ))

    columns = ("course_code", "name", "semester", "is_obligatory", "is_english", "ects",
               "hours_lecture", "hours_classes", "hours_lab", "hours_project",
               "assessment_type", "source_url", "last_updated")
    return [row_to_dict(columns, row) for row in cursor.fetchall()]


def delete_courses(cursor: DBCursor) -> None:
    """Delete every course.

    Args:
        cursor: DB cursor.
    """
    cursor.execute("""
        DELETE FROM courses;
    """)
