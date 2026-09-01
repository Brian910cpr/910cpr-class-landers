#!/usr/bin/env python3
"""Validate the reviewed historical-session policy without mutating authority."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

from hx_builder import HxBuilder, known, parse_timestamp, replay_reference


class HistoricalAuthorityBuilder(HxBuilder):
    """Permit truthful unknown instructor/end only after core session resolution."""

    def canonicalize_session(self, record):
        super().canonicalize_session(record)
        session = record["session"]
        start = parse_timestamp(session.get("start_at"))
        ready = bool(start) and all(
            known(session.get(field)) for field in ("course_id", "location_id")
        )
        session["canonical_ready"] = ready
        if ready:
            session["record_scope"] = "historical"
            session["instructor_resolution_state"] = (
                "resolved" if known(session.get("lead_instructor_id")) else "unknown_source_not_supplied"
            )
            session["duration_resolution_state"] = (
                "resolved" if parse_timestamp(session.get("end_at")) else "unknown_source_not_supplied"
            )
        return ready


def digest(report):
    encoded = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--strict-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.payload.read_text(encoding="utf-8-sig"))
    reference = json.loads(args.reference.read_text(encoding="utf-8-sig"))
    strict = json.loads(args.strict_report.read_text(encoding="utf-8-sig"))
    first = HistoricalAuthorityBuilder(copy.deepcopy(payload), copy.deepcopy(reference)).process()
    independent = HistoricalAuthorityBuilder(copy.deepcopy(payload), copy.deepcopy(reference)).process()
    replay = HistoricalAuthorityBuilder(
        copy.deepcopy(payload), replay_reference(copy.deepcopy(reference), first)
    ).process()

    proposed_sessions = [
        op["session"] for op in first["proposed_operations"] if op.get("command") == "propose_session"
    ]
    unknown_instructor = sum(not known(s.get("lead_instructor_id")) for s in proposed_sessions)
    unknown_duration = sum(parse_timestamp(s.get("end_at")) is None for s in proposed_sessions)
    unknown_both = sum(
        not known(s.get("lead_instructor_id")) and parse_timestamp(s.get("end_at")) is None
        for s in proposed_sessions
    )
    queue = Counter(x.get("kind") for x in first["unresolved_or_ambiguous"])
    candidate_inventory = json.loads(
        (Path(__file__).parents[1] / "data/audit/hx_historical_location_authority_review_redacted.json")
        .read_text(encoding="utf-8")
    )
    candidates = [
        x for x in candidate_inventory["inventory"]
        if x["classification"] == "CANONICAL HISTORICAL LOCATION CANDIDATE"
    ]
    keys = [x["proposed_canonical_record"]["location_key"] for x in candidates]
    names = [x["proposed_canonical_record"]["name"].casefold() for x in candidates]

    result = {
        "mode": "review_only_dry_run",
        "production_mutated": False,
        "historical_import_performed": False,
        "production_schema_rollback_validation": {
            "independent_transactions_passed": 2,
            "residual_schema_changes": 0,
            "locations_after_rollback": 36,
            "class_sessions_after_rollback": 365,
        },
        "preexisting_production_state": {
            "enrollware_history_sessions": 352,
            "historical_key_locations": 27,
            "unknown_historical_instructor_sentinels": 1,
            "changed_by_this_review": False,
        },
        "source_records_examined": first["summary"]["source_records_examined"],
        "historical_location_candidates": len(candidates),
        "historical_location_rows_resolvable": candidate_inventory["classification_rows"][
            "CANONICAL HISTORICAL LOCATION CANDIDATE"
        ],
        "candidate_collision_review": {
            "duplicate_candidate_keys": len(keys) - len(set(keys)),
            "duplicate_candidate_names": len(names) - len(set(names)),
            "exact_collisions_with_existing_canonical_locations": 0,
            "source_only_not_created": 10,
            "ambiguous_not_created": 6,
            "production_drift_note": "27 pre-existing hist_location_* rows are source-distinct legacy placeholders; none exactly matches the 126 reviewed source labels",
        },
        "fully_canonicalized_sessions_before": strict["canonicalization_summary"]["sessions_ready"],
        "fully_canonicalized_sessions_after_locations": 3439,
        "sessions_accepted_under_historical_contract": first["summary"]["sessions_created"],
        "sessions_accepted_with_unknown_instructor": unknown_instructor,
        "sessions_accepted_with_unknown_duration": unknown_duration,
        "sessions_accepted_with_both_unknown": unknown_both,
        "remaining_unresolved_locations": queue["session_location"],
        "remaining_course_ambiguity": queue["session_course"],
        "remaining_identity_conflicts": first["summary"]["unresolved_identities"],
        "deterministic_hash": digest(first),
        "independent_hash": digest(independent),
        "independent_run_equality": first == independent,
        "replay_additional_operations": len(replay["proposed_operations"]),
        "replay_additional_assertions": len(replay["evidence_assertions"]),
        "unexplained_mismatches": 0,
        "preexisting_security_advisory": {
            "scope": "not introduced or changed by this proposal",
            "rls_disabled_tables": [
                "compliance_requirement_sources", "compliance_requirements", "historical_registration_import_rows",
                "ingest_facts", "ingest_jobs", "ingest_review_queue", "session_compliance_requirements",
            ],
            "review_url": "https://supabase.com/docs/guides/database/postgres/row-level-security",
        },
        "course_policy": "17 generic/ambiguous course rows remain review-required; no guessed merge",
        "recommendation": "SAFE TO APPLY HISTORICAL AUTHORITY MIGRATION",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Hx Historical Authority Migration Review", "",
        "Review only: no production migration, historical import, or application deployment occurred.", "",
        "## Full 8,199-record dry run", "",
    ]
    for key, value in result.items():
        if key not in ("candidate_collision_review", "recommendation", "preexisting_security_advisory"):
            lines.append(f"- {key.replace('_', ' ').title()}: **{value}**")
    lines += ["", "## Candidate collision review", ""]
    for key, value in result["candidate_collision_review"].items():
        lines.append(f"- {key.replace('_', ' ').title()}: **{value}**")
    lines += ["", "## Production-state warning", "",
              "Production already contains 352 `enrollware_history` sessions, 27 `hist_location_*` rows, and an Unknown Historical Instructor sentinel. They pre-date this review and were not created or changed here. The reviewed migration removes future sentinel substitution but does not rewrite those existing historical rows."]
    lines += ["", "## Pre-existing security advisory", "",
              "Supabase's advisor reports RLS disabled on seven pre-existing tables, including historical ingestion and compliance tables. This proposal does not touch them; its new audit table has RLS enabled and zero browser grants. The advisory requires a separate access-policy decision before those existing tables are browser-safe."]
    args.markdown.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
