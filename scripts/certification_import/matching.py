from __future__ import annotations

from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any

from .models import MatchResult, NormalizedCertification
from .normalize import compatible_course, normalize_email, split_name


def _profile_name(profile: dict[str, Any]) -> str:
    customer = profile.get("customers") or {}
    return split_name(
        customer.get("first_name"), customer.get("last_name")
    )[2]


def _profile_email(profile: dict[str, Any]) -> str | None:
    return normalize_email((profile.get("customers") or {}).get("email"))


def _date_compatible(record: NormalizedCertification, profile: dict[str, Any]) -> bool:
    source_date = record.class_date or record.issue_date
    if not source_date:
        return False
    candidates = (
        profile.get("scheduled_class_date"),
        profile.get("prior_class_date"),
    )
    return any(value and str(value)[:10] == source_date for value in candidates)


class DeterministicMatcher:
    def __init__(
        self, profiles: list[dict[str, Any]], history: list[dict[str, Any]]
    ):
        self.profiles = profiles
        self.profiles_by_id = {row["id"]: row for row in profiles}
        self.history_by_ecard: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in history:
            if row.get("ecard_number"):
                self.history_by_ecard[str(row["ecard_number"]).replace("-", "").replace(" ", "").upper()].append(row)
        self.by_email: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for profile in profiles:
            email = _profile_email(profile)
            if email:
                self.by_email[email].append(profile)
            name = _profile_name(profile)
            if name:
                self.by_name[name].append(profile)

    def match(self, record: NormalizedCertification) -> MatchResult:
        if record.record_category == "historical_expiration_reference":
            return MatchResult(
                status="reference_only",
                method="historical_expiration_reference",
            )
        if record.corporate_customer and record.corporate_customer.casefold() not in {
            "maxim", "maxim healthcare", "maxim bh", "maxim dsp",
        }:
            return MatchResult(
                status="non_maxim",
                method="explicit_non_maxim_customer",
                evidence={"corporate_customer": record.corporate_customer},
            )
        if record.validation_errors:
            return MatchResult(
                status="invalid",
                method="validation_failed",
                evidence={"errors": record.validation_errors},
            )

        history_rows = self.history_by_ecard.get(record.ecard_code, [])
        history_profile_ids = {
            row.get("employee_profile_id") for row in history_rows if row.get("employee_profile_id")
        }
        if len(history_profile_ids) == 1:
            profile_id = next(iter(history_profile_ids))
            profile = self.profiles_by_id.get(profile_id)
            identity_conflicts: list[str] = []
            if profile:
                profile_email = _profile_email(profile)
                profile_name = _profile_name(profile)
                if (
                    record.email and profile_email
                    and record.email != profile_email
                ):
                    identity_conflicts.append("email")
                if (
                    record.normalized_name and profile_name
                    and record.normalized_name != profile_name
                ):
                    identity_conflicts.append("normalized_name")
            if identity_conflicts:
                return MatchResult(
                    status="conflict",
                    method="existing_ecard_identity_conflict",
                    evidence={
                        "candidates": [{
                            "profile_id": profile_id,
                            "conflicting_fields": identity_conflicts,
                        }]
                    },
                )
            if profile and compatible_course(
                record.normalized_course, profile.get("required_training", "")
            ):
                return MatchResult(
                    status="exact_match",
                    employee_profile_id=profile_id,
                    method="existing_exact_ecard",
                    confidence=1.0,
                )
            return MatchResult(
                status="conflict",
                method="existing_ecard_course_conflict",
                evidence={"candidates": [{
                    "profile_id": profile_id,
                    "source_course": record.normalized_course,
                    "required_training": (
                        profile.get("required_training") if profile else None
                    ),
                    "course_compatible": False,
                    "date_compatible": (
                        _date_compatible(record, profile) if profile else False
                    ),
                }]},
            )
        if len(history_profile_ids) > 1:
            return MatchResult(
                status="conflict",
                method="existing_ecard_multiple_profiles",
                evidence={
                    "profile_count": len(history_profile_ids),
                    "candidates": [
                        {"profile_id": profile_id}
                        for profile_id in sorted(history_profile_ids)
                    ],
                },
            )

        if record.email:
            email_matches = self.by_email.get(record.email, [])
            compatible = [
                row for row in email_matches
                if compatible_course(record.normalized_course, row.get("required_training", ""))
            ]
            if len(compatible) == 1:
                return MatchResult(
                    status="exact_match",
                    employee_profile_id=compatible[0]["id"],
                    method="exact_email_compatible_course",
                    confidence=1.0,
                )
            if len(email_matches) > 1 or len(compatible) > 1:
                return MatchResult(
                    status="ambiguous",
                    method="exact_email_multiple_profiles",
                    evidence={
                        "candidate_count": len(email_matches),
                        "candidates": [{
                            "profile_id": row["id"],
                            "source_course": record.normalized_course,
                            "required_training": row.get("required_training"),
                            "course_compatible": compatible_course(
                                record.normalized_course,
                                row.get("required_training", ""),
                            ),
                            "date_compatible": _date_compatible(record, row),
                        } for row in email_matches],
                    },
                )
            if len(email_matches) == 1:
                return MatchResult(
                    status="ambiguous",
                    method="exact_email_incompatible_or_unknown_course",
                    evidence={
                        "candidates": [{
                            "profile_id": email_matches[0]["id"],
                            "source_course": record.normalized_course,
                            "required_training": email_matches[0].get(
                                "required_training"
                            ),
                            "course_compatible": False,
                            "date_compatible": _date_compatible(
                                record, email_matches[0]
                            ),
                        }]
                    },
                )

        name_matches = self.by_name.get(record.normalized_name, [])
        account_value = (record.corporate_customer or "").casefold()
        if account_value and len(name_matches) == 1:
            candidate = name_matches[0]
            if compatible_course(
                record.normalized_course, candidate.get("required_training", "")
            ):
                return MatchResult(
                    status="exact_match",
                    employee_profile_id=candidate["id"],
                    method="exact_name_customer_compatible_course",
                    confidence=1.0,
                )
        date_course_matches = [
            row for row in name_matches
            if compatible_course(record.normalized_course, row.get("required_training", ""))
            and _date_compatible(record, row)
        ]
        if len(date_course_matches) == 1:
            return MatchResult(
                status="exact_match",
                employee_profile_id=date_course_matches[0]["id"],
                method="exact_name_compatible_course_and_date",
                confidence=1.0,
            )
        compatible_name_matches = [
            row for row in name_matches
            if compatible_course(
                record.normalized_course, row.get("required_training", "")
            )
        ]
        if len(name_matches) == 1 and len(compatible_name_matches) == 1:
            return MatchResult(
                status="exact_match",
                employee_profile_id=compatible_name_matches[0]["id"],
                method="exact_name_unique_compatible_profile",
                confidence=1.0,
            )
        if len(name_matches) > 1 or len(date_course_matches) > 1:
            return MatchResult(
                status="ambiguous",
                method="exact_name_multiple_profiles",
                evidence={
                    "candidate_count": len(name_matches),
                    "candidates": [
                        {
                            "profile_id": row["id"],
                            "normalized_name": _profile_name(row),
                            "course_compatible": compatible_course(
                                record.normalized_course,
                                row.get("required_training", ""),
                            ),
                            "date_compatible": _date_compatible(record, row),
                        }
                        for row in name_matches
                    ],
                },
            )

        suggestions: list[tuple[float, dict[str, Any]]] = []
        for profile in self.profiles:
            if not compatible_course(
                record.normalized_course, profile.get("required_training", "")
            ):
                continue
            if not _date_compatible(record, profile):
                continue
            score = SequenceMatcher(
                None, record.normalized_name, _profile_name(profile)
            ).ratio()
            suggestions.append((score, profile))
        suggestions.sort(key=lambda item: item[0], reverse=True)
        if (
            suggestions
            and suggestions[0][0] >= 0.94
            and (
                len(suggestions) == 1
                or suggestions[0][0] - suggestions[1][0] >= 0.04
            )
        ):
            return MatchResult(
                status="probable_match",
                method="fuzzy_name_compatible_course_and_date_review_only",
                confidence=round(suggestions[0][0], 4),
                suggested_employee_profile_id=suggestions[0][1]["id"],
            )
        return MatchResult(status="unmatched", method="no_deterministic_match")
