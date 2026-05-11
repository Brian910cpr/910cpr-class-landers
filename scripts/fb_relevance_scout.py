"""Generate Facebook Post Machine draft ideas from public relevance sources.

The scout is intentionally conservative:
- Reads configured public source URLs from data/facebook_sources.json.
- Uses local topic/source metadata rather than scraping private pages.
- Appends new draft items without overwriting existing queue entries.
- Does not call Meta or publish anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = ROOT / "data" / "facebook_sources.json"
QUEUE_PATH = ROOT / "data" / "facebook_post_queue.json"
DEBUG_PATH = ROOT / "debug" / "facebook_relevance_scout.json"
BASE_URL = "https://910cpr.com"

DESTINATION_RULES = [
    {
        "id": "nursing_healthcare_students",
        "keywords": ["nursing", "healthcare", "student", "clinical", "onboarding", "dental", "ems", "bls"],
        "preferred_paths": ["/courses/aha-bls-provider.html", "/topics/bls.html", "/bls.html"],
        "image_category": "AHA/BLS healthcare",
    },
    {
        "id": "church_safety_teams",
        "keywords": ["church", "faith", "safety team", "aed", "volunteer", "group training"],
        "preferred_paths": ["/courses/cpr-aed-first-aid-on-site-group-class.html", "/group-training.html", "/courses/aha-heartsaver-cpr-aed.html"],
        "image_category": "church/community safety",
    },
    {
        "id": "hoa_pool_community",
        "keywords": ["hoa", "pool", "water", "community", "neighborhood", "aed"],
        "preferred_paths": ["/courses/aha-heartsaver-first-aid-cpr-aed.html", "/topics/aed.html", "/courses/aha-heartsaver-cpr-aed.html"],
        "image_category": "AED readiness",
    },
    {
        "id": "parents_infant_choking",
        "keywords": ["infant", "choking", "parent", "grandparent", "babysitter", "family"],
        "preferred_paths": ["/courses/infant-cpr-and-choking-relief.html", "/courses/aha-family-friends-cpr.html", "/topics/family-friends.html"],
        "image_category": "family/infant/choking",
    },
    {
        "id": "workplace_first_aid",
        "keywords": ["workplace", "osha", "first aid", "kit", "business", "supervisor"],
        "preferred_paths": ["/courses/hsi-first-aid-cpr-aed.html", "/topics/first-aid.html", "/hsi.html"],
        "image_category": "workplace safety",
    },
    {
        "id": "hurricane_coastal_prep",
        "keywords": ["hurricane", "storm", "coastal", "preparedness", "first aid", "ems"],
        "preferred_paths": ["/courses/hsi-first-aid-cpr-aed.html", "/topics/first-aid.html", "/courses/aha-heartsaver-first-aid-cpr-aed.html"],
        "image_category": "hurricane/coastal prep",
    },
    {
        "id": "daycare_camp_staff",
        "keywords": ["daycare", "camp", "childcare", "pediatric", "summer", "youth"],
        "preferred_paths": ["/courses/aha-heartsaver-pediatric-first-aid-cpr-aed.html", "/courses/hsi-pediatric-first-aid-cpr-aed.html", "/courses/aha-heartsaver-first-aid-cpr-aed.html"],
        "image_category": "family/infant/choking",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:72] or "draft"


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value.lower())).strip()


def path_exists(site_path: str) -> bool:
    return (ROOT / "docs" / site_path.lstrip("/")).exists()


def best_destination(source: dict[str, Any]) -> dict[str, str]:
    haystack = " ".join(
        str(source.get(key, ""))
        for key in ("category", "topic", "audience", "relevance_reason", "course_angle", "draft_seed")
    ).lower()
    haystack += " " + " ".join(str(keyword).lower() for keyword in source.get("keywords", []))

    ranked: list[tuple[int, dict[str, Any]]] = []
    for rule in DESTINATION_RULES:
        score = 0
        if source.get("category") == rule["id"]:
            score += 10
        score += sum(1 for keyword in rule["keywords"] if keyword in haystack)
        ranked.append((score, rule))
    ranked.sort(key=lambda item: item[0], reverse=True)

    for _, rule in ranked:
        for site_path in rule["preferred_paths"]:
            if path_exists(site_path):
                return {
                    "url": f"{BASE_URL}{site_path}",
                    "image_category": rule["image_category"],
                    "destination_rule": rule["id"],
                }
    return {
        "url": f"{BASE_URL}/",
        "image_category": "910CPR brand/wave fallback",
        "destination_rule": "fallback_homepage",
    }


def draft_message(source: dict[str, Any], link: str) -> str:
    topic = str(source.get("topic", "Local safety reminder")).strip()
    seed = str(source.get("draft_seed", "")).strip()
    course_angle = str(source.get("course_angle", "CPR, AED, and first aid readiness")).strip()
    location = str(source.get("location", "our area")).strip()
    return (
        f"{topic}\n\n"
        f"{seed}\n\n"
        f"For {location}, 910CPR can help connect that reminder to practical {course_angle}.\n\n"
        f"{link}"
    )


def source_to_draft(source: dict[str, Any]) -> dict[str, Any]:
    destination = best_destination(source)
    source_id = str(source.get("id") or slugify(str(source.get("topic", "source"))))
    created_at = utc_now()
    return {
        "id": f"fb-scout-{slugify(source_id)}",
        "status": "draft",
        "post_type": source.get("recommended_post_type", "community"),
        "topic": str(source.get("topic", "")).strip(),
        "audience": str(source.get("audience", "")).strip(),
        "message": draft_message(source, destination["url"]),
        "recommended_910cpr_link": destination["url"],
        "image_category": destination["image_category"],
        "reason": str(source.get("relevance_reason", "")).strip(),
        "source_url": str(source.get("source_url", "")).strip(),
        "source_name": str(source.get("source_name", "")).strip(),
        "confidence": int(source.get("confidence", 3)),
        "course_angle": str(source.get("course_angle", "")).strip(),
        "location": str(source.get("location", "")).strip(),
        "destination_rule": destination["destination_rule"],
        "created_at": created_at,
        "approved_at": None,
        "published_at": None,
        "facebook_post_id": None,
        "error": None,
        "generated_by": "fb_relevance_scout",
        "generated_at": created_at,
    }


def fingerprint(item: dict[str, Any]) -> str:
    parts = [
        normalized_text(str(item.get("topic", ""))),
        normalized_text(str(item.get("audience", ""))),
        str(item.get("recommended_910cpr_link", "")).strip().lower(),
    ]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()


def is_duplicate(candidate: dict[str, Any], existing: list[dict[str, Any]]) -> tuple[bool, str]:
    candidate_id = candidate["id"]
    candidate_fp = fingerprint(candidate)
    candidate_source = str(candidate.get("source_url", "")).strip().lower()
    for item in existing:
        if item.get("id") == candidate_id:
            return True, f"id:{candidate_id}"
        if fingerprint(item) == candidate_fp:
            return True, f"fingerprint:{candidate_fp}"
        if candidate_source and str(item.get("source_url", "")).strip().lower() == candidate_source:
            return True, f"source_url:{candidate_source}"
    return False, ""


def validate_draft(item: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("id", "status", "topic", "audience", "message", "recommended_910cpr_link", "reason", "source_url"):
        if not str(item.get(field, "")).strip():
            errors.append(f"missing {field}")
    link = str(item.get("recommended_910cpr_link", ""))
    if not link.startswith(f"{BASE_URL}/"):
        errors.append("recommended_910cpr_link must begin with https://910cpr.com/")
    site_path = "/" + link.removeprefix(BASE_URL).lstrip("/")
    if site_path != "/" and not path_exists(site_path):
        errors.append(f"destination does not exist locally: {site_path}")
    confidence = item.get("confidence")
    if not isinstance(confidence, int) or not 1 <= confidence <= 5:
        errors.append("confidence must be an integer from 1 to 5")
    return errors


def generate(args: argparse.Namespace) -> int:
    sources = read_json(SOURCES_PATH, [])
    queue = read_json(QUEUE_PATH, [])
    if not isinstance(sources, list):
        raise SystemExit("data/facebook_sources.json must contain a JSON array")
    if not isinstance(queue, list):
        raise SystemExit("data/facebook_post_queue.json must contain a JSON array")

    existing = [item for item in queue if isinstance(item, dict)]
    candidates = [source_to_draft(source) for source in sources if isinstance(source, dict)]
    accepted: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    errors: list[dict[str, Any]] = []

    for candidate in candidates:
        validation_errors = validate_draft(candidate)
        duplicate, duplicate_reason = is_duplicate(candidate, existing + accepted)
        if validation_errors:
            errors.append({"id": candidate.get("id", ""), "errors": validation_errors})
            continue
        if duplicate:
            skipped.append({"id": candidate["id"], "reason": duplicate_reason})
            continue
        accepted.append(candidate)
        if args.limit and len(accepted) >= args.limit:
            break

    report = {
        "generated_at": utc_now(),
        "write": bool(args.write),
        "sources": len(sources),
        "existing_queue_items": len(queue),
        "accepted_count": len(accepted),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "accepted": accepted,
        "skipped": skipped,
        "errors": errors,
    }
    write_json(DEBUG_PATH, report)

    if errors and args.fail_on_error:
        raise SystemExit(f"Scout validation failed for {len(errors)} candidate(s). See {DEBUG_PATH}.")

    if args.write and accepted:
        queue.extend(accepted)
        write_json(QUEUE_PATH, queue)

    print(json.dumps({key: report[key] for key in ("sources", "existing_queue_items", "accepted_count", "skipped_count", "error_count", "write")}, indent=2))
    print(f"Debug report: {DEBUG_PATH}")
    if args.write:
        print(f"Queue updated: {QUEUE_PATH}")
    else:
        print("Dry run only. Re-run with --write to append accepted drafts.")
    return 0 if not errors else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Facebook Post Machine drafts from configured public relevance sources.")
    parser.add_argument("--write", action="store_true", help="Append accepted generated drafts to data/facebook_post_queue.json.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum accepted drafts to generate.")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit non-zero if any candidate fails validation.")
    args = parser.parse_args()
    return generate(args)


if __name__ == "__main__":
    raise SystemExit(main())
