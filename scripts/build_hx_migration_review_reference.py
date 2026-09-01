#!/usr/bin/env python3
"""Overlay reviewed canonical references onto a read-only Hx production snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


MERGED_LISTS = (
    "courses", "course_aliases", "locations", "location_aliases", "people",
    "instructor_aliases", "products", "product_aliases",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production-reference", type=Path, required=True)
    parser.add_argument("--review-reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    production = json.loads(args.production_reference.read_text(encoding="utf-8"))
    review = json.loads(args.review_reference.read_text(encoding="utf-8"))
    result = dict(production)
    for key in MERGED_LISTS:
        result[key] = review.get(key, []) + production.get(key, [])
    result["aha_reference_only_products"] = review.get("aha_reference_only_products", [])
    result["reference_review_state"] = review.get("review_state")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: len(result.get(key, [])) for key in MERGED_LISTS}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
