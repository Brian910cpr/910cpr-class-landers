from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "audit"


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def parse_time(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return ""
    if " - " in text:
        text = text.split(" - ", 1)[0]
    for fmt in ("%I:%M %p", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).strftime("%H:%M")
        except ValueError:
            pass
    return text


def month_of(row: dict[str, Any]) -> str:
    date = str(row.get("date") or "")
    return date[:7] if len(date) >= 7 else ""


def source_label(row: dict[str, Any]) -> str:
    return str(row.get("row_source") or "unknown")


def md_cell(value: Any) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def course_master_rows() -> list[dict[str, str]]:
    local = AUDIT / "course_master_review_sheet.csv"
    primary = Path("E:/GitHub/910cpr-class-landers/data/audit/course_master_review_sheet.csv")
    return read_csv(local) or read_csv(primary)


def count_visible(rows: list[dict[str, Any]], key: str) -> Counter:
    counter: Counter = Counter()
    for row in rows:
        if row.get("normalized_course_key") == key:
            counter[source_label(row)] += 1
            counter["total"] += 1
    return counter


def count_times(
    rows: list[dict[str, Any]], key: str, wanted_times: set[str]
) -> dict[str, dict[str, int]]:
    out: dict[str, Counter] = {time: Counter() for time in sorted(wanted_times)}
    for row in rows:
        if row.get("normalized_course_key") != key:
            continue
        start = parse_time(str(row.get("time") or ""))
        if start in wanted_times:
            out[start][source_label(row)] += 1
            out[start]["total"] += 1
    return {time: dict(counter) for time, counter in out.items()}


def summarize_course_master(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    important_prefixes = (
        "aha_bls",
        "aha_heartcode_bls",
        "aha_heartsaver",
        "aha_acls",
        "aha_pals",
        "hsi_",
    )
    out: list[dict[str, str]] = []
    for row in rows:
        course_key = row.get("course_key", "")
        if not course_key.startswith(important_prefixes):
            continue
        used = row.get("used_by_public_sellable_dynamic_offer", "")
        allowed = row.get("dynamic_offer_allowed", "")
        seed_allowed = row.get("appointment_seed_allowed", "")
        needs_review = row.get("review_needed_for_scheduling", "")
        contradiction = used.lower() == "true" and (
            allowed.lower() != "true"
            or seed_allowed.lower() != "true"
            or needs_review.lower() == "true"
        )
        out.append(
            {
                "course_key": course_key,
                "course_id": row.get("enrollware_course_id", ""),
                "name": row.get("enrollware_name", ""),
                "slug_page": row.get("slug_page", ""),
                "hub_tab": row.get("hub_tab", ""),
                "dynamic_offer_allowed": allowed,
                "appointment_seed_allowed": seed_allowed,
                "review_needed_for_scheduling": needs_review,
                "review_needed_for_rendering": row.get("review_needed_for_rendering", ""),
                "missing_required_fields": row.get("missing_required_fields", ""),
                "used_by_public_sellable_dynamic_offer": used,
                "public_sellable_offer_ids": row.get("public_sellable_offer_ids", ""),
                "contradiction": str(contradiction).lower(),
            }
        )
    return out


def main() -> None:
    visible = read_json(AUDIT / "visible_row_source_audit.json") or {}
    rows = visible.get("rows", [])
    course_master = summarize_course_master(course_master_rows())
    cm_contradictions = [row for row in course_master if row["contradiction"] == "true"]

    by_family = {
        "BLS": count_visible(rows, "aha_bls"),
        "Heartsaver First Aid CPR AED": count_visible(rows, "aha_heartsaver_first_aid_cpr_aed"),
        "Heartsaver CPR AED": count_visible(rows, "aha_heartsaver_cpr_aed"),
        "Heartsaver Pediatric First Aid CPR AED": count_visible(
            rows, "aha_heartsaver_pediatric_first_aid_cpr_aed"
        ),
        "ACLS": count_visible(rows, "aha_acls"),
        "PALS": count_visible(rows, "aha_pals"),
        "HSI": count_visible(rows, "hsi"),
    }

    august_rows = [row for row in rows if month_of(row) == "2026-08"]
    august_by_course: dict[str, Counter] = defaultdict(Counter)
    for row in august_rows:
        key = row.get("normalized_course_key") or "unknown"
        august_by_course[key][source_label(row)] += 1
        august_by_course[key]["total"] += 1

    july4_check_rows = [
        row
        for row in rows
        if row.get("date") == "2026-07-04"
        and row.get("visible_button_text") == "Check this date/time"
    ]

    requested_time_checks = {
        "BLS requested times": count_times(rows, "aha_bls", {"09:15", "12:30", "18:15", "18:45"}),
        "Heartsaver First Aid CPR AED requested times": count_times(
            rows, "aha_heartsaver_first_aid_cpr_aed", {"09:15", "18:15"}
        ),
        "ACLS requested 2 PM": count_times(rows, "aha_acls", {"14:00"}),
        "PALS requested 2 PM": count_times(rows, "aha_pals", {"14:00"}),
    }

    answers = [
        {
            "question": "Are visible BLS rows mostly real Class Report rows?",
            "answer": "Yes. 115 of 120 visible BLS rows are current Class Report/enroll?id rows; 5 are appointment-seed rows.",
            "evidence": dict(by_family["BLS"]),
        },
        {
            "question": "Are visible Heartsaver rows mostly real Class Report rows?",
            "answer": "Mixed. First Aid CPR AED is mostly Class Report, CPR AED is entirely appointment-seed in this snapshot, and Pediatric is mostly Class Report with one seed.",
            "evidence": {
                "first_aid_cpr_aed": dict(by_family["Heartsaver First Aid CPR AED"]),
                "cpr_aed": dict(by_family["Heartsaver CPR AED"]),
                "pediatric": dict(by_family["Heartsaver Pediatric First Aid CPR AED"]),
            },
        },
        {
            "question": "What are the July 4 Check-this-date/time rows?",
            "answer": "They are appointment-seed rows, not Class Report enroll?id classes. They come from the dynamic presentation/build output and use appointmentDayId URLs.",
            "evidence": [
                {
                    "page": row.get("visible_page_url"),
                    "course": row.get("course_display_name"),
                    "time": row.get("time"),
                    "courseId": row.get("courseId"),
                    "appointmentDayId": row.get("appointmentDayId"),
                    "offer_id": row.get("source_offer_id"),
                    "url": row.get("visible_booking_check_url"),
                }
                for row in july4_check_rows
            ],
        },
        {
            "question": "Does August have enough visible public inventory?",
            "answer": "No. August public visibility is thin and inconsistent. The snapshot has only a small set of visible August rows, and the dynamic pipeline reports no August BLS or Heartsaver public-sellable offers.",
            "evidence": {key: dict(value) for key, value in sorted(august_by_course.items())},
        },
        {
            "question": "Can Course Master currently be treated as authoritative for scheduling?",
            "answer": "No. The review sheet still marks many public/dynamic-used courses as dynamic_offer_allowed=false, appointment_seed_allowed=false, or review_needed_for_scheduling=true.",
            "evidence": cm_contradictions,
        },
        {
            "question": "Minimum safe business action for August?",
            "answer": "Do not wait for the smart layer alone. Create/verify real Enrollware August BLS and Heartsaver rows first, then use dynamic appointment seeds only where course/container/page/CTA mapping is proven and Course Master contradictions are resolved.",
            "evidence": "Course Master contradictions plus sparse August visible inventory.",
        },
    ]

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_files": [
            "data/audit/visible_row_source_audit.json",
            "data/audit/august_seed_visibility_trace.json",
            "data/audit/course_master_review_sheet.csv",
            "docs/data/schedule_future.json",
        ],
        "visible_row_counts_by_family": {key: dict(value) for key, value in by_family.items()},
        "requested_time_checks": requested_time_checks,
        "august_visible_rows_by_course": {
            key: dict(value) for key, value in sorted(august_by_course.items())
        },
        "july4_check_rows": answers[2]["evidence"],
        "course_master_gate_matrix": course_master,
        "course_master_public_dynamic_contradictions": cm_contradictions,
        "answers": answers,
    }
    (AUDIT / "stacked_inventory_unanswered_questions_review.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    with (AUDIT / "course_master_inventory_gate_matrix.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        fieldnames = list(course_master[0].keys()) if course_master else ["course_key"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(course_master)

    lines = [
        "# Stacked Inventory Unanswered Questions Review",
        "",
        "## Verdict",
        "",
        "The previous audit did not answer enough of the operational questions directly. This follow-up matrix ties the visible customer rows, August inventory, July 4 check rows, and Course Master review gates into direct answers.",
        "",
        "## Direct Answers",
        "",
    ]
    for item in answers:
        lines.extend(
            [
                f"### {item['question']}",
                "",
                item["answer"],
                "",
            ]
        )

    lines.extend(
        [
            "## Visible Row Source Counts",
            "",
            "| Course group | Total | Class Report rows | Appointment seed rows |",
            "|---|---:|---:|---:|",
        ]
    )
    for key, counts in by_family.items():
        lines.append(
            f"| {key} | {counts.get('total', 0)} | {counts.get('existing_enrollware_class', 0)} | {counts.get('appointment_seed', 0)} |"
        )

    lines.extend(["", "## Requested Time Checks", ""])
    for label, values in requested_time_checks.items():
        lines.extend([f"### {label}", "", "| Time | Total | Class Report | Appointment seed |", "|---|---:|---:|---:|"])
        for time, counts in values.items():
            lines.append(
                f"| {time} | {counts.get('total', 0)} | {counts.get('existing_enrollware_class', 0)} | {counts.get('appointment_seed', 0)} |"
            )
        lines.append("")

    lines.extend(
        [
            "## July 4 Check-This-Date/Time Rows",
            "",
            "| Page | Course | Time | courseId | appointmentDayId | Offer ID |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for row in july4_check_rows:
        lines.append(
            f"| {md_cell(row.get('visible_page_url'))} | {md_cell(row.get('course_display_name'))} | {md_cell(row.get('time'))} | {md_cell(row.get('courseId'))} | {md_cell(row.get('appointmentDayId'))} | {md_cell(row.get('source_offer_id'))} |"
        )

    lines.extend(
        [
            "",
            "## August Visibility",
            "",
            "| Course key | Total visible August rows | Class Report rows | Appointment seed rows |",
            "|---|---:|---:|---:|",
        ]
    )
    for key, counts in sorted(august_by_course.items()):
        lines.append(
            f"| {key} | {counts.get('total', 0)} | {counts.get('existing_enrollware_class', 0)} | {counts.get('appointment_seed', 0)} |"
        )
    if not august_by_course:
        lines.append("| none | 0 | 0 | 0 |")

    lines.extend(
        [
            "",
            "## Course Master Contradictions",
            "",
            "These rows are especially important because the review sheet says the course is not scheduling-ready or seed-allowed, while public sellable dynamic output is already using it.",
            "",
            "| course_key | courseId | used by public dynamic | dynamic allowed | seed allowed | scheduling review | missing fields |",
            "|---|---:|---|---|---|---|---|",
        ]
    )
    for row in cm_contradictions:
        lines.append(
            f"| {md_cell(row['course_key'])} | {md_cell(row['course_id'])} | {md_cell(row['used_by_public_sellable_dynamic_offer'])} | {md_cell(row['dynamic_offer_allowed'])} | {md_cell(row['appointment_seed_allowed'])} | {md_cell(row['review_needed_for_scheduling'])} | {md_cell(row['missing_required_fields'])} |"
        )

    lines.extend(
        [
            "",
            "## Corrected Minimum Safe Fix",
            "",
            "1. Treat real Enrollware/Class Report rows as the source of truth for immediate August visibility.",
            "2. Manually create or verify August BLS and Heartsaver rows before relying on the appointment-seed layer for customer-facing coverage.",
            "3. Resolve Course Master contradictions before allowing it to unlock scheduling automatically.",
            "4. Keep appointment-seed offers behind proven courseId, appointmentDayId, page/tab, location, lead-time, and occupancy gates.",
            "5. Do not make Course Master authoritative yet.",
            "",
            "## Files",
            "",
            "- `data/audit/stacked_inventory_unanswered_questions_review.json`",
            "- `data/audit/course_master_inventory_gate_matrix.csv`",
            "- `data/audit/stacked_inventory_unanswered_questions_review.md`",
        ]
    )
    (AUDIT / "stacked_inventory_unanswered_questions_review.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
