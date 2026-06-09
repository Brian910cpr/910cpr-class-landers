#!/usr/bin/env python3
"""Validate report-only claimed appointment conflict suppression."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_appointment_offer_inventory import build_inventory, clean_text, course_family, norm
from scripts.build_instructor_availability_report import DEBUG_DIR, SOURCE_MODES, TZ, load_json, parse_dt
from scripts.build_proposed_seed_review import format_date


CLAIMS_PATH = ROOT / "data" / "state" / "appointment_claims_test.json"
REPORT_JSON_PATH = DEBUG_DIR / "claimed_appointment_conflict_validation.json"
REPORT_MD_PATH = DEBUG_DIR / "claimed_appointment_conflict_validation.md"


SISTER_CONFLICT_FAMILIES = {
    "bls": {"bls"},
    "acls": {"acls"},
    "pals": {"pals"},
    "heartsaver": {"heartsaver"},
}


def load_claims() -> list[dict[str, Any]]:
    if not CLAIMS_PATH.exists():
        return []
    config = load_json(CLAIMS_PATH)
    return [row for row in config.get("claims", []) if isinstance(row, dict)]


def time_matches(value: Any, expected: Any) -> bool:
    return norm(value).lower() == norm(expected).lower()


def overlaps(offer: dict[str, Any], claim: dict[str, Any]) -> bool:
    offer_start = parse_dt(offer.get("start_datetime"))
    offer_end = parse_dt(offer.get("end_datetime"))
    claim_start = parse_dt(f"{claim.get('date')}T{time_to_24h(claim.get('start_time'))}:00")
    claim_end = parse_dt(f"{claim.get('date')}T{time_to_24h(claim.get('end_time'))}:00")
    if not offer_start or not offer_end or not claim_start or not claim_end:
        return False
    return offer_start < claim_end and claim_start < offer_end


def time_to_24h(value: Any) -> str:
    text = norm(value)
    for fmt in ("%I:%M %p", "%H:%M"):
        try:
            return datetime.strptime(text, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return text[:5]


def same_appointment_tuple(offer: dict[str, Any], claim: dict[str, Any]) -> bool:
    return (
        offer.get("appointmentDayId") is not None
        and str(offer.get("appointmentDayId")) == str(claim.get("appointmentDayId"))
        and time_matches(offer.get("start_time"), claim.get("start_time"))
    )


def same_instructor_overlap(offer: dict[str, Any], claim: dict[str, Any]) -> bool:
    return norm(offer.get("instructor_key")) == norm(claim.get("instructor_key")) and overlaps(offer, claim)


def same_location_overlap(offer: dict[str, Any], claim: dict[str, Any]) -> bool:
    return norm(offer.get("location_key")) == norm(claim.get("location_key")) and overlaps(offer, claim)


def sister_course_conflict(offer: dict[str, Any], claim: dict[str, Any]) -> bool:
    offer_family = norm(offer.get("course_family")) or course_family(offer.get("course_key"), offer.get("course_title"))
    claim_family = course_family(claim.get("course_key"), claim.get("course_key"))
    related = offer_family in SISTER_CONFLICT_FAMILIES.get(claim_family, set())
    return related and norm(offer.get("location_key")) == norm(claim.get("location_key")) and overlaps(offer, claim)


def conflict_reasons(offer: dict[str, Any], claim: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if norm(offer.get("seed_id")) == norm(claim.get("seed_id")):
        reasons.append("claimed_offer_not_available")
    if same_instructor_overlap(offer, claim):
        reasons.append("same_instructor_overlapping_time")
    if same_location_overlap(offer, claim):
        reasons.append("same_location_overlapping_time")
    if same_appointment_tuple(offer, claim):
        reasons.append("same_appointmentDayId_startTime_tuple")
    if sister_course_conflict(offer, claim):
        reasons.append("sister_conflict_course_practical_slot")
    return sorted(set(reasons))


def is_winner(offer: dict[str, Any], claim: dict[str, Any]) -> bool:
    return norm(offer.get("seed_id")) == norm(claim.get("seed_id"))


def row_for_offer(offer: dict[str, Any], claim: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    winner = is_winner(offer, claim)
    alternate_suppressed = bool(reasons) and not winner
    return {
        "seed_id": offer.get("seed_id"),
        "course_key": offer.get("course_key"),
        "course_title": offer.get("course_title"),
        "instructor_key": offer.get("instructor_key"),
        "location_key": offer.get("location_key"),
        "date": offer.get("date"),
        "start_time": offer.get("start_time"),
        "end_time": offer.get("end_time"),
        "appointmentDayId": offer.get("appointmentDayId"),
        "appointment_registration_url": offer.get("appointment_registration_url"),
        "standalone_class_lander_allowed": offer.get("standalone_class_lander_allowed"),
        "offer_source": offer.get("offer_source") or "appointment_offer_inventory",
        "slot_winner_course_key": claim.get("course_key"),
        "slot_winner_seed_id": claim.get("seed_id"),
        "slot_winner_registration_url": claim.get("appointment_registration_url"),
        "claimed_slot_status": "canonical_winner" if winner else ("suppressed_by_winner" if alternate_suppressed else "not_in_claimed_slot"),
        "suppressed_by_slot_winner_policy": alternate_suppressed,
        "slot_conflict_reason": ", ".join(reasons) if reasons else None,
        "canonical_offer_for_claimed_slot": winner,
        "alternate_course_suppressed": alternate_suppressed,
    }


def claim_test_alternates(claim: dict[str, Any]) -> list[dict[str, Any]]:
    alternates: list[dict[str, Any]] = []
    for offer in claim.get("test_conflicting_offers", []):
        if isinstance(offer, dict):
            row = dict(offer)
            row["offer_source"] = "appointment_claims_test_fixture"
            alternates.append(row)
    return alternates


def validate_claims(source_mode: str) -> dict[str, Any]:
    inventory = build_inventory(source_mode)
    claims = load_claims()
    inventory_offers = inventory.get("appointment_offers", [])
    suppressed: list[dict[str, Any]] = []
    canonical: list[dict[str, Any]] = []
    retained: list[dict[str, Any]] = []
    claim_results: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []

    for claim in claims:
        offers = list(inventory_offers) + claim_test_alternates(claim)
        claim_suppressed: list[dict[str, Any]] = []
        claim_canonical: list[dict[str, Any]] = []
        claim_retained: list[dict[str, Any]] = []
        for offer in offers:
            reasons = conflict_reasons(offer, claim)
            row = row_for_offer(offer, claim, reasons)
            if is_winner(offer, claim):
                row["suppression_reasons"] = reasons
                row["post_claim_inventory_status"] = (
                    "canonical_winner_available_for_additional_registration"
                    if claim.get("additional_registrations_allowed")
                    else "claimed_winner_not_open_unclaimed_seed"
                )
                claim_canonical.append(row)
                canonical.append(row)
            elif reasons:
                row["suppression_reasons"] = reasons
                row["post_claim_inventory_status"] = "suppressed_alternate_course_claim_conflict"
                claim_suppressed.append(row)
                suppressed.append(row)
            else:
                row["post_claim_inventory_status"] = "available_inventory"
                claim_retained.append(row)
                retained.append(row)

        if len(claim_canonical) != 1:
            violations.append(
                {
                    "rule": "one_canonical_winner_for_claimed_slot",
                    "claim_id": claim.get("claim_id"),
                    "recommendation": "Claimed slot must have exactly one canonical winner.",
                }
            )
        if not any(row.get("appointment_registration_url") == claim.get("appointment_registration_url") for row in claim_canonical):
            violations.append(
                {
                    "rule": "winner_registration_url_retained",
                    "claim_id": claim.get("claim_id"),
                    "recommendation": "Canonical winner must retain the winner registration URL.",
                }
            )
        if any(row.get("seed_id") == claim.get("seed_id") for row in claim_retained):
            violations.append(
                {
                    "rule": "claimed_winner_not_open_unclaimed_seed",
                    "claim_id": claim.get("claim_id"),
                    "recommendation": "Claimed winning seed must not remain in generic available inventory.",
                }
            )
        if claim.get("test_conflicting_offers") and not claim_suppressed:
            violations.append(
                {
                    "rule": "conflicting_alternate_courses_suppressed",
                    "claim_id": claim.get("claim_id"),
                    "recommendation": "Fixture alternate-course conflict should be suppressed by slot winner policy.",
                }
            )
        for row in claim_suppressed:
            if row.get("standalone_class_lander_allowed") is not False:
                violations.append(
                    {
                        "rule": "no_standalone_class_lander_created",
                        "seed_id": row.get("seed_id"),
                        "recommendation": "Appointment generated offers must not create standalone class landers.",
                    }
                )

        claim_results.append(
            {
                "claim": claim,
                "slot_winner_course_key": claim.get("course_key"),
                "slot_winner_seed_id": claim.get("seed_id"),
                "slot_winner_registration_url": claim.get("appointment_registration_url"),
                "claimed_slot_status": "claimed_with_canonical_winner",
                "canonical_winner": claim_canonical[0] if claim_canonical else None,
                "canonical_winner_count": len(claim_canonical),
                "suppressed_count": len(claim_suppressed),
                "alternate_course_suppressed_count": sum(1 for row in claim_suppressed if row.get("alternate_course_suppressed")),
                "retained_count": len(claim_retained),
                "suppressed": claim_suppressed,
                "retained_examples": claim_retained[:10],
            }
        )

    reason_counts = Counter(reason for row in suppressed for reason in row.get("suppression_reasons", []))
    retained_non_overlapping = [
        row for row in retained
        if row.get("date") != claims[0].get("date") or row.get("start_time") != claims[0].get("start_time")
    ] if claims else retained
    if claims and not retained_non_overlapping:
        violations.append(
            {
                "rule": "non_overlapping_future_offers_remain_available",
                "recommendation": "At least one non-conflicting future offer should remain available after the test claim.",
            }
        )

    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "public_files_modified": False,
        "source_mode": source_mode,
        "claims_source": str(CLAIMS_PATH),
        "inventory_source": "scripts/build_appointment_offer_inventory.py",
        "validation_passed": len(violations) == 0,
        "violation_count": len(violations),
        "violations": violations,
        "summary": {
            "claims_tested": len(claims),
            "appointment_offers_checked": len(inventory_offers),
            "test_fixture_alternate_offers_checked": sum(len(claim_test_alternates(claim)) for claim in claims),
            "canonical_winner_count": len(canonical),
            "conflicting_offers_suppressed": len({row.get("seed_id") for row in suppressed}),
            "conflicting_alternate_offers_suppressed": sum(1 for row in suppressed if row.get("alternate_course_suppressed")),
            "non_conflicting_offers_retained": len({row.get("seed_id") for row in retained}),
            "suppression_reason_counts": dict(sorted(reason_counts.items())),
            "standalone_class_landers_created": 0,
            "claimed_registration_urls_retained": sum(
                1
                for result in claim_results
                for row in [result.get("canonical_winner")]
                if row and row.get("seed_id") == result["claim"].get("seed_id") and row.get("appointment_registration_url")
            ),
        },
        "claim_results": claim_results,
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Claimed Appointment Conflict Validation",
        "",
        "> REPORT ONLY - no public schedule files, class landers, CTAs, or Enrollware records were changed.",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Validation passed: {report['validation_passed']}",
        f"- Violation count: {report['violation_count']}",
        f"- Claims tested: {report['summary']['claims_tested']}",
        f"- Appointment offers checked: {report['summary']['appointment_offers_checked']}",
        f"- Test fixture alternate offers checked: {report['summary']['test_fixture_alternate_offers_checked']}",
        f"- Canonical winners: {report['summary']['canonical_winner_count']}",
        f"- Conflicting offers suppressed: {report['summary']['conflicting_offers_suppressed']}",
        f"- Conflicting alternate offers suppressed: {report['summary']['conflicting_alternate_offers_suppressed']}",
        f"- Non-conflicting offers retained: {report['summary']['non_conflicting_offers_retained']}",
        f"- Suppression reasons: {json.dumps(report['summary']['suppression_reason_counts'], sort_keys=True)}",
        f"- Standalone class landers created: {report['summary']['standalone_class_landers_created']}",
        "",
    ]
    if report["violations"]:
        lines.append("## Violations")
        lines.append("")
        for violation in report["violations"]:
            lines.append(f"- {violation.get('rule')}: {violation.get('recommendation')}")
        lines.append("")

    for result in report["claim_results"]:
        claim = result["claim"]
        lines.extend(
            [
                f"## Claim {claim.get('claim_id')}",
                "",
                f"- Selected slot: {claim.get('date')} {claim.get('start_time')} - {claim.get('end_time')}",
                f"- Instructor: {claim.get('instructor_key')}",
                f"- Location: {claim.get('location_key')}",
                f"- Course: {claim.get('course_key')}",
                f"- AppointmentDayId: {claim.get('appointmentDayId')}",
                f"- Appointment URL: {claim.get('appointment_registration_url')}",
                f"- Slot winner course: {result.get('slot_winner_course_key')}",
                f"- Slot winner seed: {result.get('slot_winner_seed_id')}",
                f"- Slot winner URL: {result.get('slot_winner_registration_url')}",
                f"- Claimed slot status: {result.get('claimed_slot_status')}",
                f"- Canonical winner count: {result.get('canonical_winner_count')}",
                f"- Suppressed: {result['suppressed_count']}",
                f"- Alternate-course suppressed: {result.get('alternate_course_suppressed_count')}",
                f"- Retained: {result['retained_count']}",
                "",
                "### Canonical Winner",
                "",
            ]
        )
        winner = result.get("canonical_winner") or {}
        if winner:
            lines.append(
                f"- {winner.get('date')} {winner.get('start_time')} - {winner.get('end_time')} "
                f"{winner.get('instructor_key')} {winner.get('course_key')} ({winner.get('seed_id')})"
            )
            lines.append(f"  - Canonical offer for claimed slot: {winner.get('canonical_offer_for_claimed_slot')}")
            lines.append(f"  - Winner URL: {winner.get('slot_winner_registration_url')}")
            lines.append(f"  - Post-claim status: {winner.get('post_claim_inventory_status')}")
        else:
            lines.append("- No canonical winner found.")
        lines.extend(
            [
                "",
                "### Suppressed Examples",
                "",
            ]
        )
        for row in result["suppressed"][:12]:
            lines.append(
                f"- {row.get('date')} {row.get('start_time')} - {row.get('end_time')} "
                f"{row.get('instructor_key')} {row.get('course_key')} ({row.get('seed_id')})"
            )
            lines.append(f"  - Reasons: {', '.join(row.get('suppression_reasons', []))}")
        lines.extend(["", "### Retained Examples", ""])
        for row in result["retained_examples"]:
            lines.append(
                f"- {row.get('date')} {row.get('start_time')} - {row.get('end_time')} "
                f"{row.get('instructor_key')} {row.get('course_key')} ({row.get('seed_id')})"
            )
        lines.append("")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate claimed appointment conflict suppression.")
    parser.add_argument("--source", choices=sorted(SOURCE_MODES), default="auto", help="Seed calendar source mode.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = validate_claims(args.source)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    if not report["validation_passed"]:
        print(json.dumps(report["violations"], indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
