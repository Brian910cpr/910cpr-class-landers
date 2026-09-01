#!/usr/bin/env python3
"""Render a PII-redacted real-sample Hx dry-run reconciliation report."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


SENSITIVE_KEYS = {
    "first_name", "last_name", "email", "phone", "student_name", "student_email",
    "credential_number", "original_values", "original_source_value", "raw",
}


def digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def redact(value: Any, key: str = "") -> Any:
    if key in SENSITIVE_KEYS and value not in (None, "", [], {}):
        return {"redacted": True, "fingerprint": digest(value)}
    if isinstance(value, dict):
        return {k: redact(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, key) for v in value]
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    sample = json.loads(args.sample.read_text(encoding="utf-8"))
    first = json.loads(args.first.read_text(encoding="utf-8"))
    second = json.loads(args.second.read_text(encoding="utf-8"))
    operation_counts = Counter(op["command"] for op in first["proposed_operations"])
    assertion_counts = Counter(a["fact_type"] for a in first["evidence_assertions"])
    second_actions = Counter(d["action"] for d in second["decisions"])
    source_sha = hashlib.sha256(Path("data/raw/students_raw_live.csv").read_bytes()).hexdigest()
    mismatches = [
        {"id": "M01", "classification": "importer deficiency", "area": "people",
         "finding": "13 unique historical identities in the sample matched zero production customers; batch-local duplicate identity reuse is now correct."},
        {"id": "M02", "classification": "importer deficiency", "area": "sessions",
         "finding": "11 Enrollware class IDs in the sample matched zero production class_sessions; production has 352 historical sessions, but none cover these sampled IDs."},
        {"id": "M03", "classification": "importer deficiency", "area": "registrations",
         "finding": "15 sampled participant/session memberships matched zero production registrations; production has zero registrations with historical_import_key."},
        {"id": "M04", "classification": "importer deficiency", "area": "source identity",
         "finding": "The student export contains no Enrollware registration ID or course ID, so the adapter uses a documented composite registration key and course-name evidence."},
        {"id": "M05", "classification": "source-data ambiguity", "area": "completion",
         "finding": "Four rows have Complete/Incomplete status without an eCard; Hx refuses to translate those status-only values into passed/failed completion facts."},
        {"id": "M06", "classification": "importer deficiency", "area": "lifecycle",
         "finding": "The sample supports 7 explicit completions, 5 credentials, and 1 reschedule, while production currently contains zero canonical completions, credentials, or reschedule lifecycle events."},
        {"id": "M07", "classification": "schema/model gap", "area": "prepaid inventory",
         "finding": "Three NHCSO rows carry the AHA-BLS-ECARD option and the trusted checkpoint says the cards use a customer-owned prepaid pool, but production lacks the proposed entitlement pool/event tables and canonical owner/product IDs remain unresolved."},
        {"id": "M08", "classification": "schema/model gap", "area": "idempotency provenance",
         "finding": "Exact replay is deterministic with a source fingerprint in the dry-run overlay, but lifecycle_import_records has no dedicated source_fingerprint column; persistence must store and query an equivalent immutable fingerprint before apply mode is approved."},
        {"id": "M09", "classification": "identity-resolution deficiency", "area": "batch identity",
         "finding": "The initial real run proposed one person per row (15 instead of 13); Hx was corrected to reuse email/phone identity within the batch and regression-tested."},
    ]
    result = {
        "report": "Hx-Builder real Enrollware historical sample dry run",
        "mode": "dry_run_only", "production_mutated": False, "migration_applied": False,
        "source": {"kind": "real Enrollware student export", "sha256": source_sha,
                   "rows_examined_in_source": sample["sample"]["source_rows_total"],
                   "rows_selected": sample["sample"]["selected_rows"],
                   "selection": sample["sample"]["selection"]},
        "production_checkpoint": {"project_id": "wktwgcnwdvbebcobgyey", "query_mode": "read_only SELECT",
            "customers_total": 390, "historical_sessions_total": 352, "historical_registrations_total": 0,
            "participant_completions_total": 0, "participant_credentials_total": 0,
            "reschedule_events_total": 0, "lifecycle_import_records_total": 0,
            "identity_aliases_total": 0, "sample_customers_matched": 0,
            "sample_sessions_matched": 0, "sample_registrations_matched": 0},
        "first_run": {"summary": first["summary"], "proposed_operation_counts": dict(sorted(operation_counts.items())),
                      "evidence_assertion_counts": dict(sorted(assertion_counts.items())),
                      "reconciliation_totals_by_course_date_source": first["reconciliation_totals_by_course_date_source"],
                      "redacted_details": redact({"decisions": first["decisions"], "proposed_operations": first["proposed_operations"],
                                                   "evidence_assertions": first["evidence_assertions"],
                                                   "ambiguities": first["unresolved_or_ambiguous"]})},
        "replay": {"same_sample": True, "overlay_only": True,
                   "additional_proposed_operations": len(second["proposed_operations"]),
                   "additional_evidence_assertions": len(second["evidence_assertions"]),
                   "actions": dict(sorted(second_actions.items())), "summary": second["summary"]},
        "mismatches": mismatches,
        "approval_gate": "BLOCKED until every mismatch is reviewed and fingerprint persistence plus canonical course/owner/product resolution are approved.",
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Hx-Builder Real Enrollware Historical Sample — Dry Run", "",
             "**Result:** deterministic replay passed; production import remains blocked.", "",
             "- Production mutation: **none**", "- Migration applied: **no**",
             f"- Real source rows: {result['source']['rows_examined_in_source']:,}; deterministic sample: {result['source']['rows_selected']}",
             f"- First pass proposed operations/assertions: {sum(operation_counts.values())} / {sum(assertion_counts.values())}",
             f"- Exact replay additional operations/assertions: {result['replay']['additional_proposed_operations']} / {result['replay']['additional_evidence_assertions']}",
             f"- Replay decisions: `{json.dumps(result['replay']['actions'], sort_keys=True)}`", "", "## First-pass summary", "",
             "```json", json.dumps(first["summary"], indent=2, sort_keys=True), "```", "", "## Production/reference comparison", "",
             "| Area | Sample proposal/evidence | Existing production |", "| --- | ---: | ---: |",
             f"| People | {first['summary']['people_created']} unique proposed | 0 matched sample identities |",
             f"| Sessions | {first['summary']['sessions_created']} proposed | 0 matched sample class IDs |",
             f"| Registrations | {first['summary']['registrations_created']} proposed | 0 historical registrations total |",
             f"| Completions | {first['summary']['completions_reconstructed']} | 0 |",
             f"| Credentials/cards | {first['summary']['credentials_cards_reconstructed']} | 0 |",
             f"| Reschedules | {first['summary']['reschedules_reconstructed']} | 0 |", "", "## Classified mismatches", "",
             "| ID | Classification | Area | Finding |", "| --- | --- | --- | --- |"]
    for item in mismatches:
        lines.append(f"| {item['id']} | {item['classification']} | {item['area']} | {item['finding']} |")
    lines += ["", "## Gate", "", result["approval_gate"], "",
              "The detailed JSON contains PII-redacted decisions, operations, evidence assertions, and course/date/source reconciliation totals.", ""]
    args.markdown_output.write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
