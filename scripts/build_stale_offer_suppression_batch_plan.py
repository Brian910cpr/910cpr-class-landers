#!/usr/bin/env python3
"""Build report-only batch approval plans for stale offer suppressions."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_instructor_availability_report import DEBUG_DIR, TZ
from scripts.build_stale_offer_review_report import build_review_report
from scripts.build_stale_offer_suppression_candidates import build_report as build_candidate_report
from scripts.validate_stale_offer_suppression_execution import build_validation_report


REPORT_JSON_PATH = DEBUG_DIR / "stale_offer_suppression_batch_plan.json"
REPORT_MD_PATH = DEBUG_DIR / "stale_offer_suppression_batch_plan.md"


def slugify(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")
    return slug[:80] or "unknown"


def clean_course_title(value: Any) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def course_family(value: Any) -> str:
    text = clean_course_title(value).lower()
    if "acls" in text:
        return "acls"
    if "pals" in text:
        return "pals"
    if "bls" in text:
        return "bls"
    if "heartsaver" in text or "first aid" in text:
        return "heartsaver"
    if "elementary first aid" in text or "coast guard" in text:
        return "uscg"
    return "other"


def source_label(path: Any) -> str:
    text = str(path or "")
    if text.endswith("public_schedule.json"):
        return "public_schedule"
    if text.endswith("customer_facing_offers.json"):
        return "customer_facing_offers"
    return slugify(Path(text).name)


def date_range(items: list[dict[str, Any]]) -> dict[str, str | None]:
    dates = sorted(str(item.get("date") or "") for item in items if item.get("date"))
    return {
        "start_date": dates[0] if dates else None,
        "end_date": dates[-1] if dates else None,
    }


def confidence_level(items: list[dict[str, Any]]) -> str:
    levels = {str(item.get("confidence") or "unknown") for item in items}
    if levels == {"high"}:
        return "high"
    if "low" in levels:
        return "mixed_or_low"
    return "mixed"


def risk_level(items: list[dict[str, Any]]) -> str:
    sources = {source_label(item.get("source_file")) for item in items}
    count = len(items)
    confidence = confidence_level(items)
    if confidence != "high":
        return "needs_review"
    if sources == {"public_schedule"} and count <= 25:
        return "low"
    if sources == {"public_schedule"}:
        return "medium"
    return "medium_high"


def course_breakdown(items: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(clean_course_title(item.get("course_title") or item.get("course_key") or "unknown") for item in items)
    return dict(sorted(counts.items()))


def build_batch(batch_id: str, batch_name: str, items: list[dict[str, Any]], why: str) -> dict[str, Any]:
    actions = Counter(str(item.get("recommended_action") or "unknown") for item in items)
    sources = sorted({str(item.get("source_file") or "unknown") for item in items})
    risk = risk_level(items)
    return {
        "batch_id": batch_id,
        "batch_name": batch_name,
        "source_files_affected": sources,
        "recommended_action": "mixed" if len(actions) > 1 else next(iter(actions), "unknown"),
        "recommended_action_breakdown": dict(sorted(actions.items())),
        "candidate_count": len(items),
        "course_breakdown": course_breakdown(items),
        **date_range(items),
        "confidence_level": confidence_level(items),
        "risk_level": risk,
        "example_suppression_action_ids": [str(item.get("suppression_action_id")) for item in items[:15]],
        "why_this_batch_is_safe_or_needs_review": why,
        "approval_state_mutation_required": False,
        "candidates": [
            {
                "suppression_action_id": item.get("suppression_action_id"),
                "source_file": item.get("source_file"),
                "course_title": clean_course_title(item.get("course_title")),
                "date": item.get("date"),
                "start_time": item.get("start_time"),
                "recommended_action": item.get("recommended_action"),
                "confidence": item.get("confidence"),
            }
            for item in items
        ],
    }


def add_batch_if_items(batches: list[dict[str, Any]], batch_id: str, batch_name: str, items: list[dict[str, Any]], why: str) -> None:
    if items:
        batches.append(build_batch(batch_id, batch_name, sorted_items(items), why))


def sorted_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: (
            str(item.get("source_file") or ""),
            str(item.get("date") or ""),
            str(item.get("start_time") or ""),
            str(item.get("course_title") or ""),
            str(item.get("suppression_action_id") or ""),
        ),
    )


def build_batches(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    batches: list[dict[str, Any]] = []
    public_schedule = [item for item in candidates if source_label(item.get("source_file")) == "public_schedule"]
    customer_facing = [item for item in candidates if source_label(item.get("source_file")) == "customer_facing_offers"]
    high_confidence = [item for item in candidates if item.get("confidence") == "high"]

    add_batch_if_items(
        batches,
        "public_schedule_march_2026_acls",
        "Public schedule March 2026 ACLS stale offers",
        [item for item in public_schedule if item.get("month") == "2026-03" and course_family(item.get("course_title")) == "acls"],
        "Focused public_schedule batch with high-confidence stale ACLS records from one month.",
    )
    add_batch_if_items(
        batches,
        "public_schedule_march_2026_bls",
        "Public schedule March 2026 BLS stale offers",
        [item for item in public_schedule if item.get("month") == "2026-03" and course_family(item.get("course_title")) == "bls"],
        "Focused public_schedule batch with high-confidence stale BLS records from one month.",
    )
    add_batch_if_items(
        batches,
        "public_schedule_all_high_confidence",
        "All high-confidence public schedule stale offers",
        [item for item in public_schedule if item.get("confidence") == "high"],
        "Large batch; technically high confidence, but should be reviewed because it spans many courses and months.",
    )
    add_batch_if_items(
        batches,
        "customer_facing_offers_high_confidence",
        "High-confidence customer-facing stale offers",
        [item for item in customer_facing if item.get("confidence") == "high"],
        "Customer-facing offer batch should be reviewed carefully because it affects offer blocks, not only schedule rows.",
    )
    add_batch_if_items(
        batches,
        "customer_facing_offers_needs_review",
        "Customer-facing stale offers needing review",
        [item for item in customer_facing if item.get("confidence") != "high"],
        "Lower-confidence customer-facing offers need manual review before approval.",
    )

    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_month: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in candidates:
        by_source[source_label(item.get("source_file"))].append(item)
        by_month[str(item.get("month") or "unknown")].append(item)
        by_family[course_family(item.get("course_title"))].append(item)

    for source, items in sorted(by_source.items()):
        add_batch_if_items(
            batches,
            f"source_file_{slugify(source)}",
            f"All stale offers from {source}",
            items,
            "Source-file batch; review size and destination before approval.",
        )
    for month, items in sorted(by_month.items()):
        add_batch_if_items(
            batches,
            f"month_{slugify(month)}",
            f"All stale offers in {month}",
            items,
            "Month batch; useful for approving older stale records in time order.",
        )
    for family, items in sorted(by_family.items()):
        add_batch_if_items(
            batches,
            f"course_family_{slugify(family)}",
            f"All stale {family.upper()} family offers",
            items,
            "Course-family batch; review customer-facing impact before approval.",
        )

    # De-duplicate by batch_id while preserving first curated definition.
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for batch in batches:
        if batch["batch_id"] in seen:
            continue
        seen.add(batch["batch_id"])
        unique.append(batch)
    return sorted(unique, key=lambda item: (risk_sort(item["risk_level"]), item["candidate_count"], item["batch_id"]))


def risk_sort(value: str) -> int:
    return {
        "low": 0,
        "medium": 1,
        "medium_high": 2,
        "needs_review": 3,
    }.get(value, 9)


def build_report() -> dict[str, Any]:
    candidate_report = build_candidate_report()
    review_report = build_review_report()
    validation_report = build_validation_report()
    candidates = [
        item
        for item in candidate_report.get("candidates", [])
        if item.get("suppression_approval_status") == "needs_review"
    ]
    batches = build_batches(candidates)
    source_counts = Counter(str(item.get("source_file") or "unknown") for item in candidates)
    family_counts = Counter(course_family(item.get("course_title")) for item in candidates)
    high_confidence_batches = [batch for batch in batches if batch["confidence_level"] == "high" and batch["risk_level"] in {"low", "medium"}]
    needs_review_batches = [batch for batch in batches if batch["risk_level"] in {"medium_high", "needs_review"}]
    largest = max(batches, key=lambda item: item["candidate_count"], default=None)
    smallest = min(batches, key=lambda item: item["candidate_count"], default=None)
    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "banner": "REPORT ONLY - DOES NOT APPROVE OR SUPPRESS ANYTHING",
        "source_reports": {
            "candidate_report_generated_at": candidate_report.get("generated_at"),
            "review_report_generated_at": review_report.get("generated_at"),
            "validation_report_generated_at": validation_report.get("generated_at"),
        },
        "summary": {
            "total_suppression_candidates": len(candidates),
            "total_suggested_batches": len(batches),
            "high_confidence_batches": len(high_confidence_batches),
            "needs_review_batches": len(needs_review_batches),
            "largest_batch": {
                "batch_id": largest.get("batch_id"),
                "candidate_count": largest.get("candidate_count"),
            }
            if largest
            else None,
            "smallest_batch": {
                "batch_id": smallest.get("batch_id"),
                "candidate_count": smallest.get("candidate_count"),
            }
            if smallest
            else None,
            "source_file_breakdown": dict(sorted(source_counts.items())),
            "course_family_breakdown": dict(sorted(family_counts.items())),
            "current_executable_suppressions": validation_report.get("summary", {}).get("executable_suppressions"),
        },
        "suggested_first_safe_batch": next((batch for batch in batches if batch["risk_level"] == "low"), None),
        "high_risk_or_needs_review_batches": needs_review_batches[:20],
        "batches": batches,
        "operator_next_steps_text_only": [
            "Review a batch_id in this report before changing approval state.",
            "To approve a batch later, add its suppression_action_ids to data/state/stale_offer_suppression_approvals.json with suppression_approval_status approved_for_suppression.",
            "Then run: python scripts/validate_stale_offer_suppression_execution.py",
            "Then run: python scripts/execute_stale_offer_suppression.py --dry-run",
            "Only after review, run: python scripts/execute_stale_offer_suppression.py --apply",
        ],
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    summary = report["summary"]
    lines = [
        "# Stale Offer Suppression Batch Plan",
        "",
        "> REPORT ONLY - DOES NOT APPROVE OR SUPPRESS ANYTHING",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Total suppression candidates: {summary['total_suppression_candidates']}",
        f"- Total suggested batches: {summary['total_suggested_batches']}",
        f"- High-confidence batches: {summary['high_confidence_batches']}",
        f"- Needs-review batches: {summary['needs_review_batches']}",
        f"- Largest batch: {json.dumps(summary['largest_batch'], sort_keys=True)}",
        f"- Smallest batch: {json.dumps(summary['smallest_batch'], sort_keys=True)}",
        f"- Source file breakdown: {json.dumps(summary['source_file_breakdown'], sort_keys=True)}",
        f"- Course family breakdown: {json.dumps(summary['course_family_breakdown'], sort_keys=True)}",
        f"- Current executable suppressions: {summary['current_executable_suppressions']}",
        "",
        "## Suggested First Safe Batch",
        "",
    ]
    append_batch(lines, report.get("suggested_first_safe_batch"))

    lines.extend(["", "## High-Risk / Needs-Review Batch Examples", ""])
    if not report["high_risk_or_needs_review_batches"]:
        lines.append("No high-risk/needs-review batches.")
    for batch in report["high_risk_or_needs_review_batches"][:10]:
        append_batch(lines, batch)

    lines.extend(["", "## All Suggested Batches", ""])
    for batch in report["batches"]:
        append_batch(lines, batch)

    lines.extend(["", "## Operator Next Steps (Text Only)", ""])
    for step in report["operator_next_steps_text_only"]:
        lines.append(f"- {step}")

    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def append_batch(lines: list[str], batch: dict[str, Any] | None) -> None:
    if not batch:
        lines.append("No batch available.")
        return
    lines.append(f"### {batch['batch_id']}")
    lines.append(f"- Name: {batch['batch_name']}")
    lines.append(f"- Candidate count: {batch['candidate_count']}")
    lines.append(f"- Source files: {', '.join(batch['source_files_affected'])}")
    lines.append(f"- Recommended action: {batch['recommended_action']}")
    lines.append(f"- Date range: {batch.get('start_date')} to {batch.get('end_date')}")
    lines.append(f"- Confidence: {batch['confidence_level']}")
    lines.append(f"- Risk: {batch['risk_level']}")
    lines.append(f"- Approval state mutation required now: {batch['approval_state_mutation_required']}")
    lines.append(f"- Why: {batch['why_this_batch_is_safe_or_needs_review']}")
    lines.append(f"- Example suppression IDs: {', '.join(batch['example_suppression_action_ids'][:8])}")
    lines.append("")


def main() -> int:
    report = build_report()
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
