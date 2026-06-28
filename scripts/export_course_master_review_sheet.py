from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
COURSE_MASTER_PATH = ROOT / "data" / "config" / "course_master.json"
PUBLIC_SELLABLE_PATH = AUDIT_DIR / "public_sellable_offers_preview.json"

CSV_PATH = AUDIT_DIR / "course_master_review_sheet.csv"
MD_PATH = AUDIT_DIR / "course_master_review_sheet.md"
JSON_PATH = AUDIT_DIR / "course_master_review_sheet.json"

REVIEW_COLUMNS = [
    "course_key",
    "enrollware_course_id",
    "enrollware_name",
    "public_short_title",
    "public_long_title",
    "course_family",
    "course_family_type",
    "provider",
    "discipline",
    "format",
    "status",
    "classroom_duration_minutes",
    "skills_duration_minutes",
    "scheduler_display_duration_minutes",
    "setup_buffer_minutes",
    "cleanup_buffer_minutes",
    "scheduler_consumption_minutes",
    "minimum_lead_time_hours",
    "maximum_lookahead_days",
    "dynamic_offer_allowed",
    "appointment_seed_allowed",
    "review_needed_for_scheduling",
    "public_visibility",
    "slug_page",
    "hub_tab",
    "cta_text",
    "review_needed_for_rendering",
    "base_price",
    "shipping_price",
    "add_ons",
    "card_type",
    "secondary_card_type",
    "ecard_code",
    "keycode_bank",
    "review_needed_for_pricing_or_cards",
    "allowed_instructor_ids",
    "allowed_location_ids",
    "max_students_default",
    "min_students_default",
    "required_equipment",
    "room_requirements",
    "data_quality_status",
    "missing_required_fields",
    "source_files",
    "used_by_public_sellable_dynamic_offer",
    "public_sellable_offer_ids",
    "brian_review_notes",
]

SCHEDULING_FIELDS = {
    "classroom_duration_minutes",
    "skills_duration_minutes",
    "scheduler_display_duration_minutes",
    "setup_buffer_minutes",
    "cleanup_buffer_minutes",
    "scheduler_consumption_minutes",
    "minimum_lead_time_hours",
    "maximum_lookahead_days",
}
RENDERING_FIELDS = {"public_visibility", "slug_page", "hub_tab", "cta_text"}
PRICING_CARD_FIELDS = {
    "base_price",
    "shipping_price",
    "add_ons",
    "card_type",
    "secondary_card_type",
    "ecard_code",
    "keycode_bank",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def as_cell(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def public_sellable_offer_ids_by_course(payload: Any) -> dict[str, list[str]]:
    offers = payload.get("offers", []) if isinstance(payload, dict) else []
    grouped: dict[str, list[str]] = {}
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        course_id = str(offer.get("course_id") or "").strip()
        offer_id = str(offer.get("offer_id") or "").strip()
        if course_id and offer_id:
            grouped.setdefault(course_id, []).append(offer_id)
    return {course_id: sorted(offer_ids) for course_id, offer_ids in grouped.items()}


def needs_review(course: dict[str, Any], fields: set[str]) -> bool:
    missing = set(course.get("missing_required_fields", []))
    if missing.intersection(fields):
        return True
    for field in fields:
        value = course.get(field)
        if value in (None, "", "unknown") or value == []:
            return True
    return False


def review_row(course: dict[str, Any], public_offer_ids: list[str]) -> dict[str, Any]:
    row = {column: course.get(column) for column in REVIEW_COLUMNS if column in course}
    row["review_needed_for_scheduling"] = needs_review(course, SCHEDULING_FIELDS)
    row["review_needed_for_rendering"] = needs_review(course, RENDERING_FIELDS)
    row["review_needed_for_pricing_or_cards"] = needs_review(course, PRICING_CARD_FIELDS)
    row["used_by_public_sellable_dynamic_offer"] = bool(public_offer_ids)
    row["public_sellable_offer_ids"] = public_offer_ids
    row["brian_review_notes"] = ""
    return {column: row.get(column, "") for column in REVIEW_COLUMNS}


def sort_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("data_quality_status") or ""),
        str(row.get("course_family") or ""),
        str(row.get("public_short_title") or ""),
    )


def build_rows(master: dict[str, Any], public_payload: Any) -> list[dict[str, Any]]:
    offer_ids_by_course = public_sellable_offer_ids_by_course(public_payload)
    rows = [
        review_row(course, offer_ids_by_course.get(str(course.get("enrollware_course_id")), []))
        for course in master.get("courses", [])
        if isinstance(course, dict)
    ]
    return sorted(rows, key=sort_key)


def write_csv(rows: list[dict[str, Any]]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: as_cell(row.get(column)) for column in REVIEW_COLUMNS})


def compact(value: Any, limit: int = 80) -> str:
    text = as_cell(value)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def render_markdown(rows: list[dict[str, Any]], public_course_ids: list[str]) -> str:
    scheduling = [row for row in rows if row["review_needed_for_scheduling"]]
    rendering = [row for row in rows if row["review_needed_for_rendering"]]
    pricing = [row for row in rows if row["review_needed_for_pricing_or_cards"]]
    lines = [
        "# Course Master Review Sheet",
        "",
        "Human review worksheet generated from non-authoritative Course Master data. No production behavior was changed.",
        "",
        "## Summary",
        "",
        f"- Total courses: `{len(rows)}`",
        f"- Courses needing scheduling review: `{len(scheduling)}`",
        f"- Courses needing rendering review: `{len(rendering)}`",
        f"- Courses needing pricing/card review: `{len(pricing)}`",
        "",
        "## Missing Fields By Course",
        "",
        "| course_id | course | family | quality | missing_required_fields | public dynamic |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    compact(row["enrollware_course_id"]),
                    compact(row["public_short_title"]).replace("|", "\\|"),
                    compact(row["course_family"]),
                    compact(row["data_quality_status"]),
                    compact(row["missing_required_fields"]).replace("|", "\\|"),
                    "yes" if row["used_by_public_sellable_dynamic_offer"] else "no",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Public Sellable Dynamic Offer Courses",
            "",
        ]
    )
    public_rows = [row for row in rows if row["used_by_public_sellable_dynamic_offer"]]
    if not public_rows:
        lines.append("- None")
    for row in public_rows:
        lines.append(
            f"- `{row['enrollware_course_id']}` `{row['public_short_title']}` "
            f"offers: `{as_cell(row['public_sellable_offer_ids'])}`"
        )
    lines.extend(
        [
            "",
            "## Most Common Missing Fields",
            "",
        ]
    )
    counts = Counter(field for row in rows for field in row["missing_required_fields"])
    for field, count in counts.most_common():
        lines.append(f"- `{field}`: `{count}`")
    lines.append("")
    return "\n".join(lines)


def build_summary(rows: list[dict[str, Any]], master: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "deployed": False,
        "course_master_authoritative": bool(master.get("authoritative")) is True,
        "review_columns": REVIEW_COLUMNS,
        "stats": {
            "total_courses": len(rows),
            "courses_needing_scheduling_review": sum(1 for row in rows if row["review_needed_for_scheduling"]),
            "courses_needing_rendering_review": sum(1 for row in rows if row["review_needed_for_rendering"]),
            "courses_needing_pricing_or_card_review": sum(1 for row in rows if row["review_needed_for_pricing_or_cards"]),
            "courses_used_by_public_sellable_dynamic_offers": sum(1 for row in rows if row["used_by_public_sellable_dynamic_offer"]),
        },
        "rows": rows,
    }


def run() -> dict[str, Any]:
    master = read_json(COURSE_MASTER_PATH)
    public_payload = read_json(PUBLIC_SELLABLE_PATH) if PUBLIC_SELLABLE_PATH.exists() else {}
    rows = build_rows(master, public_payload)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(rows)
    summary = build_summary(rows, master)
    JSON_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    MD_PATH.write_text(render_markdown(rows, sorted(public_sellable_offer_ids_by_course(public_payload))), encoding="utf-8")
    return summary


def main() -> int:
    summary = run()
    stats = summary["stats"]
    print("Course Master review sheet exported (READ ONLY).")
    print(f"Total courses: {stats['total_courses']}")
    print(f"Courses needing scheduling review: {stats['courses_needing_scheduling_review']}")
    print(f"Courses needing rendering review: {stats['courses_needing_rendering_review']}")
    print(f"Courses needing pricing/card review: {stats['courses_needing_pricing_or_card_review']}")
    print(f"Courses used by public sellable dynamic offers: {stats['courses_used_by_public_sellable_dynamic_offers']}")
    print("Output files:")
    print(f"- {CSV_PATH}")
    print(f"- {MD_PATH}")
    print(f"- {JSON_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
