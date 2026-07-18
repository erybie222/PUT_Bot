"""Project entry point for loading WIiT data into PostgreSQL."""
from src.database.queries import create_major, initialize_lookups
from src.database.connection import get_db_connection, close_pool
from src.scrapers.html_ects import process_full_catalog
from src.scrapers.informator_staff_office_hours import process_informator
from src.scrapers.pdf_threshholds import process_pdf
from datetime import datetime

CURRENT_YEAR = int(datetime.now().year)

THRESHOLDS_PDF_PATH = f"data/progi punktowe {CURRENT_YEAR}-{CURRENT_YEAR - 4}.pdf"
BASE_ECTS_URL = f"https://put.poznan.pl/karty-ects/{CURRENT_YEAR}_{CURRENT_YEAR + 1}"
print(BASE_ECTS_URL, THRESHOLDS_PDF_PATH)
STUDY_PATH = "stacjonarne/studia%20pierwszego%20stopnia"

# Dictionary of WIiT majors with custom ECTS path segment support
WIIT_MAJORS_PL_FIRST_CYCLE = [
    'Informatyka', 'Bioinformatyka', 'Teleinformatyka', 'Cyberbezpieczeństwo', 'Mikroelektronika i komunikacja cyfrowa'
]

WIIT_MAJORS_EN_FIRST_CYCLE = [
    ('Sztuczna inteligencja', 'Artificial Intelligence'),
]

# TODO: PROVIDE SECOND CYCLE MAJORS AND COURSES AND PART TIME ONES
# WIIT_MAJORS_PL_SECOND_CYCLE = []
#
# WIIT_MAJORS_EN_SECOND_CYCLE = []

def main() -> None:
    """
    Run the ingestion pipeline: majors + ECTS catalog, thresholds, then staff.

    Everything runs on one connection/cursor and commits once at the end.

    Args:
        None.

    Returns:
        None: This function performs network and database side effects.
    """
    print("Starting PUT_Bot ingestion pipeline...")


    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            print("Connected to the database. Initializing basic structures...")

            # Inserting WIiT faculty if it doesn't exist
            initialize_lookups(cursor)

            # Inserting WIiT majors if they don't exist and then courses for each major
            for major in WIIT_MAJORS_PL_FIRST_CYCLE:
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

            # English majors
            for major in WIIT_MAJORS_EN_FIRST_CYCLE:
                major_id = create_major(
                    cursor,
                    major_name=major[0],
                    degree='bachelor-of-engineering',
                    study_mode="full-time",
                    profile="general-academic",
                    faculty="WIiT",
                    is_english=True,
                )
                major_name = f"{major[0]}_{major[1]}"
                normalized_major_name = major_name.replace(" ", "%20")
                major_catalog_url = f"{BASE_ECTS_URL}/{normalized_major_name}/{STUDY_PATH}"
                process_full_catalog(cursor, major_catalog_url, major_id=major_id)

            # Admission thresholds (matched to the majors created above)
            process_pdf(cursor, THRESHOLDS_PDF_PATH)


            try:
                process_informator(cursor)
            except RuntimeError as error:
                print(f"Informator staff scraping aborted: {error}")
    finally:
        close_pool()

if __name__ == "__main__":
    main()
