import pdfplumber
from src.database.connection import get_db_connection
from src.database.queries import initialize_lookups, get_or_create_major, upsert_threshold

# Dictionary of WIiT majors
WIIT_MAJORS = [
    "informatyka",
    "sztuczna inteligencja",
    "teleinformatyka",
    "bioinformatyka"
]

# Column definitions for specific years
YEAR_COLUMNS = {
    2025: (1, 2),
    2024: (3, 4),
    2023: (5, 6),
    2022: (7, 8),
    2021: (9, 10)
}

def clean_number(value, output_type):
    """Replaces Polish commas with dots and casts to int/float. Ignores empty strings."""
    if not value or value.strip() in ('', '-'):
        return None

    clean_value = value.replace(',', '.').strip()
    return output_type(clean_value)

def process_pdf(file_path):
    print(f"Starting PDF extraction process...")

    # Using the context manager to ensure safe connection handling
    with get_db_connection() as conn:
        cursor = conn.cursor()

        print("Connected to the database. Initializing basic structures...")
        initialize_lookups(cursor)

        print(f"Opening file: {file_path}")
        with pdfplumber.open(file_path) as pdf:
            table = pdf.pages[0].extract_table()

            # Skip the header row (index 0)
            for row in table[1:]:
                raw_name = row[0]
                clean_name = raw_name.split('/')[0].strip().lower()

                # Filter out non-WIiT majors
                if clean_name not in WIIT_MAJORS:
                    continue

                print(f"\nProcessing: {clean_name.capitalize()}")
                major_id = get_or_create_major(cursor, clean_name)

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

        # Commit all changes once the file is fully processed
        conn.commit()
        cursor.close()
        print("\nFinished! Changes successfully committed to the database.")
