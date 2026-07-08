from src.scrapers.pdf_threshholds import process_pdf
from src.scrapers.html_ects import process_full_catalog
from src.database.connection import get_db_connection
from src.database.queries import get_or_create_major

def main():
    print("Hello from put-bot!")
    process_pdf("data/progi punktowe 2025-2021.pdf")
    # Link to the computer science 1st degree full-time catalog
    target_url = "https://put.poznan.pl/karty-ects/2026_2027/Informatyka/stacjonarne/studia%20pierwszego%20stopnia"

    # Fetch the correct major_id dynamically
    with get_db_connection() as conn:
        cursor = conn.cursor()
        inf_major_id = get_or_create_major(cursor, "informatyka")
        conn.commit()

    # Execute the pipeline for the resolved major_id
    process_full_catalog(target_url, major_id=inf_major_id)

if __name__ == "__main__":
    main()
