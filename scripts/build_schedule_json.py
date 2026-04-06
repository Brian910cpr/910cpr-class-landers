
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ew_ingest import (
    course_slug,
    load_classes_xlsx,
    load_courses_xlsx,
    match_classes_to_courses,
    session_slug,
    topic_slug_for_session,
)

def build_schedule(course_export: Path, class_report: Path, output_path: Path) -> None:
    courses = load_courses_xlsx(course_export)
    classes = load_classes_xlsx(class_report)
    sessions = match_classes_to_courses(classes, courses)

    enriched = []
    for s in sessions:
        s = dict(s)
        s["topic_slug"] = topic_slug_for_session(s)
        s["session_slug"] = session_slug(s)
        matched = s.get("matched_course") or {}
        s["course_slug"] = course_slug(matched) if matched else None
        enriched.append(s)

    payload = {
        "build": {
            "course_export": str(course_export),
            "class_report": str(class_report),
            "course_count": len(courses),
            "session_count": len(enriched),
        },
        "courses": courses,
        "sessions": enriched,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {output_path}")
    print(json.dumps(payload["build"], indent=2))

def main() -> int:
    parser = argparse.ArgumentParser(description="Build schedule.json from Course Export and Class Report xlsx files")
    parser.add_argument("--course-export", required=True)
    parser.add_argument("--class-report", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    build_schedule(Path(args.course_export), Path(args.class_report), Path(args.output))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
