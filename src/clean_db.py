from database.queries.majors import delete_majors
from database.queries.staff import delete_staff
from database.queries.departments import delete_departments
from database.queries.courses import delete_courses
from database.queries.admission_thresholds import delete_admission_thresholds
from database.queries.office_hours import delete_office_hours
from database.queries.staff_functions import delete_staff_functions
from database.connection import get_db_connection, close_pool

def clean_db() -> None:
    """Clean the database."""
    print("Cleaning database...")
    try:
        with get_db_connection() as connection:
                print("Connected to database.")
                cursor = connection.cursor()
                delete_office_hours(cursor)
                delete_staff_functions(cursor)
                delete_staff(cursor)
                delete_departments(cursor)
                delete_courses(cursor)
                delete_admission_thresholds(cursor)
                delete_majors(cursor)
                print("Done.")
    except Exception as e:
        print(e)
        print("Error while cleaning database.")
    finally:
        close_pool()

if __name__ == "__main__":
    clean_db()