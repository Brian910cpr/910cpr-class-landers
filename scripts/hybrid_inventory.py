from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("America/New_York")
ENROLLWARE_BASE = "https://coastalcprtraining.enrollware.com"
APPOINTMENT_ENDPOINT = f"{ENROLLWARE_BASE}/reg/appointment.aspx/GetAvailableAppointmentTimes"
COURSE_CONSUMPTION_RULES_PATH = ROOT / "data" / "inventory" / "course_consumption_rules.json"
AVAILABILITY_WINDOW_POLICIES_PATH = ROOT / "data" / "inventory" / "availability_window_policies.json"


def load_json_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_course_consumption_rules(path: Path = COURSE_CONSUMPTION_RULES_PATH) -> dict[str, Any]:
    return load_json_config(path)


def load_availability_window_policies(path: Path = AVAILABILITY_WINDOW_POLICIES_PATH) -> dict[str, Any]:
    return load_json_config(path)


def normalize_token(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def course_consumption_rule_for(course: dict[str, Any], rules_config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the course-specific capacity rule without consulting instructor identity."""
    rules_config = rules_config or load_course_consumption_rules()
    course_id = str(course.get("course_id") or course.get("course_number") or "").strip()
    course_family = normalize_token(course.get("course_family") or course.get("family"))
    clean_name = normalize_token(course.get("clean_course_name") or course.get("clean_title") or course.get("course_name"))

    for rule in rules_config.get("rules", []):
        rule_course_id = str(rule.get("course_id") or "").strip()
        if rule_course_id and course_id and rule_course_id == course_id:
            return rule

    for rule in rules_config.get("rules", []):
        rule_family = normalize_token(rule.get("course_family"))
        if rule_family and course_family and rule_family == course_family:
            return rule

    for rule in rules_config.get("rules", []):
        rule_name = normalize_token(rule.get("clean_course_name"))
        if rule_name and clean_name and rule_name == clean_name:
            return rule

    return dict(rules_config.get("defaults", {}))


def availability_window_policy_for(
    window: dict[str, Any],
    policies_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policies_config = policies_config or load_availability_window_policies()
    policy_id = str(window.get("policy_id") or "").strip()
    capacity_mode = str(window.get("capacity_mode") or "").strip()

    for policy in policies_config.get("policies", []):
        if policy_id and str(policy.get("policy_id") or "") == policy_id:
            merged = dict(policy)
            merged.update({k: v for k, v in window.items() if k in merged and v is not None})
            return merged

    if capacity_mode:
        capacity_modes = policies_config.get("capacity_modes", {})
        if capacity_mode in capacity_modes:
            policy = dict(capacity_modes[capacity_mode])
            policy["capacity_mode"] = capacity_mode
            policy.update({k: v for k, v in window.items() if k in policy and v is not None})
            return policy

    return dict(policies_config.get("defaults", {}))


def course_family_allowed(rule: dict[str, Any], policy: dict[str, Any]) -> bool:
    family = str(rule.get("course_family") or "").strip()
    allowed = [str(value).strip() for value in policy.get("allowed_course_families", [])]
    fallback = [str(value).strip() for value in policy.get("fallback_course_families", [])]
    if not family:
        return False
    return family in allowed or family in fallback


def course_family_requires_manual_fallback(rule: dict[str, Any], policy: dict[str, Any]) -> bool:
    family = str(rule.get("course_family") or "").strip()
    fallback = [str(value).strip() for value in policy.get("fallback_course_families", [])]
    return bool(family and family in fallback and policy.get("fallback_requires_manual_approval") is True)


def can_consume_availability_window(
    course_rule: dict[str, Any],
    window_policy: dict[str, Any],
    *,
    existing_reservation_count: int = 0,
    existing_overlapping_reservation_count: int = 0,
) -> tuple[bool, str]:
    """Check rule compatibility; appointment slot spacing is intentionally ignored."""
    duration = int(course_rule.get("minimum_reservation_block_minutes") or course_rule.get("duration_minutes") or 0)
    window_min = int(window_policy.get("minimum_duration_minutes") or 0)
    preferred = int(window_policy.get("preferred_duration_minutes") or 0)
    max_per_window = int(window_policy.get("maximum_appointments_per_window") or 1)
    split_allowed = window_policy.get("split_allowed") is True

    if not course_family_allowed(course_rule, window_policy):
        return False, "course_family_not_allowed_by_window_policy"

    if course_family_requires_manual_fallback(course_rule, window_policy):
        return False, "fallback_course_family_requires_manual_approval"

    if max_per_window > 0 and existing_reservation_count >= max_per_window:
        return False, "maximum_appointments_per_window_reached"

    if window_min and duration < window_min:
        return False, "course_block_shorter_than_window_minimum"

    if not split_allowed and preferred and duration != preferred:
        return False, "window_policy_requires_single_preferred_block"

    if course_rule.get("requires_contiguous_block") is True and course_rule.get("fragmentation_tolerant") is False:
        if split_allowed and preferred and duration > preferred:
            return False, "course_requires_contiguous_block_larger_than_preferred_window"

    if course_rule.get("overlapping_allowed") is False and existing_overlapping_reservation_count > 0:
        return False, "course_prohibits_overlapping_reservations"

    return True, "allowed"


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def session_enrolled_count(session: dict[str, Any]) -> int:
    raw = session.get("enrolled_count", session.get("registered_count", 0))
    try:
        return max(0, int(raw or 0))
    except (TypeError, ValueError):
        return 0


def session_registration_url(session: dict[str, Any]) -> str:
    return str(session.get("registration_url") or session.get("register_url") or "").strip()


def is_real_scheduled_inventory(session: dict[str, Any]) -> bool:
    return "enroll?id=" in session_registration_url(session)


def extract_schedule_course_id(url: str | None) -> str | None:
    text = str(url or "").strip()
    match = re.search(r"#ct(\d+)", text)
    if match:
        return match.group(1)
    return None


def build_appointment_page_url(location_id: str, course_id: str) -> str:
    return f"{ENROLLWARE_BASE}/reg/appointment.aspx?locationId={location_id}&courseId={course_id}"


def seed_dates_from_sessions(sessions: list[dict[str, Any]], *, limit: int = 5) -> list[str]:
    seen: set[str] = set()
    seeds: list[str] = []
    for session in sessions:
        dt = parse_dt(str(session.get("start_at") or ""))
        if not dt:
            continue
        token = dt.strftime("%m%d%y")
        if token in seen:
            continue
        seen.add(token)
        seeds.append(token)
        if len(seeds) >= limit:
            break
    return seeds


def sort_by_momentum(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(session: dict[str, Any]) -> tuple[int, str, str]:
        dt = parse_dt(str(session.get("start_at") or ""))
        return (
            -session_enrolled_count(session),
            dt.isoformat() if dt else "9999-12-31T23:59:59-05:00",
            str(session.get("session_id") or ""),
        )

    return sorted(sessions, key=key)


def sort_by_start(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(session: dict[str, Any]) -> tuple[str, str]:
        dt = parse_dt(str(session.get("start_at") or ""))
        return (
            dt.isoformat() if dt else "9999-12-31T23:59:59-05:00",
            str(session.get("session_id") or ""),
        )

    return sorted(sessions, key=key)
