"""SQL helpers for the departments table."""

from psycopg import Cursor as DBCursor

from database.serialization import row_to_dict


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
    """Upsert a unit inside a faculty, keyed by its Polish name.

    Args:
        cursor: DB cursor.
        name: Unit name (PK).
        symbol: Source symbol; not unique (a zakład shares its institute's).
        parent: Parent unit name; None directly under the faculty.
        unit_type: e.g. "instytut", "zakład".
        faculty: Faculty symbol, e.g. "WIiT".
        address: Postal address, or None.
        phone: Phone number(s), or None.
        email: Office e-mail, or None.
        source_url: Provenance URL.
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


def get_department(cursor: DBCursor, name: str) -> dict | None:
    """One unit plus its direct sub-units.

    Args:
        cursor: DB cursor.
        name: Unit name, case-insensitive.

    Returns:
        dict | None: Unit row with ``children``; None if no such unit.
            ``children: []`` means it exists without sub-units — don't conflate.
    """
    cursor.execute("""
        SELECT name, symbol, parent, unit_type, faculty, address, phone, email,
               source_url, last_updated
        FROM departments
        WHERE LOWER(name) = LOWER(%s);
    """, (name,))

    row = cursor.fetchone()
    if row is None:
        return None

    columns = ("name", "symbol", "parent", "unit_type", "faculty", "address",
               "phone", "email", "source_url", "last_updated")
    department = row_to_dict(columns, row)

    cursor.execute("""
        SELECT name FROM departments WHERE LOWER(parent) = LOWER(%s) ORDER BY name;
    """, (department["name"],))
    department["children"] = [child[0] for child in cursor.fetchall()]

    return department


def delete_departments(cursor: DBCursor) -> None:
    """Delete every unit.

    Args:
        cursor: DB cursor.
    """
    cursor.execute("""
        DELETE FROM departments;
    """)
