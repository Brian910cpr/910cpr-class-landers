#!/usr/bin/env python3
"""Build a bounded canonical Hx sample from a real Enrollware student export.

The command is read-only with respect to its sources and production. Output is
intended for a local/private work directory because it contains source PII.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def identity_key(row: dict[str, str]) -> str:
    email = clean(row.get("Email")).lower()
    phone = re.sub(r"\D", "", clean(row.get("Phone")))
    return email or phone or f"row:{row['_row_number']}"


def record_key(row: dict[str, str]) -> str:
    parts = [identity_key(row), clean(row.get("Class ID")), clean(row.get("Course Date")), clean(row.get("Reg. Date"))]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:24]


def parse_date(value: str) -> str | None:
    raw = clean(value)
    for fmt in ("%m/%d/%y %H:%M", "%m/%d/%Y %H:%M", "%m/%d/%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).astimezone().isoformat()
        except ValueError:
            pass
    return None


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row_number, row in enumerate(rows, 2):
        row["_row_number"] = str(row_number)
    return rows


def select_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    selected: dict[int, dict[str, str]] = {}
    def add(row: dict[str, str]) -> None:
        selected[int(row["_row_number"])] = row

    credential_rows = [r for r in rows if clean(r.get("eCard Code"))]
    for row in credential_rows[:5]:
        add(row)

    rescheduled = [r for r in rows if re.search(r"rescheduled from\s+\d", clean(r.get("Comments")), re.I)]
    for row in rescheduled[:3]:
        add(row)

    repeated = {}
    for row in rows:
        repeated.setdefault(identity_key(row), []).append(row)
    for row in list(selected.values()):
        for related in repeated.get(identity_key(row), [])[:3]:
            add(related)

    prepaid = [
        r for r in rows
        if "nhcso" in clean(r.get("Course")).lower() and "ecard" in clean(r.get("Options")).lower()
    ]
    for row in prepaid[:3]:
        add(row)

    for status in ("Pending", "Incomplete", "Cancelled", "No Show"):
        match = next((r for r in rows if clean(r.get("Status")) == status), None)
        if match:
            add(match)
    return [selected[key] for key in sorted(selected)]


def canonical_record(row: dict[str, str]) -> dict[str, Any]:
    status = clean(row.get("Status"))
    checked_in = clean(row.get("Checked In")).upper()
    ecard = clean(row.get("eCard Code"))
    facts: dict[str, Any] = {
        "attendance": {"status": "attended" if checked_in == "Y" else "not_attended", "source_value": checked_in},
        "payment": {
            "order_total": clean(row.get("Order Total")),
            "balance_due": clean(row.get("Balance Due")),
            "state": "paid" if clean(row.get("Balance Due")) in ("0", "0.00") else "unknown",
        },
    }
    if clean(row.get("Options")):
        facts["products"] = [{"source_option": clean(row.get("Options")), "fulfillment_state": "unknown"}]
    if ecard:
        facts["completion"] = {"status": "passed", "evidence": "Enrollware eCard Code present"}
        facts["credential"] = {"credential_number": ecard, "status": "issued"}
    elif status in ("Complete", "Incomplete"):
        facts["completion"] = {"status": status.lower(), "evidence": "Enrollware Status only"}
    if "nhcso" in clean(row.get("Course")).lower() and "ecard" in clean(row.get("Options")).lower():
        facts["inventory_entitlement"] = {
            "pool_key": "organization-prepaid-ecards:nhcso",
            "owner_kind": "organization",
            "owner_organization_id": "unresolved:nhcso",
            "product_id": "unresolved:aha-bls-ecard",
            "unit_kind": "ecard",
            "quantity_delta": -1,
            "event_type": "consumed",
            "evidence": "known prepaid checkpoint plus Enrollware AHA-BLS-ECARD option",
        }
    comment = clean(row.get("Comments"))
    reschedule = None
    known_origins = {"33145": "30103", "16738": "16285"}
    if clean(row.get("Class ID")) in known_origins and re.search(r"rescheduled? .*from", comment, re.I):
        reschedule = {
            "from_session_source_id": known_origins[clean(row.get("Class ID"))],
            "reason": "Enrollware comment explicitly identifies a reschedule origin date; origin class uniquely reconciled to schedule export",
            "occurred_at": parse_date(row.get("Reg. Date", "")),
        }
    first, last = clean(row.get("First Name")), clean(row.get("Last Name"))
    return {
        "source": "enrollware_student_report",
        "source_record_id": f"student-report:{record_key(row)}",
        "source_created_at": parse_date(row.get("Reg. Date", "")),
        "observed_at": None,
        "confidence_state": "confirmed" if ecard else "possible",
        "person": {"first_name": first, "last_name": last, "email": clean(row.get("Email")), "phone": clean(row.get("Phone"))},
        "session": {
            "source_id": clean(row.get("Class ID")), "course_name": clean(row.get("Course")),
            "start_at": parse_date(row.get("Course Date", "")), "location_name": clean(row.get("Course Location")),
        },
        "registration": {"source_id": f"composite:{record_key(row)}", "status": status},
        "facts": facts,
        "reschedule": reschedule,
        "raw": {**row, "_source_record_strategy": "sha256(identity|class_id|course_date|registration_date)"},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = read_rows(args.input)
    sample = select_rows(rows)
    payload = {
        "batch": {
            "batch_key": f"enrollware-student-sample:{hashlib.sha256(args.input.read_bytes()).hexdigest()[:16]}",
            "source": "enrollware_student_report", "source_file_id": args.input.name,
            "parser_version": "hx-builder-enrollware-student-v1", "created_at": None,
        },
        "records": [canonical_record(row) for row in sample],
        "sample": {"source_rows_total": len(rows), "selected_rows": len(sample), "selection": "deterministic lifecycle coverage"},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_rows_total": len(rows), "selected_rows": len(sample)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
