from __future__ import annotations

import calendar
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from typing import Any

from .models import NormalizedCertification
from .normalize import normalize_course

AHA_MONTH_END_POLICY = "aha_two_years_through_end_of_issue_month"
AHA_MONTH_END_VERSION = "1.0"
AHA_CALCULATED_FAMILIES = {
    "BLS",
    "HS_TOTAL",
    "HEARTSAVER_OTHER",
    "CHILD_INFANT_CPR",
    "ACLS",
    "PALS",
}


@dataclass(frozen=True)
class CertificationAssessment:
    certification_status: str
    expiration_date: str | None
    expiration_source: str
    calculation_policy: str | None = None
    calculation_version: str | None = None
    calculated_from_date: str | None = None
    calculated_at: str | None = None
    evidence_missing: list[str] | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def two_years_through_end_of_month(value: str) -> str:
    source = date.fromisoformat(value)
    target_year = source.year + 2
    target_month = source.month
    last_day = calendar.monthrange(target_year, target_month)[1]
    return date(target_year, target_month, last_day).isoformat()


def _status(expiration_date: str, today: date) -> str:
    return "current" if expiration_date >= today.isoformat() else "expired"


def assess_certification(
    record: NormalizedCertification,
    profile: dict[str, Any],
    *,
    today: date | None = None,
    calculated_at: datetime | None = None,
) -> CertificationAssessment:
    today = today or date.today()
    calculated_at = calculated_at or datetime.now(timezone.utc)

    if record.source_expiration_date:
        return CertificationAssessment(
            certification_status=_status(
                record.source_expiration_date, today
            ),
            expiration_date=record.source_expiration_date,
            expiration_source="source",
        )

    profile_ecard = str(profile.get("prior_ecard_code") or "").replace(
        "-", ""
    ).replace(" ", "").upper()
    profile_expiration = (
        str(profile.get("expiration_date"))[:10]
        if profile.get("expiration_date")
        else None
    )
    if (
        profile_ecard
        and profile_ecard == record.ecard_code
        and profile_expiration
    ):
        return CertificationAssessment(
            certification_status=_status(profile_expiration, today),
            expiration_date=profile_expiration,
            expiration_source="existing_production",
        )

    calculated_from = record.issue_date or record.class_date
    if (
        record.normalized_course in AHA_CALCULATED_FAMILIES
        and calculated_from
    ):
        expiration = two_years_through_end_of_month(calculated_from)
        return CertificationAssessment(
            certification_status=_status(expiration, today),
            expiration_date=expiration,
            expiration_source="calculated_policy",
            calculation_policy=AHA_MONTH_END_POLICY,
            calculation_version=AHA_MONTH_END_VERSION,
            calculated_from_date=calculated_from,
            calculated_at=calculated_at.isoformat(),
        )

    missing: list[str] = []
    if record.normalized_course not in AHA_CALCULATED_FAMILIES:
        missing.append("no_verified_course_specific_expiration_policy")
    if not calculated_from:
        missing.append("missing_issue_or_class_date")
    return CertificationAssessment(
        certification_status="historical_unknown",
        expiration_date=None,
        expiration_source="unknown",
        evidence_missing=missing,
    )


def credential_family(course: str) -> str:
    normalized = normalize_course(course)
    if normalized == "HS_TOTAL":
        return "HS_TOTAL"
    if normalized == "HEARTSAVER_OTHER":
        return "HEARTSAVER_OTHER"
    if normalized == "CHILD_INFANT_CPR":
        return "CHILD_INFANT_CPR"
    return normalized


def same_credential_family(left: str, right: str) -> bool:
    left_family = credential_family(left)
    right_family = credential_family(right)
    return left_family != "UNKNOWN" and left_family == right_family
