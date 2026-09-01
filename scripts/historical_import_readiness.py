#!/usr/bin/env python3
"""Read-only historical lifecycle reconciliation.

The harness consumes a representative source sample plus a production-shaped
reference snapshot. It never connects to Supabase and never mutates data.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPORT_KEYS = (
    "sessions_discovered",
    "customers_matched_exactly",
    "customers_matched_through_aliases",
    "customers_newly_proposed",
    "ambiguous_identities",
    "registrations_proposed",
    "duplicates_suppressed",
    "reschedules_inferred",
    "completions_found",
    "credentials_found",
    "payments_found",
    "materials_found",
    "unknown_unresolved_facts",
    "documents_attachable",
    "records_rejected",
    "records_changing_existing_facts",
)


def norm_email(value: Any) -> str:
    return str(value or "").strip().lower()


def norm_phone(value: Any) -> str:
    return "".join(c for c in str(value or "") if c.isdigit())


def reconcile(sample: dict[str, Any], reference: dict[str, Any]) -> dict[str, Any]:
    counts = Counter({key: 0 for key in REPORT_KEYS})
    decisions: list[dict[str, Any]] = []
    sessions = {str(x["source_session_id"]) for x in sample.get("records", []) if x.get("source_session_id")}
    counts["sessions_discovered"] = len(sessions)

    customers = reference.get("customers", [])
    aliases = {
        (str(a["source_system"]), str(a["source_identity"])): a
        for a in reference.get("aliases", [])
    }
    registrations = {
        (str(r["customer_id"]), str(r["class_session_id"])): r
        for r in reference.get("registrations", [])
    }
    external_registrations = {
        (str(r.get("registration_source")), str(r.get("external_registration_id"))): r
        for r in reference.get("registrations", [])
        if r.get("external_registration_id")
    }

    for record in sample.get("records", []):
        source_system = str(record.get("source_system") or sample.get("source_system") or "unknown")
        source_record_id = str(record.get("source_record_id") or "")
        decision = {"source_record_id": source_record_id, "source_system": source_system}
        if not source_record_id or not record.get("source_session_id"):
            counts["records_rejected"] += 1
            decision.update(action="reject", reason="missing source_record_id or source_session_id")
            decisions.append(decision)
            continue

        alias_key = str(record.get("customer_source_identity") or "")
        alias = aliases.get((source_system, alias_key)) if alias_key else None
        customer_id = None
        if alias and alias.get("resolution_status") == "matched":
            customer_id = str(alias["customer_id"])
            counts["customers_matched_through_aliases"] += 1
            decision["identity_resolution"] = "alias"
        elif alias and alias.get("resolution_status") in {"ambiguous", "pending_review"}:
            counts["ambiguous_identities"] += 1
            decision.update(action="review", reason="existing ambiguous alias")
            decisions.append(decision)
            continue
        else:
            email = norm_email(record.get("email"))
            phone = norm_phone(record.get("phone"))
            email_matches = {str(c["id"]) for c in customers if email and norm_email(c.get("email")) == email}
            phone_matches = {str(c["id"]) for c in customers if phone and norm_phone(c.get("phone")) == phone}
            candidates = email_matches | phone_matches
            contradictory = bool(email_matches and phone_matches and email_matches != phone_matches)
            if contradictory or len(candidates) > 1:
                counts["ambiguous_identities"] += 1
                decision.update(action="review", reason="conflicting or non-unique exact identity", candidates=sorted(candidates))
                decisions.append(decision)
                continue
            if len(candidates) == 1:
                customer_id = next(iter(candidates))
                counts["customers_matched_exactly"] += 1
                decision["identity_resolution"] = "exact"
            else:
                counts["customers_newly_proposed"] += 1
                customer_id = f"proposed:{source_system}:{alias_key or source_record_id}"
                decision["identity_resolution"] = "new"

        session_id = str(record["source_session_id"])
        external_registration_id = str(record.get("external_registration_id") or "")
        existing_external = external_registrations.get((source_system, external_registration_id)) if external_registration_id else None
        existing_membership = registrations.get((customer_id, session_id))
        if existing_external or existing_membership:
            counts["duplicates_suppressed"] += 1
            decision["registration_action"] = "suppress_duplicate"
        else:
            counts["registrations_proposed"] += 1
            decision["registration_action"] = "propose"

        prior_sessions = {
            str(r["class_session_id"])
            for r in reference.get("registrations", [])
            if str(r["customer_id"]) == customer_id and str(r["class_session_id"]) != session_id
        }
        if record.get("rescheduled_from_session_id") in prior_sessions:
            counts["reschedules_inferred"] += 1
            decision["reschedule_from"] = record["rescheduled_from_session_id"]

        for fact, key in (
            ("completion", "completions_found"),
            ("credential", "credentials_found"),
            ("payment", "payments_found"),
            ("materials", "materials_found"),
        ):
            if record.get(fact) not in (None, "", [], {}):
                counts[key] += 1
        if record.get("document_identity") and customer_id and session_id:
            counts["documents_attachable"] += 1

        unknown = sorted(k for k in ("payment", "materials", "completion", "credential") if k not in record)
        counts["unknown_unresolved_facts"] += len(unknown)
        decision["unknown_facts"] = unknown

        local = existing_external or existing_membership
        if local:
            protected = {
                field: {"existing": local.get(field), "incoming": record.get(field)}
                for field in ("status", "payment_status", "material_choice")
                if field in record and local.get(field) not in (None, record.get(field))
            }
            if protected:
                counts["records_changing_existing_facts"] += 1
                decision["protected_conflicts"] = protected
                decision["rule"] = "do_not_overwrite"
        decision.setdefault("action", "dry_run_only")
        decisions.append(decision)

    return {
        "mode": "dry_run",
        "mutation_performed": False,
        "batch_key": sample.get("batch_key"),
        "source_system": sample.get("source_system"),
        "parser_version": sample.get("parser_version"),
        "counts": {key: counts[key] for key in REPORT_KEYS},
        "decisions": decisions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sample", type=Path)
    parser.add_argument("reference", type=Path, nargs="?")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sample_payload = json.loads(args.sample.read_text(encoding="utf-8"))
    if args.reference:
        source_sample = sample_payload
        reference = json.loads(args.reference.read_text(encoding="utf-8"))
    elif "sample" in sample_payload and "reference" in sample_payload:
        source_sample = sample_payload["sample"]
        reference = sample_payload["reference"]
    else:
        parser.error("reference is required unless sample contains sample/reference keys")
    report = reconcile(source_sample, reference)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
