#!/usr/bin/env python3
"""Review stale class lander redirects that still fall back to /index.html."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_instructor_availability_report import DEBUG_DIR, TZ
from scripts.build_public_artifact_cleanup_plan import build_cleanup_plan


REPORT_JSON_PATH = DEBUG_DIR / "fallback_redirect_review.json"
REPORT_MD_PATH = DEBUG_DIR / "fallback_redirect_review.md"


def clean_text(value: Any) -> str:
    text = re.sub(r"<[^>]+>", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def class_title(path_value: Any) -> str | None:
    if not path_value:
        return None
    path = Path(str(path_value))
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"<title>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    return clean_text(match.group(1)) if match else None


def enrollware_ids_for(item: dict[str, Any]) -> list[str]:
    values = [
        item.get("artifact_id"),
        item.get("current_file_path"),
        item.get("destination_source_title"),
        item.get("course_title"),
    ]
    ids: set[str] = set()
    for value in values:
        for match in re.findall(r"\b\d{5,}\b", str(value or "")):
            ids.add(match)
    if str(item.get("artifact_id") or "").startswith("class:"):
        ids.add(str(item["artifact_id"]).split(":", 1)[1])
    return sorted(ids)


def infer_alternate_hub(item: dict[str, Any]) -> dict[str, Any]:
    haystack = " ".join(
        str(item.get(key) or "")
        for key in ["course_title", "course_key", "destination_source_title"]
    ).lower()
    checks = [
        ("/bls.html", "BLS pattern inferred from title/course text.", ["bls", "basic life support", "heartcode bls"]),
        ("/acls.html", "ACLS pattern inferred from title/course text.", ["acls", "advanced cardiovascular"]),
        ("/pals.html", "PALS pattern inferred from title/course text.", ["pals", "pediatric advanced"]),
        ("/heartsaver.html", "Heartsaver/First Aid/CPR AED pattern inferred from title/course text.", ["heartsaver", "first aid", "cpr aed", "cpr/aed"]),
        ("/arc.html", "ARC pattern inferred from title/course text.", ["arc", "red cross", "american red cross"]),
        ("/hsi.html", "HSI pattern inferred from title/course text.", ["hsi", "health and safety institute"]),
        ("/uscg-elementary-first-aid-cpr.html", "USCG Elementary First Aid pattern inferred from title/course text.", ["uscg", "coast guard", "elementary first aid"]),
    ]
    for hub, reason, keywords in checks:
        if any(keyword in haystack for keyword in keywords):
            return {
                "suggested_alternate_hub": hub,
                "suggested_reason": reason,
                "suggested_confidence": "medium",
            }
    return {
        "suggested_alternate_hub": None,
        "suggested_reason": "No reliable title/course pattern was inferable from available metadata.",
        "suggested_confidence": "low",
    }


def pattern_label(item: dict[str, Any]) -> str:
    text = " ".join(str(item.get(key) or "") for key in ["course_title", "destination_source_title"]).lower()
    if not text or "course options" in text:
        return "generic_course_options"
    for label in ["bls", "acls", "pals", "heartsaver", "hsi", "arc", "uscg"]:
        if label in text:
            return label
    if "first aid" in text or "cpr" in text:
        return "first_aid_cpr"
    return "unknown_pattern"


def review_item(item: dict[str, Any]) -> dict[str, Any]:
    inferred = infer_alternate_hub(item)
    title = class_title(item.get("current_file_path"))
    still_unknown = inferred["suggested_alternate_hub"] is None
    return {
        "artifact_id": item.get("artifact_id"),
        "class_file_path": item.get("current_file_path"),
        "title": title,
        "course_title": item.get("course_title"),
        "course_key": item.get("course_key"),
        "date": item.get("date"),
        "time": item.get("time"),
        "enrollware_or_course_ids": enrollware_ids_for(item),
        "fallback_reason": item.get("destination_reason"),
        "suggested_alternate_hub": inferred["suggested_alternate_hub"],
        "suggested_reason": inferred["suggested_reason"],
        "confidence": inferred["suggested_confidence"],
        "manual_review_note": "Still unknown; keep /index.html fallback until Brian maps this class family." if still_unknown else "Candidate alternate hub inferred; review before updating redirect target mapping.",
        "title_course_pattern": pattern_label(item),
    }


def build_review() -> dict[str, Any]:
    plan = build_cleanup_plan()
    fallback_items = [
        item
        for item in plan.get("cleanup_items", [])
        if item.get("proposed_action") == "redirect_class_lander_to_hub"
        and item.get("destination_hub") == "/index.html"
        and item.get("destination_needs_review") is True
    ]
    reviewed = [review_item(item) for item in fallback_items]
    pattern_counts = Counter(str(item["title_course_pattern"]) for item in reviewed)
    suggested_count = sum(1 for item in reviewed if item.get("suggested_alternate_hub"))
    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "report_only": True,
        "public_behavior_changed": False,
        "source_cleanup_plan_generated_at": plan.get("generated_at"),
        "summary": {
            "total_fallback_redirects": len(reviewed),
            "suggested_better_hub_count": suggested_count,
            "still_unknown_count": len(reviewed) - suggested_count,
            "by_title_course_pattern": dict(sorted(pattern_counts.items())),
        },
        "fallback_redirects": reviewed,
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Fallback Redirect Review",
        "",
        "> REPORT ONLY - no public files or redirect mappings were modified.",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Total fallback redirects: {report['summary']['total_fallback_redirects']}",
        f"- Suggested better hub count: {report['summary']['suggested_better_hub_count']}",
        f"- Still unknown count: {report['summary']['still_unknown_count']}",
        f"- By title/course pattern: {json.dumps(report['summary']['by_title_course_pattern'], sort_keys=True)}",
        "",
        "## Suggested Better Hub",
        "",
    ]
    suggested = [item for item in report["fallback_redirects"] if item.get("suggested_alternate_hub")]
    if not suggested:
        lines.append("No fallback redirects had a reliable alternate hub inference.")
    for item in suggested[:50]:
        lines.append(f"- {item['artifact_id']} -> {item['suggested_alternate_hub']}")
        lines.append(f"  - Title: {item.get('title')}")
        lines.append(f"  - Course title: {item.get('course_title')}")
        lines.append(f"  - Reason: {item['suggested_reason']}")
        lines.append(f"  - Confidence: {item['confidence']}")
    lines.extend(["", "## Still Unknown", ""])
    unknown = [item for item in report["fallback_redirects"] if not item.get("suggested_alternate_hub")]
    if not unknown:
        lines.append("No unknown fallback redirects remain.")
    for item in unknown[:50]:
        lines.append(f"- {item['artifact_id']}")
        lines.append(f"  - File: {item['class_file_path']}")
        lines.append(f"  - Title: {item.get('title')}")
        lines.append(f"  - Course title: {item.get('course_title')}")
        lines.append(f"  - IDs: {', '.join(item['enrollware_or_course_ids'])}")
        lines.append(f"  - Note: {item['manual_review_note']}")
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    report = build_review()
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
