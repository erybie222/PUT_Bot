"""Project entry point for loading WIiT data into PostgreSQL."""

from src.database.queries import get_or_create_major
from src.database.connection import get_db_connection
from src.scrapers.html_ects import process_full_catalog
from src.scrapers.pdf_threshholds import process_pdf

THRESHOLDS_PDF_PATH = "data/progi punktowe 2025-2021.pdf"
COMPUTER_SCIENCE_MAJOR_NAME = "informatyka"
COMPUTER_SCIENCE_CATALOG_URL = (
    "https://put.poznan.pl/karty-ects/2026_2027/Informatyka/stacjonarne/studia%20pierwszego%20stopnia"
)


def main() -> None:
    """
    Run the ingestion pipeline: thresholds first, then ECTS catalog.

    Args:
        None.

    Returns:
        None: This function performs network and database side effects.
    """
    print("Starting PUT_Bot ingestion pipeline...")
    process_pdf(THRESHOLDS_PDF_PATH)

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            computer_science_major_id = get_or_create_major(cursor, COMPUTER_SCIENCE_MAJOR_NAME)
        conn.commit()

    if computer_science_major_id is None:
        raise RuntimeError("Could not resolve major ID for Computer Science (Informatyka).")

    process_full_catalog(COMPUTER_SCIENCE_CATALOG_URL, major_id=computer_science_major_id)


if __name__ == "__main__":
    main()
