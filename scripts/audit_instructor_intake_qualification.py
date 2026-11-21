"""Read-only qualification gate for native instructor availability intake.

Never edits catalogs, fetches calendars, or grants scheduling eligibility.
Family ceilings are not exact-course qualification evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit_qualification(profiles: dict, catalog: dict, instructor_id: str) -> dict:
    profiles_found = [r for r in profiles.get("instructors", []) if r.get("instructor_key") == instructor_id]
    qualifications = [r for r in catalog.get("instructors", []) if r.get("instructor_id") == instructor_id]
    reasons = []
    if len(profiles_found) != 1:
        reasons.append("instructor_profile_missing_or_ambiguous")
    if len(qualifications) != 1:
        reasons.append("qualification_record_missing_or_ambiguous")
    profile = profiles_found[0] if len(profiles_found) == 1 else {}
    qualification = qualifications[0] if len(qualifications) == 1 else {}
    if qualification.get("active") is not True:
        reasons.append("active_qualification_not_confirmed")
    ids = qualification.get("can_teach_course_ids")
    if not isinstance(ids, list) or not ids or any(not isinstance(v, str) or not v.strip() or v == "UNKNOWN" for v in ids):
        reasons.append("exact_course_qualifications_unreviewed")
    certifications = qualification.get("certifications")
    if not isinstance(certifications, list) or not certifications:
        reasons.append("certification_evidence_missing")
    else:
        for cert in certifications:
            if not isinstance(cert, dict) or not cert.get("source") or cert.get("certification_code") in (None, "", "UNKNOWN"):
                reasons.append("certification_evidence_incomplete")
                break
        if any(not isinstance(c, dict) or c.get("expiration_date") in (None, "", "UNKNOWN") for c in certifications):
            reasons.append("certification_expiry_unreviewed")
    profile_families = set(profile.get("allowed_course_groups") or [])
    qualification_families = set(qualification.get("can_teach_course_families") or [])
    if profile_families != qualification_families:
        reasons.append("profile_and_qualification_family_mismatch")
    return {
        "schema_version": "instructor-intake-qualification-audit.v1",
        "instructor_id": instructor_id,
        "state": "REVIEW_REQUIRED" if reasons else "STATIC_CHECKS_PASSED",
        "can_publish": False,
        "limitations": "Static checks cannot prove current credentials, canonical identity binding, conflicts, payment, or live intake safety.",
        "reasons": reasons,
        "profile_families": sorted(profile_families),
        "qualification_families": sorted(qualification_families),
        "exact_course_ids": ids if isinstance(ids, list) else [],
        "sources": ["data/config/instructors.json", "data/config/instructor_catalog.json"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instructor", default="amy")
    args = parser.parse_args()
    profiles = json.loads((ROOT / "data/config/instructors.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "data/config/instructor_catalog.json").read_text(encoding="utf-8"))
    result = audit_qualification(profiles, catalog, args.instructor)
    print(json.dumps(result, indent=2))
    return 2 if result["reasons"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
