"""Project entry point for loading WIiT data into PostgreSQL."""

from src.database.queries import create_major, initialize_lookups, create_major
from src.database.connection import get_db_connection
from src.scrapers.html_ects import process_full_catalog
from src.scrapers.pdf_threshholds import process_pdf

THRESHOLDS_PDF_PATH = "data/progi punktowe 2025-2021.pdf"

# Dictionary of WIiT majors
WIIT_MAJORS = [
    "informatyka",
    "sztuczna inteligencja",
    "teleinformatyka",
    "bioinformatyka"
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

        # Inserting WIiT majors if they don't exist
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
            major_catalog_url = f"https://put.poznan.pl/karty-ects/2026_2027/{major}/stacjonarne/studia%20pierwszego%20stopnia"
            # Inserting courses for every major
            process_full_catalog(major_catalog_url, major_id=major_id)




if __name__ == "__main__":
    main()
