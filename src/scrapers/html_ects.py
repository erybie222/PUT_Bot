import requests
from bs4 import BeautifulSoup
import re
from src.database.connection import get_db_connection
from src.database.queries import upsert_course


def parse_hours(hours_str: str) -> tuple[int, bool]:
    """
    Parses strings like '30h', '30h (E)', or empty strings.
    Returns a tuple: (hours_int, exam_boolean)
    """
    if not hours_str or hours_str.strip() == '':
        return 0, False

    # Check for the Exam flag (case-insensitive)
    has_exam = '(e)' in hours_str.lower()

    # Extract only the digits using regex
    digits = re.findall(r'\d+', hours_str)
    hours_int = int(digits[0]) if digits else 0

    return hours_int, has_exam


def process_full_catalog(url: str, major_id: int) -> None:
    """
    Fetches the full catalog of courses from the provided URL and upserts them into the database.
    :param url: The URL to fetch the catalog from.
    :param major_id: The ID of the major for which to upsert courses.
    :return: None
    """
    print(f"Fetching full catalog from: {url}")

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the catalog: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all h3 headers (Obligatory / Elective subjects)
    sections = soup.find_all('h3')

    print("Connecting to the database...")

    # Using context manager for safe database connection
    with get_db_connection() as conn:
        cursor = conn.cursor()

        for section in sections:
            section_title = section.get_text(strip=True).lower()

            # Ignore h3 tags that do not relate to subjects
            if 'przedmioty' not in section_title:
                continue

            # Check if course is obligatory or elective based on the section title
            is_obligatory = 'obligatoryjne' in section_title

            # --- DYNAMIC SEMESTER DISCOVERY ---
            # Find the nearest H2 header located above in the HTML structure
            parent_h2 = section.find_previous('h2')
            if not parent_h2:
                continue

            semester_text = parent_h2.get_text(strip=True)  # e.g., "Semestr 1"
            semester_match = re.search(r'\d+', semester_text)
            semester = int(semester_match.group()) if semester_match else 0

            # The table containing courses immediately follows the H3 tag
            table = section.find_next_sibling('table')
            if not table:
                continue

            print(f"\n--- SEMESTER {semester} | {'Obligatory' if is_obligatory else 'Elective'} ---")

            # Find the tbody element and all rows within it (courses are set in table)
            tbody = table.find('tbody')
            rows = tbody.find_all('tr') if tbody else table.find_all('tr')

            for row in rows:
                # Check if the row is an elective group row and adjust the obligatory flag accordingly
                if 'elective-group-row' in row.get('class', []):
                    is_obligatory = False

                # Skip rows that don't have enough cells to extract data
                cells = row.find_all('td')
                if len(cells) < 8:
                    continue

                # 1. Extract Name and Code securely using their CSS classes
                name_span = cells[0].find('span', class_='course-name')
                code_span = cells[0].find('span', class_='course-code')

                if not name_span or not code_span:
                    continue

                subject_name = name_span.get_text(strip=True)
                subject_code = code_span.get_text(strip=True)

                # If course code endswith ang then change boolean flag to true
                is_english = subject_code.lower().endswith('ang')

                # 2. Extract ECTS points
                ects_text = cells[1].get_text(strip=True)
                ects = int(ects_text) if ects_text.isdigit() else 0

                # 3. Extract Hours and Exam info
                w_hours, w_exam = parse_hours(cells[2].get_text(strip=True))
                c_hours, _ = parse_hours(cells[3].get_text(strip=True))
                l_hours, _ = parse_hours(cells[4].get_text(strip=True))
                p_hours, _ = parse_hours(cells[5].get_text(strip=True))

                form_of_assessment = "Egzamin" if w_exam else "Zaliczenie z ocena"

                # 4. Extract the PDF Link in Polish language (from the 'PL' column - index 7)
                pdf_link = None
                pl_cell = cells[7]
                anchor = pl_cell.find('a', class_='course-link')
                if anchor and 'href' in anchor.attrs:
                    pdf_link = anchor['href']
                    # Prefix with the main domain if the link is relative
                    if pdf_link.startswith('/'):
                        pdf_link = f"https://put.poznan.pl{pdf_link}"

                print(f"Upserting -> [{subject_code}] {subject_name} (ECTS: {ects})")

                # Push the data to PostgreSQL
                upsert_course(
                    cursor=cursor,
                    code=subject_code,
                    major_id=major_id,
                    semester=semester,
                    name=subject_name,
                    is_obligatory=is_obligatory,
                    is_english=is_english,
                    ects=ects,
                    w=w_hours,
                    c=c_hours,
                    l=l_hours,
                    p=p_hours,
                    form=form_of_assessment,
                    source_url=pdf_link
                )

        # Commit all changes to the database at the very end
        conn.commit()

    print("\nDatabase commit successful. Catalog processing complete!")
