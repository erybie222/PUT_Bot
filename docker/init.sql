CREATE EXTENSION IF NOT EXISTS vector;
-- Lets name lookups ignore Polish diacritics ("Cyberbezpieczenstwo" finds "Cyberbezpieczeństwo").
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TABLE IF NOT EXISTS faculties (
    symbol VARCHAR(10) CONSTRAINT pk_faculties PRIMARY KEY,
    name VARCHAR(50) CONSTRAINT uk_faculty_name UNIQUE
);

CREATE TABLE IF NOT EXISTS majors (
    id SERIAL CONSTRAINT pk_majors PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    degree VARCHAR(50) NOT NULL CHECK (degree IN ('bachelor-of-engineering', 'masters')),
    study_mode VARCHAR(50) NOT NULL CHECK (study_mode IN ('full-time', 'part-time')),
    profile VARCHAR(50) NOT NULL DEFAULT 'general-academic' CHECK (profile IN ('general-academic', 'practical')),
    faculty VARCHAR(10) CONSTRAINT fk_major_faculty REFERENCES faculties(symbol),
    is_english BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uk_major UNIQUE (name, degree, study_mode)
);

CREATE TABLE IF NOT EXISTS admission_thresholds (
    id SERIAL CONSTRAINT pk_admission_thresholds PRIMARY KEY,
    major_id INT NOT NULL CONSTRAINT fk_threshold_major REFERENCES majors(id) ON DELETE CASCADE,
    year INT NOT NULL,
    round INT NOT NULL DEFAULT 1 CONSTRAINT ck_round CHECK(round BETWEEN 1 AND 2),
    min_points NUMERIC(5,2) NOT NULL,
    capacity INT NOT NULL,
    source_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_admission_thresholds UNIQUE (major_id, year, round)
);

CREATE TABLE IF NOT EXISTS courses (
    course_code VARCHAR(50) NOT NULL,
    major_id INT NOT NULL CONSTRAINT fk_course_major REFERENCES majors(id) ON DELETE CASCADE,
    semester INT NOT NULL CHECK (semester BETWEEN 1 AND 8),
    name VARCHAR(200) NOT NULL,
    is_english BOOLEAN NOT NULL DEFAULT FALSE,
    is_obligatory BOOLEAN NOT NULL DEFAULT TRUE,
    ects INT NOT NULL CHECK (ects >= 0),
    hours_lecture INT NOT NULL DEFAULT 0,
    hours_classes INT NOT NULL DEFAULT 0,
    hours_lab INT NOT NULL DEFAULT 0,
    hours_project INT NOT NULL DEFAULT 0,
    assessment_type VARCHAR(50),
    source_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- One row per catalog row: the same code (e.g. a PE elective) is listed on every
    -- major's page, and some electives in more than one semester.
    CONSTRAINT pk_courses PRIMARY KEY (course_code, major_id, semester)
);

CREATE TABLE IF NOT EXISTS departments (
    name VARCHAR(100) CONSTRAINT pk_departments PRIMARY KEY,
    symbol VARCHAR(10),
    parent VARCHAR(100) CONSTRAINT fk_department_parent REFERENCES departments(name),
    unit_type VARCHAR(50),
    description TEXT,
    faculty VARCHAR(10) NOT NULL CONSTRAINT fk_department_faculty REFERENCES faculties(symbol),
    address TEXT,
    phone VARCHAR(100),
    email VARCHAR(100),
    source_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staff (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    academic_title VARCHAR(100),
    position VARCHAR(100),
    user_type VARCHAR(50),
    department VARCHAR(100) CONSTRAINT fk_staff_department REFERENCES departments(name),
    email VARCHAR(100) CONSTRAINT uk_staff_email UNIQUE,
    phone VARCHAR(100),
    source_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staff_functions (
    id SERIAL PRIMARY KEY,
    staff_id INT NOT NULL CONSTRAINT fk_staff_functions_staff REFERENCES staff(id) ON DELETE CASCADE,
    function_name VARCHAR(150) NOT NULL,
    department_name VARCHAR(100),
    source_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- NULLS NOT DISTINCT: a function with no department_name is still a duplicate of itself.
    CONSTRAINT uk_staff_function UNIQUE NULLS NOT DISTINCT (staff_id, function_name, department_name)
);

CREATE TABLE IF NOT EXISTS office_hours (
    id SERIAL PRIMARY KEY,
    staff_id INT NOT NULL CONSTRAINT fk_office_hours_staff REFERENCES staff(id) ON DELETE CASCADE,
    day_of_week VARCHAR(20) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    location VARCHAR(100),
    comment TEXT,
    source_url TEXT,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_office_hours UNIQUE (staff_id, day_of_week, start_time)
);