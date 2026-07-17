"""SQL helper functions for data insertion and upserts."""

from psycopg import Cursor as DBCursor


def initialize_lookups(cursor: DBCursor) -> None:
    """
    Ensure base lookup records required by the project are present.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        INSERT INTO faculties (symbol, name)
        VALUES ('WIiT', 'Wydział Informatyki i Telekomunikacji')
        ON CONFLICT (symbol) DO NOTHING;
    """)

def create_major(
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
        WHERE name = %s AND degree = %s AND study_mode = %s;
    """, (major_name, degree, study_mode))

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

def upsert_department(
    cursor: DBCursor,
    name: str,
    symbol: str | None,
    parent: str | None,
    unit_type: str | None,
    faculty: str,
    address: str | None,
    phone: str | None,
    email: str | None,
    source_url: str | None,
) -> None:
    """
    Insert or update a single organizational unit (institute/division/dean's office).

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        name: Polish unit name, primary key (e.g. ``"Instytut Informatyki"``).
        symbol: Unit symbol from the source (e.g. ``"II"``); NOT unique — divisions
            share the symbol of their institute. Can be None when unavailable.
        parent: Name of the parent unit within the same faculty, or None for units
            directly under the faculty (institutes, dean's office).
        unit_type: Unit type label from the source (e.g. ``"instytut"``, ``"zakład"``).
        faculty: Symbol of the faculty the unit belongs to (e.g. ``"WIiT"``).
        address: Postal address of the unit; can be None when unavailable.
        phone: Office phone number(s); can be None when unavailable.
        email: Office e-mail address; can be None when unavailable.
        source_url: Source reference used for provenance tracking.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        INSERT INTO departments (name, symbol, parent, unit_type, faculty, address, phone, email, source_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (name)
        DO UPDATE SET
            symbol = EXCLUDED.symbol,
            parent = EXCLUDED.parent,
            unit_type = EXCLUDED.unit_type,
            faculty = EXCLUDED.faculty,
            address = EXCLUDED.address,
            phone = EXCLUDED.phone,
            email = EXCLUDED.email,
            source_url = EXCLUDED.source_url,
            last_updated = CURRENT_TIMESTAMP;
    """, (name, symbol, parent, unit_type, faculty, address, phone, email, source_url))

def upsert_staff(
    cursor: DBCursor,
    first_name: str,
    last_name: str,
    academic_title: str | None,
    department: str | None,
    email: str,
    phone: str | None,
    source_url: str,
) -> int:
    """
    Insert or update a staff member record and return its ID.

    Identity is the (unique) university e-mail address.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        first_name: Given name(s) of the staff member.
        last_name: Family name of the staff member.
        academic_title: Academic title prefix (e.g. ``"dr hab. inż."``); can be None.
        department: Name of the unit the member belongs to (FK to ``departments``); can be None.
        email: University e-mail address, used as the natural key for upserts.
        phone: Phone number(s); can be None when unavailable.
        source_url: URL of the source business card used for provenance tracking.

    Returns:
        int: The ID of the created or existing staff record.
    """
    cursor.execute("""
        INSERT INTO staff
        (first_name, last_name, academic_title, department, email, phone, source_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (email)
        DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            academic_title = EXCLUDED.academic_title,
            department = EXCLUDED.department,
            phone = EXCLUDED.phone,
            source_url = EXCLUDED.source_url,
            last_updated = CURRENT_TIMESTAMP
        RETURNING id;
    """, (first_name, last_name, academic_title, department, email, phone, source_url))
    return cursor.fetchone()[0]

def delete_office_hours(cursor: DBCursor, staff_id: int) -> None:
    """
    Remove all office hours of one staff member.

    Used before re-inserting the currently published set, so office hours
    removed at the source disappear from the database as well.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        staff_id: Foreign key pointing to the ``staff`` table.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        DELETE FROM office_hours
        WHERE staff_id = %s;
    """, (staff_id,))

def insert_office_hour(
    cursor: DBCursor,
    staff_id: int,
    day_of_week: str,
    start_time: str,
    end_time: str,
    location: str | None,
    source_url: str,
) -> None:
    """
    Insert a single weekly office-hours slot for a staff member.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        staff_id: Foreign key pointing to the ``staff`` table.
        day_of_week: Polish weekday name (e.g. ``"poniedziałek"``).
        start_time: Slot start in ``HH:MM`` format.
        end_time: Slot end in ``HH:MM`` format.
        location: Building/room or ``"online"``; can be None when unavailable.
        source_url: URL of the source business card used for provenance tracking.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        INSERT INTO office_hours
        (staff_id, day_of_week, start_time, end_time, location, source_url)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (staff_id, day_of_week, start_time) DO NOTHING;
    """, (staff_id, day_of_week, start_time, end_time, location, source_url))