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


def get_course(
    cursor: DBCursor,
    major_name: str,
    course_name: str | None = None,
    semester: int | None = None,
    is_obligatory: bool | None = None,
    is_english: bool | None = None,
) -> dict:
    """
    Look up courses for a major, optionally narrowed by name/semester/type.

    Returns the matching rows together with their summed ECTS points.
    An empty result means no course is stored for that major — either because the major wasn't offered that semester or because the semester is outside WIiT's scope.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        major_name: Major name, matched case-insensitively.
        course_name: Optional case-insensitive substring filter on course name.
        semester: Optional exact filter on semester (1..8).
        is_obligatory: Optional exact filter on obligatory vs elective.
        is_english: Optional exact filter on English-taught courses.

    Returns:
        dict: ``{"courses": [...], "total_ects": int}`` — each course row has
            course_code, name, semester, is_obligatory, is_english, ects,
            hours_lecture, hours_classes, hours_lab, hours_project,
            assessment_type, source_url, last_updated. Empty list/zero total
            when nothing matches.
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
    courses = [row_to_dict(columns, row) for row in cursor.fetchall()]
    return {"courses": courses, "total_ects": sum(c["ects"] for c in courses)}


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
