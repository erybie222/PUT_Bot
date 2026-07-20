import os
import time
from typing import Iterator
from requests import Session
from psycopg import Cursor as DBCursor
from requests.exceptions import RequestException

from database.queries.office_hours import delete_office_hours_by_id, insert_office_hour
from database.queries.departments import upsert_department
from database.queries.staff import upsert_staff

BASE_URL = "https://informator.put.poznan.pl"
FACULTY_SYMBOL = "WIiT"
PAGE_SIZE = 100          # server-side maximum per page
REQUEST_DELAY_S = 0.2    # politeness delay between per-person card requests
MAX_RETRIES = 3          # attempts per API call before giving up
RETRY_BACKOFF_S = 2.0    # extra wait added before each retry

WEEKDAYS_PL = {
    "monday": "poniedziałek",
    "tuesday": "wtorek",
    "wednesday": "środa",
    "thursday": "czwartek",
    "friday": "piątek",
    "saturday": "sobota",
    "sunday": "niedziela",
}


class InformatorSessionError(RuntimeError):
    """Raised when the Informator session cookie is missing, expired or unverified."""


def create_session() -> Session:
    """
    Build an HTTP session authorized against the Informator API.

    Args:
        None.

    Returns:
        Session: Session carrying the captcha-verified ``informator`` cookie.

    Raises:
        InformatorSessionError: Raised when INFORMATOR_SESSION is not configured.
    """
    cookie = os.getenv("INFORMATOR_SESSION", "").strip()
    if not cookie:
        raise InformatorSessionError("INFORMATOR_SESSION is not set.\n")

    session = Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (WIiTek ingestion; student project)"
    session.cookies.set("informator", cookie, domain="informator.put.poznan.pl")
    return session


def api_call(session: Session, action: str, post: bool = True) -> dict:
    """
    Call one Informator JSON API action and return its ``result`` payload.

    Args:
        session: HTTP session created by ``create_session``.
        action: Query string after ``?do=`` (action name plus URL parameters).
        post: Whether the action expects POST ; GET otherwise.

    Transient failures (network errors, empty/HTML bodies from server hiccups
    or rate limiting) are retried up to ``MAX_RETRIES`` times with a backoff.

    Returns:
        dict: The ``result`` object of a successful API response.

    Raises:
        InformatorSessionError: Raised when the session is redirected to login
            or fails the captcha verification.
        RuntimeError: Raised for a non-SUCCESS API status or when retries run out.
    """
    url = f"{BASE_URL}/?do={action}"
    last_error = ""
    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            time.sleep(RETRY_BACKOFF_S * (attempt - 1))
        try:
            if post:
                response = session.post(url, json={"captcha": None}, allow_redirects=False, timeout=30)
            else:
                response = session.get(url, allow_redirects=False, timeout=30)
        except RequestException as error:
            last_error = f"network error: {error}"
            continue

        if response.status_code in (301, 302, 303):
            raise InformatorSessionError("Session cookie expired (redirected to login).\n")

        try:
            payload = response.json()
        except ValueError:
            last_error = f"HTTP {response.status_code}, non-JSON response: {response.text[:120]!r}"
            continue

        status = payload.get("status", {})
        if status.get("request") != "SUCCESS":
            if status.get("captcha") == "NOT_VERIFIED":
                raise InformatorSessionError("Captcha not verified.\n")
            raise RuntimeError(f"Informator API call failed: {action} -> {status}")
        return payload["result"]

    raise RuntimeError(f"Informator API call failed after {MAX_RETRIES} attempts: {action} -> {last_error}")


def find_unit_by_symbol(node: dict, symbol: str) -> dict | None:
    """
    Find a unit subtree by its symbol in the organization tree.

    Args:
        node: Organization tree node (as returned by OrganizationUnitsTree).
        symbol: Unit symbol to look for (e.g. ``"WIiT"``).

    Returns:
        dict | None: Matching subtree root, or None when not found.
    """
    if node.get("symbol") == symbol:
        return node
    for child in node.get("children") or []:
        found = find_unit_by_symbol(child, symbol)
        if found:
            return found
    return None


def iter_units(node: dict, depth: int = 0) -> Iterator[tuple[dict, int]]:
    """
    Yield all units of a subtree in pre-order (parents before children).

    Args:
        node: Subtree root node.
        depth: Depth of ``node`` relative to the subtree root.

    Returns:
        Iterator[tuple[dict, int]]: Pairs of (unit node, relative depth).
    """
    yield node, depth
    for child in node.get("children") or []:
        yield from iter_units(child, depth + 1)


def fetch_staff(session: Session, unit_id: int) -> Iterator[dict]:
    """
    Yield all employee items of a unit (including sub-units), page by page.

    Args:
        session: HTTP session created by ``create_session``.
        unit_id: ID of the unit .

    Returns:
        Iterator[dict]: Raw employee card items from the unit listing.
    """
    page = 1
    while True:
        result = api_call(
            session,
            f"Organization.OrganizationUnitDetails&id={unit_id}"
            f"&page={page}&max_results={PAGE_SIZE}&user_type=&query_name=", True
        )
        employees = result["employees"]
        yield from employees["items"]
        if page * PAGE_SIZE >= employees["total"]:
            return
        page += 1


def pick_department(positions: dict, unit_names_by_id: dict[int, tuple[str, int]]) -> str | None:
    """
    Choose the most specific unit among a person's employment positions.

    A person can hold several positions. The deepest unit in the faculty tree is chosen.

    Args:
        positions: ``employment.data.positions`` mapping from the card payload.
        unit_names_by_id: Mapping of unit ID to (Polish name, tree depth).

    Returns:
        str | None: Unit name, or None when no position is within unit.
    """
    best_name = None
    best_depth = -1
    for position in positions.values():
        department = position.get("department") or {}
        unit = unit_names_by_id.get(department.get("id"))
        if unit and unit[1] > best_depth:
            best_name, best_depth = unit[0], unit[1]
    return best_name


def build_location(meeting: dict) -> str | None:
    """
    Compose a human-readable location string for one office-hours slot.

    Args:
        meeting: Single meeting entry from the card's ``meetings`` module.

    Returns:
        str | None: ``"<building> <room>"``, ``"online"`` or None when unknown.
    """
    parts = [meeting.get("building_symbol"), meeting.get("room_number")]
    location = " ".join(part for part in parts if part)
    if not location and meeting.get("online_link"):
        location = "online"
    return location[:100] or None


def process_office_hours(cursor: DBCursor, session: Session, staff_id: int, uuid: str, source_url: str) -> int:
    """
    Fetch one person's business card and sync their weekly office hours.

    Existing rows are replaced with the currently published set, so slots
    removed at the source are removed here too.

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.
        session: HTTP session created by ``create_session``.
        staff_id: ID of the staff record the office hours belong to.
        uuid: Informator card UUID of the person.
        source_url: Card URL used for provenance tracking.

    Returns:
        int: Number of office-hours slots stored.
    """
    result = api_call(session, f"Card.CardShow&uuid={uuid}", True)
    modules = result["card"]["modules"]
    meetings_data = (modules.get("meetings", {}) or {}).get("data", {}) or {}
    meetings = meetings_data.get("meetings", {}) or {}

    delete_office_hours_by_id(cursor, staff_id)
    stored = 0
    for meeting in meetings.values():
        weekday = WEEKDAYS_PL.get(meeting.get("weekday"))
        if meeting.get("frequency") != "weekly" or not weekday:
            continue  # one-off meetings carry a date, not a weekday; out of scope
        insert_office_hour(
            cursor=cursor,
            staff_id=staff_id,
            day_of_week=weekday,
            start_time=meeting["start_hour"],
            end_time=meeting["end_hour"],
            location=build_location(meeting),
            comment=meeting.get("comment") or None,
            source_url=source_url,
        )
        stored += 1
    return stored


def process_informator(cursor: DBCursor) -> None:
    """
    Scrape all WIiT units, staff and office hours into PostgreSQL.

    Runs on the caller's cursor/transaction — the caller decides when to commit
    (in the pipeline that is ``main.py``, once at the end of the whole run).
    Requires the WIiT row in ``faculties`` to exist (``initialize_lookups``).

    Args:
        cursor: Open PostgreSQL cursor used to execute SQL statements.

    Returns:
        None: This function performs network and database side effects.

    Raises:
        InformatorSessionError: Raised when INFORMATOR_SESSION is missing or rejected.
    """
    print("Starting Informator PP staff scraper...")
    session = create_session()

    print("Fetching organization tree...")
    tree = api_call(session, "Organization.OrganizationUnitsTree", False)
    faculty = find_unit_by_symbol(tree, FACULTY_SYMBOL)
    if faculty is None:
        raise RuntimeError(f"Faculty with symbol {FACULTY_SYMBOL!r} not found in organization tree")

    units = list(iter_units(faculty))
    unit_names_by_id: dict[int, tuple[str, int]] = {}
    for node, depth in units:
        if depth == 0:
            continue  # the faculty itself lives in `faculties`, not in `departments`
        name = node["name"]["pl"][:100]
        unit_names_by_id[node["id"]] = (name, depth)
        parent = unit_names_by_id.get(node["parent_id"])
        phones = ", ".join(p["number"] for p in node.get("phones", []))
        upsert_department(
            cursor=cursor,
            name=name,
            symbol=(node.get("symbol") or "")[:10] or None,
            parent=parent[0] if parent else None,
            unit_type=node.get("type"),
            faculty=FACULTY_SYMBOL,
            address=node.get("address"),
            phone=phones[:100] or None,
            email=node.get("email"),
            source_url=f"{BASE_URL}/app/unit/{node['id']}",
        )
    print(f"Stored {len(units) - 1} units of {FACULTY_SYMBOL}.")

    processed = skipped = hours_total = 0
    for item in fetch_staff(session, faculty["id"]):
        basic = (item["modules"].get("basic", {}) or {}).get("data", {}) or {}
        contact = (item["modules"].get("contact", {}) or {}).get("data", {}) or {}
        employment = (item["modules"].get("employment", {}) or {}).get("data", {}) or {}

        email = (contact.get("email", "") or ""
                                             "").strip().lower()
        first_name = (basic.get("name", "") or "").strip()
        last_name = (basic.get("surname", "") or "").strip()
        if not (email and first_name and last_name):
            print(f"  -> Skipping (no email or name): {first_name} {last_name}")
            skipped += 1
            continue

        source_url = f"{BASE_URL}/app/card/view/{item['uuid']}"
        staff_id = upsert_staff(
            cursor=cursor,
            first_name=first_name[:50],
            last_name=last_name[:50],
            academic_title=(basic.get("title", "") or "").strip()[:100] or None,
            department=pick_department(employment.get("positions", {}) or {}, unit_names_by_id),
            email=email[:100],
            phone=", ".join(contact.get("phones", []))[:100] or None,
            source_url=source_url,
        )

        try:
            hours = process_office_hours(cursor, session, staff_id, item["uuid"], source_url)
        except InformatorSessionError:
            raise  # dead session — no point continuing with the remaining people
        except (RuntimeError, RequestException) as error:
            hours = 0
            print(f"  -> Office hours failed for {last_name} {first_name}: {error}")
        hours_total += hours
        processed += 1
        print(f"  [{processed}] {last_name} {first_name} ({email}), office hours: {hours}")
        time.sleep(REQUEST_DELAY_S)

    print(
        f"\nInformator done: {processed} staff members stored "
        f"({skipped} skipped), {hours_total} office-hours slots."
    )


