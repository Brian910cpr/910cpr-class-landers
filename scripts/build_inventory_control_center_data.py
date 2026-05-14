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


def decision_label(reason: str) -> str:
    labels = {
        "owned_appointment_container": "Verified appointment range",
        "course_family_allowed_by_block": "Allowed by availability policy",
        "course_fits_contiguous_block": "Fits inside the time block",
        "escalation_tier_1_primary_anchor_exposure": "Primary inventory exposure",
        "escalation_tier_2_secondary_inventory_enabled": "Secondary inventory unlocked by momentum",
        "remaining_fragment_can_support_small_course": "Leaves usable time",
        "consolidation_boost_no_unusable_tail_fragment": "Uses the block cleanly",
        "profitability_boost_high_value_course": "High-value course",
        "profitability_boost_moderate_value_course": "Moderate-value course",
        "certification_ceiling_boost_advanced_provider_anchor": "Uses advanced instructor capability",
        "fair_rotation_boost_bls_level_block": "BLS fair rotation",
        "brand_mix_boost_primary_aha_inventory": "Primary AHA brand mix",
        "momentum_triggered_by_anchor_strength_3": "Anchor booking created momentum",
        "momentum_triggered_by_compatible_pool_count_1": "Compatible pool already has momentum",
        "appointment_container_out_of_range": "Outside verified appointment range",
        "no_matching_appointment_container": "No matching appointment container",
        "registration_url_not_generated_outside_owned_range": "Unsafe appointment link suppressed",
        "registration_url_not_generated_without_matching_container": "No appointment link available",
        "anchor_required_unmet_non_anchor_suppressed": "Anchor required before smaller offerings",
        "course_hidden_by_anchor_or_family_policy": "Hidden by course family policy",
        "course_hidden_by_escalation_tier_policy": "Hidden until escalation momentum exists",
        "escalation_tier_2_suppressed_until_momentum": "Tier 2 waiting for momentum",
        "course_does_not_fit_contiguous_block": "Does not fit in the block",
        "overlaps_existing_anchor_booking": "Overlaps existing anchor booking",
        "anchor_already_exists_anchor_course_not_icing": "Anchor already exists",
        "duplicate_same_course_suppressed_for_consolidation": "Duplicate suppressed for consolidation",
        "compatible_occupancy_pool_public_limit_reached": "Shared pool exposure limit reached",
        "fragmentation_risk_penalty_remaining_fragment_too_small": "Fragmentation risk penalty",
        "suppressed_due_to_fragmentation_risk": "Suppressed due to fragmentation risk",
        "score_below_public_threshold": "Score below public threshold",
        "instructor_certification_ceiling_blocks_advanced_course": "Instructor certification ceiling blocks course",
    }
    if reason.startswith("occupancy_pool_"):
        return f"Occupancy pool: {reason.removeprefix('occupancy_pool_')}"
    if reason.startswith("escalation_tier_"):
        return reason.replace("_", " ").title()
    return labels.get(reason, reason.replace("_", " ").title())


def primary_public_reason(candidate: dict[str, Any]) -> str:
    reasons = candidate.get("reasons", [])
    for reason in (
        "certification_ceiling_boost_advanced_provider_anchor",
        "profitability_boost_high_value_course",
        "escalation_tier_2_secondary_inventory_enabled",
        "fair_rotation_boost_bls_level_block",
        "brand_mix_boost_primary_aha_inventory",
        "consolidation_boost_no_unusable_tail_fragment",
        "remaining_fragment_can_support_small_course",
        "escalation_tier_1_primary_anchor_exposure",
    ):
        if reason in reasons:
            return reason
    return reasons[-1] if reasons else "public_without_reason"


def primary_suppression_reason(candidate: dict[str, Any]) -> str:
    reasons = candidate.get("reasons", [])
    for reason in (
        "appointment_container_out_of_range",
        "no_matching_appointment_container",
        "course_does_not_fit_contiguous_block",
        "anchor_required_unmet_non_anchor_suppressed",
        "course_hidden_by_escalation_tier_policy",
        "escalation_tier_2_suppressed_until_momentum",
        "overlaps_existing_anchor_booking",
        "duplicate_same_course_suppressed_for_consolidation",
        "compatible_occupancy_pool_public_limit_reached",
        "suppressed_due_to_fragmentation_risk",
        "score_below_public_threshold",
        "instructor_certification_ceiling_blocks_advanced_course",
        "course_hidden_by_anchor_or_family_policy",
    ):
        if reason in reasons:
            return reason
    return reasons[-1] if reasons else "suppressed_without_reason"


SUPPRESSION_REASON_CATEGORIES = {
    "no_matching_appointment_container": ("no_matching_appointment_container", "No matching appointment container"),
    "appointment_container_out_of_range": ("appointment_container_out_of_range", "Appointment container out of range"),
    "anchor_required_unmet_non_anchor_suppressed": ("anchor_required_unmet", "Anchor required before smaller offerings"),
    "escalation_tier_2_suppressed_until_momentum": ("tier_suppressed_until_momentum", "Tier suppressed until momentum"),
    "course_hidden_by_escalation_tier_policy": ("tier_suppressed_until_momentum", "Tier suppressed until momentum"),
    "duplicate_same_course_suppressed_for_consolidation": ("duplicate_same_course_too_close", "Duplicate suppressed for consolidation"),
    "suppressed_due_to_fragmentation_risk": ("fragmentation_risk", "Fragmentation risk"),
    "fragmentation_risk_penalty_remaining_fragment_too_small": ("fragmentation_risk", "Fragmentation risk"),
    "course_does_not_fit_contiguous_block": ("course_does_not_fit_block", "Course does not fit block"),
    "score_below_public_threshold": ("below_public_threshold", "Score below public threshold"),
    "overlaps_existing_anchor_booking": ("no_remaining_geometry", "No remaining geometry"),
    "compatible_occupancy_pool_public_limit_reached": ("pool_limit_reached", "Shared pool exposure limit reached"),
    "instructor_certification_ceiling_blocks_advanced_course": ("instructor_not_eligible", "Instructor not eligible"),
    "course_hidden_by_anchor_or_family_policy": ("course_policy_hidden", "Hidden by course policy"),
}

HEALTHY_SUPPRESSION_REASONS = {
    "anchor_required_unmet",
    "tier_suppressed_until_momentum",
    "duplicate_same_course_too_close",
    "pool_limit_reached",
}

ALARMING_SUPPRESSION_REASONS = {
    "no_matching_appointment_container",
    "appointment_container_out_of_range",
    "unknown_or_other",
}


def suppression_category(candidate: dict[str, Any]) -> tuple[str, str]:
    for reason in candidate.get("reasons", []):
        if reason in SUPPRESSION_REASON_CATEGORIES:
            return SUPPRESSION_REASON_CATEGORIES[reason]
    return "unknown_or_other", "Other / unknown"


def top_counts(items: list[dict[str, Any]], field: str, limit: int = 5) -> list[dict[str, Any]]:
    counter = Counter(str(item.get(field) or "Unknown") for item in items)
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]


def count_rows(items: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    return [
        {"value": value, "count": count}
        for value, count in Counter(str(item.get(field) or "Unknown") for item in items).most_common()
    ]


def reason_rows(items: list[dict[str, Any]], primary_reason_fn, *, include_percent: bool = False) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[primary_reason_fn(item)].append(item)
    rows = []
    for reason, reason_items in grouped.items():
        row = {
            "reason": reason,
            "label": decision_label(reason),
            "count": len(reason_items),
            "examples": reason_items[:5],
        }
        if include_percent:
            row["percent"] = round((len(reason_items) / max(1, len(items))) * 100, 1)
            row["top_instructors"] = top_counts(reason_items, "instructor")
            row["top_course_families"] = top_counts(reason_items, "course_family")
            row["top_dates"] = top_counts(reason_items, "date")
        rows.append(row)
    return sorted(rows, key=lambda row: row["count"], reverse=True)


def suppression_breakdown(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    labels: dict[str, str] = {}
    for item in items:
        key, label = suppression_category(item)
        grouped[key].append(item)
        labels[key] = label
    return [
        {
            "reason": key,
            "label": labels[key],
            "count": len(reason_items),
            "percent": round((len(reason_items) / max(1, len(items))) * 100, 1),
            "health": "alarming" if key in ALARMING_SUPPRESSION_REASONS else "healthy" if key in HEALTHY_SUPPRESSION_REASONS else "watch",
            "top_instructors": top_counts(reason_items, "instructor"),
            "top_course_families": top_counts(reason_items, "course_family"),
            "top_dates": top_counts(reason_items, "date"),
            "examples": reason_items[:8],
        }
        for key, reason_items in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)
    ]


def all_reason_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for item in items:
        counter.update(item.get("reasons", []))
    return [
        {"reason": reason, "label": decision_label(reason), "count": count}
        for reason, count in counter.most_common()
    ]


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

    invalid = [
        item for item in candidates
        if item.get("status") == "invalid"
        or "appointment_container_out_of_range" in item.get("reasons", [])
    ]
    no_matching_container_candidates = [
        item for item in candidates
        if "no_matching_appointment_container" in item.get("reasons", [])
    ]
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
    if no_matching_container_candidates:
        add_warning(warnings, "action", "Availability blocks without matching containers", f"{len(no_matching_container_candidates)} candidates have no matching appointment container.", "Add or tag an active appointment container for the instructor/location/date range.", "Appointment Blocks")
    if public and not containers:
        add_warning(warnings, "action", "Public offerings without verified appointment range", "Public offerings exist but no appointment container registry loaded.", "Load appointment_containers.json before publishing any links.", "Inventory")
    if len(suppressed) > max(1, len(public) * 8):
        add_warning(warnings, "due", "Too many suppressed offerings", f"{len(suppressed)} suppressed vs {len(public)} public.", "Review escalation tiers, grouping limits, and fragmentation rules.", "Inventory")
    if high_value_fragmented:
        add_warning(warnings, "due", "High-value block fragmented early", f"{len(high_value_fragmented)} public high-value candidates carry a fragmentation penalty.", "Prefer stronger anchor starts or fewer public alternatives.", "Inventory")

    offerings_without_urls = [item for item in public if not item.get("registration_url")]
    if offerings_without_urls:
        add_warning(warnings, "action", "Public offering missing registration URL", f"{len(offerings_without_urls)} public offerings have no registration URL.", "Do not publish these rows until URL generation is fixed.", "Inventory")

    public_by_block = defaultdict(list)
    suppressed_by_block = defaultdict(list)
    invalid_by_block = defaultdict(list)
    for item in public:
        public_by_block[block_key_from_candidate(item)].append(item)
    for item in suppressed:
        key = block_key_from_candidate(item)
        if item.get("status") == "invalid" or "appointment_container_out_of_range" in item.get("reasons", []):
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

    zero_public_blocks = [block for block in block_summaries if block["public_count"] == 0]
    for block in zero_public_blocks:
        add_warning(warnings, "due", "Availability block has zero public offerings", f"{block['instructor']} {block['date']} {block['start_time']}-{block['end_time']}", "Open Inventory Geometry and review suppression reasons for this block.", "Inventory")

    public_dates = {item.get("date") for item in public}
    suppressed_dates = {item.get("date") for item in suppressed}
    all_suppressed_dates = sorted(date_value for date_value in suppressed_dates if date_value and date_value not in public_dates)
    for date_value in all_suppressed_dates[:5]:
        add_warning(warnings, "due", "All offerings for a day are suppressed", str(date_value), "Review appointment container range, availability policy, and course fit for that date.", "Inventory")

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

    public_by_container = Counter(str(item.get("appointment_container_id") or "") for item in public if item.get("appointment_container_id"))
    container_groups: dict[str, dict[str, Any]] = {}
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
        container_id = str(container.get("container_id", ""))
        container_group = str(container.get("container_group") or "ungrouped")
        public_dependency_count = public_by_container.get(container_id, 0)
        if public_dependency_count == 0 and container.get("status") == "active":
            flags.append("unused_container")
        container_row = {
            **container,
            "days_remaining_until_expiration": days_remaining,
            "public_offering_dependency_count": public_dependency_count,
            "flags": flags,
        }
        appointment_blocks.append(container_row)
        group = container_groups.setdefault(container_group, {
            "container_group": container_group,
            "container_count": 0,
            "active_count": 0,
            "expired_count": 0,
            "missing_or_unsafe_count": 0,
            "public_offering_dependency_count": 0,
            "unused_container_count": 0,
            "containers": [],
        })
        group["container_count"] += 1
        if container.get("status") == "active":
            group["active_count"] += 1
        if "expired" in flags:
            group["expired_count"] += 1
        if any(flag.startswith("missing_") or flag == "unsafe_range" for flag in flags):
            group["missing_or_unsafe_count"] += 1
        if "unused_container" in flags:
            group["unused_container_count"] += 1
        group["public_offering_dependency_count"] += public_dependency_count
        group["containers"].append(container_row)

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
        if "occupancy_pool" in missing or "escalation_tier" in missing:
            add_warning(warnings, "action", "Course missing grouping fields", str(rule.get("clean_course_name")), "Add occupancy_pool and escalation_tier to the course rule.", "Course Rules")

    revenue = summarize_price(public)
    working_hours = round(sum(int(item.get("duration_minutes", 0)) for item in public) / 60, 1)
    revenue_per_hour = "unknown" if revenue["unknown_price_count"] else round(revenue["known_revenue"] / working_hours, 2) if working_hours else "unknown"
    suppression_breakdown_rows = suppression_breakdown(suppressed)
    alarming_reasons = [row for row in suppression_breakdown_rows if row["health"] == "alarming"]
    healthy_reasons = [row for row in suppression_breakdown_rows if row["health"] == "healthy"]
    unknown_suppression = next((row for row in suppression_breakdown_rows if row["reason"] == "unknown_or_other"), None)
    if unknown_suppression:
        add_warning(warnings, "due", "Unknown suppression reason exists", f"{unknown_suppression['count']} suppressed candidates fell into other/unknown.", "Add explicit reason mapping so operators can interpret the outcome.", "Inventory")
    public_percent = round((len(public) / max(1, len(candidates))) * 100, 1)
    suppression_percent = round((len(suppressed) / max(1, len(candidates))) * 100, 1)
    alarming_count = sum(row["count"] for row in alarming_reasons)
    suppression_health = "alarming" if alarming_count else "healthy" if healthy_reasons else "watch"

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
        "decision_explanations": {
            "public_total": len(public),
            "suppressed_total": len(suppressed),
            "invalid_total": len(invalid),
            "total_candidates": len(candidates),
            "public_percent": public_percent,
            "suppression_percent": suppression_percent,
            "suppression_health": suppression_health,
            "suppression_health_detail": f"{alarming_count} suppressed candidates are in alarming categories." if alarming_count else "Suppression is mostly protecting inventory pacing, anchors, and grouping.",
            "public_by_instructor": count_rows(public, "instructor"),
            "public_by_family": count_rows(public, "course_family"),
            "public_by_pool": count_rows(public, "occupancy_pool"),
            "public_by_tier": count_rows(public, "escalation_tier"),
            "public_by_container": count_rows(public, "appointment_container_id"),
            "public_primary_reasons": reason_rows(public, primary_public_reason),
            "suppressed_primary_reasons": reason_rows(suppressed, primary_suppression_reason, include_percent=True),
            "suppressed_by_reason": suppression_breakdown_rows,
            "suppressed_reason_examples": {row["reason"]: row["examples"] for row in suppression_breakdown_rows},
            "alarming_suppression_reasons": alarming_reasons,
            "healthy_suppression_reasons": healthy_reasons,
            "offerings_without_urls": offerings_without_urls,
            "availability_blocks_with_zero_public_offerings": zero_public_blocks,
            "public_all_reasons": all_reason_rows(public),
            "suppressed_all_reasons": all_reason_rows(suppressed),
        },
        "inventory_geometry": block_summaries,
        "escalation_rings": tier_stats,
        "occupancy_pools": pool_stats,
        "appointment_blocks": appointment_blocks,
        "appointment_container_groups": sorted(container_groups.values(), key=lambda row: row["container_group"]),
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
