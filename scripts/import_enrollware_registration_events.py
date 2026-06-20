from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "data" / "audit"
DEFAULT_SEEDS_PATH = AUDIT_DIR / "schedule_seeds_preview.json"
NORMALIZED_EVENTS_PATH = AUDIT_DIR / "enrollware_registration_events_normalized.json"
SUMMARY_PATH = AUDIT_DIR / "enrollware_registration_event_import_summary.json"
REPORT_PATH = AUDIT_DIR / "enrollware_registration_event_import_report.md"
MATCHED_SEEDS_PATH = AUDIT_DIR / "appointment_seed_registration_matches.json"
UNKNOWN = "UNKNOWN"


HEADER_ALIASES = {
    "regId": ["regId", "reg_id", "Registration ID", "RegistrationId", "Registration Id", "Reg ID", "RegId"],
    "courseId": ["courseId", "course_id", "Course ID", "CourseId", "Course Id"],
    "courseSchedId": [
        "courseSchedId",
        "course_sched_id",
        "Course Schedule ID",
        "CourseSchedId",
        "Course Sched ID",
        "CourseSched ID",
        "Class ID",
        "classId",
    ],
    "courseName": ["courseName", "course_name", "Course Name", "CourseName", "Class Name", "Course"],
    "discipline": ["discipline", "Discipline", "Course Discipline"],
    "locationName": ["locationName", "location_name", "Location Name", "LocationName", "Location", "Class Location"],
    "startTime": ["startTime", "start_time", "Start Time", "StartTime", "Class Start", "Class Start Time", "Start"],
    "instructor": ["instructor", "Instructor", "Instructor Name"],
    "student": ["student", "Student", "Student Name", "Name", "Registrant", "Registrant Name"],
    "firstName": ["firstName", "first_name", "First Name", "Firstname"],
    "lastName": ["lastName", "last_name", "Last Name", "Lastname"],
    "emailAddress": ["emailAddress", "email_address", "Email Address", "Email", "Student Email", "email"],
    "phoneNumber": ["phoneNumber", "phone_number", "Phone Number", "Phone", "Student Phone"],
    "altPhoneNumber": ["altPhoneNumber", "alt_phone_number", "Alt Phone Number", "Alternate Phone", "Alternate Phone Number"],
    "address1": ["address1", "address_1", "Address 1", "Address1", "Street Address", "Street"],
    "address2": ["address2", "address_2", "Address 2", "Address2", "Suite", "Unit"],
    "city": ["city", "City"],
    "state": ["state", "State"],
    "zip": ["zip", "Zip", "ZIP", "Postal Code", "Zip Code"],
    "country": ["country", "Country"],
    "license": ["license", "License", "License Number", "Professional License"],
    "promoCode": ["promoCode", "promo_code", "Promo Code", "PromoCode", "Coupon Code"],
    "classPriceCode": ["classPriceCode", "class_price_code", "Class Price Code", "Price Code"],
    "status": ["status", "Status"],
    "balanceDue": ["balanceDue", "balance_due", "Balance Due", "BalanceDue"],
    "classPrice": ["classPrice", "class_price", "Class Price", "Course Price", "Price"],
    "orderTotal": ["orderTotal", "order_total", "Order Total", "Total"],
    "optionTotal": ["optionTotal", "option_total", "Option Total", "Options Total", "Add-on Total"],
    "shipPrice": ["shipPrice", "ship_price", "Ship Price", "Shipping", "Shipping Price"],
    "comments": ["comments", "Comments", "Registration Comments", "Student Comments"],
    "options": ["options", "Options", "Selected Options", "Option Details", "Addons", "Add-ons", "Add Ons"],
    "questions": ["questions", "Questions", "Question Answers", "Registration Questions", "Custom Questions"],
    "payments": ["payments", "Payments", "Payment Details", "Payment"],
    "queryString": ["queryString", "query_string", "Query String", "Source Query String", "UTM Query"],
    "sourceMetadata": ["sourceMetadata", "source_metadata", "Source Metadata", "Zap Meta", "Zapier Metadata"],
    "importedAt": ["importedAt", "imported_at", "Imported At", "Import Time"],
    "receivedAt": ["receivedAt", "received_at", "Received At", "Zap Meta Timestamp", "Zapier Timestamp"],
}


REQUIRED_IDENTIFIER_FIELDS = ["regId", "courseId", "courseSchedId", "startTime"]


def read_json(path: Path) -> tuple[Any | None, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid_json: {exc}"
    except OSError as exc:
        return None, f"read_error: {exc}"


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean_text(value).lower()).strip("_")


def normalize_location(value: Any) -> str:
    text = clean_text(value).lower()
    text = text.replace("@ 910cpr's office", "")
    text = re.sub(r";?\s*room\s+[a-z0-9]+", "", text)
    text = text.replace(";", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_course_title(value: Any) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_dt(value: Any) -> datetime | None:
    text = clean_text(value)
    if not text:
        return None
    for candidate in [text, text.replace(" ", "T")]:
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
    for fmt in ("%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def canonical_header_map(headers: list[str]) -> dict[str, str]:
    normalized_headers = {normalize_key(header): header for header in headers}
    out: dict[str, str] = {}
    for canonical, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            key = normalize_key(alias)
            if key in normalized_headers:
                out[canonical] = normalized_headers[key]
                break
    return out


def read_csv_rows(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        header_map = canonical_header_map(headers)
        mapped_headers = canonical_source_headers(header_map)
        rows = []
        for index, raw in enumerate(reader, start=2):
            row = {"_row_number": index, "_raw": raw, "_mapped_headers": mapped_headers}
            for canonical, source_header in header_map.items():
                row[canonical] = raw.get(source_header, "")
            rows.append(row)
    return rows, {"headers": headers, "header_map": header_map}


def canonical_source_headers(header_map: dict[str, str]) -> set[str]:
    return {source_header for source_header in header_map.values() if source_header}


def is_blank_row(row: dict[str, Any]) -> bool:
    raw = row.get("_raw", {})
    if not isinstance(raw, dict):
        return True
    return all(clean_text(value) == "" for value in raw.values())


def raw_unmapped_fields(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get("_raw", {})
    if not isinstance(raw, dict):
        return {}
    mapped_headers = row.get("_mapped_headers", set())
    return {
        header: value for header, value in raw.items()
        if header not in mapped_headers and clean_text(value)
    }


def email_domain(value: Any) -> str:
    text = clean_text(value).lower()
    if "@" not in text:
        return UNKNOWN
    domain = text.rsplit("@", 1)[-1].strip()
    return domain or UNKNOWN


def find_employer_clue(*values: Any) -> str:
    text = "\n".join(clean_text(value) for value in values if clean_text(value))
    if not text:
        return UNKNOWN
    patterns = [
        r"(?:employer|company|organization|agency|department)\s*[:=-]\s*([^;\n\r|]+)",
        r"(?:employer|company|organization|agency|department)\?\s*([^;\n\r|]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return clean_text(match.group(1))
    return UNKNOWN


def possible_person_key(first_name: str, last_name: str, email: str, phone: str) -> str:
    if email != UNKNOWN:
        return f"email:{email.lower()}"
    if first_name != UNKNOWN and last_name != UNKNOWN and phone != UNKNOWN:
        return f"name_phone:{normalize_key(first_name)}_{normalize_key(last_name)}_{normalize_key(phone)}"
    if first_name != UNKNOWN and last_name != UNKNOWN:
        return f"name:{normalize_key(first_name)}_{normalize_key(last_name)}"
    return UNKNOWN


def normalize_registration_row(row: dict[str, Any], source: str) -> dict[str, Any]:
    start = parse_dt(row.get("startTime"))
    reg_id = clean_text(row.get("regId"))
    course_sched_id = clean_text(row.get("courseSchedId"))
    first_name = clean_text(row.get("firstName"))
    last_name = clean_text(row.get("lastName"))
    student = clean_text(row.get("student")) or clean_text(f"{first_name} {last_name}")
    email = clean_text(row.get("emailAddress")) or UNKNOWN
    phone = clean_text(row.get("phoneNumber")) or UNKNOWN
    employer = find_employer_clue(row.get("questions"), row.get("comments"), row.get("sourceMetadata"), row.get("queryString"))
    domain = email_domain(email)
    missing_identifiers = [
        field for field in REQUIRED_IDENTIFIER_FIELDS
        if not clean_text(row.get(field))
    ]
    warnings = []
    if missing_identifiers:
        warnings.append("missing_required_identifier")
    if clean_text(row.get("startTime")) and start is None:
        warnings.append("unparseable_startTime")
    return {
        "event_id": reg_id or f"missing-regId-row-{row.get('_row_number', UNKNOWN)}",
        "regId": reg_id or UNKNOWN,
        "courseId": clean_text(row.get("courseId")) or UNKNOWN,
        "courseSchedId": course_sched_id or UNKNOWN,
        "courseName": clean_text(row.get("courseName")) or UNKNOWN,
        "discipline": clean_text(row.get("discipline")) or UNKNOWN,
        "locationName": clean_text(row.get("locationName")) or UNKNOWN,
        "startTime": start.isoformat() if start else clean_text(row.get("startTime")) or UNKNOWN,
        "startTime_parseable": start is not None,
        "instructor": clean_text(row.get("instructor")) or UNKNOWN,
        "firstName": first_name or UNKNOWN,
        "lastName": last_name or UNKNOWN,
        "student": student or UNKNOWN,
        "emailAddress": email,
        "phoneNumber": phone,
        "altPhoneNumber": clean_text(row.get("altPhoneNumber")) or UNKNOWN,
        "address1": clean_text(row.get("address1")) or UNKNOWN,
        "address2": clean_text(row.get("address2")) or UNKNOWN,
        "city": clean_text(row.get("city")) or UNKNOWN,
        "state": clean_text(row.get("state")) or UNKNOWN,
        "zip": clean_text(row.get("zip")) or UNKNOWN,
        "country": clean_text(row.get("country")) or UNKNOWN,
        "license": clean_text(row.get("license")) or UNKNOWN,
        "promoCode": clean_text(row.get("promoCode")) or UNKNOWN,
        "classPriceCode": clean_text(row.get("classPriceCode")) or UNKNOWN,
        "status": clean_text(row.get("status")) or UNKNOWN,
        "balanceDue": clean_text(row.get("balanceDue")) or UNKNOWN,
        "classPrice": clean_text(row.get("classPrice")) or UNKNOWN,
        "orderTotal": clean_text(row.get("orderTotal")) or UNKNOWN,
        "optionTotal": clean_text(row.get("optionTotal")) or UNKNOWN,
        "shipPrice": clean_text(row.get("shipPrice")) or UNKNOWN,
        "comments": clean_text(row.get("comments")) or UNKNOWN,
        "options": clean_text(row.get("options")) or UNKNOWN,
        "addons": clean_text(row.get("options")) or UNKNOWN,
        "questions": clean_text(row.get("questions")) or UNKNOWN,
        "payments": clean_text(row.get("payments")) or UNKNOWN,
        "queryString": clean_text(row.get("queryString")) or UNKNOWN,
        "sourceMetadata": clean_text(row.get("sourceMetadata")) or UNKNOWN,
        "importedAt": clean_text(row.get("importedAt")) or UNKNOWN,
        "receivedAt": clean_text(row.get("receivedAt")) or UNKNOWN,
        "source_file": source,
        "source_sheet_metadata": {
            "source_file": source,
            "row_number": row.get("_row_number", UNKNOWN),
            "receivedAt": clean_text(row.get("receivedAt")) or UNKNOWN,
            "importedAt": clean_text(row.get("importedAt")) or UNKNOWN,
        },
        "corporate_account_preview": {
            "provisional": True,
            "email_domain": domain,
            "employer_clue": employer,
            "billing_contact_clues": clean_text(" ".join([
                clean_text(row.get("comments")),
                clean_text(row.get("questions")),
                clean_text(row.get("queryString")),
            ])) or UNKNOWN,
            "possible_person_key": possible_person_key(first_name or UNKNOWN, last_name or UNKNOWN, email, phone),
            "possible_account_key": f"email_domain:{domain}" if domain != UNKNOWN else UNKNOWN,
            "same_courseSchedId_group_key": f"courseSchedId:{course_sched_id}" if course_sched_id else UNKNOWN,
            "same_courseId_startTime_group_key": (
                f"course_start:{clean_text(row.get('courseId'))}:{start.isoformat()}"
                if clean_text(row.get("courseId")) and start else UNKNOWN
            ),
            "duplicate_risk_cluster": UNKNOWN,
        },
        "missing_identifiers": missing_identifiers,
        "warnings": warnings,
        "source": source,
        "raw": row.get("_raw", {}),
        "raw_unmapped_fields": raw_unmapped_fields(row),
    }


def seed_records(seeds_payload: Any) -> list[dict[str, Any]]:
    if not isinstance(seeds_payload, dict):
        return []
    rows = seeds_payload.get("seeds")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def event_start_matches_seed(event: dict[str, Any], seed: dict[str, Any]) -> bool:
    event_start = parse_dt(event.get("startTime"))
    seed_start = parse_dt(seed.get("appointment_display_start") or seed.get("start_time"))
    return bool(event_start and seed_start and event_start == seed_start)


def location_matches(event: dict[str, Any], seed: dict[str, Any]) -> bool:
    event_loc = normalize_location(event.get("locationName"))
    seed_loc = normalize_location(seed.get("location") or seed.get("offer_location") or seed.get("public_offer_location"))
    if not event_loc or not seed_loc:
        return False
    if event_loc == seed_loc:
        return True
    return "4018 shipyard blvd" in event_loc and "4018 shipyard blvd" in seed_loc


def course_name_matches(event: dict[str, Any], seed: dict[str, Any]) -> bool:
    event_title = normalize_course_title(event.get("courseName"))
    seed_title = normalize_course_title(seed.get("course_title"))
    return bool(event_title and seed_title and (event_title in seed_title or seed_title in event_title))


def instructor_matches(event: dict[str, Any], seed: dict[str, Any]) -> bool:
    event_instructor = normalize_key(event.get("instructor"))
    seed_instructor = normalize_key(seed.get("instructor_display_name"))
    if not event_instructor or event_instructor == normalize_key(UNKNOWN):
        return True
    return bool(seed_instructor and (event_instructor == seed_instructor or seed_instructor.startswith(event_instructor)))


def match_event_to_seed(event: dict[str, Any], seeds: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, list[str]]:
    candidates = []
    reasons: list[str] = []
    for seed in seeds:
        checks = {
            "course_id": str(event.get("courseId")) == str(seed.get("course_id")),
            "start_time": event_start_matches_seed(event, seed),
            "location": location_matches(event, seed),
            "course_name_fallback": course_name_matches(event, seed),
            "instructor_optional": instructor_matches(event, seed),
        }
        if checks["course_id"] and checks["start_time"] and checks["location"] and checks["instructor_optional"]:
            candidates.append((seed, checks))
    if not candidates:
        if not any(str(event.get("courseId")) == str(seed.get("course_id")) for seed in seeds):
            reasons.append("no_seed_with_matching_course_id")
        if not any(event_start_matches_seed(event, seed) for seed in seeds):
            reasons.append("no_seed_with_matching_start_time")
        if not any(location_matches(event, seed) for seed in seeds):
            reasons.append("no_seed_with_matching_location")
        if event.get("instructor") not in (None, "", UNKNOWN) and not any(instructor_matches(event, seed) for seed in seeds):
            reasons.append("no_seed_with_matching_instructor")
        return None, reasons or ["no_matching_seed"]
    candidates.sort(key=lambda item: (not item[1]["course_name_fallback"], str(item[0].get("seed_id", ""))))
    return candidates[0][0], []


def import_events(input_path: Path, seeds_payload: Any) -> dict[str, Any]:
    rows, input_meta = read_csv_rows(input_path)
    blank_rows = [row for row in rows if is_blank_row(row)]
    data_rows = [row for row in rows if not is_blank_row(row)]
    normalized = [normalize_registration_row(row, str(input_path)) for row in data_rows]
    duplicate_reg_ids = [
        reg_id for reg_id, count in Counter(event["regId"] for event in normalized if event["regId"] != UNKNOWN).items()
        if count > 1
    ]
    missing_required_identifiers = {
        field: sum(1 for event in normalized if field in event.get("missing_identifiers", []))
        for field in REQUIRED_IDENTIFIER_FIELDS
    }
    unparseable_start_times = [
        event["event_id"] for event in normalized
        if "unparseable_startTime" in event.get("warnings", [])
    ]
    unique_events = []
    seen_reg_ids = set()
    for event in normalized:
        reg_id = event["regId"]
        if reg_id != UNKNOWN and reg_id in seen_reg_ids:
            continue
        if reg_id != UNKNOWN:
            seen_reg_ids.add(reg_id)
        unique_events.append(event)

    seeds = seed_records(seeds_payload)
    matched = []
    unmatched = []
    events_by_course_sched_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in unique_events:
        if event.get("courseSchedId") != UNKNOWN:
            events_by_course_sched_id[str(event["courseSchedId"])].append(event)
        if event.get("missing_identifiers"):
            unmatched.append({
                "event": event,
                "reason_codes": [f"missing_{field}" for field in event.get("missing_identifiers", [])],
            })
            continue
        if "unparseable_startTime" in event.get("warnings", []):
            unmatched.append({"event": event, "reason_codes": ["unparseable_startTime"]})
            continue
        seed, reasons = match_event_to_seed(event, seeds)
        if not seed:
            unmatched.append({"event": event, "reason_codes": reasons})
            continue
        matched.append({
            "registration_event_id": event["event_id"],
            "regId": event["regId"],
            "courseSchedId": event["courseSchedId"],
            "seed_id": seed.get("seed_id", UNKNOWN),
            "source_offer_id": seed.get("source_offer_id", UNKNOWN),
            "course_id": seed.get("course_id", UNKNOWN),
            "course_title": seed.get("course_title", UNKNOWN),
            "appointment_display_start": seed.get("appointment_display_start", UNKNOWN),
            "scheduler_consumption_start": seed.get("scheduler_consumption_start", UNKNOWN),
            "scheduler_consumption_end": seed.get("scheduler_consumption_end", UNKNOWN),
            "registration_status": "booked_pending_class_report",
            "status_history": [
                "registration_signal_seen",
                "booked_pending_class_report",
            ],
            "event": event,
        })

    newly_discovered_course_sched_ids = sorted(
        course_sched_id for course_sched_id in events_by_course_sched_id
        if course_sched_id and course_sched_id != UNKNOWN
    )
    duplicate_course_sched_ids_with_different_reg_ids = {
        course_sched_id: sorted({
            event["regId"] for event in events
            if event.get("regId") != UNKNOWN
        })
        for course_sched_id, events in sorted(events_by_course_sched_id.items())
        if len({
            event["regId"] for event in events
            if event.get("regId") != UNKNOWN
        }) > 1
    }
    email_counts = Counter(
        event["emailAddress"].lower() for event in unique_events
        if event.get("emailAddress") not in (None, "", UNKNOWN)
    )
    phone_counts = Counter(
        normalize_key(event["phoneNumber"]) for event in unique_events
        if event.get("phoneNumber") not in (None, "", UNKNOWN)
    )
    email_domain_counts = Counter(
        event.get("corporate_account_preview", {}).get("email_domain")
        for event in unique_events
        if event.get("corporate_account_preview", {}).get("email_domain") not in (None, "", UNKNOWN)
    )
    employer_clues = sorted({
        event.get("corporate_account_preview", {}).get("employer_clue")
        for event in unique_events
        if event.get("corporate_account_preview", {}).get("employer_clue") not in (None, "", UNKNOWN)
    })
    for event in normalized:
        duplicate_cluster = []
        email = event.get("emailAddress")
        phone = event.get("phoneNumber")
        course_sched_id = event.get("courseSchedId")
        if email not in (None, "", UNKNOWN) and email_counts[email.lower()] > 1:
            duplicate_cluster.append(f"email:{email.lower()}")
        if phone not in (None, "", UNKNOWN) and phone_counts[normalize_key(phone)] > 1:
            duplicate_cluster.append(f"phone:{normalize_key(phone)}")
        if course_sched_id not in (None, "", UNKNOWN) and len(events_by_course_sched_id.get(str(course_sched_id), [])) > 1:
            duplicate_cluster.append(f"courseSchedId:{course_sched_id}")
        if duplicate_cluster:
            event["corporate_account_preview"]["duplicate_risk_cluster"] = "|".join(duplicate_cluster)
    summary = {
        "input_path": str(input_path),
        "headers": input_meta["headers"],
        "header_map": input_meta["header_map"],
        "rows_read": len(rows),
        "blank_rows_skipped": len(blank_rows),
        "data_rows_processed": len(data_rows),
        "normalized_events": len(normalized),
        "unique_registration_events": len(unique_events),
        "missing_required_identifiers": missing_required_identifiers,
        "unparseable_startTimes": unparseable_start_times,
        "duplicate_regIds": duplicate_reg_ids,
        "new_registrations": len(unique_events),
        "matched_appointment_seeds": len(matched),
        "unmatched_registrations": len(unmatched),
        "newly_discovered_courseSchedIds": newly_discovered_course_sched_ids,
        "courseSchedId_registration_counts": {
            course_sched_id: len(events)
            for course_sched_id, events in sorted(events_by_course_sched_id.items())
        },
        "duplicate_courseSchedIds_with_different_regIds": duplicate_course_sched_ids_with_different_reg_ids,
        "corporate_account_preview": {
            "provisional": True,
            "email_domain_counts": dict(sorted(email_domain_counts.items())),
            "employer_clues": employer_clues,
            "duplicate_email_counts": {
                email: count for email, count in sorted(email_counts.items())
                if count > 1
            },
            "duplicate_phone_counts": {
                phone: count for phone, count in sorted(phone_counts.items())
                if count > 1
            },
        },
        "status_values": [
            "registration_signal_seen",
            "booked_pending_class_report",
            "converted_to_enrollware_class",
        ],
        "cadence_rule": "Fast path should be Zapier event-driven. Fallback reconciliation should run no more than every 30-60 minutes, or only during manual/admin build, unless explicitly approved.",
    }
    return {
        "summary": summary,
        "normalized_events": normalized,
        "unique_events": unique_events,
        "matched_seed_records": matched,
        "unmatched_registrations": unmatched,
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# Enrollware Registration Event Import Report",
        "",
        "Report-only import. This did not call Enrollware, call Google Sheets, create appointments, change appointment URLs, modify public pages, enable Worker routes, deploy, or commit.",
        "",
        "## Summary",
        "",
        f"- Input: `{summary['input_path']}`",
        f"- Total rows: {summary['rows_read']}",
        f"- Blank/skipped rows: {summary['blank_rows_skipped']}",
        f"- Data rows processed: {summary['data_rows_processed']}",
        f"- Normalized events: {summary['normalized_events']}",
        f"- Unique registration events: {summary['unique_registration_events']}",
        f"- Missing required identifiers: {json.dumps(summary['missing_required_identifiers'], ensure_ascii=False)}",
        f"- Unparseable startTimes: {len(summary['unparseable_startTimes'])}",
        f"- Duplicate regIds: {len(summary['duplicate_regIds'])}",
        f"- Matched appointment seeds: {summary['matched_appointment_seeds']}",
        f"- Unmatched registrations: {summary['unmatched_registrations']}",
        f"- Newly discovered courseSchedIds: {', '.join(summary['newly_discovered_courseSchedIds']) or 'None'}",
        f"- Duplicate courseSchedIds with different regIds: {len(summary['duplicate_courseSchedIds_with_different_regIds'])}",
        "",
        "## Course Schedule ID Registration Counts",
        "",
        "```json",
        json.dumps(summary["courseSchedId_registration_counts"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Matched Seeds",
        "",
    ]
    matched = result["matched_seed_records"]
    if matched:
        lines.extend(["| regId | courseSchedId | Seed | Course | Appointment Start | Status |", "| --- | --- | --- | --- | --- | --- |"])
        for item in matched:
            lines.append(
                f"| {item['regId']} | {item['courseSchedId']} | `{item['seed_id']}` | "
                f"{item['course_title']} | {item['appointment_display_start']} | {item['registration_status']} |"
            )
    else:
        lines.append("- None")
    lines.extend(["", "## Unmatched Registrations", ""])
    unmatched = result["unmatched_registrations"]
    if unmatched:
        lines.extend(["| regId | courseId | courseSchedId | startTime | Reasons |", "| --- | --- | --- | --- | --- |"])
        for item in unmatched:
            event = item["event"]
            lines.append(
                f"| {event.get('regId', UNKNOWN)} | {event.get('courseId', UNKNOWN)} | {event.get('courseSchedId', UNKNOWN)} | "
                f"{event.get('startTime', UNKNOWN)} | `{', '.join(item.get('reason_codes', []))}` |"
            )
    else:
        lines.append("- None")
    lines.extend([
        "",
        "## Idempotency",
        "",
        "- `regId` is treated as the unique registration event key.",
        "- Duplicate `regId` rows are normalized but not double-counted in unique event totals.",
        "- Multiple registration events with the same `courseSchedId` are grouped as one real Enrollware class/session.",
        "",
        "## Cadence Rule",
        "",
        f"- {summary['cadence_rule']}",
        "",
    ])
    return "\n".join(lines)


def run(input_path: Path, seeds_path: Path = DEFAULT_SEEDS_PATH) -> dict[str, Any]:
    seeds_payload, seeds_error = read_json(seeds_path)
    if seeds_error:
        seeds_payload = {}
    result = import_events(input_path, seeds_payload)
    result["summary"]["seeds_path"] = str(seeds_path)
    result["summary"]["seeds_read_error"] = seeds_error
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    NORMALIZED_EVENTS_PATH.write_text(json.dumps({
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "registration_events": result["normalized_events"],
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    MATCHED_SEEDS_PATH.write_text(json.dumps({
        "generated_at": datetime.now().astimezone().isoformat(),
        "read_only": True,
        "matched_seed_records": result["matched_seed_records"],
        "unmatched_registrations": result["unmatched_registrations"],
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(json.dumps(result["summary"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_report(result), encoding="utf-8")
    return {
        "summary": result["summary"],
        "output_paths": [NORMALIZED_EVENTS_PATH, MATCHED_SEEDS_PATH, SUMMARY_PATH, REPORT_PATH],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Report-only import for Enrollware Zapier/Sheet registration events.")
    parser.add_argument("--input", required=True, help="Path to Google Sheet CSV export or Zapier registration CSV.")
    parser.add_argument("--seeds", default=str(DEFAULT_SEEDS_PATH), help="Path to schedule_seeds_preview.json.")
    parser.add_argument("--report-only", action="store_true", help="Document intent: this command writes audit outputs only.")
    args = parser.parse_args()
    result = run(Path(args.input), Path(args.seeds))
    summary = result["summary"]
    print("Enrollware registration event import complete (REPORT ONLY).")
    print("No Enrollware calls, Google Sheet calls, appointments, public pages, appointment URLs, Worker routes, deploys, or commits were performed.")
    print("")
    print(f"Rows read: {summary['rows_read']}")
    print(f"New registrations: {summary['new_registrations']}")
    print(f"Matched appointment seeds: {summary['matched_appointment_seeds']}")
    print(f"Unmatched registrations: {summary['unmatched_registrations']}")
    print(f"Newly discovered courseSchedIds: {', '.join(summary['newly_discovered_courseSchedIds']) or 'None'}")
    print(f"Duplicate regIds: {', '.join(summary['duplicate_regIds']) or 'None'}")
    print("")
    print("Output files:")
    for path in result["output_paths"]:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
