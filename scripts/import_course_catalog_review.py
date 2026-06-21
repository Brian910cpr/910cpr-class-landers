from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REVIEW_PATH = Path(r"d:\Users\ten77\Downloads\Untitled11.csv")
COURSE_CATALOG_PATH = ROOT / "data" / "config" / "course_catalog.json"
REPORT_PATH = ROOT / "data" / "audit" / "course_catalog_review_import_report.md"
SUMMARY_PATH = ROOT / "data" / "audit" / "course_catalog_review_import_summary.json"
UNKNOWN = "UNKNOWN"


HEADER_ALIASES = {
    "course id": "course_id",
    "course_id": "course_id",
    "id": "course_id",
    "title": "title",
    "course title": "title",
    "duration": "duration_minutes",
    "duration minutes": "duration_minutes",
    "duration_minutes": "duration_minutes",
    "capacity": "default_capacity",
    "default capacity": "default_capacity",
    "default_capacity": "default_capacity",
    "appointment?": "appointment_allowed",
    "appointment": "appointment_allowed",
    "appointment allowed": "appointment_allowed",
    "appointment_allowed": "appointment_allowed",
    "instructor requirement": "required_instructor_certifications",
    "instructor requirements": "required_instructor_certifications",
    "required instructor certifications": "required_instructor_certifications",
    "required_instructor_certifications": "required_instructor_certifications",
    "notes": "review_notes",
    "note": "review_notes",
    "resource notes": "review_notes",
    "resource note": "review_notes",
}

INSTRUCTOR_NORMALIZATION = {
    "AHA_BLS": "AHA_BLS_INSTRUCTOR",
    "AHA_ACLS": "AHA_ACLS_INSTRUCTOR",
    "AHA_PALS": "AHA_PALS_INSTRUCTOR",
    "AHA_HEARTSAVER": "AHA_HEARTSAVER_INSTRUCTOR",
    "ARC_BLS": "ARC_BLS_INSTRUCTOR",
    "ARC": "ARC_INSTRUCTOR",
    "HSI": "HSI_INSTRUCTOR",
    "HSI_LEVELI": "HSI_INSTRUCTOR",
    "HSI_LEVEL_I": "HSI_INSTRUCTOR",
    "USCG": "AHA_HEARTSAVER_INSTRUCTOR",
    "USCG/AHA": "AHA_HEARTSAVER_INSTRUCTOR",
}


def normalize_header(value: Any) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip().lower())
    return HEADER_ALIASES.get(text, text)


def normalize_course_id(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    if re.fullmatch(r"\d+\.0", text):
        return text[:-2]
    return text


def parse_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text or text.upper() == UNKNOWN:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    if parsed.is_integer():
        return int(parsed)
    return None


def parse_appointment(value: Any) -> bool | None:
    text = str(value or "").strip()
    if not text or text.upper() == UNKNOWN:
        return None
    if text in {"1", "1.0"}:
        return True
    if text in {"0", "0.0"}:
        return False
    normalized = text.lower()
    if normalized in {"yes", "y", "true"}:
        return True
    if normalized in {"no", "n", "false"}:
        return False
    return None


def normalize_instructor_requirements(value: Any) -> list[str] | None:
    text = str(value or "").strip()
    if not text or text.upper() == UNKNOWN:
        return None
    parts = [part.strip() for part in re.split(r"[,;/\n]+", text) if part.strip()]
    normalized: list[str] = []
    for part in parts:
        key = re.sub(r"\s+", "_", part.strip().upper())
        normalized.append(INSTRUCTOR_NORMALIZATION.get(key, key))
    return normalized or None


def read_xls_rows(path: Path) -> tuple[str, int, dict[str, int], list[dict[str, Any]]]:
    try:
        import xlrd
    except ImportError as exc:
        raise RuntimeError("xlrd is required to read .xls review spreadsheets. Install it with: python -m pip install xlrd") from exc

    book = xlrd.open_workbook(str(path))
    sheet = next((candidate for candidate in book.sheets() if candidate.nrows and candidate.ncols), None)
    if sheet is None:
        raise RuntimeError("No non-empty worksheet found in review spreadsheet.")

    header_row_index = -1
    header_map: dict[str, int] = {}
    for row_index in range(min(sheet.nrows, 20)):
        values = [normalize_header(sheet.cell_value(row_index, col_index)) for col_index in range(sheet.ncols)]
        if "course_id" in values and ("duration_minutes" in values or "default_capacity" in values):
            header_row_index = row_index
            header_map = {value: index for index, value in enumerate(values) if value}
            break
    if header_row_index < 0:
        raise RuntimeError("Could not identify header row with Course ID and scheduler review fields.")

    rows: list[dict[str, Any]] = []
    for row_index in range(header_row_index + 1, sheet.nrows):
        raw = {name: sheet.cell_value(row_index, col_index) for name, col_index in header_map.items()}
        raw["_row_number"] = row_index + 1
        rows.append(raw)
    return sheet.name, header_row_index + 1, header_map, rows


def read_csv_rows(path: Path) -> tuple[str, int, dict[str, int], list[dict[str, Any]]]:
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                reader = list(csv.reader(handle))
            break
        except UnicodeDecodeError as exc:
            last_error = exc
    else:
        raise RuntimeError(f"Could not decode CSV review spreadsheet: {last_error}") from last_error
    header_row_index = -1
    header_map: dict[str, int] = {}
    for row_index, row in enumerate(reader[:20]):
        values = [normalize_header(value) for value in row]
        if "course_id" in values and ("duration_minutes" in values or "default_capacity" in values):
            header_row_index = row_index
            header_map = {value: index for index, value in enumerate(values) if value}
            break
    if header_row_index < 0:
        raise RuntimeError("Could not identify header row with Course ID and scheduler review fields.")

    rows: list[dict[str, Any]] = []
    for row_index in range(header_row_index + 1, len(reader)):
        row = reader[row_index]
        raw = {
            name: row[col_index] if col_index < len(row) else ""
            for name, col_index in header_map.items()
        }
        raw["_row_number"] = row_index + 1
        rows.append(raw)
    return path.name, header_row_index + 1, header_map, rows


def read_review_rows(path: Path) -> tuple[str, int, dict[str, int], list[dict[str, Any]]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return read_csv_rows(path)
    if suffix in {".xls", ".xlsx", ".xlsm"}:
        return read_xls_rows(path)
    raise RuntimeError(f"Unsupported review spreadsheet format: {path.suffix}")


def meaningful(value: Any) -> bool:
    if value in (None, ""):
        return False
    return str(value).strip().upper() != UNKNOWN


def apply_review(catalog: dict[str, Any], rows: list[dict[str, Any]], source_path: Path) -> dict[str, Any]:
    courses = catalog.get("courses", [])
    if not isinstance(courses, list):
        raise RuntimeError("course_catalog.json does not contain a courses list.")
    by_id = {str(course.get("course_id") or ""): course for course in courses if isinstance(course, dict)}

    updated: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    fields_counter: Counter[str] = Counter()

    for row in rows:
        course_id = normalize_course_id(row.get("course_id"))
        title = str(row.get("title") or "").strip()
        if not course_id or not course_id.isdigit():
            skipped.append({"row_number": row["_row_number"], "course_id": course_id or None, "title": title, "reason": "missing_course_id_or_group_row"})
            continue
        course = by_id.get(course_id)
        if not course:
            skipped.append({"row_number": row["_row_number"], "course_id": course_id, "title": title, "reason": "course_id_not_found_in_course_catalog"})
            continue

        field_changes: dict[str, dict[str, Any]] = {}

        duration = parse_int(row.get("duration_minutes"))
        if duration is not None and course.get("duration_minutes") != duration:
            field_changes["duration_minutes"] = {"old": course.get("duration_minutes"), "new": duration}
            course["duration_minutes"] = duration

        capacity = parse_int(row.get("default_capacity"))
        if capacity is not None and course.get("default_capacity") != capacity:
            field_changes["default_capacity"] = {"old": course.get("default_capacity"), "new": capacity}
            course["default_capacity"] = capacity

        appointment = parse_appointment(row.get("appointment_allowed"))
        if appointment is not None and course.get("appointment_allowed") is not appointment:
            field_changes["appointment_allowed"] = {"old": course.get("appointment_allowed"), "new": appointment}
            course["appointment_allowed"] = appointment

        instructor_requirements = normalize_instructor_requirements(row.get("required_instructor_certifications"))
        if instructor_requirements is not None and course.get("required_instructor_certifications") != instructor_requirements:
            field_changes["required_instructor_certifications"] = {
                "old": course.get("required_instructor_certifications"),
                "new": instructor_requirements,
            }
            course["required_instructor_certifications"] = instructor_requirements

        if "review_notes" in row and meaningful(row.get("review_notes")):
            notes = str(row.get("review_notes")).strip()
            if course.get("review_notes") != notes:
                field_changes["review_notes"] = {"old": course.get("review_notes"), "new": notes}
                course["review_notes"] = notes

        if field_changes:
            for field in field_changes:
                fields_counter[field] += 1
            updated.append({
                "row_number": row["_row_number"],
                "course_id": course_id,
                "title": course.get("official_title") or title,
                "fields_updated": field_changes,
            })

    catalog["updated_at"] = datetime.now().astimezone().isoformat()
    catalog["last_review_import"] = {
        "source": str(source_path),
        "updated_at": catalog["updated_at"],
        "updated_course_count": len(updated),
        "fields_updated": dict(fields_counter),
        "safety_note": "Only scheduler-critical reviewed fields were imported by course_id.",
    }
    return {"updated": updated, "skipped": skipped, "fields_updated": dict(fields_counter)}


def unknowns(catalog: dict[str, Any]) -> dict[str, list[dict[str, str]]]:
    result = {
        "missing_duration": [],
        "missing_capacity": [],
        "missing_appointment_allowed": [],
        "missing_required_instructor_certifications": [],
    }
    for course in catalog.get("courses", []):
        if not isinstance(course, dict):
            continue
        base = {
            "course_id": str(course.get("course_id") or UNKNOWN),
            "title": str(course.get("official_title") or UNKNOWN),
        }
        if course.get("duration_minutes") == UNKNOWN:
            result["missing_duration"].append(base)
        if course.get("default_capacity") == UNKNOWN:
            result["missing_capacity"].append(base)
        if course.get("appointment_allowed") == UNKNOWN:
            result["missing_appointment_allowed"].append(base)
        if course.get("required_instructor_certifications") == [UNKNOWN]:
            result["missing_required_instructor_certifications"].append(base)
    return result


def write_reports(
    *,
    spreadsheet_path: Path,
    worksheet_name: str,
    header_row: int,
    header_map: dict[str, int],
    row_count: int,
    import_result: dict[str, Any],
    remaining_unknowns: dict[str, list[dict[str, str]]],
) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "spreadsheet_file_read": str(spreadsheet_path),
        "worksheet_name": worksheet_name,
        "header_row": header_row,
        "mapped_columns": sorted(header_map),
        "rows_processed": row_count,
        "rows_updated": len(import_result["updated"]),
        "rows_skipped": len(import_result["skipped"]),
        "fields_updated": import_result["fields_updated"],
        "unknowns_remaining_after_import": {key: len(value) for key, value in remaining_unknowns.items()},
        "updated_courses": import_result["updated"],
        "skipped_rows": import_result["skipped"],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Course Catalog Review Import Report",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Spreadsheet file read: `{spreadsheet_path}`",
        f"- Worksheet: `{worksheet_name}`",
        f"- Header row: {header_row}",
        f"- Rows processed: {row_count}",
        f"- Rows updated: {summary['rows_updated']}",
        f"- Rows skipped: {summary['rows_skipped']}",
        "",
        "Safety: this import updates only scheduler-critical fields in `data/config/course_catalog.json` by matching `course_id`. It does not touch public pages, Enrollware behavior, appointment URLs, Worker settings, product systems, or generated HTML.",
        "",
        "## Mapped Columns",
        "",
    ]
    lines.extend(f"- `{name}`" for name in sorted(header_map))
    lines.extend(["", "## Fields Updated By Course", ""])
    if import_result["updated"]:
        lines.extend(["| Course ID | Title | Fields Updated |", "|---|---|---|"])
        for item in import_result["updated"]:
            fields = ", ".join(item["fields_updated"])
            title = str(item.get("title") or "").replace("|", "/")
            lines.append(f"| {item['course_id']} | {title} | {fields} |")
    else:
        lines.append("- None")
    lines.extend(["", "## Skipped Rows", ""])
    if import_result["skipped"]:
        lines.extend(["| Row | Course ID | Title | Reason |", "|---:|---|---|---|"])
        for item in import_result["skipped"]:
            title = str(item.get("title") or "").replace("|", "/")
            lines.append(f"| {item['row_number']} | {item.get('course_id') or ''} | {title} | {item['reason']} |")
    else:
        lines.append("- None")
    lines.extend(["", "## Unknowns Remaining After Import", ""])
    for key, values in remaining_unknowns.items():
        lines.append(f"### {key.replace('_', ' ').title()}")
        lines.append("")
        if values:
            for item in values:
                lines.append(f"- {item['course_id']}: {item['title']}")
        else:
            lines.append("- None")
        lines.append("")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Brian's scheduler course review into course_catalog.json.")
    parser.add_argument("--input", default=str(DEFAULT_REVIEW_PATH), help="Path to Brian's reviewed .xls/.xlsx spreadsheet.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    spreadsheet_path = Path(args.input)
    if not spreadsheet_path.exists():
        raise SystemExit(f"Review spreadsheet not found: {spreadsheet_path}")

    worksheet_name, header_row, header_map, rows = read_review_rows(spreadsheet_path)
    catalog = json.loads(COURSE_CATALOG_PATH.read_text(encoding="utf-8"))
    result = apply_review(catalog, rows, spreadsheet_path)
    COURSE_CATALOG_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    remaining = unknowns(catalog)
    write_reports(
        spreadsheet_path=spreadsheet_path,
        worksheet_name=worksheet_name,
        header_row=header_row,
        header_map=header_map,
        row_count=len(rows),
        import_result=result,
        remaining_unknowns=remaining,
    )
    print("Course catalog review import complete.")
    print(f"Spreadsheet: {spreadsheet_path}")
    print(f"Worksheet: {worksheet_name}")
    print(f"Header row: {header_row}")
    print(f"Rows processed: {len(rows)}")
    print(f"Rows updated: {len(result['updated'])}")
    print(f"Rows skipped: {len(result['skipped'])}")
    print(f"Wrote {COURSE_CATALOG_PATH}")
    print(f"Wrote {SUMMARY_PATH}")
    print(f"Wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
