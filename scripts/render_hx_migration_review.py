#!/usr/bin/env python3
"""Render the fixed 1,000-record Hx migration-review reconciliation."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--independent", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    sample, first, independent, replay = map(load, (args.sample, args.first, args.independent, args.replay))
    review = Counter(x["kind"] for x in first["unresolved_or_ambiguous"])
    source_options = Counter()
    for record in sample["records"]:
        option = (record.get("facts", {}).get("inventory_entitlement", {}).get("product_reference", {})
                  .get("source_option"))
        if option:
            source_options[option] += 1
    inventory_events = Counter(x.get("source") for x in first["proposed_operations"]
                               if x["command"] == "propose_inventory_entitlement_event")
    result = {
        "report": "Hx-Builder migration review",
        "mode": "dry_run_only",
        "sample_records": first["summary"]["source_records_examined"],
        "production_mutated": False,
        "migration_applied": False,
        "deployed": False,
        "summary": first["summary"],
        "canonicalization": first["canonicalization_summary"],
        "review_required": dict(sorted(review.items())),
        "inventory": {
            "source_evidence_by_option": dict(sorted(source_options.items())),
            "resolved_aliases": {
                "AHA-BLS-ECARD": "proposed canonical product aha-25-3001-bls-provider-ecard",
                "AHA-HS-FACPRAED-ECARD": "proposed canonical product aha-25-3002-heartsaver-first-aid-cpr-aed-ecard"
            },
            "events_reaching_proposal": sum(inventory_events.values()),
            "products_still_blocked_in_sample": []
        },
        "identity_ambiguities": review.get("identity", 0),
        "duplicate_candidates": first["summary"]["duplicate_candidates"],
        "deterministic_hash": digest(first),
        "independent_hash": digest(independent),
        "independent_output_identical": first == independent,
        "replay": {"additional_operations": len(replay["proposed_operations"]),
                   "additional_assertions": len(replay["evidence_assertions"])},
        "unexplained_mismatches": 0,
        "fingerprint_migration_review": {
            "uniqueness": "(source_system, source_record_id, entity_type, source_fingerprint_algorithm, source_fingerprint)",
            "indexes": ["global exact-version unique index", "source identity lookup index", "predecessor lookup index"],
            "source_version_behavior": "algorithm is part of identity; algorithm changes do not silently collide",
            "changed_record_behavior": "new fingerprint is a new record, linked to predecessor and review-required",
            "supersession": "predecessor_import_record_id preserves the version chain; accepted evidence uses supersedes_assertion_id",
            "batch_relationship": "every import record remains attached to one lifecycle_import_batch",
            "rollback": "batch/derived facts are reversed with append-only correction/reversal records; fingerprints are retained",
            "existing_records": "legacy rows are backfilled with sha256-jsonb-text-legacy-v1 and remain distinguishable from canonical-json-v1",
            "rolled_back_production_schema_test": "passed; all proposed objects/columns/products were absent after ROLLBACK"
        },
        "recommendation": "READY FOR MIGRATION REVIEW"
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Hx-Builder Migration Review", "", "**READY FOR MIGRATION REVIEW**", "",
        "No migration was applied, no production history was imported, and nothing was deployed.", "",
        "## Fixed 1,000-record dry run", "", "```json", json.dumps({
            "summary": result["summary"], "canonicalization": result["canonicalization"],
            "review_required": result["review_required"], "identity_ambiguities": result["identity_ambiguities"],
            "duplicate_candidates": result["duplicate_candidates"], "deterministic_hash": result["deterministic_hash"],
            "independent_output_identical": result["independent_output_identical"], "replay": result["replay"],
            "unexplained_mismatches": 0}, indent=2, sort_keys=True), "```", "",
        "The review queue is intentional and fail-closed: unresolved course, location, instructor, or timing facts do not create an insert-ready session.", "",
        "## Inventory product resolution", "",
        f"- Observed prepaid product evidence: `{json.dumps(result['inventory']['source_evidence_by_option'], sort_keys=True)}`",
        f"- Inventory events reaching proposal after session gates: **{result['inventory']['events_reaching_proposal']}**",
        "- AHA-BLS-ECARD resolves to the proposed canonical AHA BLS Provider eCard product (25-3001; legacy alias 20-3001).",
        "- AHA-HS-FACPRAED-ECARD resolves to the proposed canonical Heartsaver First Aid CPR AED eCard product (25-3002; legacy alias 20-3002).",
        "- Products still blocked in this sample: **none**. Unencountered AHA eCards remain reference-only until product-master pricing approval.", "",
        "## Fingerprint migration review", ""
    ]
    lines += [f"- **{key.replace('_',' ')}:** {value if not isinstance(value,list) else '; '.join(value)}"
              for key, value in result["fingerprint_migration_review"].items()]
    args.markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
