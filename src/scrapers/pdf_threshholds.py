import pdfplumber
from typing import Callable
from psycopg import Cursor as DBCursor
from database.queries.majors import get_major_id
from database.queries.admission_thresholds import upsert_threshold


# Column definitions for specific years
YEAR_COLUMNS = {
    2025: (1, 2),
    2024: (3, 4),
    2023: (5, 6),
    2022: (7, 8),
    2021: (9, 10)
}

def clean_number(value: str | None, output_type: Callable[[str], int | float]) -> int | float | None:
    """Cast a Polish-decimal cell (``"612,50"``) to a number.

    Args:
        value: Raw cell text.
        output_type: ``int`` or ``float``.

    Returns:
        int | float | None: The number; None for empty or ``-``.
    """
    if not value or value.strip() in ('', '-'):
        return None

    clean_value = value.replace(',', '.').strip()
    return output_type(clean_value)

def process_pdf(cursor: DBCursor, file_path: str) -> None:
    """Upsert thresholds from the PDF table; majors must already exist (matched by name).

    Args:
        cursor: DB cursor.
        file_path: Path to the thresholds PDF.
    """
    print(f"Starting PDF extraction process...")

    print(f"Opening file: {file_path}")
    with pdfplumber.open(file_path) as pdf:
        table = pdf.pages[0].extract_table()

        # Skip the header row (index 0)
        for row in table[1:]:
            raw_name = row[0]
            clean_name = raw_name.split('/')[0].strip()

            print(f"\nProcessing: {clean_name.capitalize()}")
            major_id = get_major_id(cursor, clean_name, 'bachelor-of-engineering', 'full-time')

            if not major_id:
                print(f"  -> Error: Could not resolve ID for {clean_name}")
                continue

            # Extract data for each year
            for year, (idx_capacity, idx_points) in YEAR_COLUMNS.items():
                capacity_str = row[idx_capacity]
                points_str = row[idx_points]

                capacity = clean_number(capacity_str, int)
                points = clean_number(points_str, float)

                if capacity is None or points is None:
                    continue

                # Upsert using our queries module
                upsert_threshold(
                    cursor=cursor,
                    major_id=major_id,
                    year=year,
                    points=points,
                    capacity=capacity,
                    source_url=f"PDF: {file_path}"
                )

                print(f"  -> Year {year}: Min Points = {points}, Capacity = {capacity}")

    print("\nThresholds PDF processed.")

