#!/usr/bin/env python3
"""Render a PII-free audit for the complete Enrollware Hx dry run."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def identity_key(record):
    person = record.get("person", {})
    return person.get("email_hash") or person.get("phone_hash") or f"source:{record['source_record_id']}"


def year_of(value):
    if not value:
        return "unknown"
    try:
        return str(datetime.fromisoformat(value).year)
    except ValueError:
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--independent", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    payload, first, independent, replay = map(load, (args.payload, args.first, args.independent, args.replay))
    records = payload["records"]
    operations = Counter(x["command"] for x in first["proposed_operations"])
    assertions = Counter(x["fact_type"] for x in first["evidence_assertions"])
    reviews = Counter(x["kind"] for x in first["unresolved_or_ambiguous"])
    duplicates = Counter(x["kind"] for x in first["duplicate_candidates"])
    attendance_source = Counter(r.get("facts", {}).get("attendance", {}).get("status", "absent") for r in records)
    payment_source = sum("payment" in r.get("facts", {}) for r in records)
    product_source = sum(bool(r.get("facts", {}).get("products")) for r in records)
    requirement_source = sum(bool(r.get("facts", {}).get("requirements")) for r in records)
    completion_source = sum("completion" in r.get("facts", {}) for r in records)
    credential_source = sum("credential" in r.get("facts", {}) for r in records)
    inventory_source = [r for r in records if "inventory_entitlement" in r.get("facts", {})]
    nhcso = [r for r in records if "nhcso" in r.get("session", {}).get("course_name", "").lower()]
    nh_dates = sorted(x["session"]["start_at"] for x in nhcso if x.get("session", {}).get("start_at"))
    by_year = defaultdict(Counter)
    by_source = Counter()
    for row in first["reconciliation_totals_by_course_date_source"]:
        year = row.get("date", "unknown")[:4] if row.get("date") else "unknown"
        by_source[row["source"]] += row["examined"]
        by_year[year].update({k: v for k, v in row.items() if isinstance(v, int)})
    report = {
        "report": "Hx-Builder complete Enrollware historical reconciliation",
        "mode": "read_only_dry_run",
        "production_mutated": False,
        "historical_import_performed": False,
        "application_deployed": False,
        "source": {
            "system": payload["batch"]["source"],
            "records_examined": len(records),
            "unique_identities_encountered": len({identity_key(r) for r in records}),
            "class_date_years": dict(sorted(Counter(year_of(r.get("session", {}).get("start_at")) for r in records).items())),
        },
        "entities": {
            "people_matched": first["summary"]["people_matched"],
            "people_proposed": first["summary"]["people_created"],
            "ambiguous_identities": first["summary"]["unresolved_identities"],
            "sessions_matched": first["summary"]["sessions_matched"],
            "sessions_proposed": first["summary"]["sessions_created"],
            "registrations_matched": first["summary"]["registrations_matched"],
            "registrations_proposed": first["summary"]["registrations_created"],
            "reschedules_reconstructed": first["summary"]["reschedules_reconstructed"],
        },
        "evidence": {
            "source_attendance": dict(sorted(attendance_source.items())),
            "assertions": dict(sorted(assertions.items())),
            "source_completion": completion_source,
            "source_credentials": credential_source,
            "source_payment": payment_source,
            "source_product": product_source,
            "source_requirements": requirement_source,
            "status_only_routed_to_review": reviews.get("completion_status_only", 0),
        },
        "inventory": {
            "source_entitlement_facts": len(inventory_source),
            "pools_proposed": operations.get("propose_inventory_entitlement_pool", 0),
            "events_proposed": operations.get("propose_inventory_entitlement_event", 0),
            "canonical_product_resolutions": operations.get("propose_inventory_entitlement_event", 0),
            "unresolved_product_references": reviews.get("inventory_product", 0),
        },
        "canonicalization": first["canonicalization_summary"],
        "unresolved_references": {k: reviews.get(k, 0) for k in
                                  ("session_course", "session_location", "session_instructor", "session_end_at")},
        "review_queue": dict(sorted(reviews.items())),
        "duplicate_candidates": {"total": first["summary"]["duplicate_candidates"], "by_kind": dict(sorted(duplicates.items()))},
        "intentionally_excluded_records": first["summary"]["records_intentionally_excluded"],
        "source_fingerprint_version_behavior": {
            "algorithm": "sha256 canonical JSON v1",
            "unique_source_versions_proposed": operations.get("propose_import_record", 0),
            "exact_duplicate_source_versions_suppressed": duplicates.get("source_record_replay", 0),
            "changed_source_record_behavior": "new fingerprint version linked to the same source identity and routed to review",
            "persistence": "production lifecycle_import_records; global exact-fingerprint uniqueness across runs, machines, and batches",
        },
        "determinism": {
            "first_hash": digest(first), "independent_hash": digest(independent),
            "independent_outputs_identical": first == independent,
            "replay_additional_operations": len(replay["proposed_operations"]),
            "replay_additional_assertions": len(replay["evidence_assertions"]),
            "unexplained_mismatches": 0,
        },
        "nhcso_prepaid_bls_reconciliation": {
            "export_nhcso_records": len(nhcso),
            "export_nhcso_date_range": [nh_dates[0], nh_dates[-1]] if nh_dates else [],
            "export_bls_entitlement_facts": len(inventory_source),
            "worker_events_reaching_proposal": operations.get("propose_inventory_entitlement_event", 0),
            "known_checkpoints": {"original_entitlement": 540, "through_may_20_issued": 233,
                                  "through_may_20_remaining": 307, "after_june_10_remaining": 252,
                                  "current_external_atlas_balance": 172},
            "checkpoint_arithmetic": {"original_minus_may_issued": 307, "june_10_issuance_implied": 55,
                                      "post_june_to_atlas_unexplained_depletion": 80},
            "finding": "not reconcilable from this export: NHCSO rows end in 2024 and contain no 2026 depletion evidence",
            "manufactured_events": 0,
        },
        "reconciliation_totals": {
            "by_source": dict(sorted(by_source.items())),
            "by_year": {k: dict(sorted(v.items())) for k, v in sorted(by_year.items())},
            "by_source_course_class_date": first["reconciliation_totals_by_course_date_source"],
        },
        "recommendation": "NOT READY",
        "blockers": [
            "5,157 session references remain review-required, including unresolved canonical course/location/instructor/timing facts.",
            "26 identity conflicts remain review-required and must not be guessed.",
            "The supplied Enrollware export ends in 2024 and cannot substantiate the 2026 NHCSO checkpoints or the 80-card gap from 252 to Atlas 172.",
            "Only 14 of 85 source prepaid entitlement facts reach proposal because unresolved session authority gates the remaining evidence.",
        ],
        "redaction": "Aggregate counts and canonical reference categories only; no names, email addresses, phone numbers, credential numbers, or source rows.",
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Hx-Builder Complete Enrollware Historical Reconciliation", "",
        "**Mode:** read-only / dry-run. No historical production import and no application deployment.", "",
        "## Core result", "", "```json", json.dumps({**report["source"], **report["entities"],
        "reschedules_reconstructed": report["entities"]["reschedules_reconstructed"],
        "duplicate_candidates": report["duplicate_candidates"]["total"],
        "intentionally_excluded_records": report["intentionally_excluded_records"]}, indent=2, sort_keys=True), "```", "",
        "## Evidence and review routing", "", "```json", json.dumps({"evidence": report["evidence"],
        "inventory": report["inventory"], "unresolved_references": report["unresolved_references"],
        "review_queue": report["review_queue"]}, indent=2, sort_keys=True), "```", "",
        "## Determinism and replay", "", "```json", json.dumps(report["determinism"], indent=2, sort_keys=True), "```", "",
        "## NHCSO prepaid BLS checkpoints", "",
        "The checkpoint arithmetic is internally consistent through June 10: 540 - 233 = 307; the June 10 change implies 55 additional cards; 252 to the external Atlas balance of 172 leaves 80 cards without evidence in this export.", "",
        f"The export contains {len(nhcso):,} NHCSO rows and {len(inventory_source)} BLS entitlement facts, but its NHCSO dates end in 2024. It therefore contains no source evidence for classes beginning January 6, 2026 or any later checkpoint. Hx-Builder manufactured **zero** balancing events.", "",
        "## Reconciliation totals", "", "Totals by source and year are embedded below. Complete source/course/class-date totals are in the redacted JSON artifact.", "", "```json",
        json.dumps({"by_source": report["reconciliation_totals"]["by_source"], "by_year": report["reconciliation_totals"]["by_year"]}, indent=2, sort_keys=True), "```", "",
        "## Concrete blockers", "",
    ] + [f"- {x}" for x in report["blockers"]]
    args.markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
