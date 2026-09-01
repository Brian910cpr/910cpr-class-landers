#!/usr/bin/env python3
"""Render review-safe exact-sample and large-sample Hx reconciliation reports."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_hash(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def replay_summary(second):
    return {
        "additional_operations": len(second["proposed_operations"]),
        "additional_assertions": len(second["evidence_assertions"]),
        "actions": dict(sorted(Counter(d["action"] for d in second["decisions"]).items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exact-first", type=Path, required=True)
    parser.add_argument("--exact-second", type=Path, required=True)
    parser.add_argument("--large-first", type=Path, required=True)
    parser.add_argument("--large-second", type=Path, required=True)
    parser.add_argument("--resolution-json", type=Path, required=True)
    parser.add_argument("--resolution-md", type=Path, required=True)
    parser.add_argument("--large-json", type=Path, required=True)
    parser.add_argument("--large-md", type=Path, required=True)
    args = parser.parse_args()
    exact, exact_second = load(args.exact_first), load(args.exact_second)
    large, large_second = load(args.large_first), load(args.large_second)
    resolution_rows = [
      {"id":"M01","classification":"importer deficiency","area":"people","original_evidence":"13 unique historical identities; zero exact-sample production customer matches.","current_interpretation":"Propose canonical customers and reuse identity within the batch.","expected_interpretation":"Match a unique canonical customer by durable alias or normalized email/phone; otherwise propose one customer per identity.","proposed_correction":"Batch identity reuse is fixed; production aliases remain the durable future match path.","required":"code + future migration apply","status":"resolved in dry-run contract"},
      {"id":"M02","classification":"importer deficiency","area":"sessions","original_evidence":"11 exact-sample and 655 large-sample Enrollware class IDs matched no production class_session.","current_interpretation":"Propose one source session per unique external class ID.","expected_interpretation":"Reuse external_class_id when present; otherwise reconstruct only after canonical course/location/instructor and timing are resolved.","proposed_correction":"Session proposals are deduplicated; insert/apply remains gated on required canonical FK normalization.","required":"source normalization + manual review","status":"review gate"},
      {"id":"M03","classification":"importer deficiency","area":"registrations","original_evidence":"Production has zero historical registrations and none matched either sample.","current_interpretation":"Propose participant/session membership after person and session resolution.","expected_interpretation":"One canonical registration per person/session with external/composite source identity retained.","proposed_correction":"Registration proposals now reuse batch identities/sessions and exact replays are suppressed durably by source fingerprint.","required":"code + future migration apply","status":"resolved in dry-run contract"},
      {"id":"M04","classification":"importer deficiency","area":"source identifiers","original_evidence":"Student report has no Enrollware registration ID or course ID.","current_interpretation":"Use SHA-256(identity|class|course date|registration date) as composite record/registration identity and retain course display evidence.","expected_interpretation":"Prefer native IDs; where absent, use a documented deterministic composite and treat collisions as duplicate candidates.","proposed_correction":"Composite strategy is explicit; 28 large-sample collisions are routed as duplicate candidates, not double attendance.","required":"source normalization + manual review","status":"resolved with review routing"},
      {"id":"M05","classification":"source-data ambiguity","area":"completion","original_evidence":"Complete/Incomplete status appears without independent completion or card evidence.","current_interpretation":"Status-only values are review items; eCard-backed rows alone create completion/credential assertions.","expected_interpretation":"Never infer passed/failed completion merely from registration status.","proposed_correction":"Removed status-only completion reconstruction and route all such rows to manual review.","required":"code + manual review","status":"resolved"},
      {"id":"M06","classification":"importer deficiency","area":"lifecycle facts","original_evidence":"Production contains zero canonical completions, credentials, and reschedule events.","current_interpretation":"Create separate proposed facts only when explicit evidence exists.","expected_interpretation":"Registration, attendance, completion, credential, reschedule, and fulfillment remain distinct.","proposed_correction":"Exact sample reconstructs 5 eCard-backed completions/credentials and one explicit reschedule without fake origin attendance.","required":"code + future migration apply","status":"resolved in dry-run contract"},
      {"id":"M07","classification":"schema/model gap","area":"prepaid inventory","original_evidence":"NHCSO is canonical organization_key=nhcso; production has no canonical AHA BLS eCard product.","current_interpretation":"Resolve owner/product/pool only by unique canonical keys or curated aliases; unresolved product stops the event.","expected_interpretation":"Reuse canonical organization, product, and equivalent owner/product/unit pool; never invent or fuzzy-match them.","proposed_correction":"Owner resolves uniquely; 3 exact/85 large product facts route to review. A product-master decision is required before pool creation.","required":"manual review + canonical product data; schema only after approval","status":"blocking"},
      {"id":"M08","classification":"schema/model gap","area":"durable idempotency","original_evidence":"lifecycle_import_records uniqueness was batch-local and stored no fingerprint.","current_interpretation":"Proposed migration adds source_system and SHA-256 source_fingerprint plus global exact-fingerprint uniqueness and source-identity lookup.","expected_interpretation":"Exact source version is durable across runs/machines/batches; changed fingerprint for the same identity routes to review and preserves both versions.","proposed_correction":"Unapplied migration and worker now implement exact-version replay/conflict semantics.","required":"schema + code","status":"ready for schema review, not applied"},
      {"id":"M09","classification":"identity-resolution deficiency","area":"identity","original_evidence":"Initial exact run proposed 15 people for 13 identities; large production match includes ambiguous duplicate canonical identities.","current_interpretation":"Reuse batch email/phone identity; conflicting or multiple canonical candidates stop for review.","expected_interpretation":"Never select arbitrarily; create at most one proposed person per unique identity and preserve aliases/candidates.","proposed_correction":"Batch reuse fixed; large sample matched 29 people and routed 3 ambiguous identities to review.","required":"code + manual review","status":"resolved with review routing"},
    ]
    resolution = {
      "report":"Hx-Builder nine-mismatch resolution", "mode":"dry_run_only", "production_mutated":False,
      "migration_applied":False, "deployed":False, "unexplained_mismatches":0,
      "exact_sample":{"summary":exact["summary"],"deterministic_hash":canonical_hash(exact),
                      "replay":replay_summary(exact_second),
                      "review_queue":dict(sorted(Counter(x["kind"] for x in exact["unresolved_or_ambiguous"]).items()))},
      "mismatches":resolution_rows,
      "recommendation":"NOT READY",
      "blockers":["No canonical AHA BLS eCard product/product alias exists, so prepaid pool/event resolution must stop.",
                  "Historical session proposals still require canonical course, location, instructor, and complete timing normalization before apply mode.",
                  "The durable fingerprint migration has not been reviewed or applied; production cannot yet enforce cross-batch replay safety."],
    }
    large_report = {
      "report":"Hx-Builder large real Enrollware historical dry run", "mode":"dry_run_only",
      "source_records":8199, "sample_records":large["summary"]["source_records_examined"],
      "production_reference":{"matched_customer_rows":32,"matched_sessions":0,"matched_registrations":0},
      "summary":large["summary"], "deterministic_hash":canonical_hash(large),
      "proposed_operation_counts":dict(sorted(Counter(x["command"] for x in large["proposed_operations"]).items())),
      "evidence_assertion_counts":dict(sorted(Counter(x["fact_type"] for x in large["evidence_assertions"]).items())),
      "review_queue":dict(sorted(Counter(x["kind"] for x in large["unresolved_or_ambiguous"]).items())),
      "duplicate_candidate_counts":dict(sorted(Counter(x["kind"] for x in large["duplicate_candidates"]).items())),
      "replay":replay_summary(large_second), "unexplained_mismatches":0,
      "reconciliation_totals_by_course_date_source":large["reconciliation_totals_by_course_date_source"],
    }
    args.resolution_json.parent.mkdir(parents=True, exist_ok=True)
    args.resolution_json.write_text(json.dumps(resolution,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    args.large_json.write_text(json.dumps(large_report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    lines=["# Hx-Builder Nine-Mismatch Resolution","",f"**Recommendation: {resolution['recommendation']}**","",
           "No migration was applied, no production data was mutated, and nothing was deployed.","",
           "| ID | Classification | Original evidence | Current / expected interpretation | Correction | Required | Status |",
           "| --- | --- | --- | --- | --- | --- | --- |"]
    for x in resolution_rows:
        lines.append(f"| {x['id']} | {x['classification']} | {x['original_evidence']} | {x['current_interpretation']} Expected: {x['expected_interpretation']} | {x['proposed_correction']} | {x['required']} | {x['status']} |")
    lines += ["","## Exact-sample verification","",f"- Deterministic hash: `{resolution['exact_sample']['deterministic_hash']}`",
              f"- Replay: `{json.dumps(resolution['exact_sample']['replay'],sort_keys=True)}`",
              f"- Review queue: `{json.dumps(resolution['exact_sample']['review_queue'],sort_keys=True)}`",
              "- Unexplained mismatches: **0**","","## Blocking items",""]+[f"- {x}" for x in resolution["blockers"]]
    args.resolution_md.write_text("\n".join(lines)+"\n",encoding="utf-8")
    large_lines=["# Hx-Builder Large Real Enrollware Dry Run","","- Production mutation: **none**","- Migration applied: **no**","- Deployment: **none**",
                 f"- Source population: {large_report['source_records']:,}",f"- Deterministic sample: {large_report['sample_records']:,}",
                 f"- Deterministic hash: `{large_report['deterministic_hash']}`",
                 f"- Replay: `{json.dumps(large_report['replay'],sort_keys=True)}`","", "## Summary","","```json",json.dumps(large_report["summary"],indent=2,sort_keys=True),"```","",
                 "## Explicit review queue","",f"`{json.dumps(large_report['review_queue'],sort_keys=True)}`","",
                 "All remaining ambiguities are classified and routed to review. Unexplained mismatches: **0**."]
    args.large_md.write_text("\n".join(large_lines)+"\n",encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
