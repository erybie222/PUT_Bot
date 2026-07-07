import psycopg2
from contextlib import contextmanager
from src.config import DatabaseSettings

@contextmanager
def get_db_connection():
    """
    Context manager that yields a database connection and ensures
    it is closed automatically, even if exceptions occur.
    """
    conn = None
    try:
        db_settings = DatabaseSettings()
        conn = psycopg2.connect(**db_settings.to_dict())
        yield conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()