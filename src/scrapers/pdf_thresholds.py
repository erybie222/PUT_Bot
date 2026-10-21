"""Scraper for the admission thresholds PDF published by the university.

The PDF has one table on its first page: one row per major, and for each of
the last five recruitment years two columns — number of places and minimum
points. Only the first recruitment round is listed.

Majors are matched to the database by name, so they must be ingested first.
"""

import pdfplumber
from typing import Callable
from psycopg import Cursor as DBCursor
from database.queries.majors import get_major_id
from database.queries.admission_thresholds import upsert_threshold


# Year -> (capacity column, min-points column) in the PDF table. Column 0 is the
# major name. Update when a new PDF shifts the year range.
YEAR_COLUMNS = {
    2025: (1, 2),
    2024: (3, 4),
    2023: (5, 6),
    2022: (7, 8),
    2021: (9, 10)
}

def parse_polish_number(value: str | None, output_type: Callable[[str], int | float]) -> int | float | None:
    """Convert a number written the Polish way (comma as decimal point) to a Python number.

    Args:
        value: Cell text, e.g. ``"612,50"``.
        output_type: ``int`` or ``float`` — what to convert to.

    Returns:
        int | float | None: The number, or None if the cell is empty or "-".
    """
    if not value or value.strip() in ('', '-'):
        return None

    clean_value = value.replace(',', '.').strip()
    return output_type(clean_value)

def ingest_thresholds_pdf(cursor: DBCursor, file_path: str) -> None:
    """Read the thresholds table from the PDF and store every major's thresholds.

    A major in the PDF that is not in the database is reported and skipped.

    Args:
        cursor: Database cursor to run the SQL on.
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

                capacity = parse_polish_number(capacity_str, int)
                points = parse_polish_number(points_str, float)

                # Empty or "-" cell: no threshold published for that year.
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

