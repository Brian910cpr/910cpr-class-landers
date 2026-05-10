from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from scripts.course_identity_resolver import stable_course_key
except ModuleNotFoundError:
    from course_identity_resolver import stable_course_key


TZ_CUTOFF = datetime.now().astimezone()
OLD_IGNORE_YEAR = 2025


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_dt(value: Any) -> datetime | None:
    text = clean(value)
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=TZ_CUTOFF.tzinfo)
        return dt.astimezone(TZ_CUTOFF.tzinfo)
    except Exception:
        return None


def unique_sample(values: list[Any], limit: int = 5) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = clean(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
        if len(out) >= limit:
            break
    return out


def numeric(value: Any) -> int:
    try:
        return int(float(value or 0))
    except Exception:
        return 0


def suggested_status(raw_course: str, normalized_course: str, future_count: int, latest: datetime | None, locations: list[str]) -> str:
    text = f"{raw_course} {normalized_course}".lower()
    location_text = " ".join(locations).lower()
    if future_count > 0:
        if any(token in text for token in ("private", "corporate", "staff", "employee", "team", "custom", "group")):
            return "likely_custom_or_corporate"
        if any(token in location_text for token in ("lowes", "cvs", "walgreens", "walmart", "dentistry", "fire", "school", "church")):
            return "likely_custom_or_corporate"
        return "needs_alias"
    if latest and latest.year < OLD_IGNORE_YEAR:
        return "likely_old_ignore"
    if any(token in text for token in ("private", "corporate", "personal event", "staff", "employee", "custom", "group")):
        return "likely_custom_or_corporate"
    return "needs_human_review"


def sort_key(group: dict[str, Any]) -> tuple[int, int, str]:
    latest = clean(group.get("latest_start_datetime"))
    return (-int(group.get("future_count") or 0), -int(group.get("count") or 0), latest)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize debug/unmatched_courses.json into grouped review artifacts.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--input", default="debug/unmatched_courses.json", help="Input unmatched course debug JSON.")
    parser.add_argument("--json-output", default="debug/unmatched_courses_grouped.json", help="Grouped JSON output path.")
    parser.add_argument("--csv-output", default="debug/unmatched_courses_grouped.csv", help="Grouped CSV output path.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    input_path = (repo_root / args.input).resolve()
    json_output = (repo_root / args.json_output).resolve()
    csv_output = (repo_root / args.csv_output).resolve()

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    records = payload.get("unmatched", [])
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if not isinstance(record, dict):
            continue
        key = (clean(record.get("normalized_course")), clean(record.get("raw_course")))
        grouped[key].append(record)

    groups: list[dict[str, Any]] = []
    for (normalized_course, raw_course), rows in grouped.items():
        starts = [parse_dt(row.get("start_datetime")) for row in rows]
        valid_starts = [dt for dt in starts if dt is not None]
        earliest = min(valid_starts).isoformat() if valid_starts else ""
        latest_dt = max(valid_starts) if valid_starts else None
        latest = latest_dt.isoformat() if latest_dt else ""
        future_count = sum(1 for dt in valid_starts if dt >= TZ_CUTOFF)
        past_count = len(rows) - future_count
        locations = unique_sample([row.get("location") for row in rows], 5)
        instructors = unique_sample(
            [row.get("instructor") or row.get("lead_instructor_name") for row in rows],
            5,
        )
        group = {
            "raw_course": raw_course,
            "normalized_course": normalized_course,
            "count": len(rows),
            "earliest_start_datetime": earliest,
            "latest_start_datetime": latest,
            "future_count": future_count,
            "past_count": past_count,
            "total_students": sum(numeric(row.get("students")) for row in rows),
            "sample_session_ids": unique_sample([row.get("session_id") for row in rows], 5),
            "sample_locations": locations,
            "sample_instructors": instructors,
            "suggested_course_key": stable_course_key(normalized_course or raw_course),
            "suggested_status": suggested_status(raw_course, normalized_course, future_count, latest_dt, locations),
        }
        groups.append(group)

    groups.sort(key=sort_key)
    # sort_key uses ascending latest for the third element; reverse just that by doing a stable secondary sort.
    groups.sort(key=lambda group: clean(group.get("latest_start_datetime")), reverse=True)
    groups.sort(key=lambda group: (-int(group["future_count"]), -int(group["count"])))

    output = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": str(input_path.relative_to(repo_root)).replace("\\", "/"),
        "group_count": len(groups),
        "record_count": sum(group["count"] for group in groups),
        "groups": groups,
    }

    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    fieldnames = [
        "raw_course",
        "normalized_course",
        "count",
        "earliest_start_datetime",
        "latest_start_datetime",
        "future_count",
        "past_count",
        "total_students",
        "sample_session_ids",
        "sample_locations",
        "sample_instructors",
        "suggested_course_key",
        "suggested_status",
    ]
    with csv_output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for group in groups:
            row = dict(group)
            for key in ("sample_session_ids", "sample_locations", "sample_instructors"):
                row[key] = "|".join(row.get(key) or [])
            writer.writerow(row)

    print(json.dumps({
        "group_count": len(groups),
        "record_count": output["record_count"],
        "json_output": str(json_output.relative_to(repo_root)).replace("\\", "/"),
        "csv_output": str(csv_output.relative_to(repo_root)).replace("\\", "/"),
        "top_20": groups[:20],
    }, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
