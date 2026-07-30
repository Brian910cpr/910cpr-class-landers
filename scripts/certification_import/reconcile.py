from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .matching import DeterministicMatcher
from .models import MatchResult, NormalizedCertification, ReconciledRecord
from .normalize import compatible_course


def _date_value(value: Any) -> str | None:
    return str(value)[:10] if value else None


def _is_later(candidate: str | None, existing: str | None) -> bool:
    return bool(candidate and (not existing or candidate > existing))


def _history_payload(
    record: NormalizedCertification, profile: dict[str, Any]
) -> dict[str, Any]:
    return {
        "employee_profile_id": profile["id"],
        "ecard_number": record.ecard_code,
        "course": record.normalized_course,
        "course_source": "drive_source",
        "issue_date": record.issue_date or record.class_date,
        "expiration_date": record.expiration_date,
        "expiration_source": "imported" if record.expiration_date else None,
        "expiration_rule": None,
        "training_provider": "AHA",
        "source_drive_file_id": record.source_file_id,
        "source_filename": record.source_file_name,
        "source_occurrences": [{
            "file_id": record.source_file_id,
            "sheet": record.source_sheet,
            "row": record.source_row,
            "record_fingerprint": record.record_fingerprint,
        }],
        "source_payload": record.raw_record,
        "certification_status": "current",
        "match_method": "pending",
    }


def _profile_projection(
    record: NormalizedCertification, profile: dict[str, Any]
) -> tuple[dict[str, Any] | None, list[str]]:
    skips: list[str] = []
    if not compatible_course(
        record.normalized_course, profile.get("required_training", "")
    ):
        return None, ["incompatible_course"]
    existing_expiration = _date_value(profile.get("expiration_date"))
    existing_class = _date_value(profile.get("prior_class_date"))
    existing_ecard = str(profile.get("prior_ecard_code") or "")
    if record.expiration_date and not _is_later(
        record.expiration_date, existing_expiration
    ):
        skips.append("earlier_or_equal_expiration")
    if record.class_date and existing_class and record.class_date < existing_class:
        skips.append("older_class_date")
    if existing_ecard and not (
        _is_later(record.expiration_date, existing_expiration)
        or _is_later(record.class_date, existing_class)
    ):
        skips.append("older_or_unproven_replacement_ecard")
    if skips:
        return None, skips

    patch: dict[str, Any] = {
        "prior_ecard_code": record.ecard_code,
        "ecard_detected_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if record.class_date:
        patch["prior_class_date"] = f"{record.class_date}T12:00:00Z"
    if record.expiration_date:
        patch["expiration_date"] = record.expiration_date

    scheduled = _date_value(profile.get("scheduled_class_date"))
    stage = int(profile.get("workflow_stage") or 0)
    if scheduled and record.class_date == scheduled and stage in (2, 3):
        patch["workflow_stage"] = 4
        existing_detail = str(profile.get("status_detail") or "")
        if not existing_detail or existing_detail.casefold().startswith(
            ("registered", "awaiting", "class complete")
        ):
            patch["status_detail"] = f"eCard issued {record.class_date}"
    return patch, skips


def reconcile(
    records: list[NormalizedCertification],
    snapshot: dict[str, list[dict[str, Any]]],
) -> list[ReconciledRecord]:
    matcher = DeterministicMatcher(snapshot["profiles"], snapshot["history"])
    profiles_by_id = {row["id"]: row for row in snapshot["profiles"]}
    existing_ecards = {
        str(row.get("ecard_number") or "").replace("-", "").replace(" ", "").upper()
        for row in snapshot["history"]
    }
    seen: dict[str, str] = {}
    seen_ecards: dict[str, str] = {}
    output: list[ReconciledRecord] = []
    for record in records:
        source_identity = (
            f"{record.source_file_id}:{record.source_sheet}:{record.source_row}"
        )
        if record.record_fingerprint in seen:
            output.append(
                ReconciledRecord(
                    certification=record,
                    match=MatchResult(
                        status="duplicate",
                        method="duplicate_semantic_record",
                    ),
                    duplicate_of=seen[record.record_fingerprint],
                    skip_reasons=["duplicate_semantic_record"],
                )
            )
            continue
        seen[record.record_fingerprint] = source_identity
        if record.ecard_code and record.ecard_code in seen_ecards:
            output.append(
                ReconciledRecord(
                    certification=record,
                    match=MatchResult(
                        status="duplicate",
                        method="duplicate_ecard_in_source_batch",
                    ),
                    duplicate_of=seen_ecards[record.ecard_code],
                    skip_reasons=["duplicate_ecard_in_source_batch"],
                )
            )
            continue
        if record.ecard_code:
            seen_ecards[record.ecard_code] = source_identity
        match = matcher.match(record)
        result = ReconciledRecord(certification=record, match=match)
        if record.ecard_code in existing_ecards:
            result.skip_reasons.append("ecard_already_in_certification_history")
        elif match.status == "exact_match" and match.employee_profile_id:
            profile = profiles_by_id[match.employee_profile_id]
            payload = _history_payload(record, profile)
            payload["match_method"] = match.method
            result.proposed_history_insert = payload
            result.proposed_profile_update, skips = _profile_projection(record, profile)
            result.skip_reasons.extend(skips)
        output.append(result)
    return output
