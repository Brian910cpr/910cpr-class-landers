from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from scripts.canonical_scheduling_demand import load_publication_demand, resolve_canonical_demand


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


def is_durable_admin_session(row: dict[str, Any]) -> bool:
    source = str(row.get("source") or "").strip().lower()
    native = (source == "landerware_event"
        and row.get("registration_backend") == "landerware"
        and str(row.get("session_id") or "").startswith("lw-")
        and row.get("count_available") is True
        and row.get("workspace_projection_status") == "current")
    return native or (bool(row.get("hot_sync")) and source.startswith("hot_sync"))


def validate_admin_reconciliation(current_payload: Any, admin_payload: Any) -> set[str]:
    hot_sync_source = (admin_payload.get("sources") or {}).get("hot_sync", {}) if isinstance(admin_payload, dict) else {}
    require(hot_sync_source.get("available") is True, "admin schedule was not reconciled with authoritative HOT_SYNC")
    current_ids = {
        str(row.get("session_id") or row.get("sessionId") or row.get("id") or "")
        for row in session_rows(current_payload)
        if row.get("session_id") or row.get("sessionId") or row.get("id")
    }
    admin_rows = session_rows(admin_payload)
    invalid_stale_ids = {
        str(row.get("session_id") or row.get("sessionId") or row.get("id") or "")
        for row in admin_rows
        if (row.get("session_id") or row.get("sessionId") or row.get("id"))
        and str(row.get("session_id") or row.get("sessionId") or row.get("id")) not in current_ids
        and not is_durable_admin_session(row)
    }
    require(not invalid_stale_ids, f"admin schedule contains stale sessions: {sorted(invalid_stale_ids)[:10]}")

    durable_lineages: list[str] = []
    for row in admin_rows:
        if not is_durable_admin_session(row):
            continue
        session_id = str(row.get("copied_from_session_id") or row.get("session_id") or "").strip()
        while session_id.startswith("manual-copy-"):
            session_id = session_id.removeprefix("manual-copy-")
        durable_lineages.append(session_id)
    duplicate_lineages = {lineage for lineage in durable_lineages if durable_lineages.count(lineage) > 1}
    require(not duplicate_lineages, f"admin schedule contains duplicate durable sessions: {sorted(duplicate_lineages)[:10]}")
    return {
        str(row.get("session_id") or row.get("sessionId") or row.get("id"))
        for row in admin_rows
        if row.get("session_id") or row.get("sessionId") or row.get("id")
    }


def validate_selector_lease(payload: dict, page_key: str) -> None:
    expiry = datetime.fromisoformat(str(payload.get("validUntil") or "").replace("Z", "+00:00"))
    require(expiry.tzinfo is not None, f"{page_key}: publication expiry lacks timezone")
    # Existing classes survive expired offer leases in both V2 finalization
    # and the browser. Only calculated offers depend on that availability proof.
    calculated = any(course.get('offerType') != 'seated_class'
                     for day in payload.get('dates', [])
                     for slot in day.get('startTimes', [])
                     for course in slot.get('courses', []))
    if calculated:
        require(expiry > datetime.now(timezone.utc), f"{page_key}: expired publication")


def validate_selector(page_key: str, public_session_ids: set[str]) -> dict[str, int]:
    path = SELECTOR_DIR / f"{page_key}.json"
    payload = load_json(path)
    require(payload.get("schemaVersion") == "selector-resolved-availability.v1", f"{page_key}: invalid schema")
    require((payload.get("anchor_policy") or {}).get("finalized") is True, f"{page_key}: selector has not passed final policy")
    validate_selector_lease(payload, page_key)
    blocked = set(payload.get("synthesisBlockedDates", []))
    occupied = set(payload.get("occupiedDates", []))
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
                    # Public selector payloads are intentionally compact: they retain
                    # the seated identity as availabilityBlockId="seated:<session_id>"
                    # and expose the registration destination as appointmentUrl.
                    source_block = course.get("sourceAvailabilityBlock") or {}
                    session_id = str(source_block.get("sessionId") or "").strip()
                    block_id = str(course.get("availabilityBlockId") or "").strip()
                    if not session_id and block_id.startswith("seated:"):
                        session_id = block_id.removeprefix("seated:").strip()
                    require(session_id, f"{page_key}: seated offer lacks session identity")
                    require(session_id in public_session_ids, f"{page_key}: stale seated session {session_id}")
                    registration_url = course.get("registrationUrl") or course.get("appointmentUrl")
                    require(registration_url, f"{page_key}: seated session {session_id} lacks registration URL")
                else:
                    require(day["date"] not in blocked, f"{page_key}: synthetic offer on unreconciled date {day['date']}")
                    require(day["date"] not in occupied or (
                        (course.get("schedule_role") or course.get("scheduleRole")) == "barnacle" and course.get("attached_to_session_id")
                    ), f"{page_key}: orphan synthetic offer on occupied date {day['date']}")
                    # matchedContainerId is an internal planning field and is omitted
                    # from the compact public selector contract.
                    for field in ("appointmentDayId", "appointmentUrl", "availabilityBlockId"):
                        require(course.get(field) not in (None, ""), f"{page_key}: dynamic offer lacks {field}")

    counts = payload.get("counts") or {}
    require(counts.get("publicSelectableDateCount") == date_count, f"{page_key}: date count mismatch")
    require(counts.get("publicSelectableStartTimeCount") == start_count, f"{page_key}: start count mismatch")
    require(counts.get("publicSelectableOfferCount") == offer_count, f"{page_key}: offer count mismatch")
    # A correctly closed feed must replace stale inventory even when it has no offers.
    return {"dates": date_count, "starts": start_count, "offers": offer_count}


def validate_non_session_publication(root: Path, demand: dict[str, Any]) -> None:
    ids = {str(row["external_class_id"]) for row in demand.get("non_session_sources", [])}
    for name in ("schedule_future.json", "admin_schedule.json"):
        rows = session_rows(load_json(root / "docs/data" / name))
        leaked = ids & {str(row.get("external_session_id") or row.get("session_id")) for row in rows}
        require(not leaked, f"{name}: classified non-sessions were published: {sorted(leaked)}")
    calendar = (root / "docs/data/landerware.ics").read_text(encoding="utf-8")
    for external_id in ids:
        require(not (root / "docs/classes" / f"{external_id}.html").exists(), f"Classified non-session page remains: {external_id}")
        require(f"-{external_id}@" not in calendar, f"Classified non-session calendar block remains: {external_id}")


def validate_public_demand(rows: list[dict[str, Any]], demand: dict[str, Any]) -> None:
    """Fail closed on roster *counts* without freezing fresh occupancy.

    The public schedule and selector blockers must stay current even when the
    canonical participant projection is temporarily stale or incomplete. Unknown
    demand may therefore publish only as unknown: it must not carry an
    authoritative registration count or promote an Anchor. Enrollware remains the
    registration destination for these seated classes and enforces its own seat
    availability.
    """
    resolved, _ = resolve_canonical_demand(rows, demand["sessions"])
    unknown: list[str] = []
    unsafe_counts: list[str] = []

    for published, current in zip(rows, resolved):
        if current.get("count_available") is True:
            continue

        session_id = str(
            current.get("session_id")
            or published.get("session_id")
            or published.get("external_session_id")
            or "unknown"
        )
        status = str(current.get("demand_status") or "unknown")
        unknown.append(f"{session_id}: {status}")

        published_count = published.get("active_registration_count")
        published_basis = str(published.get("demand_basis") or "").strip()
        published_available = published.get("count_available")
        if (
            published_count is not None
            or published_available is True
            or published_basis == "canonical_active_registrations"
        ):
            unsafe_counts.append(f"{session_id}: {status}")

    require(
        not unsafe_counts,
        "Refusing publication because unknown canonical demand is still exposed "
        "as an authoritative registration count for: "
        + "; ".join(unsafe_counts),
    )

    if unknown:
        print(
            "::warning title=Canonical demand unavailable::"
            "Publishing fresh occupied-session timing with participant counts "
            "failed closed for: "
            + "; ".join(unknown)
        )


def main() -> int:
    schedule = load_json(SCHEDULE_PATH)
    rows = session_rows(schedule)
    require(rows, "schedule_future.json contains no public sessions")
    public_session_ids = {
        str(row.get("session_id") or row.get("sessionId") or row.get("id") or "")
        for row in rows
        if row.get("session_id") or row.get("sessionId") or row.get("id")
    }

    admin_ids = validate_admin_reconciliation(load_json(CURRENT_SESSIONS_PATH), load_json(ADMIN_SCHEDULE_PATH))
    demand = load_publication_demand(ROOT)
    validate_public_demand(rows, demand)
    validate_non_session_publication(ROOT, demand)

    results = {page_key: validate_selector(page_key, public_session_ids) for page_key in REQUIRED_SELECTORS}
    print(f"Validated public sessions: {len(public_session_ids)}")
    print(f"Validated admin sessions: {len(admin_ids)}")
    for page_key, counts in results.items():
        print(f"{page_key}: dates={counts['dates']} starts={counts['starts']} offers={counts['offers']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
