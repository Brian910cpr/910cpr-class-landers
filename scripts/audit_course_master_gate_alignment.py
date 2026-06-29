from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts import build_slug_hubs


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "audit"


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: Any) -> str:
    return str(value or "").strip()


def bool_text(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if value is None:
        return ""
    return str(value)


def course_master_by_id() -> dict[str, dict[str, Any]]:
    return build_slug_hubs.load_course_master_by_id()


def row_course_id(row: dict[str, Any], master: dict[str, dict[str, Any]]) -> str:
    explicit = clean(row.get("courseId") or row.get("course_id"))
    if explicit:
        return explicit
    key = clean(row.get("source_offer_id"))
    if key.startswith("offer-"):
        parts = key.split("-")
        if len(parts) > 1 and parts[1].isdigit():
            return parts[1]
    display = clean(row.get("course_display_name"))
    for course_id, course in master.items():
        names = {
            clean(course.get("public_short_title")),
            clean(course.get("public_long_title")),
            clean(course.get("enrollware_name")),
        }
        if display in names:
            return course_id
    return ""


def page_to_hub(page: str) -> str:
    page = clean(page).lower()
    if "bls" in page:
        return "bls"
    if "acls" in page:
        return "acls"
    if "pals" in page:
        return "pals"
    if "heartsaver" in page:
        return "heartsaver"
    if "hsi" in page:
        return "hsi"
    if "arc" in page:
        return "arc"
    return ""


def tab_ids_for_course(course: dict[str, Any]) -> list[str]:
    hub_tab = clean(course.get("hub_tab"))
    if hub_tab:
        return [part.strip() for part in hub_tab.split(";") if part.strip()]
    course_key = clean(course.get("course_key"))
    return sorted(build_slug_hubs.APPOINTMENT_COURSE_TAB_IDS.get(course_key, set()))


def start_time_from_url(row: dict[str, Any]) -> str:
    href = clean(row.get("visible_booking_check_url"))
    if "startTime=" not in href:
        return clean(row.get("time")).split(" - ", 1)[0]
    from urllib.parse import parse_qs, urlparse

    query = parse_qs(urlparse(href).query)
    return clean((query.get("startTime") or [""])[0])


def visible_gate_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    visible = read_json(AUDIT / "visible_row_source_audit.json") or {}
    rows = visible.get("rows", [])
    master = course_master_by_id()
    out: list[dict[str, Any]] = []
    for row in rows:
        row_source = clean(row.get("row_source"))
        course_id = row_course_id(row, master)
        course = master.get(course_id, {})
        course_key = clean(course.get("course_key") or row.get("normalized_course_key"))
        hub_slug = page_to_hub(clean(row.get("visible_page_url") or row.get("page_path")))
        tabs = tab_ids_for_course(course)
        decision = build_slug_hubs.course_master_public_row_gate(
            row_source=row_source,
            course_id=course_id,
            course_key=course_key,
            hub_slug=hub_slug,
            tab_ids=tabs,
            appointment_day_id=clean(row.get("appointmentDayId")),
            start_time=start_time_from_url(row),
            registration_url=clean(row.get("visible_booking_check_url")),
            course_master_by_id=master,
        )
        out.append(
            {
                "course_key": course_key,
                "courseId": course_id,
                "course_display_name": clean(row.get("course_display_name")),
                "date": clean(row.get("date")),
                "time": clean(row.get("time")),
                "row_source": row_source,
                "visible_page": clean(row.get("visible_page_url")),
                "visible_card_or_tabs": "; ".join(tabs),
                "dynamic_offer_allowed": bool_text(course.get("dynamic_offer_allowed")),
                "appointment_seed_allowed": bool_text(course.get("appointment_seed_allowed")),
                "review_needed_for_scheduling": bool_text(course.get("review_needed_for_scheduling")),
                "allowed_by_rule": "yes" if decision["allowed"] else "no",
                "reason": "; ".join(decision["reasons"]),
                "appointmentDayId": clean(row.get("appointmentDayId")),
                "source_offer_id": clean(row.get("source_offer_id")),
                "url": clean(row.get("visible_booking_check_url")),
            }
        )
    stats = {
        "total_rows": len(out),
        "allowed_rows": sum(1 for row in out if row["allowed_by_rule"] == "yes"),
        "blocked_rows": sum(1 for row in out if row["allowed_by_rule"] == "no"),
        "by_source": dict(Counter(row["row_source"] for row in out)),
        "blocked_reasons": dict(
            Counter(reason for row in out if row["allowed_by_rule"] == "no" for reason in row["reason"].split("; ") if reason)
        ),
    }
    return out, stats


def august_rows(gate_rows: list[dict[str, Any]], page_filter: str) -> list[dict[str, Any]]:
    return [
        row
        for row in gate_rows
        if row["date"].startswith("2026-08")
        and page_filter in (row["visible_page"] + " " + row["course_key"] + " " + row["course_display_name"]).lower()
    ]


def hidden_august_public_sellable() -> list[dict[str, Any]]:
    payload = read_json(AUDIT / "public_sellable_offers_preview.json") or {}
    hidden = payload.get("hidden_offers", [])
    rows: list[dict[str, Any]] = []
    for row in hidden if isinstance(hidden, list) else []:
        if not isinstance(row, dict):
            continue
        date = clean(row.get("date") or row.get("start_date") or row.get("appointment_date"))
        start = clean(row.get("appointment_display_start") or row.get("start_datetime"))
        if not date and start.startswith("2026-08"):
            date = start[:10]
        if not date.startswith("2026-08"):
            continue
        course_text = " ".join(
            clean(row.get(key)).lower()
            for key in ("course_key", "course_title", "course_family", "course_name")
        )
        if "bls" not in course_text and "heartsaver" not in course_text:
            continue
        reasons = row.get("public_filter_reasons") or row.get("rejection_reasons") or row.get("hidden_reasons") or []
        rows.append(
            {
                "offer_id": clean(row.get("offer_id")),
                "course_id": clean(row.get("course_id")),
                "course_key": clean(row.get("course_key")),
                "course_title": clean(row.get("course_title") or row.get("course_name")),
                "date": date,
                "start": start,
                "reasons": reasons,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else [
        "course_key",
        "courseId",
        "course_display_name",
        "date",
        "time",
        "row_source",
        "visible_page",
        "visible_card_or_tabs",
        "dynamic_offer_allowed",
        "appointment_seed_allowed",
        "review_needed_for_scheduling",
        "allowed_by_rule",
        "reason",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    def cell(value: Any) -> str:
        return clean(value).replace("|", "\\|")

    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell(row.get(col)) for col in columns) + " |")
    if not rows:
        lines.append("| " + " | ".join("none" if i == 0 else "" for i, _ in enumerate(columns)) + " |")
    return lines


def main() -> None:
    gate_rows, stats = visible_gate_rows()
    write_csv(AUDIT / "public_row_gate_audit.csv", gate_rows)

    violations = [row for row in gate_rows if row["allowed_by_rule"] == "no"]
    seed_violations = [row for row in gate_rows if row["row_source"] == "appointment_seed" and row["allowed_by_rule"] == "no"]
    dynamic_flag_visible = [
        row for row in gate_rows if row["dynamic_offer_allowed"] == "false" and row["row_source"] != "existing_enrollware_class"
    ]
    seed_flag_visible = [
        row for row in gate_rows if row["appointment_seed_allowed"] == "false" and row["row_source"] == "appointment_seed"
    ]
    review_needed_visible = [
        row for row in gate_rows if row["review_needed_for_scheduling"] == "true" and row["row_source"] != "existing_enrollware_class"
    ]

    bls_august = august_rows(gate_rows, "bls")
    heartsaver_august = august_rows(gate_rows, "heartsaver")
    july4_seed_rows = [
        row for row in gate_rows if row["date"] == "2026-07-04" and row["row_source"] == "appointment_seed"
    ]
    hidden_august = hidden_august_public_sellable()

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "course_master_authoritative": False,
        "rule_categories": {
            "existing_enrollware_class": "Allowed when it matches Class Report and has /enroll?id= URL; dynamic flags do not control real scheduled classes.",
            "appointment_seed": "Requires appointment_seed_allowed=true or explicit exception, reviewed mapping, appointmentDayId, startTime, page/card, and no scheduling review flag.",
            "dynamic_offer": "Requires dynamic_offer_allowed=true, reviewed mapping, public sellable filtering, and no scheduling review flag.",
            "request_only": "Generated request-only rows require dynamic gate review and must not create checkout/class rows.",
        },
        "stats": stats,
        "violations": violations,
        "visible_despite_dynamic_offer_allowed_false": dynamic_flag_visible,
        "visible_despite_appointment_seed_allowed_false": seed_flag_visible,
        "visible_despite_review_needed_for_scheduling_true": review_needed_visible,
        "appointment_seed_violations": seed_violations,
        "august": {
            "bls_wilmington_visible_rows": bls_august,
            "heartsaver_wilmington_visible_rows": heartsaver_august,
            "hidden_august_bls_or_heartsaver_dynamic_rows": hidden_august,
        },
        "july_4_appointment_seed_rows": july4_seed_rows,
        "minimum_safe_fix": [
            "Keep existing Class Report rows rendering even when dynamic flags are false.",
            "Suppress appointment seeds whose Course Master record is not appointment_seed_allowed or still needs scheduling review.",
            "Suppress generated dynamic offers whose Course Master record is not dynamic_offer_allowed or still needs scheduling review.",
            "Preserve only reviewed appointment seeds with appointmentDayId, startTime, courseId, page/card, and location traceability.",
            "Make August visibility explicit with real Enrollware rows before relying on seed generation.",
        ],
    }
    (AUDIT / "course_master_gate_alignment_report.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    report_lines = [
        "# Course Master Gate Alignment Report",
        "",
        "## Verdict",
        "",
        "Course Master should gate generated rows, not real scheduled Enrollware classes. The current visible rows include real Class Report rows that are safe to keep, plus appointment seeds that are blocked by the stricter Course Master rule until reviewed or explicitly excepted.",
        "",
        "## Gate Matrix",
        "",
        "| Row category | Public rule |",
        "|---|---|",
        "| existing_enrollware_class | May render when it matches the latest Class Report and uses `/enroll?id=`. Dynamic flags do not block real scheduled classes. |",
        "| appointment_seed | Requires `appointment_seed_allowed=true` or an explicit reviewed exception, known course key, reviewed page/card, `appointmentDayId`, and `startTime`; blocked by `review_needed_for_scheduling=true`. |",
        "| dynamic_offer | Requires `dynamic_offer_allowed=true`, public sellable filtering, reviewed page/card, and no scheduling review flag. |",
        "| request_only | Must stay request-only and pass reviewed generated-offer gates; it must not create checkout/class rows. |",
        "",
        "## Current Public Row Audit",
        "",
        f"- Total visible rows audited: `{stats['total_rows']}`",
        f"- Allowed by rule: `{stats['allowed_rows']}`",
        f"- Blocked by rule: `{stats['blocked_rows']}`",
        f"- By source: `{stats['by_source']}`",
        f"- Blocked reasons: `{stats['blocked_reasons']}`",
        "",
        "## Visible Generated-Row Violations",
        "",
        *md_table(seed_violations, ["course_key", "courseId", "course_display_name", "date", "time", "visible_page", "reason"]),
        "",
        "## Investigation Answers",
        "",
        f"- Visible despite `dynamic_offer_allowed=false`: `{len(dynamic_flag_visible)}` generated/non-Class-Report rows.",
        f"- Visible despite `appointment_seed_allowed=false`: `{len(seed_flag_visible)}` appointment seed rows.",
        f"- Visible despite `review_needed_for_scheduling=true`: `{len(review_needed_visible)}` generated/non-Class-Report rows.",
        "- These are not real Class Report rows misclassified as dynamic; the blocked rows are appointment seed rows with appointmentDayId URLs.",
        "- Under the new gate, they should be suppressed unless Brian explicitly reviews and allowlists the course/seed behavior.",
        "",
        "## Output Files",
        "",
        "- `data/audit/course_master_gate_alignment_report.json`",
        "- `data/audit/public_row_gate_audit.csv`",
        "- `data/audit/august_manual_schedule_floor_recommendation.md`",
        "- `data/audit/july_4_seed_decision_report.md`",
        "- `data/audit/minimum_safe_gate_fix_plan.md`",
    ]
    (AUDIT / "course_master_gate_alignment_report.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )

    august_lines = [
        "# August Manual Schedule Floor Recommendation",
        "",
        "## BLS Wilmington",
        "",
        *md_table(bls_august, ["course_key", "courseId", "course_display_name", "date", "time", "row_source", "allowed_by_rule", "reason"]),
        "",
        "## Heartsaver Wilmington",
        "",
        *md_table(heartsaver_august, ["course_key", "courseId", "course_display_name", "date", "time", "row_source", "allowed_by_rule", "reason"]),
        "",
        "## Hidden August Generated Rows",
        "",
        *md_table(hidden_august, ["offer_id", "course_id", "course_key", "course_title", "date", "start", "reasons"]),
        "",
        "## Minimum Manual Floor",
        "",
        "- Add or verify real Enrollware BLS Wilmington classes across the common proven public times: 9:15 AM, 12:30 PM, 6:15 PM, and 6:45 PM.",
        "- Add or verify real Enrollware Heartsaver First Aid CPR AED Wilmington classes at the proven public times: 9:15 AM and 6:15 PM.",
        "- Do not count suppressed appointment seeds as August coverage until Course Master gates are reviewed and the generated rows are visible in rendered HTML.",
    ]
    (AUDIT / "august_manual_schedule_floor_recommendation.md").write_text(
        "\n".join(august_lines) + "\n", encoding="utf-8"
    )

    july_lines = [
        "# July 4 Seed Decision Report",
        "",
        "## Confirmed July 4 Appointment Seed Rows",
        "",
        *md_table(july4_seed_rows, ["course_key", "courseId", "course_display_name", "date", "time", "visible_page", "appointmentDayId", "source_offer_id", "allowed_by_rule", "reason"]),
        "",
        "## Decision",
        "",
        "These rows are appointment seeds, not Class Report enroll?id rows. With the stricter Course Master gate, the Heartsaver July 4 seeds are blocked because their Course Master records still say `appointment_seed_allowed=false` and `review_needed_for_scheduling=true`.",
        "",
        "If they were temporary proof artifacts, suppress them. If Brian wants them as valid examples, review and explicitly allowlist the exact Course Master seed behavior before rendering. August is not producing more safe rows because the generated seed path is not aligned with Course Master reviewed scheduling gates and August real Enrollware coverage is sparse.",
    ]
    (AUDIT / "july_4_seed_decision_report.md").write_text(
        "\n".join(july_lines) + "\n", encoding="utf-8"
    )

    fix_lines = [
        "# Minimum Safe Gate Fix Plan",
        "",
        "1. Keep existing Class Report rows rendering when they have `/enroll?id=` URLs and reviewed page/card mapping.",
        "2. Apply Course Master gates only to generated public rows: appointment seeds, dynamic offers, and request-only rows.",
        "3. Suppress appointment seeds unless `appointment_seed_allowed=true` or an explicit reviewed exception exists.",
        "4. Suppress dynamic offers unless `dynamic_offer_allowed=true`.",
        "5. Block generated rows when `review_needed_for_scheduling=true` or `course_key` is `UNKNOWN`.",
        "6. Preserve the stacked renderer; do not replace it.",
        "7. Make August visibility explicit by creating/verifying real Enrollware rows before relying on generated seeds.",
    ]
    (AUDIT / "minimum_safe_gate_fix_plan.md").write_text(
        "\n".join(fix_lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
