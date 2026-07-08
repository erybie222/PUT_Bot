def initialize_lookups(cursor):
    """Ensures the WIiT faculty exists in the database."""
    cursor.execute("""
        INSERT INTO faculties (acronym, name)
        VALUES ('WIiT', 'Wydział Informatyki i Telekomunikacji')
        ON CONFLICT (acronym) DO NOTHING;
    """)

def get_or_create_major(cursor, major_name: str) -> int:
    """
    Checks if a major exists. If not, creates it (defaulting to full-time, 1st degree)
    and returns its ID.
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

def upsert_threshold(cursor, major_id: int, year: int, points: float, capacity: int, source_url: str):
    """Upserts admission threshold data into the database."""
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

def upsert_course(cursor, code: str, major_id: int, semester: int, name: str,
                  is_obligatory: bool, is_english: bool, ects: int, w: int, c: int, l: int, p: int,
                  form: str, source_url: str):
    """Upserts course (ECTS card) data into the database using the course code as the primary key."""
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