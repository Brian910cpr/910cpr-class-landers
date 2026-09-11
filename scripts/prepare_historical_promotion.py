#!/usr/bin/env python3
"""Build deterministic, restartable SQL batches for issue #141.

The generated files contain source-derived PII and must remain outside git.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

import openpyxl


EASTERN = ZoneInfo("America/New_York")


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def iso(value):
    if value in (None, ""):
        return ""
    if isinstance(value, datetime):
        return value.replace(tzinfo=EASTERN).isoformat()
    return datetime.fromisoformat(str(value)).replace(tzinfo=EASTERN).isoformat()


def source_datetime(value):
    if isinstance(value, datetime):
        return iso(value)
    text = clean(value)
    if not text:
        return ""
    for pattern in ("%m/%d/%y %H:%M", "%m/%d/%Y %H:%M", "%m/%d/%y", "%m/%d/%Y"):
        try:
            return iso(datetime.strptime(text, pattern))
        except ValueError:
            pass
    raise ValueError(f"unsupported source date: {text!r}")


def number(value):
    text = clean(value).replace("$", "").replace(",", "")
    return text if text else ""


def numeric_or_none(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    text = clean(value)
    return float(text) if re.fullmatch(r"-?\d+(?:\.\d+)?", text) else None


def external_id(url):
    values = parse_qs(urlparse(clean(url)).query).get("id", [])
    return values[0] if len(values) == 1 and values[0].isdigit() else ""


def sql_json(value):
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    tag = "$hist$"
    if tag in payload:
        raise ValueError("unexpected SQL delimiter in payload")
    return f"{tag}{payload}{tag}::jsonb"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--classes", type=Path, required=True)
    parser.add_argument("--registrations", type=Path, required=True)
    parser.add_argument("--exceptions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=250)
    parser.add_argument("--first-batch-size", type=int, default=10)
    parser.add_argument("--through", type=datetime.fromisoformat, default=datetime.now())
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    source_sha = hashlib.sha256(args.registrations.read_bytes()).hexdigest()
    exceptions_doc = json.loads(args.exceptions.read_text(encoding="utf-8"))
    exceptions = {
        *exceptions_doc["current_only_vs_historical"]["class_ids"],
        *exceptions_doc["student_only_vs_historical"]["class_ids"],
    }

    workbook = openpyxl.load_workbook(args.classes, read_only=True, data_only=True)
    sheet = workbook.active
    headers = [clean(cell.value) for cell in next(sheet.iter_rows(max_row=1))]
    class_by_source = {}
    for row_number, cells in enumerate(sheet.iter_rows(min_row=2, values_only=True), 2):
        raw = dict(zip(headers, cells))
        source_id = clean(raw["ID"])
        ext_id = external_id(raw["Registration Link"])
        start_at = raw["Start Date / Time"]
        source_end_at = raw["End Date / Time"]
        hours = numeric_or_none(raw["Hours"])
        effective_end_at = source_end_at
        inferred_end = False
        if start_at and (not effective_end_at or effective_end_at <= start_at) and hours and hours > 0:
            effective_end_at = start_at + timedelta(hours=hours)
            inferred_end = True
        if (not source_id or source_id in exceptions or not ext_id or not start_at or start_at > args.through
                or not effective_end_at or effective_end_at <= start_at
                or not clean(raw["Course"]) or not clean(raw["Location"])):
            continue
        class_by_source[source_id] = {
            "import_key": f"class-report-61:{source_id}",
            "source_file": args.classes.name,
            "source_row_number": row_number,
            "source_id": source_id,
            "external_class_id": ext_id,
            "course_label": clean(raw["Course"]),
            "start_at": iso(start_at),
            "source_end_at": iso(source_end_at) or None,
            "effective_end_at": iso(effective_end_at),
            "end_date_inferred": inferred_end,
            "location_label": clean(raw["Location"]),
            "client_label": clean(raw["Client"]),
            "instructor_label": clean(raw["Instructor"]),
            "assistants_label": clean(raw["Assistants"]),
            "student_count": max(numeric_or_none(raw["Students"]) or 0, 1),
            "seats": numeric_or_none(raw["Seats"]),
            "source_hours": hours,
            "registration_url": clean(raw["Registration Link"]),
            "raw_row": {key: clean(value) for key, value in raw.items()},
        }

    registrations = []
    quarantined = []
    referenced_ids = set()
    if args.registrations.suffix.lower() == ".xlsx":
        registration_book = openpyxl.load_workbook(args.registrations, read_only=True, data_only=True)
        registration_sheet = registration_book.active
        registration_headers = [clean(cell.value) for cell in next(registration_sheet.iter_rows(max_row=1))]
        registration_source = (
            (row_number, dict(zip(registration_headers, cells)))
            for row_number, cells in enumerate(registration_sheet.iter_rows(min_row=2, values_only=True), 2)
        )
    else:
        handle = args.registrations.open("r", encoding="utf-8-sig", newline="")
        registration_source = enumerate(csv.DictReader(handle), 2)
    try:
        for row_number, raw in registration_source:
            source_id = clean(raw["Class ID"])
            digits = re.sub(r"[^0-9]", "", clean(raw["Phone"]))
            email = clean(raw["Email"]).lower()
            first = clean(raw["First Name"])
            last = clean(raw["Last Name"])
            reason = None
            if source_id in exceptions or source_id not in class_by_source:
                reason = "unresolved_class_id"
            elif not first or not last:
                reason = "missing_customer_name"
            elif not email and len(digits) < 7:
                reason = "unresolved_customer_identity"
            if reason:
                quarantined.append({"source_row_number": row_number, "class_id": source_id, "reason": reason})
                continue
            referenced_ids.add(source_id)
            stable = f"{source_sha[:16]}:{row_number}"
            registrations.append({
                "import_key": f"students-raw-live:{stable}",
                "source_file": args.registrations.name,
                "source_row_number": row_number,
                "external_class_id": class_by_source[source_id]["external_class_id"],
                "registration_date": source_datetime(raw["Reg. Date"]),
                "first_name": first,
                "last_name": last,
                "email": clean(raw["Email"]),
                "phone": clean(raw["Phone"]),
                "course": clean(raw["Course"]),
                "course_date": source_datetime(raw["Course Date"]),
                "course_location": clean(raw["Course Location"]),
                "instructor": clean(raw["Instructor"]),
                "status": clean(raw["Status"]),
                "score": clean(raw["Score"]),
                "options": clean(raw["Options"]),
                "class_price": number(raw["Class Price"]),
                "options_price": number(raw["Options Price"]),
                "shipping": number(raw["Shipping"]),
                "order_total": number(raw["Order Total"]),
                "balance_due": number(raw["Balance Due"]),
                "delivery": clean(raw["Delivery"]),
                "codes": clean(raw["Codes"]),
                "comments": clean(raw["Comments"]),
                "checked_in": clean(raw["Checked In"]),
                "ecard_code": clean(raw["eCard Code"]),
            })
    finally:
        if args.registrations.suffix.lower() != ".xlsx":
            handle.close()

    classes = [class_by_source[key] for key in sorted(referenced_ids, key=int)]
    first_registrations = registrations[:args.first_batch_size]
    first_external_ids = {row["external_class_id"] for row in first_registrations}
    first_classes = [row for row in classes if row["external_class_id"] in first_external_ids]
    remaining_classes = [row for row in classes if row["external_class_id"] not in first_external_ids]
    remaining_registrations = registrations[args.first_batch_size:]
    (args.output / "quarantine.json").write_text(json.dumps(quarantined, indent=2), encoding="utf-8")
    manifest = {
        "source_sha256": source_sha,
        "classes": len(classes),
        "registrations": len(registrations),
        "quarantined": len(quarantined),
        "first_batch": {"classes": len(first_classes), "registrations": len(first_registrations)},
        "class_batches": [],
        "registration_batches": [],
    }
    proof = "insert into _promotion_receipts select 'proof',jsonb_build_object('class_sessions',count(distinct s.id),'participants',count(distinct c.id),'registrations',count(distinct r.id)) from public.registrations r join public.customers c on c.id=r.customer_id join public.class_sessions s on s.id=r.class_session_id where r.historical_import_key like 'students-raw-live:%';"
    first_calls = (
        "create temporary table _promotion_receipts(kind text,receipt jsonb) on commit drop;\n"
        f"insert into _promotion_receipts select 'class',public.import_historical_class_batch({sql_json(first_classes)});\n"
        f"insert into _promotion_receipts select 'registration',public.promote_historical_registration_batch({sql_json(first_registrations)},'{source_sha}',false);\n"
        "insert into _promotion_receipts select 'errors',coalesce(jsonb_object_agg(last_error,n), '{}'::jsonb) from (select last_error,count(*) n from public.historical_registration_import_rows where import_key like 'students-raw-live:%' and last_error is not null group by last_error) e;\n"
        f"{proof}\n"
        "select jsonb_object_agg(kind,receipt) as production_receipt from _promotion_receipts;\n"
    )
    (args.output / "first_batch_dry_run.sql").write_text("begin;\n" + first_calls + "rollback;\n", encoding="utf-8")
    (args.output / "first_batch_apply.sql").write_text("begin;\n" + first_calls + "commit;\n", encoding="utf-8")
    (args.output / "first_batch_replay.sql").write_text("begin;\n" + first_calls + "commit;\n", encoding="utf-8")

    for kind, rows, function in (
        ("class", remaining_classes, "import_historical_class_batch"),
        ("registration", remaining_registrations, "promote_historical_registration_batch"),
    ):
        for index in range(0, len(rows), args.batch_size):
            batch = rows[index:index + args.batch_size]
            name = f"{kind}_{index // args.batch_size + 1:03d}.sql"
            if kind == "class":
                payload = sql_json(batch)
                statement = (
                    f"with payload as materialized (select {payload} value), "
                    "before_count as materialized (select count(*) n from payload p cross join lateral jsonb_array_elements(p.value) r join public.class_sessions s on s.historical_import_key=r->>'import_key'), "
                    f"run as materialized (select public.{function}(p.value) detail from payload p cross join before_count) "
                    "select jsonb_build_object('scanned',jsonb_array_length(p.value),'matched_existing',b.n,'inserted',jsonb_array_length(p.value)-b.n,'repaired',0,'duplicates_suppressed',0,'quarantined',0,'failed',0,'detail',run.detail) as batch_receipt from payload p cross join before_count b cross join run;\n"
                )
            else:
                statement = f"select public.{function}({sql_json(batch)},'{source_sha}',false);\n"
            (args.output / name).write_text(statement, encoding="utf-8")
            manifest[f"{kind}_batches"].append({"file": name, "rows": len(batch)})
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
