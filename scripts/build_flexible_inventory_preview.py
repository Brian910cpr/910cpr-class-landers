from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("America/New_York")

SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
AVAILABILITY_PATHS = [
    ROOT / "docs" / "data" / "instructor_availability.json",
    ROOT / "data" / "inventory" / "instructor_availability.json",
]
PROFILE_PATH = ROOT / "docs" / "data" / "instructor_profiles.json"
APPOINTMENT_RANGE_PATH = ROOT / "docs" / "data" / "appointment_range_registry.json"
APPOINTMENT_CONTAINER_PATH = ROOT / "data" / "inventory" / "appointment_containers.json"
COURSE_RULES_PATH = ROOT / "data" / "inventory" / "course_consumption_rules.json"
HUB_CONFIG_PATH = ROOT / "data" / "config" / "slug_hubs.json"
OUTPUT_PATH = ROOT / "debug" / "flexible_inventory_preview.json"
SUMMARY_PATH = ROOT / "debug" / "flexible_inventory_preview_summary.md"

SLOT_LENGTHS = {
    "BLS": 120,
    "Heartsaver": 120,
    "ACLS": 180,
    "PALS": 180,
    "HeartCode": 150,
    "HSI": 120,
    "ARC": 120,
}
DEFAULT_SLOT_LENGTH = 120
START_STEP_MINUTES = 30
MAX_CANDIDATES_PER_BLOCK_FAMILY = 8


def load_json(path: Path, default: Any) -> tuple[Any, str | None]:
    if not path.exists():
        return default, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return default, f"invalid_json: {exc}"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def clean_text(value: Any) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = text.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean_text(value).lower())


def instructor_key(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    parts = re.findall(r"[A-Za-z]+", text)
    if not parts:
        return normalize_key(text)
    if len(parts) == 1:
        return normalize_key(parts[0])
    return normalize_key(parts[0][0] + parts[-1])


def location_key(value: Any) -> str:
    text = clean_text(value).lower()
    text = text.replace("::", " ")
    replacements = {
        "nc - wilmington": "wilmington",
        "910cpr's office": "shipyard",
        "4018 shipyard blvd": "shipyard",
        "wilmington; shipyard blvd": "shipyard",
        "wilmington shipyard": "shipyard",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return normalize_key(text)


def parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def parse_time(value: Any) -> time | None:
    if not value:
        return None
    try:
        return time.fromisoformat(str(value)[:5])
    except ValueError:
        return None


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def combine(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock, tzinfo=TZ)


def time_label(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def read_schedule(warnings: list[str]) -> list[dict[str, Any]]:
    payload, err = load_json(SCHEDULE_PATH, {"sessions": []})
    if err:
        warnings.append(f"{rel(SCHEDULE_PATH)} {err}; scheduled conflict checks will be incomplete.")
        return []
    sessions = payload.get("sessions", payload) if isinstance(payload, dict) else payload
    if not isinstance(sessions, list):
        warnings.append(f"{rel(SCHEDULE_PATH)} did not contain a sessions list; scheduled conflict checks will be incomplete.")
        return []
    return [row for row in sessions if isinstance(row, dict)]


def read_availability(warnings: list[str]) -> tuple[list[dict[str, Any]], Path | None]:
    missing = []
    for path in AVAILABILITY_PATHS:
        payload, err = load_json(path, {"availability_blocks": []})
        if err:
            missing.append(f"{rel(path)} {err}")
            continue
        blocks = payload.get("availability_blocks", payload) if isinstance(payload, dict) else payload
        if isinstance(blocks, list):
            return [row for row in blocks if isinstance(row, dict)], path
        warnings.append(f"{rel(path)} did not contain an availability_blocks list.")
    warnings.append("No usable instructor availability file found: " + "; ".join(missing))
    return [], None


def normalize_availability_block(block: dict[str, Any], index: int) -> dict[str, Any] | None:
    day = parse_date(block.get("date") or block.get("available_date"))
    start = parse_time(block.get("available_start") or block.get("start_time") or block.get("start"))
    end = parse_time(block.get("available_end") or block.get("end_time") or block.get("end"))
    instructor = clean_text(block.get("instructor") or block.get("instructor_name") or block.get("owner"))
    if not day or not start or not end or not instructor:
        return None
    location = clean_text(block.get("location") or block.get("location_name") or block.get("resource") or "")
    return {
        "block_id": clean_text(block.get("block_id")) or f"availability_{index}",
        "instructor": instructor,
        "instructor_key": instructor_key(instructor),
        "date": day,
        "start": combine(day, start),
        "end": combine(day, end),
        "location": location,
        "location_key": location_key(location),
        "room": clean_text(block.get("room") or block.get("room_or_resource") or block.get("room_or_resource_name")),
        "notes": clean_text(block.get("notes")),
        "source": clean_text(block.get("source")) or "unknown",
        "allowed_course_families": [clean_text(item) for item in block.get("allowed_course_families", []) if clean_text(item)],
        "preferred_course_families": [clean_text(item) for item in block.get("preferred_course_families", []) if clean_text(item)],
        "raw": block,
    }


def normalize_session(session: dict[str, Any]) -> dict[str, Any] | None:
    start = parse_dt(session.get("start_at") or session.get("start"))
    end = parse_dt(session.get("end_at") or session.get("end"))
    if not start:
        return None
    if not end or end <= start:
        end = start + timedelta(hours=2)
    instructor = clean_text(
        session.get("lead_instructor_name")
        or session.get("instructor")
        or session.get("lead_instructor")
        or ""
    )
    location = clean_text(session.get("location_display") or session.get("location_name") or "")
    return {
        "session_id": clean_text(session.get("session_id") or session.get("id")),
        "course_name": clean_text(session.get("course_name") or session.get("official_course_name") or session.get("raw_course_name")),
        "course_family": clean_text(session.get("mapped_family") or session.get("course_family")),
        "start": start,
        "end": end,
        "date": start.date(),
        "instructor": instructor,
        "instructor_key": instructor_key(instructor),
        "location": location,
        "location_key": location_key(location),
        "room": clean_text(session.get("room") or session.get("room_or_resource") or ""),
    }


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def load_profiles(warnings: list[str]) -> dict[str, dict[str, Any]]:
    payload, err = load_json(PROFILE_PATH, {"instructors": []})
    if err:
        warnings.append(f"{rel(PROFILE_PATH)} {err}; instructor eligibility will be unknown unless embedded in availability.")
        return {}
    profiles = payload.get("instructors", []) if isinstance(payload, dict) else []
    result = {}
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        names = [profile.get("display_name"), profile.get("short_name"), profile.get("id")]
        for name in names:
            key = instructor_key(name)
            if key:
                result[key] = profile
    return result


def load_course_families(warnings: list[str]) -> list[str]:
    payload, err = load_json(COURSE_RULES_PATH, {"rules": []})
    if err:
        warnings.append(f"{rel(COURSE_RULES_PATH)} {err}; using built-in simple course families.")
        return list(SLOT_LENGTHS)
    families = []
    for rule in payload.get("rules", []):
        family = clean_text(rule.get("course_family")) if isinstance(rule, dict) else ""
        if family and family not in families:
            families.append(family)
    return families or list(SLOT_LENGTHS)


def appointment_ranges(warnings: list[str]) -> list[dict[str, Any]]:
    ranges: list[dict[str, Any]] = []
    payload, err = load_json(APPOINTMENT_RANGE_PATH, {"ranges": []})
    if err:
        warnings.append(f"{rel(APPOINTMENT_RANGE_PATH)} {err}; appointmentDayId prediction from registry unavailable.")
    else:
        ranges.extend(payload.get("ranges", []) if isinstance(payload, dict) else [])

    payload, err = load_json(APPOINTMENT_CONTAINER_PATH, {"containers": []})
    if err:
        warnings.append(f"{rel(APPOINTMENT_CONTAINER_PATH)} {err}; appointment container verification unavailable.")
    else:
        for item in payload.get("containers", []) if isinstance(payload, dict) else []:
            if isinstance(item, dict):
                ranges.append(
                    {
                        "range_id": item.get("container_id"),
                        "owner": item.get("instructor_name"),
                        "location": item.get("location_name"),
                        "verified_date": item.get("base_date") or item.get("first_valid_date"),
                        "verified_appointmentDayId": item.get("base_appointmentDayId") or item.get("first_valid_appointmentDayId"),
                        "last_valid_date": item.get("last_valid_date"),
                        "last_valid_appointmentDayId": item.get("last_valid_appointmentDayId"),
                        "generation_mode": "daily_contiguous",
                        "status": item.get("status"),
                        "source": "appointment_containers",
                    }
                )
    return [row for row in ranges if isinstance(row, dict)]


def appointment_mapping_for(candidate: dict[str, Any], ranges: list[dict[str, Any]]) -> dict[str, Any]:
    c_day = parse_date(candidate["date"])
    c_instructor = instructor_key(candidate["instructor"])
    c_location = location_key(candidate.get("location"))
    if not c_day:
        return {"status": "no_url", "url": None, "range_id": None}

    for row in ranges:
        owner_key = instructor_key(row.get("owner") or row.get("instructor_name"))
        if owner_key and owner_key != c_instructor:
            continue
        row_location = location_key(row.get("location") or row.get("location_name"))
        if row_location and c_location and row_location != c_location and "shipyard" not in {row_location, c_location}:
            continue

        verified_day = parse_date(row.get("verified_date") or row.get("start_date") or row.get("base_date"))
        last_day = parse_date(row.get("last_valid_date"))
        verified_id = row.get("verified_appointmentDayId") or row.get("start_appointmentDayId") or row.get("base_appointmentDayId")
        if not verified_day or not last_day or verified_id is None:
            continue
        if not (verified_day <= c_day <= last_day):
            continue
        if row.get("generation_mode") != "daily_contiguous":
            return {"status": "no_url", "url": None, "range_id": row.get("range_id")}
        appointment_id = int(verified_id) + (c_day - verified_day).days
        if row.get("source") == "appointment_containers" or row.get("status") == "active":
            status = "verified_url"
        else:
            status = "predicted_url"
        return {
            "status": status,
            "url": f"https://coastalcprtraining.enrollware.com/enroll?appointmentDayId={appointment_id}",
            "range_id": row.get("range_id"),
        }
    return {"status": "blocked_no_appointment_mapping", "url": None, "range_id": None}


def conflicts_for(candidate: dict[str, Any], sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    conflicts = []
    c_start = candidate["_start_dt"]
    c_end = candidate["_end_dt"]
    c_instructor = instructor_key(candidate["instructor"])
    c_location = location_key(candidate.get("location"))
    c_room = normalize_key(candidate.get("room"))
    for session in sessions:
        if session["date"] != c_start.date():
            continue
        if not overlaps(c_start, c_end, session["start"], session["end"]):
            continue
        reason_parts = []
        if c_instructor and session["instructor_key"] and c_instructor == session["instructor_key"]:
            reason_parts.append("same_instructor")
        if c_room and normalize_key(session.get("room")) and c_room == normalize_key(session.get("room")):
            reason_parts.append("same_room")
        if c_location and session["location_key"] and c_location == session["location_key"]:
            reason_parts.append("same_time_location")
        if not reason_parts:
            continue
        conflicts.append(
            {
                "session_id": session.get("session_id"),
                "course_name": session.get("course_name"),
                "start_time": time_label(session["start"]),
                "end_time": time_label(session["end"]),
                "reason": ",".join(reason_parts),
            }
        )
    return conflicts


def score_candidate(
    *,
    has_availability: bool,
    conflicts: list[dict[str, Any]],
    room_known: bool,
    eligibility_known: bool,
    appointment_status: str,
    warnings: list[str],
) -> int:
    score = 0
    if has_availability:
        score += 30
    if not conflicts:
        score += 20
    if room_known:
        score += 15
    if eligibility_known:
        score += 15
    if appointment_status in {"verified_url", "predicted_url"}:
        score += 20
    score -= min(30, len(warnings) * 5)
    if conflicts:
        score -= 30
    if appointment_status == "blocked_no_appointment_mapping":
        score -= 10
    return max(0, min(100, score))


def candidate_status(conflicts: list[dict[str, Any]], warnings: list[str], appointment_status: str, confidence: int, eligibility_known: bool, room_known: bool) -> str:
    if conflicts:
        return "blocked_conflict"
    if not eligibility_known:
        return "low_confidence"
    if appointment_status == "blocked_no_appointment_mapping":
        return "blocked_no_appointment_mapping"
    if not room_known and confidence < 65:
        return "blocked_missing_room"
    if confidence < 60:
        return "low_confidence"
    if appointment_status in {"verified_url", "predicted_url"} and confidence >= 80:
        return "public_ready_candidate"
    return "viable_internal"


def generate_candidates() -> dict[str, Any]:
    warnings: list[str] = []
    schedule = [item for item in (normalize_session(row) for row in read_schedule(warnings)) if item]
    availability_raw, availability_path = read_availability(warnings)
    availability = []
    for index, block in enumerate(availability_raw, start=1):
        normalized = normalize_availability_block(block, index)
        if normalized:
            availability.append(normalized)
        else:
            warnings.append(f"Skipped malformed availability block at index {index}.")

    profiles = load_profiles(warnings)
    families_from_rules = load_course_families(warnings)
    ranges = appointment_ranges(warnings)

    now = datetime.now(TZ)
    candidates: list[dict[str, Any]] = []
    for block in availability:
        if block["end"] <= now:
            continue
        if block["date"].weekday() == 6 and not re.search(r"\bsunday\b", block["notes"], flags=re.I):
            warnings.append(f"Skipped Sunday availability block {block['block_id']} because Sunday was not explicitly allowed.")
            continue

        profile = profiles.get(block["instructor_key"], {})
        allowed = block["allowed_course_families"] or profile.get("allowed_families") or families_from_rules
        eligible_known = bool(block["allowed_course_families"] or profile.get("allowed_families"))
        room_known = bool(block["room"])
        base_warnings = []
        if not eligible_known:
            base_warnings.append("Instructor eligibility source missing; allowed course families are inferred from generic course rules.")
        if not room_known:
            base_warnings.append("Room/resource availability is unknown; location is known but no room/resource was recorded.")

        for family in allowed:
            family = clean_text(family)
            duration = SLOT_LENGTHS.get(family, DEFAULT_SLOT_LENGTH)
            cursor = block["start"]
            generated_for_family = 0
            while cursor + timedelta(minutes=duration) <= block["end"] and generated_for_family < MAX_CANDIDATES_PER_BLOCK_FAMILY:
                if cursor <= now:
                    cursor += timedelta(minutes=START_STEP_MINUTES)
                    continue
                end = cursor + timedelta(minutes=duration)
                candidate: dict[str, Any] = {
                    "date": cursor.date().isoformat(),
                    "start_time": time_label(cursor),
                    "end_time": time_label(end),
                    "instructor": block["instructor"],
                    "location": block["location"] or profile.get("default_location") or None,
                    "room": block["room"] or None,
                    "course_family": family,
                    "eligible_course_families": allowed,
                    "unknown_eligibility_warnings": [] if eligible_known else ["instructor_course_eligibility_unknown"],
                    "_start_dt": cursor,
                    "_end_dt": end,
                }
                conflicts = conflicts_for(candidate, schedule)
                appointment = appointment_mapping_for(candidate, ranges)
                item_warnings = list(base_warnings)
                if appointment["status"] == "blocked_no_appointment_mapping":
                    item_warnings.append("No verified or predictable appointmentDayId mapping found for this instructor/date/location.")
                confidence = score_candidate(
                    has_availability=True,
                    conflicts=conflicts,
                    room_known=room_known,
                    eligibility_known=eligible_known,
                    appointment_status=appointment["status"],
                    warnings=item_warnings,
                )
                status = candidate_status(conflicts, item_warnings, appointment["status"], confidence, eligible_known, room_known)
                reason_bits = []
                if conflicts:
                    reason_bits.append("Blocked by scheduled-session conflict.")
                else:
                    reason_bits.append("Instructor available and no scheduled conflict found.")
                if appointment["status"] in {"verified_url", "predicted_url"}:
                    reason_bits.append(f"Appointment URL status: {appointment['status']}.")
                else:
                    reason_bits.append("Appointment URL not verified or mapped.")
                if not room_known:
                    reason_bits.append("Room/resource unknown.")

                candidate.update(
                    {
                        "status": status,
                        "confidence_score": confidence,
                        "appointment_url_status": appointment["status"],
                        "appointment_url": appointment["url"] if appointment["status"] == "verified_url" else None,
                        "appointment_range_id": appointment["range_id"],
                        "public_bookable": status == "public_ready_candidate" and appointment["status"] == "verified_url",
                        "conflicts": conflicts,
                        "warnings": item_warnings,
                        "reason": " ".join(reason_bits),
                        "source_availability_block_id": block["block_id"],
                        "source": block["source"],
                    }
                )
                candidate.pop("_start_dt")
                candidate.pop("_end_dt")
                candidates.append(candidate)
                generated_for_family += 1
                cursor += timedelta(minutes=START_STEP_MINUTES)

    status_counts = Counter(item["status"] for item in candidates)
    summary = {
        "candidate_slots_total": len(candidates),
        "public_ready_candidates": status_counts.get("public_ready_candidate", 0),
        "blocked_conflicts": status_counts.get("blocked_conflict", 0),
        "low_confidence": status_counts.get("low_confidence", 0),
        "status_counts": dict(sorted(status_counts.items())),
    }

    source_files = {
        "schedule_future": {"path": rel(SCHEDULE_PATH), "found": SCHEDULE_PATH.exists()},
        "instructor_availability": {"path": rel(availability_path) if availability_path else None, "found": availability_path is not None},
        "instructor_profiles": {"path": rel(PROFILE_PATH), "found": PROFILE_PATH.exists()},
        "appointment_range_registry": {"path": rel(APPOINTMENT_RANGE_PATH), "found": APPOINTMENT_RANGE_PATH.exists()},
        "appointment_containers": {"path": rel(APPOINTMENT_CONTAINER_PATH), "found": APPOINTMENT_CONTAINER_PATH.exists()},
        "course_consumption_rules": {"path": rel(COURSE_RULES_PATH), "found": COURSE_RULES_PATH.exists()},
        "slug_hubs": {"path": rel(HUB_CONFIG_PATH), "found": HUB_CONFIG_PATH.exists()},
    }

    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "schema_version": "0.1",
        "source_files": source_files,
        "overall_status": "preview",
        "summary": summary,
        "warnings": sorted(set(warnings)),
        "candidates": sorted(candidates, key=lambda row: (-row["confidence_score"], row["date"], row["start_time"], row["course_family"])),
    }


def write_summary(audit: dict[str, Any]) -> None:
    candidates = audit["candidates"]
    top = candidates[:20]
    blocked = [item for item in candidates if item["status"].startswith("blocked")][:20]
    lines = [
        "# Flexible Inventory Preview",
        "",
        f"- Generated: {audit['generated_at']}",
        f"- Overall status: {audit['overall_status']}",
        f"- Candidate slots: {audit['summary']['candidate_slots_total']}",
        f"- Public-ready candidates: {audit['summary']['public_ready_candidates']}",
        f"- Internal viable candidates: {audit['summary']['status_counts'].get('viable_internal', 0)}",
        f"- Low-confidence candidates: {audit['summary']['low_confidence']}",
        "",
        "## Missing Input / Resolver Warnings",
        "",
    ]
    if audit["warnings"]:
        lines.extend(f"- {warning}" for warning in audit["warnings"])
    else:
        lines.append("- None.")

    lines.extend(["", "## Top 20 Candidates", "", "| Date | Time | Instructor | Family | Status | Confidence | URL | Reason |", "| --- | --- | --- | --- | --- | ---: | --- | --- |"])
    for item in top:
        lines.append(
            f"| {item['date']} | {item['start_time']}-{item['end_time']} | {item['instructor']} | {item['course_family']} | {item['status']} | {item['confidence_score']} | {item['appointment_url_status']} | {item['reason']} |"
        )

    lines.extend(["", "## Blocked Conflicts / Blockers", "", "| Date | Time | Instructor | Family | Status | Conflicts | Warnings |", "| --- | --- | --- | --- | --- | --- | --- |"])
    if blocked:
        for item in blocked:
            conflict_text = "; ".join(f"{c.get('session_id')} {c.get('reason')}" for c in item["conflicts"]) or "none"
            warning_text = "; ".join(item["warnings"]) or "none"
            lines.append(
                f"| {item['date']} | {item['start_time']}-{item['end_time']} | {item['instructor']} | {item['course_family']} | {item['status']} | {conflict_text} | {warning_text} |"
            )
    else:
        lines.append("| none |  |  |  |  |  |  |")

    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    audit = generate_candidates()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    write_summary(audit)
    print(f"Wrote {rel(OUTPUT_PATH)}")
    print(f"Wrote {rel(SUMMARY_PATH)}")
    print(f"Candidate slots: {audit['summary']['candidate_slots_total']}")
    print(f"Public-ready candidates: {audit['summary']['public_ready_candidates']}")


if __name__ == "__main__":
    main()
