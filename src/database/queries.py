def initialize_lookups(cursor):
    """Ensures the WIiT faculty exists in the database."""
    cursor.execute("""
                   INSERT INTO wydzialy_uczelni (akronim, nazwa)
                   VALUES ('WIiT', 'Wydział Informatyki i Telekomunikacji') ON CONFLICT (akronim) DO NOTHING;
                   """)


def get_or_create_major(cursor, major_name: str) -> int:
    """
    Checks if a major exists. If not, creates it (defaulting to full-time, 1st degree)
    and returns its artificial ID.
    """
    cursor.execute("""
                   INSERT INTO kierunki_studiow (nazwa, stopien, tryb, wydzial)
                   VALUES (%s, 1, 'stacjonarne', 'WIiT') ON CONFLICT (nazwa, stopien, tryb) DO NOTHING;
                   """, (major_name,))

    cursor.execute("""
                   SELECT id
                   FROM kierunki_studiow
                   WHERE nazwa = %s
                     AND stopien = 1
                     AND tryb = 'stacjonarne';
                   """, (major_name,))

    result = cursor.fetchone()
    return result[0] if result else None


def upsert_threshold(cursor, major_id: int, year: int, points: float, limit: int, source_url: str):
    """Upserts admission threshold data into the database."""
    cursor.execute("""
                   INSERT INTO progi_punktowe
                       (id_kierunku, rok, tura, min_l_pkt, limit_przyjec, source_url)
                   VALUES (%s, %s, 1, %s, %s, %s) ON CONFLICT (id_kierunku, rok, tura) 
        DO
                   UPDATE SET
                       min_l_pkt = EXCLUDED.min_l_pkt,
                       limit_przyjec = EXCLUDED.limit_przyjec,
                       last_updated = CURRENT_TIMESTAMP;
                   """, (major_id, year, points, limit, source_url))