from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import urllib.parse


APPLY_CONFIRMATION = "CERTIFICATION-HISTORY"
PARSER_VERSION = "certification-history-importer/1.0"
AUTOMATIC_MATCH_METHODS = {
    "exact_email_compatible_course",
    "existing_ecard_exact",
    "exact_name_unique_compatible_profile",
    "exact_name_course_date_evidence",
}


@dataclass(frozen=True)
class ApprovedCounts:
    history_inserts: int
    history_reconciliations: int
    profile_updates: int
    file_ledger_upserts: int


def validate_apply_plan(
    report: dict[str, Any], approved: ApprovedCounts
) -> dict[str, list[dict[str, Any]]]:
    records = report.get("records") or []
    inserts: list[dict[str, Any]] = []
    reconciliations: list[dict[str, Any]] = []
    profile_updates: list[dict[str, Any]] = []

    for row in records:
        match = row.get("match") or {}
        proposals = [
            row.get("proposed_history_insert"),
            row.get("proposed_history_reconciliation"),
            row.get("proposed_profile_update"),
        ]
        if any(proposals):
            if match.get("status") != "exact_match":
                raise ValueError("write proposal exists for a non-exact match")
            if match.get("method") not in AUTOMATIC_MATCH_METHODS:
                raise ValueError(
                    f"write proposal uses unapproved match method: {match.get('method')}"
                )
            if not match.get("employee_profile_id"):
                raise ValueError("write proposal has no employee profile id")
        if row.get("proposed_history_insert"):
            payload = dict(row["proposed_history_insert"])
            if payload.get("certification_status") not in {
                "current", "expired", "superseded", "historical_unknown"
            }:
                raise ValueError("history insert has an invalid certification status")
            inserts.append(payload)
        if row.get("proposed_history_reconciliation"):
            reconciliations.append(dict(row["proposed_history_reconciliation"]))
        if row.get("proposed_profile_update"):
            if (row.get("proposed_history_insert") or {}).get(
                "certification_status"
            ) != "current":
                raise ValueError("profile projection is not backed by a current credential")
            profile_updates.append({
                "employee_profile_id": match["employee_profile_id"],
                "existing_state": (match.get("evidence") or {}).get(
                    "existing_profile_state"
                ) or {},
                "payload": dict(row["proposed_profile_update"]),
            })

    file_count = len((report.get("files") or {}).get("inspected") or [])
    actual = ApprovedCounts(
        history_inserts=len(inserts),
        history_reconciliations=len(reconciliations),
        profile_updates=len(profile_updates),
        file_ledger_upserts=file_count,
    )
    if actual != approved:
        raise ValueError(f"write counts changed: approved={approved}, actual={actual}")
    return {
        "history_inserts": inserts,
        "history_reconciliations": reconciliations,
        "profile_updates": profile_updates,
    }


def build_file_ledger_rows(
    report: dict[str, Any], folder_id: str
) -> list[dict[str, Any]]:
    inspected_at = datetime.now(timezone.utc).isoformat()
    records = report.get("records") or []
    parsed = Counter()
    invalid = Counter()
    duplicate = Counter()
    sha_by_file: dict[str, str] = {}
    for row in records:
        cert = row.get("certification") or {}
        file_id = cert.get("source_file_id")
        if not file_id:
            continue
        parsed[file_id] += 1
        if row.get("match", {}).get("status") == "invalid":
            invalid[file_id] += 1
        if row.get("duplicate_of"):
            duplicate[file_id] += 1
        if cert.get("source_file_sha256"):
            sha_by_file[file_id] = cert["source_file_sha256"]

    errors_by_file: dict[str, list[str]] = {}
    for error in (report.get("files") or {}).get("errors") or []:
        errors_by_file.setdefault(error["file_id"], []).append(error["error"])

    rows = []
    for source in (report.get("files") or {}).get("inspected") or []:
        file_id = source["id"]
        rows.append({
            "source_system": "google_drive",
            "source_folder_id": folder_id,
            "source_file_id": file_id,
            "source_file_name": source["name"],
            "source_file_modified_at": source.get("modified_at"),
            "source_file_size": source.get("size"),
            "source_file_md5": source.get("md5_checksum"),
            "source_file_sha256": sha_by_file.get(file_id),
            "parser_version": PARSER_VERSION,
            "inspection_status": (
                "partial_failure" if errors_by_file.get(file_id) else "inspected"
            ),
            "rows_parsed": parsed[file_id],
            "rows_invalid": invalid[file_id],
            "rows_duplicate": duplicate[file_id],
            "error_summary": errors_by_file.get(file_id, []),
            "last_seen_at": inspected_at,
            "last_inspected_at": inspected_at,
            "updated_at": inspected_at,
        })
    return rows


def apply_plan(
    client: Any,
    report: dict[str, Any],
    folder_id: str,
    approved: ApprovedCounts,
) -> dict[str, int]:
    plan = validate_apply_plan(report, approved)
    counts = Counter()

    for payload in plan["history_inserts"]:
        # source_payload is intentionally limited to source field names; reports retain
        # raw PII locally and the authoritative history row does not need it.
        payload = dict(payload)
        payload["source_payload"] = {
            "source_fields": payload.pop("source_payload_fields", [])
        }
        client.request(
            "maxim_certification_history?on_conflict=ecard_number",
            method="POST",
            payload=payload,
            prefer="resolution=ignore-duplicates,return=representation",
        )
        counts["history_inserts_attempted"] += 1

    for item in plan["history_reconciliations"]:
        history_id = item["history_id"]
        current = client.request(
            "maxim_certification_history?"
            + urllib.parse.urlencode({
                "select": "id,source_occurrences",
                "id": f"eq.{history_id}",
                "limit": "1",
            })
        )
        if not current:
            raise RuntimeError(f"history reconciliation target disappeared: {history_id}")
        occurrences = current[0].get("source_occurrences") or []
        fingerprint = item["append_source_occurrence"]["record_fingerprint"]
        if not any(row.get("record_fingerprint") == fingerprint for row in occurrences):
            client.request(
                "maxim_certification_history?"
                + urllib.parse.urlencode({"id": f"eq.{history_id}"}),
                method="PATCH",
                payload={
                    "source_occurrences": occurrences
                    + [item["append_source_occurrence"]]
                },
                prefer="return=representation",
            )
        counts["history_reconciliations_attempted"] += 1

    for item in plan["profile_updates"]:
        existing = item["existing_state"]
        payload = item["payload"]
        query = {
            "id": f"eq.{item['employee_profile_id']}",
            "workflow_stage": f"eq.{existing.get('workflow_stage')}",
        }
        if existing.get("expiration_date") is None:
            query["expiration_date"] = "is.null"
        else:
            query["expiration_date"] = f"eq.{existing['expiration_date']}"
        result = client.request(
            "maxim_employee_profiles?" + urllib.parse.urlencode(query),
            method="PATCH",
            payload=payload,
            prefer="return=representation",
        )
        if len(result or []) != 1:
            raise RuntimeError("profile optimistic lock failed; apply stopped")
        counts["profile_updates_applied"] += 1

    ledger = build_file_ledger_rows(report, folder_id)
    for start in range(0, len(ledger), 100):
        batch = ledger[start:start + 100]
        client.request(
            "certification_import_files?"
            "on_conflict=source_system,source_file_id",
            method="POST",
            payload=batch,
            prefer="resolution=merge-duplicates,return=minimal",
        )
        counts["file_ledger_upserts_attempted"] += len(batch)
    return dict(counts)
