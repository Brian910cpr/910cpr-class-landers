#!/usr/bin/env python3
"""Create a deterministic, read-only Google durable-record intermediate.

Input/output may contain PII. Keep real runs in an ignored private/runtime path.
This command does not contact Supabase or Google and performs no writes upstream.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "durable-record-envelope.v1"
SOURCE_SYSTEM = "landerware_supabase"
PAYLOAD_STRATEGY = "inline_allowlisted_v1"


@dataclass(frozen=True)
class EntitySpec:
    entity_type: str
    table: str
    fields: tuple[str, ...]


SPECS = (
    EntitySpec("session", "landerware_sessions", (
        "id", "external_session_id", "course_id", "course_name", "starts_at", "ends_at",
        "location_name", "instructor_id", "instructor_name", "organization_id",
        "lifecycle_state", "provenance", "workspace_schema_version", "requirements_manifest",
        "document_ids", "created_at", "updated_at",
    )),
    EntitySpec("registration", "landerware_registrations", (
        "id", "person_id", "requirement_id", "session_id", "roster_id", "organization_id",
        "status", "source", "supersedes_registration_id", "superseded_by_registration_id",
        "course_id", "registration_profile_key", "entry_context", "session_selection_status",
        "payer_mode", "pricing_state", "payment_state", "billing_state", "document_ids",
        "created_at", "updated_at",
    )),
    EntitySpec("person", "landerware_people", (
        "id", "current_first_name", "current_last_name", "current_email", "current_phone",
        "prior_names", "prior_contacts", "archived_at", "document_ids", "created_at", "updated_at",
    )),
    EntitySpec("organization", "landerware_organizations", (
        "id", "display_name", "organization_type", "billing_reference", "archived_at",
        "document_ids", "created_at", "updated_at",
    )),
    EntitySpec("credential", "landerware_credentials", (
        "id", "person_id", "registration_id", "session_id", "course_id", "credential_type",
        "credential_status", "ecard_code", "issued_at", "expires_on", "document_ids", "created_at",
    )),
    EntitySpec("financial_ref", "landerware_retail_orders", (
        "id", "registration_id", "person_id", "session_id", "external_class_id", "course_id",
        "class_amount_cents", "options_amount_cents", "total_amount_cents", "currency", "status",
        "hold_expires_at", "stripe_checkout_session_id", "stripe_payment_intent_id", "paid_at",
        "created_at", "updated_at",
    )),
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def require_timestamp(value: str, name: str) -> str:
    text = str(value or "").strip()
    if not text or "T" not in text or not (text.endswith("Z") or "+" in text[10:] or "-" in text[10:]):
        raise ValueError(f"{name} must be an ISO-8601 timestamp with timezone")
    return text


def envelope(spec: EntitySpec, row: dict[str, Any], mirrored_at: str) -> dict[str, Any]:
    canonical_id = str(row.get("id") or "").strip()
    if not canonical_id:
        raise ValueError(f"{spec.table} row is missing id")
    payload = {field: row[field] for field in spec.fields if field in row}
    occurred_at = row.get("updated_at") or row.get("created_at") or row.get("issued_at")
    require_timestamp(str(occurred_at or ""), f"{spec.table}[{canonical_id}].occurred_at")
    hashed = {
        "entity_type": spec.entity_type,
        "canonical_id": canonical_id,
        "source_system": SOURCE_SYSTEM,
        "source_id": canonical_id,
        "schema_version": SCHEMA_VERSION,
        "payload_strategy": PAYLOAD_STRATEGY,
        "payload": payload,
        "provenance": {"source_table": spec.table, "source_updated_at": row.get("updated_at")},
    }
    return {
        **hashed,
        "occurred_at": str(occurred_at),
        "mirrored_at": mirrored_at,
        "content_hash": "sha256:" + hashlib.sha256(canonical_bytes(hashed)).hexdigest(),
        "reconciliation_status": "pending",
    }


def export(input_payload: dict[str, Any], output_dir: Path, mirrored_at: str) -> dict[str, Any]:
    require_timestamp(mirrored_at, "mirrored_at")
    output_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    file_hashes: dict[str, str] = {}
    total = 0
    for spec in SPECS:
        rows = input_payload.get(spec.table, [])
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise ValueError(f"{spec.table} must be an array of objects")
        records = sorted((envelope(spec, row, mirrored_at) for row in rows), key=lambda item: item["canonical_id"])
        data = b"".join(canonical_bytes(record) + b"\n" for record in records)
        filename = f"{spec.entity_type}.jsonl"
        (output_dir / filename).write_bytes(data)
        counts[spec.entity_type] = len(records)
        file_hashes[filename] = "sha256:" + hashlib.sha256(data).hexdigest()
        total += len(records)
    manifest_core = {
        "schema_version": SCHEMA_VERSION,
        "source_system": SOURCE_SYSTEM,
        "mirrored_at": mirrored_at,
        "mode": "read_only_dry_run",
        "counts": counts,
        "total_records": total,
        "files": file_hashes,
    }
    manifest = {
        **manifest_core,
        "snapshot_hash": "sha256:" + hashlib.sha256(canonical_bytes(manifest_core)).hexdigest(),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mirrored-at", required=True, help="Fixed timezone-aware ISO timestamp for replayable output")
    args = parser.parse_args()
    payload = json.loads(args.input_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("input root must be an object keyed by canonical table")
    print(json.dumps(export(payload, args.output_dir, args.mirrored_at), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
