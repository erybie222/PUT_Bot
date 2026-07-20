"""SQL helpers for the departments table."""

from psycopg import Cursor as DBCursor


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


def delete_departments(cursor: DBCursor) -> None:
    """
    Remove all departments.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.

    Returns:
        None: This function performs database side effects only.
    """
    cursor.execute("""
        DELETE FROM departments;
    """)
