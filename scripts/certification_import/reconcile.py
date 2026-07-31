from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from typing import Any

from .matching import DeterministicMatcher
from .models import MatchResult, NormalizedCertification, ReconciledRecord
from .normalize import compatible_course
from .policy import (
    AHA_CALCULATED_FAMILIES,
    CertificationAssessment,
    assess_certification,
    same_credential_family,
)


def _date_value(value: Any) -> str | None:
    return str(value)[:10] if value else None


def _is_later(candidate: str | None, existing: str | None) -> bool:
    return bool(candidate and (not existing or candidate > existing))


def _history_payload(
    record: NormalizedCertification,
    profile: dict[str, Any],
    assessment: CertificationAssessment,
) -> dict[str, Any]:
    return {
        "employee_profile_id": profile["id"],
        "ecard_number": record.ecard_code,
        "course": record.normalized_course,
        "course_source": "drive_source",
        "issue_date": record.issue_date or record.class_date,
        "expiration_date": assessment.expiration_date,
        "expiration_source": assessment.expiration_source,
        "expiration_rule": assessment.calculation_policy,
        "calculation_policy": assessment.calculation_policy,
        "calculation_version": assessment.calculation_version,
        "calculated_from_date": assessment.calculated_from_date,
        "calculated_at": assessment.calculated_at,
        "training_provider": (
            "AHA"
            if record.normalized_course in AHA_CALCULATED_FAMILIES
            else None
        ),
        "source_drive_file_id": record.source_file_id,
        "source_filename": record.source_file_name,
        "source_occurrences": [{
            "file_id": record.source_file_id,
            "sheet": record.source_sheet,
            "row": record.source_row,
            "record_fingerprint": record.record_fingerprint,
        }],
        "source_payload": record.raw_record,
        "certification_status": assessment.certification_status,
        "match_method": "pending",
        "status_evidence": assessment.as_dict(),
    }


def _profile_projection(
    record: NormalizedCertification,
    profile: dict[str, Any],
    assessment: CertificationAssessment,
) -> tuple[dict[str, Any] | None, list[str]]:
    skips: list[str] = []
    if assessment.certification_status != "current":
        return None, [
            f"certification_status_{assessment.certification_status}"
        ]
    if not compatible_course(
        record.normalized_course, profile.get("required_training", "")
    ):
        return None, ["incompatible_course"]
    existing_expiration = _date_value(profile.get("expiration_date"))
    existing_class = _date_value(profile.get("prior_class_date"))
    existing_ecard = str(profile.get("prior_ecard_code") or "")
    if not assessment.expiration_date:
        return None, ["current_status_without_expiration"]
    if (
        existing_expiration
        and assessment.expiration_date < existing_expiration
    ):
        skips.append("earlier_expiration")
    if record.class_date and existing_class and record.class_date < existing_class:
        skips.append("older_class_date")
    if existing_ecard and not (
        _is_later(assessment.expiration_date, existing_expiration)
        or _is_later(record.class_date, existing_class)
    ):
        skips.append("older_or_unproven_replacement_ecard")
    if skips:
        return None, skips

    scheduled = _date_value(profile.get("scheduled_class_date"))
    stage = int(profile.get("workflow_stage") or 0)
    source_cycle_date = record.class_date or record.issue_date
    if (
        scheduled
        and stage in (2, 3)
        and source_cycle_date != scheduled
    ):
        return None, ["not_current_certification_cycle"]

    patch: dict[str, Any] = {
        "prior_ecard_code": record.ecard_code,
        "ecard_detected_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    existing_prior = profile.get("prior_class_date")
    scheduled_value = profile.get("scheduled_class_date")
    if record.class_date:
        if _date_value(existing_prior) == record.class_date:
            patch["prior_class_date"] = existing_prior
        elif _date_value(scheduled_value) == record.class_date:
            patch["prior_class_date"] = scheduled_value
        else:
            patch["prior_class_date"] = f"{record.class_date}T12:00:00Z"
    patch["expiration_date"] = assessment.expiration_date

    current_cycle = bool(
        source_cycle_date
        and (
            source_cycle_date == scheduled
            or source_cycle_date == existing_class
        )
    )
    if current_cycle and stage < 4:
        patch["workflow_stage"] = 4
        patch["status_detail"] = f"eCard {record.ecard_code}"
    return patch, skips


def reconcile(
    records: list[NormalizedCertification],
    snapshot: dict[str, list[dict[str, Any]]],
    *,
    today: date | None = None,
    calculated_at: datetime | None = None,
) -> list[ReconciledRecord]:
    matcher = DeterministicMatcher(snapshot["profiles"], snapshot["history"])
    profiles_by_id = {row["id"]: row for row in snapshot["profiles"]}
    existing_ecards = {
        str(row.get("ecard_number") or "").replace("-", "").replace(" ", "").upper()
        for row in snapshot["history"]
    }
    history_by_ecard = {
        str(row.get("ecard_number") or "").replace("-", "").replace(" ", "").upper(): row
        for row in snapshot["history"]
        if row.get("ecard_number")
    }
    history_by_profile: dict[str, list[dict[str, Any]]] = {}
    for row in snapshot["history"]:
        history_by_profile.setdefault(
            str(row.get("employee_profile_id") or ""), []
        ).append(row)
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
        if (
            match.status == "exact_match"
            and match.method in {
                "exact_identity_date_unique_required_course",
                "existing_ecard_exact_identity_date_inferred_course",
            }
        ):
            record = replace(
                record,
                normalized_course=match.evidence["inferred_course"],
            )
        result = ReconciledRecord(certification=record, match=match)
        if match.status == "reference_only":
            output.append(result)
            continue
        if record.ecard_code in existing_ecards:
            result.skip_reasons.append("ecard_already_in_certification_history")
            existing = history_by_ecard[record.ecard_code]
            match.evidence["existing_history_state"] = {
                "id": existing.get("id"),
                "employee_profile_id": existing.get("employee_profile_id"),
                "ecard_number": existing.get("ecard_number"),
                "course": existing.get("course"),
                "issue_date": existing.get("issue_date"),
                "expiration_date": existing.get("expiration_date"),
                "certification_status": existing.get("certification_status"),
            }
            occurrence = {
                "file_id": record.source_file_id,
                "sheet": record.source_sheet,
                "row": record.source_row,
                "record_fingerprint": record.record_fingerprint,
            }
            prior_occurrences = existing.get("source_occurrences") or []
            if match.status == "exact_match" and not any(
                item.get("record_fingerprint") == record.record_fingerprint
                for item in prior_occurrences
                if isinstance(item, dict)
            ):
                result.proposed_history_reconciliation = {
                    "history_id": existing.get("id"),
                    "ecard_number": record.ecard_code,
                    "append_source_occurrence": occurrence,
                    "reason": "existing_ecard_new_source_occurrence",
                }
            if match.status == "exact_match" and match.employee_profile_id:
                profile = profiles_by_id[match.employee_profile_id]
                existing_status = str(
                    existing.get("certification_status") or ""
                )
                existing_expiration = _date_value(
                    existing.get("expiration_date")
                )
                if existing_status == "current" and existing_expiration:
                    assessment = CertificationAssessment(
                        certification_status="current",
                        expiration_date=existing_expiration,
                        expiration_source=(
                            existing.get("expiration_source")
                            or "existing_production"
                        ),
                    )
                    result.proposed_profile_update, skips = (
                        _profile_projection(record, profile, assessment)
                    )
                    result.skip_reasons.extend(skips)
        elif match.status == "exact_match" and match.employee_profile_id:
            profile = profiles_by_id[match.employee_profile_id]
            match.evidence["existing_profile_state"] = {
                "required_training": profile.get("required_training"),
                "workflow_stage": profile.get("workflow_stage"),
                "status_detail": profile.get("status_detail"),
                "prior_class_date": profile.get("prior_class_date"),
                "expiration_date": profile.get("expiration_date"),
                "prior_ecard_code": profile.get("prior_ecard_code"),
            }
            assessment = assess_certification(
                record,
                profile,
                today=today,
                calculated_at=calculated_at,
            )
            source_date = record.issue_date or record.class_date
            compatible_history = [
                row
                for row in history_by_profile.get(match.employee_profile_id, [])
                if same_credential_family(
                    record.normalized_course, str(row.get("course") or "")
                )
            ]
            newer_history = [
                row
                for row in compatible_history
                if source_date
                and _date_value(row.get("issue_date"))
                and _date_value(row.get("issue_date")) > source_date
            ]
            if newer_history:
                assessment = replace(
                    assessment,
                    certification_status="superseded",
                    evidence_missing=(
                        ["newer_compatible_certification_exists"]
                    ),
                )
            payload = _history_payload(record, profile, assessment)
            payload["match_method"] = match.method
            result.proposed_history_insert = payload
            if assessment.certification_status == "current" and source_date:
                result.proposed_history_supersessions = [
                    {
                        "history_id": row.get("id"),
                        "ecard_number": row.get("ecard_number"),
                        "existing_status": row.get("certification_status"),
                        "proposed_status": "superseded",
                        "reason": "newer_compatible_current_certification",
                    }
                    for row in compatible_history
                    if _date_value(row.get("issue_date"))
                    and _date_value(row.get("issue_date")) < source_date
                    and row.get("certification_status") != "superseded"
                ]
            result.proposed_profile_update, skips = _profile_projection(
                record, profile, assessment
            )
            result.skip_reasons.extend(skips)
        output.append(result)
    return output
