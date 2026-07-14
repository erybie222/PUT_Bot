"""Project entry point for loading WIiT data into PostgreSQL."""

from src.database.queries import create_major, initialize_lookups
from src.database.connection import get_db_connection
from src.scrapers.html_ects import process_full_catalog
from src.scrapers.pdf_threshholds import process_pdf

THRESHOLDS_PDF_PATH = "data/progi punktowe 2025-2021.pdf"
BASE_ECTS_URL = "https://put.poznan.pl/karty-ects/2026_2027"
STUDY_PATH = "stacjonarne/studia%20pierwszego%20stopnia"

# Dictionary of WIiT majors with custom ECTS path segment support
WIIT_MAJORS = [
    'Informatyka', 'Bioinformatyka', 'Teleinformatyka', 'Cyberbezpieczeństwo', 'Mikroelektronika i komunikacja cyfrowa'
]


def main() -> None:
    """
    Run the ingestion pipeline: thresholds first, then ECTS catalog.

    Args:
        None.

    Returns:
        None: This function performs network and database side effects.
    """
    print("Starting PUT_Bot ingestion pipeline...")


    with get_db_connection() as conn:
        cursor = conn.cursor()
        print("Connected to the database. Initializing basic structures...")

        # Inserting WIiT faculty if it doesn't exist
        initialize_lookups(cursor)

        # Inserting WIiT majors if they don't exist and then courses for each major
        for major in WIIT_MAJORS:
            major_id = create_major(
                cursor,
                major_name=major,
                degree='bachelor-of-engineering',
                study_mode="full-time",
                profile="general-academic",
                faculty="WIiT",
                is_english=False,
            )
            normalized_major_name = major.replace(" ", "%20")
            major_catalog_url = f"{BASE_ECTS_URL}/{normalized_major_name}/{STUDY_PATH}"
            process_full_catalog(cursor, major_catalog_url, major_id=major_id)

        conn.commit()




if __name__ == "__main__":
    main()
