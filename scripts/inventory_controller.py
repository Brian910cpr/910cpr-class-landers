from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
INVENTORY_DIR = ROOT / "data" / "inventory"
DEBUG_DIR = ROOT / "debug"
APPOINTMENT_CONTAINERS_PATH = INVENTORY_DIR / "appointment_containers.json"
COURSE_RULES_PATH = INVENTORY_DIR / "course_consumption_rules.json"
AVAILABILITY_PATH = INVENTORY_DIR / "instructor_availability.json"
MOCK_ANCHORS_PATH = INVENTORY_DIR / "mock_anchor_bookings.json"
CANDIDATES_PATH = DEBUG_DIR / "inventory_controller_candidates.json"
PUBLIC_OFFERINGS_PATH = DEBUG_DIR / "inventory_controller_public_offerings.json"
SUPPRESSED_PATH = DEBUG_DIR / "inventory_controller_suppressed.json"
AUDIT_PATH = DEBUG_DIR / "inventory_controller_audit.md"
ENROLLWARE_ENROLL_BASE = "https://coastalcprtraining.enrollware.com/enroll"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def parse_time(value: str) -> time:
    return datetime.strptime(value, "%H:%M").time()


def display_time(value: time) -> str:
    return datetime.combine(date(2000, 1, 1), value).strftime("%I:%M %p").lstrip("0")


def minutes_between(start: time, end: time) -> int:
    start_dt = datetime.combine(date(2000, 1, 1), start)
    end_dt = datetime.combine(date(2000, 1, 1), end)
    return int((end_dt - start_dt).total_seconds() // 60)


def add_minutes(value: time, minutes: int) -> time:
    return (datetime.combine(date(2000, 1, 1), value) + timedelta(minutes=minutes)).time()


def time_to_minutes(value: time) -> int:
    return value.hour * 60 + value.minute


def intervals_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
    return time_to_minutes(start_a) < time_to_minutes(end_b) and time_to_minutes(start_b) < time_to_minutes(end_a)


def find_container(containers: list[dict[str, Any]], location_name: str) -> dict[str, Any] | None:
    for container in containers:
        if container.get("status") != "active":
            continue
        if container.get("location_name") == location_name:
            return container
    return None


def compute_appointment_day_id(container: dict[str, Any], target_date: date) -> int:
    base = parse_date(container["base_date"])
    return int(container["base_appointmentDayId"]) + (target_date - base).days


def validate_appointment_day_id(container: dict[str, Any], target_date: date) -> tuple[bool, int, str]:
    appointment_day_id = compute_appointment_day_id(container, target_date)
    if target_date < parse_date(container["first_valid_date"]):
        return False, appointment_day_id, "date_before_owned_appointment_range"
    if target_date > parse_date(container["last_valid_date"]):
        return False, appointment_day_id, "date_after_owned_appointment_range"
    if appointment_day_id < int(container["first_valid_appointmentDayId"]):
        return False, appointment_day_id, "appointmentDayId_before_owned_range"
    if appointment_day_id > int(container["last_valid_appointmentDayId"]):
        return False, appointment_day_id, "appointmentDayId_after_owned_range"
    if appointment_day_id >= int(container["first_invalid_appointmentDayId"]):
        return False, appointment_day_id, "appointmentDayId_reaches_first_invalid_boundary"
    return True, appointment_day_id, "owned_appointment_container"


def build_registration_url(appointment_day_id: int, start_time: time, course_id: str) -> str:
    return (
        f"{ENROLLWARE_ENROLL_BASE}?appointmentDayId={appointment_day_id}"
        f"&startTime={quote(display_time(start_time))}"
        f"&courseId={quote(str(course_id))}"
    )


def course_bucket(rule: dict[str, Any]) -> str:
    name = str(rule.get("clean_course_name") or "")
    if "HeartCode" in name:
        return "HeartCode"
    return str(rule.get("course_family") or "")


def block_allows_course(block: dict[str, Any], rule: dict[str, Any], *, anchor_exists: bool) -> tuple[bool, str]:
    family = str(rule.get("course_family") or "")
    bucket = course_bucket(rule)
    allowed = set(block.get("allowed_course_families", []))
    fallback = set(block.get("fallback_course_families", []))
    anchor_families = set(block.get("anchor_course_families", []))

    if block.get("anchor_required") and not anchor_exists:
        if rule.get("anchor_eligible") and family in anchor_families:
            return True, "anchor_candidate_allowed_before_anchor"
        return False, "anchor_required_unmet_non_anchor_suppressed"

    if family in allowed or family in fallback or bucket in allowed or bucket in fallback:
        return True, "course_family_allowed_by_block"
    return False, "course_family_not_allowed_by_block"


def anchor_bookings_for_block(block: dict[str, Any], bookings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        booking for booking in bookings
        if booking.get("instructor_name") == block.get("instructor_name")
        and booking.get("date") == block.get("date")
    ]


def candidate_start_times(start: time, end: time) -> list[time]:
    starts: list[time] = []
    current = start
    while current < end:
        starts.append(current)
        current = add_minutes(current, 60)
    return starts


def score_candidate(
    rule: dict[str, Any],
    block: dict[str, Any],
    candidate_end: time,
    block_end: time,
    reasons: list[str],
) -> int:
    score = int(rule.get("public_priority", 50))
    leftover = minutes_between(candidate_end, block_end)
    min_useful = 60

    if leftover == 0:
        score += 10
        reasons.append("no_unusable_tail_fragment")
    elif leftover >= min_useful:
        score += 6
        reasons.append("remaining_fragment_can_support_small_course")
    else:
        score -= 20
        reasons.append("remaining_fragment_too_small")

    if block.get("anchor_required") and rule.get("anchor_eligible"):
        score += 15
        reasons.append("anchor_candidate_protects_trip_value")

    return score


@dataclass
class Candidate:
    scenario: str
    block_id: str
    instructor: str
    location: str
    date: str
    start_time: str
    end_time: str
    course_id: str
    course_name: str
    course_family: str
    duration_minutes: int
    appointmentDayId: int | None
    registration_url: str
    score: int
    status: str
    reasons: list[str]


def generate_inventory(anchor_scenario: str | None = None) -> dict[str, Any]:
    containers = load_json(APPOINTMENT_CONTAINERS_PATH)["containers"]
    rules_config = load_json(COURSE_RULES_PATH)
    course_rules = [rule for rule in rules_config["rules"] if rule.get("appointment_eligible")]
    availability_blocks = load_json(AVAILABILITY_PATH)["availability_blocks"]
    mock_anchor_config = load_json(MOCK_ANCHORS_PATH)
    scenario_name = anchor_scenario or mock_anchor_config.get("active_scenario", "no_anchor_case")
    scenario = mock_anchor_config["scenarios"][scenario_name]
    bookings = scenario.get("bookings", [])

    candidates: list[Candidate] = []
    public_counts: dict[tuple[str, str, str], int] = {}

    for block_index, block in enumerate(availability_blocks, start=1):
        block_id = f"{block['instructor_name']}|{block['date']}|{block['start_time']}|{block['end_time']}|{block_index}"
        target_date = parse_date(block["date"])
        block_start = parse_time(block["start_time"])
        block_end = parse_time(block["end_time"])
        container = find_container(containers, block["location_name"])
        anchor_bookings = anchor_bookings_for_block(block, bookings)
        anchor_exists = any(booking.get("anchor") for booking in anchor_bookings)

        if not container:
            for rule in course_rules:
                candidates.append(Candidate(
                    scenario=scenario_name,
                    block_id=block_id,
                    instructor=block["instructor_name"],
                    location=block["location_name"],
                    date=block["date"],
                    start_time=block["start_time"],
                    end_time=block["end_time"],
                    course_id=str(rule["course_id"]),
                    course_name=str(rule["clean_course_name"]),
                    course_family=str(rule["course_family"]),
                    duration_minutes=int(rule["duration_minutes"]),
                    appointmentDayId=None,
                    registration_url="",
                    score=0,
                    status="invalid",
                    reasons=["no_owned_appointment_container_for_location"],
                ))
            continue

        owned, appointment_day_id, range_reason = validate_appointment_day_id(container, target_date)

        for rule in course_rules:
            allowed, allow_reason = block_allows_course(block, rule, anchor_exists=anchor_exists)
            duration = int(rule.get("minimum_reservation_block_minutes") or rule["duration_minutes"])
            starts = candidate_start_times(block_start, block_end)

            for start in starts:
                end = add_minutes(start, duration)
                reasons = [range_reason, allow_reason]
                score = 0
                status = "suppressed"
                registration_url = ""

                if not owned:
                    status = "invalid"
                    reasons.append("registration_url_not_generated_outside_owned_range")
                elif block.get("availability_status") not in {"available", "diagnostic_out_of_range"}:
                    reasons.append("availability_status_not_public")
                elif not allowed:
                    reasons.append("course_hidden_by_anchor_or_family_policy")
                elif end > block_end:
                    reasons.append("course_does_not_fit_contiguous_block")
                elif any(intervals_overlap(start, end, parse_time(b["start_time"]), parse_time(b["end_time"])) for b in anchor_bookings):
                    reasons.append("overlaps_existing_anchor_booking")
                elif block.get("anchor_required") and anchor_exists and not rule.get("post_anchor_eligible"):
                    reasons.append("anchor_already_exists_anchor_course_not_icing")
                else:
                    reasons.append("course_fits_contiguous_block")
                    score = score_candidate(rule, block, end, block_end, reasons)
                    key = (block_id, str(rule["course_id"]), scenario_name)
                    max_public = int(rule.get("max_public_candidates_per_block", 1))
                    if public_counts.get(key, 0) >= max_public:
                        score -= 30
                        reasons.append("duplicate_same_course_too_close_in_block")
                    if score >= 50:
                        status = "public"
                        public_counts[key] = public_counts.get(key, 0) + 1
                        registration_url = build_registration_url(appointment_day_id, start, str(rule["course_id"]))
                    else:
                        reasons.append("score_below_public_threshold")

                candidates.append(Candidate(
                    scenario=scenario_name,
                    block_id=block_id,
                    instructor=block["instructor_name"],
                    location=block["location_name"],
                    date=block["date"],
                    start_time=display_time(start),
                    end_time=display_time(end),
                    course_id=str(rule["course_id"]),
                    course_name=str(rule["clean_course_name"]),
                    course_family=str(rule["course_family"]),
                    duration_minutes=duration,
                    appointmentDayId=appointment_day_id if owned else appointment_day_id,
                    registration_url=registration_url,
                    score=score,
                    status=status,
                    reasons=reasons,
                ))

    all_candidates = [asdict(candidate) for candidate in candidates]
    public = [candidate for candidate in all_candidates if candidate["status"] == "public"]
    suppressed = [candidate for candidate in all_candidates if candidate["status"] in {"suppressed", "invalid"}]
    return {
        "scenario": scenario_name,
        "availability_blocks": availability_blocks,
        "candidates": all_candidates,
        "public_offerings": public,
        "suppressed": suppressed,
    }


def write_debug_outputs(result: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    CANDIDATES_PATH.write_text(json.dumps(result["candidates"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    PUBLIC_OFFERINGS_PATH.write_text(json.dumps(result["public_offerings"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    SUPPRESSED_PATH.write_text(json.dumps(result["suppressed"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    invalid = [candidate for candidate in result["candidates"] if candidate["status"] == "invalid"]
    anchor_blocks = [block for block in result["availability_blocks"] if block.get("anchor_required")]
    lines = [
        "# Inventory Controller Audit",
        "",
        f"Scenario: `{result['scenario']}`",
        "",
        f"- Total availability blocks: {len(result['availability_blocks'])}",
        f"- Total candidates: {len(result['candidates'])}",
        f"- Public offerings: {len(result['public_offerings'])}",
        f"- Suppressed offerings: {len(result['suppressed'])}",
        f"- Invalid out-of-range offerings: {len(invalid)}",
        f"- Anchor-required blocks: {len(anchor_blocks)}",
        "",
        "## Suppression Examples",
        "",
    ]
    for candidate in result["suppressed"][:12]:
        lines.append(
            f"- {candidate['date']} {candidate['start_time']} {candidate['course_name']} "
            f"({candidate['instructor']}): {candidate['status']} because {', '.join(candidate['reasons'])}"
        )
    lines.append("")
    AUDIT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    result = generate_inventory()
    write_debug_outputs(result)
    print(json.dumps({
        "scenario": result["scenario"],
        "availability_blocks": len(result["availability_blocks"]),
        "candidates": len(result["candidates"]),
        "public_offerings": len(result["public_offerings"]),
        "suppressed": len(result["suppressed"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
