from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


from scripts.local_data_paths import dynamic_offers_preview_path, public_sellable_offers_preview_path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"

DYNAMIC_OFFERS_PATH = dynamic_offers_preview_path(ROOT)
PUBLIC_SELLABLE_OFFERS_PATH = public_sellable_offers_preview_path(ROOT)
SCHEDULE_FUTURE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
SESSIONS_CURRENT_PATH = ROOT / "data" / "sessions_current.json"
LIVE_AVAILABILITY_PATH = AUDIT_DIR / "live_availability_snapshot_preview.json"
LEGACY_AVAILABILITY_PATH = ROOT / "data" / "inventory" / "instructor_availability.json"

REPORT_MD_PATH = AUDIT_DIR / "public_offer_integrity_report.md"
REPORT_JSON_PATH = AUDIT_DIR / "public_offer_integrity_report.json"
UNKNOWN = "UNKNOWN"


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean_text(value).lower()).strip("_")


def read_json(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid_json: {exc}"
    except OSError as exc:
        return None, f"read_error: {exc}"


def parse_dt(value: Any) -> datetime | None:
    text = clean_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def intervals_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and start_b < end_a


def session_course_name(session: dict[str, Any]) -> str:
    course = session.get("course") if isinstance(session.get("course"), dict) else {}
    return clean_text(
        session.get("official_course_name")
        or session.get("mapped_clean_title")
        or session.get("course_name")
        or course.get("mapped_clean_title")
        or course.get("course_name_primary_clean")
        or UNKNOWN
    )


def session_course_id(session: dict[str, Any]) -> str:
    course = session.get("course") if isinstance(session.get("course"), dict) else {}
    return clean_text(session.get("course_id") or session.get("course_number") or course.get("course_id") or UNKNOWN)


def session_course_key(session: dict[str, Any]) -> str:
    return clean_text(session.get("course_key") or session.get("mapped_family") or UNKNOWN)


def session_location(session: dict[str, Any]) -> str:
    return clean_text(session.get("location_name") or session.get("location_display") or session.get("location") or UNKNOWN)


def session_instructor(session: dict[str, Any]) -> str:
    return clean_text(session.get("lead_instructor_name") or session.get("instructor") or UNKNOWN)


def session_start(session: dict[str, Any]) -> datetime | None:
    return parse_dt(session.get("start_at") or session.get("start") or session.get("start_datetime"))


def session_end(session: dict[str, Any]) -> datetime | None:
    return parse_dt(session.get("end_at") or session.get("end") or session.get("end_datetime"))


def normalize_sessions(payload: Any, source_file: str) -> list[dict[str, Any]]:
    sessions = payload.get("sessions", []) if isinstance(payload, dict) else []
    out: list[dict[str, Any]] = []
    if not isinstance(sessions, list):
        return out
    for session in sessions:
        if not isinstance(session, dict):
            continue
        start = session_start(session)
        end = session_end(session)
        out.append({
            "session_id": clean_text(session.get("session_id") or session.get("id") or UNKNOWN),
            "course_id": session_course_id(session),
            "course_key": session_course_key(session),
            "display_course_name": session_course_name(session),
            "instructor": session_instructor(session),
            "location": session_location(session),
            "start": start,
            "end": end,
            "source_file": source_file,
        })
    return out


def availability_start_end(block: dict[str, Any]) -> tuple[datetime | None, datetime | None]:
    start = parse_dt(block.get("start_datetime") or block.get("start_at"))
    end = parse_dt(block.get("end_datetime") or block.get("end_at"))
    if start and end:
        return start, end
    date_value = clean_text(block.get("date"))
    start_time = clean_text(block.get("start_time"))
    end_date = clean_text(block.get("end_date") or block.get("date"))
    end_time = clean_text(block.get("end_time"))
    if not date_value or not start_time or not end_date or not end_time:
        return None, None
    return parse_dt(f"{date_value}T{start_time}"), parse_dt(f"{end_date}T{end_time}")


def availability_id(block: dict[str, Any], index: int) -> str:
    return clean_text(block.get("source_event_id") or block.get("source_availability_window") or f"availability[{index}]")


def availability_blocks(*payloads: Any) -> dict[str, dict[str, Any]]:
    blocks: dict[str, dict[str, Any]] = {}
    for payload in payloads:
        raw = payload.get("availability_blocks", []) if isinstance(payload, dict) else []
        if not isinstance(raw, list):
            continue
        for index, block in enumerate(raw, start=1):
            if not isinstance(block, dict):
                continue
            start, end = availability_start_end(block)
            block_id = availability_id(block, index)
            blocks[block_id] = {
                "source_availability_window": block_id,
                "start": start,
                "end": end,
                "instructor": clean_text(block.get("instructor_name") or block.get("person_id") or UNKNOWN),
                "location": clean_text(block.get("location_name") or block.get("location") or UNKNOWN),
            }
    return blocks


def same_day_lane_matches(offer: dict[str, Any], session: dict[str, Any]) -> bool:
    offer_start = parse_dt(offer.get("scheduler_consumption_start") or offer.get("appointment_display_start") or offer.get("start_at"))
    session_start_value = session.get("start")
    if not offer_start or not session_start_value or offer_start.date() != session_start_value.date():
        return False
    same_instructor = normalize_key(offer.get("instructor")) and normalize_key(offer.get("instructor")) == normalize_key(session.get("instructor"))
    same_location = normalize_key(offer.get("location")) and normalize_key(offer.get("location")) == normalize_key(session.get("location"))
    return bool(same_instructor or same_location)


def nearest_session(offer: dict[str, Any], sessions: list[dict[str, Any]], skip_session_id: str | None = None) -> dict[str, Any] | None:
    offer_start = parse_dt(offer.get("scheduler_consumption_start") or offer.get("appointment_display_start") or offer.get("start_at"))
    if not offer_start:
        return None
    candidates = [
        session for session in sessions
        if session.get("session_id") != skip_session_id and same_day_lane_matches(offer, session) and session.get("start")
    ]
    if not candidates:
        return None
    nearest = min(candidates, key=lambda session: abs((session["start"] - offer_start).total_seconds()))
    return {
        "session_id": nearest.get("session_id", UNKNOWN),
        "course_id": nearest.get("course_id", UNKNOWN),
        "display_course_name": nearest.get("display_course_name", UNKNOWN),
        "instructor": nearest.get("instructor", UNKNOWN),
        "location": nearest.get("location", UNKNOWN),
        "start": nearest["start"].isoformat() if nearest.get("start") else None,
        "end": nearest["end"].isoformat() if nearest.get("end") else None,
        "source_file": nearest.get("source_file", UNKNOWN),
    }


def overlap_status(offer: dict[str, Any], sessions: list[dict[str, Any]], skip_session_id: str | None = None) -> str:
    display_start = parse_dt(offer.get("appointment_display_start") or offer.get("start_at"))
    display_end = parse_dt(offer.get("appointment_display_end") or offer.get("end_at"))
    lock_start = parse_dt(offer.get("scheduler_consumption_start") or offer.get("appointment_display_start") or offer.get("start_at"))
    lock_end = parse_dt(offer.get("scheduler_consumption_end") or offer.get("appointment_display_end") or offer.get("end_at"))
    if not lock_start or not lock_end:
        return "uncertain_missing_data"
    for session in sessions:
        if session.get("session_id") == skip_session_id:
            continue
        session_start_value = session.get("start")
        session_end_value = session.get("end")
        if not session_start_value or not session_end_value:
            continue
        probe = {
            "instructor": offer.get("instructor"),
            "location": offer.get("location"),
            "scheduler_consumption_start": lock_start.isoformat(),
        }
        if not same_day_lane_matches(probe, session):
            continue
        if display_start and display_end and intervals_overlap(display_start, display_end, session_start_value, session_end_value):
            return "overlaps_existing_class"
        if intervals_overlap(lock_start, lock_end, session_start_value, session_end_value):
            return "overlaps_setup_cleanup_buffer"
    return "no_overlap"


def dynamic_inside_availability(offer: dict[str, Any], availability: dict[str, dict[str, Any]]) -> bool | None:
    source_id = clean_text(offer.get("source_availability_window"))
    block = availability.get(source_id)
    start = parse_dt(offer.get("scheduler_consumption_start") or offer.get("appointment_display_start"))
    end = parse_dt(offer.get("scheduler_consumption_end") or offer.get("appointment_display_end"))
    if not block or not start or not end or not block.get("start") or not block.get("end"):
        return None
    return block["start"] <= start and end <= block["end"]


def dynamic_offer_record(
    offer: dict[str, Any],
    hidden_reasons: dict[str, list[str]],
    sessions: list[dict[str, Any]],
    availability: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_id = clean_text(offer.get("source_availability_window") or UNKNOWN)
    inside_availability = dynamic_inside_availability(offer, availability)
    public_sellable = offer.get("offer_id") not in hidden_reasons
    status = overlap_status({
        "instructor": offer.get("instructor_display_name"),
        "location": offer.get("location"),
        "appointment_display_start": offer.get("appointment_display_start"),
        "appointment_display_end": offer.get("appointment_display_end"),
        "scheduler_consumption_start": offer.get("scheduler_consumption_start"),
        "scheduler_consumption_end": offer.get("scheduler_consumption_end"),
    }, sessions)
    failure_reasons = list(hidden_reasons.get(str(offer.get("offer_id")), []))
    if inside_availability is False:
        failure_reasons.append("dynamic_offer_outside_confirmed_availability_block")
    if status != "no_overlap":
        failure_reasons.append(status)
    return {
        "offer_id": offer.get("offer_id", UNKNOWN),
        "slug": offer.get("slug") or offer.get("offer_id", UNKNOWN),
        "course_key": offer.get("course_family", UNKNOWN),
        "display_course_name": offer.get("course_title", UNKNOWN),
        "offer_source": "dynamic_appointment_seed",
        "instructor": offer.get("instructor_display_name", UNKNOWN),
        "location": offer.get("location", UNKNOWN),
        "public_display_start": offer.get("appointment_display_start") or offer.get("start_datetime"),
        "public_display_end": offer.get("appointment_display_end") or offer.get("end_datetime"),
        "scheduler_consumption_start": offer.get("scheduler_consumption_start"),
        "scheduler_consumption_end": offer.get("scheduler_consumption_end"),
        "source_availability_block_used": source_id,
        "inside_confirmed_availability_block": inside_availability,
        "matching_appointment_tuple": {
            "appointmentDayId": offer.get("appointmentDayId"),
            "startTime": offer.get("start_time"),
            "courseId": offer.get("course_id"),
        },
        "nearest_existing_enrollware_class_same_day_instructor_location": nearest_session({
            "instructor": offer.get("instructor_display_name"),
            "location": offer.get("location"),
            "scheduler_consumption_start": offer.get("scheduler_consumption_start"),
        }, sessions),
        "overlap_status": status,
        "public_sellable": public_sellable,
        "public_filter_result": "passed_public_filter" if public_sellable else "failed_public_filter",
        "public_filter_reasons": ["passed_public_sellable_filter"] if public_sellable and not failure_reasons else failure_reasons,
    }


def existing_offer_record(session: dict[str, Any], all_sessions: list[dict[str, Any]]) -> dict[str, Any]:
    session_id = session.get("session_id", UNKNOWN)
    start = session.get("start")
    end = session.get("end")
    return {
        "offer_id": session_id,
        "slug": session_id,
        "course_key": session.get("course_key", UNKNOWN),
        "display_course_name": session.get("display_course_name", UNKNOWN),
        "offer_source": "enrollware_existing_class",
        "instructor": session.get("instructor", UNKNOWN),
        "location": session.get("location", UNKNOWN),
        "public_display_start": start.isoformat() if start else None,
        "public_display_end": end.isoformat() if end else None,
        "scheduler_consumption_start": start.isoformat() if start else None,
        "scheduler_consumption_end": end.isoformat() if end else None,
        "source_availability_block_used": None,
        "inside_confirmed_availability_block": None,
        "matching_appointment_tuple": None,
        "nearest_existing_enrollware_class_same_day_instructor_location": nearest_session({
            "instructor": session.get("instructor"),
            "location": session.get("location"),
            "scheduler_consumption_start": start.isoformat() if start else None,
        }, all_sessions, skip_session_id=session_id),
        "overlap_status": overlap_status({
            "instructor": session.get("instructor"),
            "location": session.get("location"),
            "appointment_display_start": start.isoformat() if start else None,
            "appointment_display_end": end.isoformat() if end else None,
            "scheduler_consumption_start": start.isoformat() if start else None,
            "scheduler_consumption_end": end.isoformat() if end else None,
        }, all_sessions, skip_session_id=session_id),
        "public_sellable": True,
        "public_filter_result": "passed_existing_enrollware_class_filter",
        "public_filter_reasons": ["included_in_docs_data_schedule_future"],
    }


def hidden_reasons_by_offer(public_payload: Any) -> dict[str, list[str]]:
    hidden = public_payload.get("hidden_offers", []) if isinstance(public_payload, dict) else []
    out: dict[str, list[str]] = {}
    if not isinstance(hidden, list):
        return out
    for item in hidden:
        if not isinstance(item, dict) or not isinstance(item.get("offer"), dict):
            continue
        offer_id = str(item["offer"].get("offer_id") or UNKNOWN)
        out[offer_id] = [str(reason) for reason in item.get("reason_codes", [])]
    return out


def run() -> dict[str, Any]:
    dynamic_payload, dynamic_error = read_json(DYNAMIC_OFFERS_PATH)
    public_payload, public_error = read_json(PUBLIC_SELLABLE_OFFERS_PATH)
    schedule_payload, schedule_error = read_json(SCHEDULE_FUTURE_PATH)
    current_payload, current_error = read_json(SESSIONS_CURRENT_PATH)
    live_payload, live_error = read_json(LIVE_AVAILABILITY_PATH)
    legacy_payload, legacy_error = read_json(LEGACY_AVAILABILITY_PATH)

    missing = {
        name: error
        for name, error in {
            "dynamic_offers_preview": dynamic_error,
            "public_sellable_offers_preview": public_error,
            "schedule_future": schedule_error,
            "sessions_current": current_error,
            "live_availability_snapshot": live_error,
            "legacy_instructor_availability": legacy_error,
        }.items()
        if error
    }
    dynamic_payload = dynamic_payload if isinstance(dynamic_payload, dict) else {}
    public_payload = public_payload if isinstance(public_payload, dict) else {}
    schedule_sessions = normalize_sessions(schedule_payload or {}, "docs/data/schedule_future.json")
    occupancy_sessions = [
        *normalize_sessions(current_payload or {}, "data/sessions_current.json"),
        *schedule_sessions,
    ]
    availability = availability_blocks(live_payload or {}, legacy_payload or {})
    hidden_reasons = hidden_reasons_by_offer(public_payload)
    dynamic_offers = dynamic_payload.get("offers", []) if isinstance(dynamic_payload.get("offers"), list) else []
    public_dynamic_ids = {str(offer.get("offer_id")) for offer in public_payload.get("offers", []) if isinstance(offer, dict)}

    offer_records = [existing_offer_record(session, occupancy_sessions) for session in schedule_sessions]
    offer_records.extend(
        dynamic_offer_record(offer, hidden_reasons, occupancy_sessions, availability)
        for offer in dynamic_offers
        if isinstance(offer, dict) and str(offer.get("offer_id")) in public_dynamic_ids
    )

    dynamic_public_records = [item for item in offer_records if item["offer_source"] == "dynamic_appointment_seed" and item["public_sellable"]]
    fail_reasons = Counter(reason for reasons in hidden_reasons.values() for reason in reasons)
    dynamic_overlap_failures = [
        item for item in dynamic_public_records
        if item["overlap_status"] in {"overlaps_existing_class", "overlaps_setup_cleanup_buffer"}
    ]
    outside_availability_failures = [
        item for item in dynamic_public_records
        if item["inside_confirmed_availability_block"] is False
    ]
    duplicate_dynamic_existing = [
        item for item in dynamic_public_records
        if item["nearest_existing_enrollware_class_same_day_instructor_location"]
        and item["public_display_start"] == item["nearest_existing_enrollware_class_same_day_instructor_location"].get("start")
        and normalize_key(item["display_course_name"]) == normalize_key(item["nearest_existing_enrollware_class_same_day_instructor_location"].get("display_course_name"))
    ]
    failed = bool(dynamic_overlap_failures or outside_availability_failures or duplicate_dynamic_existing)

    stats = {
        "existing_enrollware_classes_shown": len(schedule_sessions),
        "dynamic_appointment_seed_offers_generated": int(dynamic_payload.get("stats", {}).get("offers_generated", len(dynamic_offers))) if isinstance(dynamic_payload.get("stats"), dict) else len(dynamic_offers),
        "public_sellable_dynamic_appointment_seed_offers": len(dynamic_public_records),
        "dynamic_offers_blocked_by_occupancy_overlap": int(dynamic_payload.get("stats", {}).get("offers_rejected_by_reason", {}).get("conflicts_with_existing_occupancy", 0)) if isinstance(dynamic_payload.get("stats"), dict) else 0,
        "dynamic_offers_blocked_by_lead_time": fail_reasons.get("inside_minimum_lead_time", 0),
        "dynamic_offers_blocked_by_insufficient_gap": int(dynamic_payload.get("stats", {}).get("offers_rejected_by_reason", {}).get("course_does_not_fit_window", 0)) if isinstance(dynamic_payload.get("stats"), dict) else 0,
        "dynamic_offers_blocked_by_missing_ids": sum(fail_reasons.get(reason, 0) for reason in ("course_not_found", "unknown_offer_start", "missing_container_for_instructor", "no_matching_appointment_container", "date_outside_container_range")),
        "public_sellable_total": sum(1 for item in offer_records if item["public_sellable"]),
        "availability_blocks_indexed": len(availability),
        "audit_failed": failed,
        "public_sellable_dynamic_overlap_failures": len(dynamic_overlap_failures),
        "public_sellable_dynamic_outside_availability_failures": len(outside_availability_failures),
        "public_sellable_dynamic_duplicate_existing_class_failures": len(duplicate_dynamic_existing),
        "top_public_filter_rejection_reasons": dict(fail_reasons.most_common(20)),
    }
    report = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "public_site_affected": False,
        "deployed": False,
        "files_missing_or_unreadable": missing,
        "validation_rules": {
            "dynamic_offers_inside_confirmed_inverse_availability": not outside_availability_failures,
            "dynamic_offers_do_not_overlap_existing_classes_or_buffers": not dynamic_overlap_failures,
            "existing_enrollware_classes_not_duplicated_as_dynamic": not duplicate_dynamic_existing,
            "public_output_distinguishes_offer_source": True,
        },
        "stats": stats,
        "offers": offer_records,
        "failures": {
            "dynamic_overlap_failures": dynamic_overlap_failures,
            "dynamic_outside_availability_failures": outside_availability_failures,
            "dynamic_duplicate_existing_class_failures": duplicate_dynamic_existing,
        },
    }
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_MD_PATH.write_text(render_markdown(report), encoding="utf-8")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    stats = report["stats"]
    lines = [
        "# Public Offer Integrity Report",
        "",
        "Read-only audit. No Enrollware calls, appointments, public pages, Worker settings, docs output, or deployment were changed.",
        "",
        "## Verdict",
        "",
        f"- Audit failed: {stats['audit_failed']}",
        f"- Public sellable dynamic overlap failures: {stats['public_sellable_dynamic_overlap_failures']}",
        f"- Public sellable dynamic outside-availability failures: {stats['public_sellable_dynamic_outside_availability_failures']}",
        f"- Public sellable dynamic duplicates of existing classes: {stats['public_sellable_dynamic_duplicate_existing_class_failures']}",
        "",
        "## Counts",
        "",
        f"- Existing Enrollware classes shown: {stats['existing_enrollware_classes_shown']}",
        f"- Dynamic appointment-seed offers generated: {stats['dynamic_appointment_seed_offers_generated']}",
        f"- Public sellable dynamic appointment-seed offers: {stats['public_sellable_dynamic_appointment_seed_offers']}",
        f"- Dynamic offers blocked by occupancy overlap: {stats['dynamic_offers_blocked_by_occupancy_overlap']}",
        f"- Dynamic offers blocked by lead time: {stats['dynamic_offers_blocked_by_lead_time']}",
        f"- Dynamic offers blocked by insufficient gap: {stats['dynamic_offers_blocked_by_insufficient_gap']}",
        f"- Dynamic offers blocked by missing IDs: {stats['dynamic_offers_blocked_by_missing_ids']}",
        f"- Public sellable total: {stats['public_sellable_total']}",
        "",
        "## Top Public Filter Rejection Reasons",
        "",
    ]
    if stats["top_public_filter_rejection_reasons"]:
        lines.extend(f"- `{reason}`: {count}" for reason, count in stats["top_public_filter_rejection_reasons"].items())
    else:
        lines.append("- None")
    lines.extend(["", "## Public-Facing Offers", ""])
    offers = report.get("offers", [])
    if offers:
        lines.extend(["| Source | Offer | Course | Instructor | Location | Display | Lock | Overlap | Sellable | Reason |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"])
        for item in offers:
            reason = ", ".join(item.get("public_filter_reasons") or []) or UNKNOWN
            lines.append(
                f"| {item.get('offer_source', UNKNOWN)} | `{item.get('offer_id', UNKNOWN)}` | {item.get('display_course_name', UNKNOWN)} | "
                f"{item.get('instructor', UNKNOWN)} | {item.get('location', UNKNOWN)} | {item.get('public_display_start')} to {item.get('public_display_end')} | "
                f"{item.get('scheduler_consumption_start')} to {item.get('scheduler_consumption_end')} | {item.get('overlap_status', UNKNOWN)} | "
                f"{item.get('public_sellable')} | {reason} |"
            )
    else:
        lines.append("- No public-facing offers found.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = run()
    stats = report["stats"]
    print("Public offer integrity audit complete (READ ONLY).")
    print("No deployment performed.")
    print("")
    print(f"Existing Enrollware classes shown: {stats['existing_enrollware_classes_shown']}")
    print(f"Dynamic appointment-seed offers generated: {stats['dynamic_appointment_seed_offers_generated']}")
    print(f"Dynamic offers blocked by occupancy overlap: {stats['dynamic_offers_blocked_by_occupancy_overlap']}")
    print(f"Dynamic offers blocked by lead time: {stats['dynamic_offers_blocked_by_lead_time']}")
    print(f"Dynamic offers blocked by insufficient gap: {stats['dynamic_offers_blocked_by_insufficient_gap']}")
    print(f"Dynamic offers blocked by missing IDs: {stats['dynamic_offers_blocked_by_missing_ids']}")
    print(f"Public sellable total: {stats['public_sellable_total']}")
    print(f"Audit failed: {stats['audit_failed']}")
    print("")
    print("Output files:")
    print(f"- {REPORT_MD_PATH}")
    print(f"- {REPORT_JSON_PATH}")
    return 1 if stats["audit_failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
