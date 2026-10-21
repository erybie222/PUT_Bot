"""Load all WIiT data into the database: ``uv run src/run_ingestion.py``.

Steps, in order (later steps depend on earlier ones):

1. the WIiT faculty row;
2. every major, and the courses from its ECTS catalog page;
3. admission thresholds from the PDF — matched to the majors from step 2 by name;
4. faculty units, staff, their functions and office hours from Informator.

Everything runs in one transaction that is committed at the end, so a crash
leaves the database as it was. The one exception is step 4: it needs a
browser cookie that often expires, so its failure is reported and skipped
instead of undoing steps 1–3. Staff saved before the failure are kept.
"""

from database.queries.faculties import insert_wiit_faculty
from database.queries.majors import upsert_major
from database.connection import get_db_connection, close_pool
from scrapers.html_ects import ingest_ects_catalog
from scrapers.informator_staff_office_hours import ingest_informator
from scrapers.pdf_thresholds import ingest_thresholds_pdf
from datetime import datetime

CURRENT_YEAR = int(datetime.now().year)

# The PDF covers the five previous recruitment years; YEAR_COLUMNS in
# scrapers/pdf_thresholds.py must list the same years.
THRESHOLDS_PDF_PATH = f"data/progi punktowe {CURRENT_YEAR - 1}-{CURRENT_YEAR - 5}.pdf"
# ECTS catalogs are published per academic year, e.g. .../2026_2027.
BASE_ECTS_URL = f"https://put.poznan.pl/karty-ects/{CURRENT_YEAR}_{CURRENT_YEAR + 1}"
# Last part of every catalog URL: full-time ("stacjonarne") first-cycle studies.
STUDY_PATH = "stacjonarne/studia%20pierwszego%20stopnia"

# Polish-taught first-cycle majors, spelled exactly as in the catalog URLs and
# the thresholds PDF (the PDF match ignores letter case).
WIIT_MAJORS_PL_FIRST_CYCLE = [
    'Informatyka', 'Bioinformatyka', 'Teleinformatyka', 'Cyberbezpieczeństwo', 'Mikroelektronika i komunikacja cyfrowa'
]

# English-taught first-cycle majors as (Polish name, English name). Only the
# Polish name is stored in the database; both are needed to build the catalog URL.
WIIT_MAJORS_EN_FIRST_CYCLE = [
    ('Sztuczna inteligencja', 'Artificial Intelligence'),
]

# TODO: add second-cycle (master's) majors and part-time studies. Both need
# their own catalog URL path and the matching degree / study_mode values.
# WIIT_MAJORS_PL_SECOND_CYCLE = []
#
# WIIT_MAJORS_EN_SECOND_CYCLE = []

def main() -> None:
    """Run every ingestion step on one database cursor and commit once at the end.

    The steps and why they run in this order are described at the top of
    this module.
    """
    print("Starting PUT_Bot ingestion pipeline...")


    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            print("Connected to the database. Initializing basic structures...")

            insert_wiit_faculty(cursor)

            for major in WIIT_MAJORS_PL_FIRST_CYCLE:
                major_id = upsert_major(
                    cursor,
                    major_name=major,
                    degree='bachelor-of-engineering',
                    study_mode="full-time",
                    profile="general-academic",
                    faculty="WIiT",
                    is_english=False,
                )
                # The major name is a URL path segment, so spaces become %20.
                normalized_major_name = major.replace(" ", "%20")
                major_catalog_url = f"{BASE_ECTS_URL}/{normalized_major_name}/{STUDY_PATH}"

                ingest_ects_catalog(cursor, major_catalog_url, major_id=major_id)

            for major in WIIT_MAJORS_EN_FIRST_CYCLE:
                major_id = upsert_major(
                    cursor,
                    major_name=major[0],
                    degree='bachelor-of-engineering',
                    study_mode="full-time",
                    profile="general-academic",
                    faculty="WIiT",
                    is_english=True,
                )
                # English-taught majors' catalog path is "<Polish name>_<English name>".
                major_name = f"{major[0]}_{major[1]}"
                normalized_major_name = major_name.replace(" ", "%20")
                major_catalog_url = f"{BASE_ECTS_URL}/{normalized_major_name}/{STUDY_PATH}"
                ingest_ects_catalog(cursor, major_catalog_url, major_id=major_id)

            # Needs the majors above: rows are matched to them by name.
            ingest_thresholds_pdf(cursor, THRESHOLDS_PDF_PATH)


            # Informator needs a manual browser cookie that often expires; a
            # failure here skips staff data instead of rolling back the run.
            try:
                ingest_informator(cursor)
            except RuntimeError as error:
                print(f"Informator staff scraping aborted: {error}")
    finally:
        close_pool()

if __name__ == "__main__":
    main()
