from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from openpyxl import load_workbook


TZ = ZoneInfo("America/New_York")


def resolve_class_report_path(repo_root: Path, requested: str) -> Path:
    requested_path = (repo_root / requested).resolve()
    if requested_path.exists():
        return requested_path

    candidates = [
        repo_root / "data" / "Class Report.xlsx",
        repo_root / "data" / "raw" / "Class Report.xlsx",
        repo_root / "data" / "raw" / "class_report.xlsx",
        repo_root / "Class Report (37).xlsx",
        repo_root / "class-report.xlsx",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return requested_path


def clean_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def clean_whitespace(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return re.sub(r"\s+", " ", value).strip() or None


def parse_int(value: Any) -> Optional[int]:
    s = clean_string(value)
    if s is None:
        return None
    s = s.replace(",", "").strip()
    if s == "":
        return None
    try:
        return int(float(s))
    except Exception:
        return None


def parse_float(value: Any) -> Optional[float]:
    s = clean_string(value)
    if s is None:
        return None
    s = s.replace("$", "").replace(",", "").strip()
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None


def strip_tags(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    no_tags = re.sub(r"<[^>]+>", " ", text)
    no_tags = html.unescape(no_tags)
    return clean_whitespace(no_tags)


def extract_enroll_id_from_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    m = re.search(r"[?&]id=(\d+)", url)
    if m:
        return m.group(1)
    return None


def parse_datetime_flexible(value: Any) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        else:
            dt = dt.astimezone(TZ)
        return dt.isoformat()

    s = clean_string(value)
    if s is None:
        return None

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%y %I:%M %p",
        "%m/%d/%y %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(s, fmt).replace(tzinfo=TZ)
            return dt.isoformat()
        except Exception:
            continue

    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        else:
            dt = dt.astimezone(TZ)
        return dt.isoformat()
    except Exception:
        return None


@dataclass
class ParsedCourseBlob:
    course_name_raw: Optional[str]
    course_name_primary_raw: Optional[str]
    course_name_primary_clean: Optional[str]
    course_tail_raw: Optional[str]
    course_subtitle_text: Optional[str]
    course_number: Optional[str]
    course_code_hint: Optional[str]
    certifying_body_hint: Optional[str]
    source_hint: Optional[str]
    price_hint: Optional[float]
    delivery_mode_hint: Optional[str]
    image_src: Optional[str]
    parse_confidence: str
    parse_notes: list[str]


def parse_longdesc_tokens(longdesc: Optional[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    if not longdesc:
        return result
    for token in longdesc.split("|"):
        if ":" not in token:
            continue
        key, value = token.split(":", 1)
        result[key.strip().lower()] = value.strip()
    return result


def parse_course_blob(raw: Optional[str]) -> ParsedCourseBlob:
    notes: list[str] = []
    raw = clean_string(raw)

    if raw is None:
        return ParsedCourseBlob(
            course_name_raw=None,
            course_name_primary_raw=None,
            course_name_primary_clean=None,
            course_tail_raw=None,
            course_subtitle_text=None,
            course_number=None,
            course_code_hint=None,
            certifying_body_hint=None,
            source_hint=None,
            price_hint=None,
            delivery_mode_hint=None,
            image_src=None,
            parse_confidence="low",
            parse_notes=["empty_course_name"],
        )

    parts = re.split(r"<br\s*/?>", raw, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2:
        primary_raw, tail_raw = parts
    else:
        primary_raw, tail_raw = raw, None
        notes.append("no_br_found")

    primary_clean = strip_tags(primary_raw)

    subtitle_text = None
    if tail_raw:
        no_img_tail = re.sub(r"<img\b[^>]*>", " ", tail_raw, flags=re.IGNORECASE)
        subtitle_text = strip_tags(no_img_tail)
        if subtitle_text == primary_clean:
            subtitle_text = None

    image_src = None
    img_match = re.search(r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']', raw, flags=re.IGNORECASE)
    if img_match:
        image_src = img_match.group(1).strip()

    longdesc = None
    longdesc_match = re.search(r'\blongdesc=["\']([^"\']+)["\']', raw, flags=re.IGNORECASE)
    if longdesc_match:
        longdesc = longdesc_match.group(1).strip()
    else:
        notes.append("no_longdesc_found")

    tokens = parse_longdesc_tokens(longdesc)
    course_number = tokens.get("r")
    course_code_hint = tokens.get("t")
    certifying_body_hint = tokens.get("cb")
    source_hint = tokens.get("src")
    delivery_mode_hint = tokens.get("d")

    price_hint = None
    if "p" in tokens:
        try:
            price_hint = float(tokens["p"])
        except Exception:
            notes.append("price_hint_parse_failed")

    if not course_number:
        notes.append("course_number_missing")

    confidence = "low"
    if primary_clean and course_number and (course_code_hint or certifying_body_hint):
        confidence = "high"
    elif primary_clean:
        confidence = "medium"

    return ParsedCourseBlob(
        course_name_raw=raw,
        course_name_primary_raw=clean_whitespace(primary_raw),
        course_name_primary_clean=primary_clean,
        course_tail_raw=clean_whitespace(tail_raw) if tail_raw else None,
        course_subtitle_text=subtitle_text,
        course_number=course_number,
        course_code_hint=course_code_hint,
        certifying_body_hint=certifying_body_hint,
        source_hint=source_hint,
        price_hint=price_hint,
        delivery_mode_hint=delivery_mode_hint,
        image_src=image_src,
        parse_confidence=confidence,
        parse_notes=notes,
    )


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def read_class_report_rows(path: Path) -> list[dict[str, Any]]:
    wb = load_workbook(filename=path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [clean_string(h) or f"col_{i}" for i, h in enumerate(rows[0])]
    out: list[dict[str, Any]] = []
    for row in rows[1:]:
        rec = {}
        for i, header in enumerate(headers):
            rec[header] = row[i] if i < len(row) else None
        out.append(rec)
    return out


def index_students_by_class_id(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        class_id = clean_string(row.get("Class ID"))
        if class_id:
            grouped[class_id].append(row)
    return grouped


def dedupe_classes_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        internal_id = clean_string(row.get("Internal ID"))
        if not internal_id:
            internal_id = extract_enroll_id_from_url(clean_string(row.get("Registration Link")))
        if internal_id:
            deduped[internal_id] = row
    return deduped


def compute_registered_count(student_rows: list[dict[str, Any]]) -> int:
    return len(student_rows)


def build_session_from_class_report(
    report_row: dict[str, Any],
    class_patch: Optional[dict[str, Any]],
    student_rows: list[dict[str, Any]],
    now_iso: str,
) -> Optional[dict[str, Any]]:
    registration_url_report = clean_string(report_row.get("Registration Link"))
    session_id = extract_enroll_id_from_url(registration_url_report)

    if not session_id:
        session_id = clean_string(report_row.get("ID"))

    if not session_id:
        return None

    course_raw = None
    if class_patch:
        course_raw = clean_string(class_patch.get("Course Name"))
    if not course_raw:
        course_raw = clean_string(report_row.get("Course"))

    parsed = parse_course_blob(course_raw)

    course_id = clean_string(class_patch.get("Course Id")) if class_patch else None
    if not course_id:
        course_id = parsed.course_number

    start_at = parse_datetime_flexible(report_row.get("Start Date / Time"))
    end_at = parse_datetime_flexible(report_row.get("End Date / Time"))

    max_students = None
    if class_patch:
        max_students = parse_int(class_patch.get("Max Students"))
    if max_students is None:
        # In class report, Seats appears to be total seat capacity in this export
        max_students = parse_int(report_row.get("Seats"))

    students_count_raw = parse_int(report_row.get("Students"))
    registered_count = compute_registered_count(student_rows)

    # Fallback to class report student count if no student rows exist
    if registered_count == 0 and students_count_raw is not None:
        registered_count = students_count_raw

    available_seats = None
    is_full = None
    if max_students is not None:
        available_seats = max_students - registered_count
        if available_seats < 0:
            available_seats = 0
        is_full = available_seats <= 0

    price = parse_float(class_patch.get("Price")) if class_patch else None
    if price is None:
        price = parsed.price_hint

    registration_url = None
    if class_patch:
        registration_url = clean_string(class_patch.get("Registration Link"))
    if not registration_url:
        registration_url = registration_url_report

    location_name = None
    if class_patch:
        location_name = clean_string(class_patch.get("Location Name"))
    if not location_name:
        location_name = clean_string(report_row.get("Location"))

    client = None
    if class_patch:
        client = clean_string(class_patch.get("Client"))
    if not client:
        client = clean_string(report_row.get("Client"))

    lead_instructor_name = None
    if class_patch:
        lead_instructor_name = clean_string(class_patch.get("Lead Instructor Name"))
    if not lead_instructor_name:
        lead_instructor_name = clean_string(report_row.get("Instructor"))

    is_future = None
    is_past = None
    if start_at:
        try:
            start_dt = datetime.fromisoformat(start_at)
            now_dt = datetime.fromisoformat(now_iso)
            is_future = start_dt >= now_dt
            is_past = start_dt < now_dt
        except Exception:
            pass

    return {
        "session_id": session_id,
        "source_keys": {
            "class_report_id": clean_string(report_row.get("ID")),
            "class_sheet_internal_id": clean_string(class_patch.get("Internal ID")) if class_patch else None,
            "student_sheet_class_id": session_id,
        },
        "course": {
            "course_id": course_id,
            "course_name_raw": parsed.course_name_raw,
            "course_name_primary_raw": parsed.course_name_primary_raw,
            "course_name_primary_clean": parsed.course_name_primary_clean,
            "course_tail_raw": parsed.course_tail_raw,
            "course_subtitle_text": parsed.course_subtitle_text,
            "course_number": parsed.course_number or course_id,
            "course_code_hint": parsed.course_code_hint,
            "certifying_body_hint": parsed.certifying_body_hint,
            "source_hint": parsed.source_hint,
            "price_hint": parsed.price_hint,
            "delivery_mode_hint": parsed.delivery_mode_hint,
            "image_src": parsed.image_src,
            "parse_confidence": parsed.parse_confidence,
            "parse_notes": parsed.parse_notes,
        },
        "timing": {
            "start_at": start_at,
            "end_at": end_at,
            "timezone": "America/New_York",
            "is_future": is_future,
            "is_past": is_past,
        },
        "location": {
            "location_name": location_name,
            "location_display": location_name,
            "client": client,
        },
        "staffing": {
            "lead_instructor_name": lead_instructor_name,
        },
        "capacity": {
            "max_students": max_students,
            "students_count_raw": students_count_raw,
            "registered_count": registered_count,
            "available_seats": available_seats,
            "is_full": is_full,
        },
        "commerce": {
            "price": price,
            "registration_url": registration_url,
        },
        "status": {
            "session_status": "active",
            "source_of_truth": "class_report_backbone",
            "last_updated_at": now_iso,
        },
        "flags": {
            "needs_review": False,
            "has_missing_start_time": start_at is None,
            "has_missing_registration_url": registration_url is None,
            "has_missing_course_name": parsed.course_name_primary_clean is None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build merged sessions_current.json from raw files.")
    parser.add_argument("--repo-root", default=".", help="Path to repo root.")
    parser.add_argument("--class-report", default="data/Class Report.xlsx")
    parser.add_argument("--classes-csv", default="data/raw/classes_raw_live.csv")
    parser.add_argument("--students-csv", default="data/raw/students_raw_live.csv")
    parser.add_argument("--output", default="data/sessions_current.json")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    class_report_path = resolve_class_report_path(repo_root, args.class_report)
    classes_csv_path = (repo_root / args.classes_csv).resolve()
    students_csv_path = (repo_root / args.students_csv).resolve()
    output_path = (repo_root / args.output).resolve()

    for path in [class_report_path, classes_csv_path, students_csv_path]:
        if not path.exists():
            raise SystemExit(f"Required input file not found: {path}")

    print(f"Reading class report: {class_report_path}")
    class_report_rows = read_class_report_rows(class_report_path)

    print(f"Reading classes csv: {classes_csv_path}")
    classes_rows = read_csv_rows(classes_csv_path)

    print(f"Reading students csv: {students_csv_path}")
    students_rows = read_csv_rows(students_csv_path)

    print("Indexing sources...")
    classes_index = dedupe_classes_rows(classes_rows)
    students_index = index_students_by_class_id(students_rows)

    now_iso = datetime.now(TZ).isoformat()

    sessions: list[dict[str, Any]] = []
    skipped_no_session_id = 0

    for report_row in class_report_rows:
        report_reg_link = clean_string(report_row.get("Registration Link"))
        session_id = extract_enroll_id_from_url(report_reg_link)
        if not session_id:
            session_id = clean_string(report_row.get("ID"))

        if not session_id:
            skipped_no_session_id += 1
            continue

        class_patch = classes_index.get(session_id)
        student_rows_for_session = students_index.get(session_id, [])

        session = build_session_from_class_report(
            report_row=report_row,
            class_patch=class_patch,
            student_rows=student_rows_for_session,
            now_iso=now_iso,
        )
        if session:
            sessions.append(session)
        else:
            skipped_no_session_id += 1

    sessions.sort(
        key=lambda s: (
            s.get("timing", {}).get("start_at") or "",
            s.get("session_id") or "",
        )
    )

    output = {
        "build": {
            "generated_at": now_iso,
            "repo_root": str(repo_root),
            "inputs": {
                "class_report": str(class_report_path),
                "classes_csv": str(classes_csv_path),
                "students_csv": str(students_csv_path),
            },
            "counts": {
                "class_report_rows": len(class_report_rows),
                "classes_csv_rows": len(classes_rows),
                "classes_deduped_sessions": len(classes_index),
                "students_csv_rows": len(students_rows),
                "sessions_written": len(sessions),
                "skipped_no_session_id": skipped_no_session_id,
            },
        },
        "sessions": sessions,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote {output_path}")
    print(f"Sessions written: {len(sessions)}")
    print(f"Skipped no session id: {skipped_no_session_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
