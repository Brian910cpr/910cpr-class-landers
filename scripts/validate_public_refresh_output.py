from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
CURRENT_SESSIONS_PATH = ROOT / "data" / "sessions_current.json"
ADMIN_SCHEDULE_PATH = ROOT / "docs" / "data" / "admin_schedule.json"
SELECTOR_DIR = ROOT / "docs" / "data" / "block-selector-availability"
REQUIRED_SELECTORS = ("bls", "heartsaver", "acls", "pals")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def session_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        for key in ("sessions", "classes", "events"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]
    return []


def validate_selector(page_key: str, public_session_ids: set[str]) -> dict[str, int]:
    path = SELECTOR_DIR / f"{page_key}.json"
    payload = load_json(path)
    require(payload.get("schemaVersion") == "selector-resolved-availability.v1", f"{page_key}: invalid schema")
    dates = payload.get("dates")
    require(isinstance(dates, list), f"{page_key}: dates must be a list")

    date_count = len(dates)
    start_count = 0
    offer_count = 0
    for day in dates:
        require(isinstance(day, dict) and day.get("date"), f"{page_key}: date row lacks date")
        starts = day.get("startTimes")
        require(isinstance(starts, list), f"{page_key}: startTimes must be a list")
        start_count += len(starts)
        for slot in starts:
            require(slot.get("startTime"), f"{page_key}: slot lacks startTime")
            courses = slot.get("courses")
            require(isinstance(courses, list) and courses, f"{page_key}: slot has no courses")
            offer_count += len(courses)
            for course in courses:
                for field in ("courseId", "courseName", "startTime", "location"):
                    require(course.get(field) not in (None, ""), f"{page_key}: offer lacks {field}")
                if course.get("offerType") == "seated_class":
                    session_id = str((course.get("sourceAvailabilityBlock") or {}).get("sessionId") or "")
                    require(session_id in public_session_ids, f"{page_key}: stale seated session {session_id}")
                    require(course.get("registrationUrl"), f"{page_key}: seated session {session_id} lacks registrationUrl")
                else:
                    for field in ("appointmentDayId", "matchedContainerId", "appointmentUrl", "availabilityBlockId"):
                        require(course.get(field) not in (None, ""), f"{page_key}: dynamic offer lacks {field}")

    counts = payload.get("counts") or {}
    require(counts.get("publicSelectableDateCount") == date_count, f"{page_key}: date count mismatch")
    require(counts.get("publicSelectableStartTimeCount") == start_count, f"{page_key}: start count mismatch")
    require(counts.get("publicSelectableOfferCount") == offer_count, f"{page_key}: offer count mismatch")
    require(offer_count > 0, f"{page_key}: public calendar is empty")
    return {"dates": date_count, "starts": start_count, "offers": offer_count}


def main() -> int:
    schedule = load_json(SCHEDULE_PATH)
    rows = session_rows(schedule)
    require(rows, "schedule_future.json contains no public sessions")
    public_session_ids = {
        str(row.get("session_id") or row.get("sessionId") or row.get("id") or "")
        for row in rows
        if row.get("session_id") or row.get("sessionId") or row.get("id")
    }

    current_ids = {
        str(row.get("session_id") or row.get("sessionId") or row.get("id") or "")
        for row in session_rows(load_json(CURRENT_SESSIONS_PATH))
        if row.get("session_id") or row.get("sessionId") or row.get("id")
    }
    admin_ids = {
        str(row.get("session_id") or row.get("sessionId") or row.get("id") or "")
        for row in session_rows(load_json(ADMIN_SCHEDULE_PATH))
        if row.get("session_id") or row.get("sessionId") or row.get("id")
    }
    stale_admin_ids = admin_ids - current_ids
    require(not stale_admin_ids, f"admin schedule contains stale sessions: {sorted(stale_admin_ids)[:10]}")

    results = {page_key: validate_selector(page_key, public_session_ids) for page_key in REQUIRED_SELECTORS}
    print(f"Validated public sessions: {len(public_session_ids)}")
    print(f"Validated admin sessions: {len(admin_ids)}")
    for page_key, counts in results.items():
        print(f"{page_key}: dates={counts['dates']} starts={counts['starts']} offers={counts['offers']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
