from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEBUG_DIR = ROOT / "debug"
INVENTORY_DIR = ROOT / "data" / "inventory"
OUTPUT_PATH = DEBUG_DIR / "inventory_control_center_data.json"

SOURCE_PATHS = {
    "candidates": DEBUG_DIR / "inventory_controller_candidates.json",
    "public_offerings": DEBUG_DIR / "inventory_controller_public_offerings.json",
    "suppressed": DEBUG_DIR / "inventory_controller_suppressed.json",
    "audit": DEBUG_DIR / "inventory_controller_audit.md",
    "appointment_containers": INVENTORY_DIR / "appointment_containers.json",
    "instructor_availability": INVENTORY_DIR / "instructor_availability.json",
    "course_consumption_rules": INVENTORY_DIR / "course_consumption_rules.json",
    "mock_anchor_bookings": INVENTORY_DIR / "mock_anchor_bookings.json",
}


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def parse_time_minutes(value: str | None) -> int | None:
    if not value:
        return None
    for pattern in ("%H:%M", "%I:%M %p"):
        try:
            parsed = datetime.strptime(value, pattern).time()
            return parsed.hour * 60 + parsed.minute
        except ValueError:
            continue
    return None


def money(value: Any) -> float | None:
    if value in (None, "", "unknown"):
        return None
    try:
        return float(str(value).replace("$", "").replace(",", ""))
    except ValueError:
        return None


def source_statuses() -> list[dict[str, Any]]:
    rows = []
    now = datetime.now()
    for key, path in SOURCE_PATHS.items():
        exists = path.exists()
        modified = datetime.fromtimestamp(path.stat().st_mtime) if exists else None
        age_hours = round((now - modified).total_seconds() / 3600, 1) if modified else None
        rows.append({
            "key": key,
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "loaded": exists,
            "modified": modified.isoformat(timespec="seconds") if modified else None,
            "age_hours": age_hours,
            "stale": bool(age_hours is not None and age_hours > 48),
        })
    return rows


def block_key_from_candidate(candidate: dict[str, Any]) -> str:
    return str(candidate.get("block_id") or "|".join([
        str(candidate.get("instructor", "")),
        str(candidate.get("date", "")),
        str(candidate.get("start_time", "")),
    ]))


def block_key_from_availability(block: dict[str, Any], index: int) -> str:
    return f"{block.get('instructor_name')}|{block.get('date')}|{block.get('start_time')}|{block.get('end_time')}|{index}"


def summarize_price(items: list[dict[str, Any]]) -> dict[str, Any]:
    known = [money(item.get("price") or item.get("course_price")) for item in items]
    known = [value for value in known if value is not None]
    unknown_count = len(items) - len(known)
    return {
        "known_revenue": round(sum(known), 2),
        "unknown_price_count": unknown_count,
        "display": "unknown" if unknown_count else f"${sum(known):,.0f}",
    }


def course_rule_map(rules_config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(rule.get("course_id")): rule
        for rule in rules_config.get("rules", [])
        if rule.get("course_id") is not None
    }


def add_warning(warnings: list[dict[str, Any]], severity: str, title: str, detail: str, fix: str, group: str = "Operations") -> None:
    warnings.append({
        "severity": severity,
        "title": title,
        "detail": detail,
        "fix": fix,
        "group": group,
    })


def build() -> dict[str, Any]:
    candidates = read_json(SOURCE_PATHS["candidates"], [])
    public = read_json(SOURCE_PATHS["public_offerings"], [])
    suppressed = read_json(SOURCE_PATHS["suppressed"], [])
    audit_text = read_text(SOURCE_PATHS["audit"])
    containers_config = read_json(SOURCE_PATHS["appointment_containers"], {"containers": []})
    availability_config = read_json(SOURCE_PATHS["instructor_availability"], {"availability_blocks": []})
    rules_config = read_json(SOURCE_PATHS["course_consumption_rules"], {"rules": []})
    anchors_config = read_json(SOURCE_PATHS["mock_anchor_bookings"], {"scenarios": {}})

    containers = containers_config.get("containers", [])
    availability = availability_config.get("availability_blocks", [])
    rules = rules_config.get("rules", [])
    rules_by_id = course_rule_map(rules_config)
    today = date.today()
    warnings: list[dict[str, Any]] = []

    invalid = [item for item in candidates if item.get("status") == "invalid"]
    anchor_blocks = [block for block in availability if block.get("anchor_required")]
    high_value_fragmented = [
        item for item in public
        if "fragmentation_risk_penalty_remaining_fragment_too_small" in item.get("reasons", [])
        and int(rules_by_id.get(str(item.get("course_id")), {}).get("economic_priority", 0)) >= 70
    ]

    for source in source_statuses():
        if not source["loaded"]:
            add_warning(warnings, "action", f"Missing data source: {source['key']}", source["path"], "Regenerate the Inventory Controller debug files.", "Data")
        elif source["stale"]:
            add_warning(warnings, "due", f"Stale debug file: {source['key']}", f"{source['path']} is {source['age_hours']} hours old.", "Regenerate inventory debug output before making decisions.", "Data")

    for container in containers:
        last_valid = parse_date(container.get("last_valid_date"))
        days_remaining = (last_valid - today).days if last_valid else None
        if days_remaining is not None and days_remaining < 0:
            add_warning(warnings, "action", "Appointment container expired", str(container.get("container_name")), "Create or verify a new owned appointmentDayId range.", "Appointment Blocks")
        elif days_remaining is not None and days_remaining <= 90:
            add_warning(warnings, "due", "Appointment container expires soon", f"{container.get('container_name')} has {days_remaining} days remaining.", "Extend and verify the owned Enrollware appointmentDayId range.", "Appointment Blocks")
        if not container.get("first_invalid_appointmentDayId"):
            add_warning(warnings, "action", "Missing first invalid appointmentDayId", str(container.get("container_name")), "Probe and record the first unsafe appointmentDayId boundary.", "Appointment Blocks")
        if not container.get("location_id"):
            add_warning(warnings, "due", "Missing appointment location id", str(container.get("container_name")), "Record the Enrollware location id for safer routing.", "Appointment Blocks")
        if not container.get("instructor_name"):
            add_warning(warnings, "due", "Missing appointment container instructor", str(container.get("container_name")), "Record the owning instructor or capacity owner.", "Appointment Blocks")

    if invalid:
        add_warning(warnings, "action", "Generated candidates outside owned range", f"{len(invalid)} candidates are invalid or out of range.", "Keep invalid rows hidden and extend appointment containers before using those dates.", "Inventory")
    if public and not containers:
        add_warning(warnings, "action", "Public offerings without verified appointment range", "Public offerings exist but no appointment container registry loaded.", "Load appointment_containers.json before publishing any links.", "Inventory")
    if len(suppressed) > max(1, len(public) * 8):
        add_warning(warnings, "due", "Too many suppressed offerings", f"{len(suppressed)} suppressed vs {len(public)} public.", "Review escalation tiers, grouping limits, and fragmentation rules.", "Inventory")
    if high_value_fragmented:
        add_warning(warnings, "due", "High-value block fragmented early", f"{len(high_value_fragmented)} public high-value candidates carry a fragmentation penalty.", "Prefer stronger anchor starts or fewer public alternatives.", "Inventory")

    public_by_block = defaultdict(list)
    suppressed_by_block = defaultdict(list)
    invalid_by_block = defaultdict(list)
    for item in public:
        public_by_block[block_key_from_candidate(item)].append(item)
    for item in suppressed:
        key = block_key_from_candidate(item)
        if item.get("status") == "invalid":
            invalid_by_block[key].append(item)
        else:
            suppressed_by_block[key].append(item)

    block_summaries = []
    for index, block in enumerate(availability, start=1):
        key = block_key_from_availability(block, index)
        block_public = public_by_block.get(key, [])
        block_suppressed = suppressed_by_block.get(key, [])
        block_invalid = invalid_by_block.get(key, [])
        start_minutes = parse_time_minutes(block.get("start_time"))
        end_minutes = parse_time_minutes(block.get("end_time"))
        block_minutes = max(0, (end_minutes or 0) - (start_minutes or 0)) if start_minutes is not None and end_minutes is not None else 0
        max_public_duration = max([int(item.get("duration_minutes", 0)) for item in block_public] or [0])
        remaining_minutes = max(0, block_minutes - max_public_duration)
        anchor_public = [item for item in block_public if item.get("course_family") in set(block.get("anchor_course_families", []))]
        if block.get("anchor_required") and not anchor_public:
            add_warning(warnings, "action", "Anchor block has no public anchor candidates", f"{block.get('instructor_name')} {block.get('date')} {block.get('start_time')}-{block.get('end_time')}", "Review allowed course families, appointment range, and anchor rules.", "Instructor Load")
        if block.get("minimum_trip_value") and not anchor_public:
            add_warning(warnings, "due", "Possible low-value trip", f"{block.get('instructor_name')} has minimum trip value {block.get('minimum_trip_value')} with no anchor visible.", "Avoid exposing small courses until anchor or momentum exists.", "Instructor Load")
        block_summaries.append({
            "block_id": key,
            "instructor": block.get("instructor_name"),
            "location": block.get("location_name"),
            "date": block.get("date"),
            "start_time": block.get("start_time"),
            "end_time": block.get("end_time"),
            "public_count": len(block_public),
            "suppressed_count": len(block_suppressed),
            "invalid_count": len(block_invalid),
            "remaining_usable_minutes": remaining_minutes,
            "anchor_required": bool(block.get("anchor_required")),
            "anchor_status": "anchor visible" if anchor_public else ("needs anchor" if block.get("anchor_required") else "not required"),
            "escalation_ring_status": sorted(set(int(item.get("escalation_tier", 0)) for item in block_public if item.get("escalation_tier"))),
            "timeline": block_public[:18] + block_suppressed[:8] + block_invalid[:6],
            "notes": block.get("notes", ""),
        })

    tier_stats = []
    for tier in sorted(set([int(item.get("escalation_tier", 0)) for item in candidates if item.get("escalation_tier")])):
        tier_candidates = [item for item in candidates if int(item.get("escalation_tier", 0)) == tier]
        tier_public = [item for item in public if int(item.get("escalation_tier", 0)) == tier]
        tier_suppressed = [item for item in suppressed if int(item.get("escalation_tier", 0)) == tier]
        tier_stats.append({
            "tier": tier,
            "label": {1: "Primary Anchor Exposure", 2: "Secondary Escalation", 3: "Tertiary Escalation"}.get(tier, "Other"),
            "candidates": len(tier_candidates),
            "public_count": len(tier_public),
            "suppressed_count": len(tier_suppressed),
            "revenue": summarize_price(tier_public),
            "seat_fill_success": "placeholder",
            "conversion_rate": "placeholder",
            "time_to_first_seat": "placeholder",
            "momentum_trigger_count": sum(1 for item in tier_public if item.get("momentum_triggered")),
        })

    pool_stats = []
    for pool in sorted(set(str(item.get("occupancy_pool") or "UNKNOWN") for item in candidates)):
        pool_candidates = [item for item in candidates if str(item.get("occupancy_pool") or "UNKNOWN") == pool]
        pool_public = [item for item in public if str(item.get("occupancy_pool") or "UNKNOWN") == pool]
        pool_suppressed = [item for item in suppressed if str(item.get("occupancy_pool") or "UNKNOWN") == pool]
        compatible_courses = sorted(set(item.get("course_id") for item in pool_candidates if item.get("course_id")))
        fragment_count = sum(1 for item in pool_suppressed if "suppressed_due_to_fragmentation_risk" in item.get("reasons", []))
        pool_stats.append({
            "occupancy_pool": pool,
            "public_count": len(pool_public),
            "suppressed_count": len(pool_suppressed),
            "compatible_course_count": len(compatible_courses),
            "compatible_course_ids": compatible_courses,
            "grouping_success": "placeholder",
            "fragmentation_warning": fragment_count > 3,
            "fragmentation_suppressed_count": fragment_count,
        })

    instructor_stats = []
    for instructor in sorted(set(block.get("instructor_name") for block in availability if block.get("instructor_name"))):
        instructor_blocks = [block for block in availability if block.get("instructor_name") == instructor]
        instructor_public = [item for item in public if item.get("instructor") == instructor]
        instructor_suppressed = [item for item in suppressed if item.get("instructor") == instructor]
        working_minutes = sum(int(item.get("duration_minutes", 0)) for item in instructor_public)
        trip_values = [block.get("minimum_trip_value") for block in instructor_blocks if block.get("minimum_trip_value")]
        instructor_stats.append({
            "instructor": instructor,
            "availability_blocks": len(instructor_blocks),
            "public_offerings": len(instructor_public),
            "suppressed_offerings": len(instructor_suppressed),
            "anchor_required_blocks": sum(1 for block in instructor_blocks if block.get("anchor_required")),
            "estimated_working_hours": round(working_minutes / 60, 1),
            "revenue": summarize_price(instructor_public),
            "preferred_anchor_style": "placeholder",
            "escalation_tolerance": "placeholder",
            "last_paid": "placeholder",
            "estimated_due": "placeholder",
            "payment_alert": "placeholder",
            "minimum_trip_value": max(trip_values) if trip_values else 0,
            "preferred_course_families": sorted(set(family for block in instructor_blocks for family in block.get("allowed_course_families", []))),
            "fallback_course_families": sorted(set(family for block in instructor_blocks for family in block.get("fallback_course_families", []))),
            "notes": " ".join(block.get("notes", "") for block in instructor_blocks if block.get("notes")),
        })

    appointment_blocks = []
    for container in containers:
        last_valid = parse_date(container.get("last_valid_date"))
        days_remaining = (last_valid - today).days if last_valid else None
        flags = []
        if days_remaining is not None and days_remaining < 0:
            flags.append("expired")
        elif days_remaining is not None and days_remaining <= 90:
            flags.append("expires_within_90_days")
        for field, flag in (
            ("first_invalid_appointmentDayId", "missing_first_invalid_appointmentDayId"),
            ("location_id", "missing_location_id"),
            ("instructor_name", "missing_instructor"),
        ):
            if not container.get(field):
                flags.append(flag)
        if int(container.get("first_invalid_appointmentDayId", 0) or 0) <= int(container.get("last_valid_appointmentDayId", 0) or 0):
            flags.append("unsafe_range")
        appointment_blocks.append({
            **container,
            "days_remaining_until_expiration": days_remaining,
            "flags": flags,
        })

    rule_rows = []
    required_rule_fields = ["course_id", "clean_course_name", "course_family", "duration_minutes", "occupancy_pool", "escalation_tier", "default_capacity"]
    for rule in rules:
        missing = [field for field in required_rule_fields if rule.get(field) in (None, "", [])]
        if not money(rule.get("price")):
            missing.append("price")
        rule_rows.append({
            **rule,
            "price": rule.get("price", "unknown"),
            "warnings": missing,
        })

    revenue = summarize_price(public)
    working_hours = round(sum(int(item.get("duration_minutes", 0)) for item in public) / 60, 1)
    revenue_per_hour = "unknown" if revenue["unknown_price_count"] else round(revenue["known_revenue"] / working_hours, 2) if working_hours else "unknown"

    data = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_statuses": source_statuses(),
        "totals": {
            "availability_blocks": len(availability),
            "total_candidates": len(candidates),
            "public_offerings": len(public),
            "suppressed_candidates": len(suppressed),
            "invalid_candidates": len(invalid),
            "anchor_required_blocks": len(anchor_blocks),
            "appointment_container_count": len(containers),
        },
        "revenue": {
            "total_public_offering_revenue_potential": revenue,
            "anchor_revenue_potential": summarize_price([item for item in public if int(item.get("escalation_tier", 0)) == 1]),
            "secondary_escalation_revenue_potential": summarize_price([item for item in public if int(item.get("escalation_tier", 0)) == 2]),
            "tertiary_escalation_revenue_potential": summarize_price([item for item in public if int(item.get("escalation_tier", 0)) == 3]),
            "estimated_working_hours_exposed": working_hours,
            "estimated_revenue_per_working_hour": revenue_per_hour,
            "admin_hours": "placeholder",
            "overhead_cost": "placeholder",
            "instructor_pay_estimate": "placeholder",
            "estimated_margin": "placeholder",
            "net_per_working_hour": "placeholder",
        },
        "warnings": sorted(warnings, key=lambda row: {"action": 0, "due": 1, "info": 2}.get(row["severity"], 3)),
        "inventory_geometry": block_summaries,
        "escalation_rings": tier_stats,
        "occupancy_pools": pool_stats,
        "appointment_blocks": appointment_blocks,
        "instructors": instructor_stats,
        "course_rules": rule_rows,
        "debug": {
            "public_offerings": public,
            "suppressed_candidates": [item for item in suppressed if item.get("status") != "invalid"],
            "invalid_candidates": invalid,
            "audit_markdown": audit_text,
            "mock_anchor_bookings": anchors_config,
        },
    }
    return data


def main() -> int:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    data = build()
    OUTPUT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT_PATH.relative_to(ROOT)).replace("\\", "/"),
        "warnings": len(data["warnings"]),
        "public_offerings": data["totals"]["public_offerings"],
        "suppressed_candidates": data["totals"]["suppressed_candidates"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
