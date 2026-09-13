"""LangChain tools wrapping the read-only queries in src/database/queries/*.py.

Each tool opens its own pooled connection via ``get_db_connection()`` and
closes it before returning. Unlike the ingestion pipeline — which shares one
connection/cursor and commits once at the end of a whole run — the online
layer serves one question at a time and has no long-lived transaction to
share, so a connection per call is the right granularity here.

Every tool docstring is written for the LLM calling it, not for a human
reader of this file: it says what the tool is for and, where it matters, how
to react to an ambiguous or empty result. That behavior is part of the
project's "zero invented numbers" rule — a tool must never be a hidden
invitation to guess.
"""

from langchain_core.tools import tool

from database.connection import get_db_connection
from database.queries.admission_thresholds import (
    get_admission_threshold as _get_admission_threshold,
)
from database.queries.courses import get_course as _get_course
from database.queries.departments import get_department as _get_department
from database.queries.faculties import get_faculties as _get_faculties
from database.queries.majors import get_major as _get_major
from database.queries.office_hours import get_office_hour as _get_office_hour
from database.queries.staff import get_staff as _get_staff
from database.queries.staff_functions import get_staff_function as _get_staff_function


@tool(parse_docstring=True)
def get_faculties() -> list[dict]:
    """List every faculty this system currently has data for.

    Call this to check the system's own scope before answering a question
    about a faculty. If the one asked about isn't in the result, say you
    don't cover it instead of guessing.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            return _get_faculties(cursor)


@tool(parse_docstring=True)
def get_major(
    major_name: str,
    degree: str | None = None,
    study_mode: str | None = None,
) -> list[dict]:
    """Look up majors (kierunki) by name.

    Returns every match instead of one best guess. If more than one row comes
    back, the name alone doesn't uniquely identify a major — ask the user
    which degree/study mode they mean before answering.

    Args:
        major_name: Major name to look up (case-insensitive).
        degree: Optional filter: "bachelor-of-engineering" or "masters".
        study_mode: Optional filter: "full-time" or "part-time".
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            return _get_major(cursor, major_name, degree, study_mode)


@tool(parse_docstring=True)
def get_admission_threshold(
    major_name: str,
    year: int,
    round: int | None = None,
    degree: str | None = None,
    study_mode: str | None = None,
) -> list[dict]:
    """Look up the admission points threshold (prog punktowy) for a major in a recruitment year.

    An empty result means there is no stored threshold for that major/year —
    it may not have been offered that year, or the year may be outside the
    data the system has. Say you don't know rather than estimate a number.

    Args:
        major_name: Major name to look up (case-insensitive).
        year: Recruitment year.
        round: Optional filter on recruitment round (1 or 2).
        degree: Optional filter: "bachelor-of-engineering" or "masters".
        study_mode: Optional filter: "full-time" or "part-time".
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            return _get_admission_threshold(cursor, major_name, year, round, degree, study_mode)


@tool(parse_docstring=True)
def get_course(
    major_name: str,
    course_name: str | None = None,
    semester: int | None = None,
    is_obligatory: bool | None = None,
    is_english: bool | None = None,
) -> list[dict]:
    """Look up study-plan courses (przedmioty) for a major.

    Args:
        major_name: Major name to look up (case-insensitive).
        course_name: Optional substring filter on course name (case-insensitive).
        semester: Optional filter on semester (1..8).
        is_obligatory: Optional filter: true for obligatory, false for elective.
        is_english: Optional filter for English-taught courses.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            return _get_course(cursor, major_name, course_name, semester, is_obligatory, is_english)


@tool(parse_docstring=True)
def get_department(name: str) -> dict | None:
    """Look up one organizational unit (institute/division/dean's office) by name.

    The result includes "parent" (the unit directly above it, or null when it
    sits directly under the faculty) and "children" (its direct sub-units). A
    null result means the unit doesn't exist; an empty "children" list means
    it exists but has no sub-units — those are different and must not be
    confused.

    Args:
        name: Unit name to look up (case-insensitive).
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            return _get_department(cursor, name)


@tool(parse_docstring=True)
def get_staff(
    last_name: str,
    first_name: str | None = None,
    department: str | None = None,
) -> list[dict]:
    """Look up staff members by last name.

    Returns every match instead of one best guess. This faculty has staff
    members who share the same first and last name, so if more than one row
    comes back, ask the user to disambiguate (e.g. by department or academic
    title) before answering anything about that person — never pick one.

    Args:
        last_name: Family name to look up (case-insensitive).
        first_name: Optional exact filter on given name (case-insensitive).
        department: Optional exact filter on unit name (case-insensitive).
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            return _get_staff(cursor, last_name, first_name, department)


@tool(parse_docstring=True)
def get_staff_function(
    staff_id: int | None = None,
    function_name: str | None = None,
    department_name: str | None = None,
) -> list[dict]:
    """Look up administrative functions (e.g. who directs an institute), with the holder's staff details.

    Use function_name/department_name for "who holds function X in unit Y"
    (e.g. function_name="Dyrektor instytutu"). Use staff_id (resolved via
    get_staff) for "what functions does this person hold". A function is an
    appointed role, distinct from the person's regular employment position.

    Args:
        staff_id: Optional exact filter on the holder's staff id.
        function_name: Optional exact filter on function name (case-insensitive).
        department_name: Optional exact filter on the unit the function is held in (case-insensitive).
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            return _get_staff_function(cursor, staff_id, function_name, department_name)


@tool(parse_docstring=True)
def get_office_hour(staff_id: int, day_of_week: str | None = None) -> list[dict]:
    """Look up weekly office hours (konsultacje) for one staff member.

    Call get_staff first to resolve staff_id, and if it returned more than
    one match, ask the user to disambiguate before calling this. An empty
    result means the person has no currently published office hours — that
    is different from the person not existing, so don't say you have no
    record of them.

    Args:
        staff_id: The staff member's id, from get_staff.
        day_of_week: Optional filter on Polish weekday name (e.g. "poniedziałek").
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            return _get_office_hour(cursor, staff_id, day_of_week)


TOOLS = [
    get_faculties,
    get_major,
    get_admission_threshold,
    get_course,
    get_department,
    get_staff,
    get_staff_function,
    get_office_hour,
]
