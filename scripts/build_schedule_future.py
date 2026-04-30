from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from scripts.build_status import BuildStatusReporter
from supervisor.status_snapshot import write_status_snapshot
from typing import Any, Optional
from zoneinfo import ZoneInfo


TZ = ZoneInfo("America/New_York")


def clean_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def parse_iso_dt(value: Any) -> Optional[datetime]:
    s = clean_string(value)
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        else:
            dt = dt.astimezone(TZ)
        return dt
    except Exception:
        return None


def build_public_future_session(session: dict[str, Any]) -> dict[str, Any]:
    course = session.get("course", {})
    timing = session.get("timing", {})
    location = session.get("location", {})
    staffing = session.get("staffing", {})
    capacity = session.get("capacity", {})
    commerce = session.get("commerce", {})
    status = session.get("status", {})

    return {
        "session_id": session.get("session_id"),
        "course_id": course.get("course_id"),
        "course_name": course.get("course_name_primary_clean"),
        "course_subtitle": course.get("course_subtitle_text"),
        "course_number": course.get("course_number"),
        "course_code": course.get("course_code_hint"),
        "certifying_body": course.get("certifying_body_hint"),
        "delivery_mode": course.get("delivery_mode_hint"),
        "start_at": timing.get("start_at"),
        "end_at": timing.get("end_at"),
        "timezone": timing.get("timezone"),
        "location_name": location.get("location_name"),
        "location_display": location.get("location_display"),
        "client": location.get("client"),
        "lead_instructor_name": staffing.get("lead_instructor_name"),
        "price": commerce.get("price"),
        "max_students": capacity.get("max_students"),
        "registered_count": capacity.get("registered_count"),
        "enrolled_count": capacity.get("registered_count"),
        "available_seats": capacity.get("available_seats"),
        "is_full": capacity.get("is_full"),
        "registration_url": commerce.get("registration_url"),
        "session_status": status.get("session_status"),
    }


def main() -> int:
    reporter = BuildStatusReporter("build_schedule_future")
    parser = argparse.ArgumentParser(description="Build docs/data/schedule_future.json from data/sessions_current.json")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to repo root. Defaults to current working directory.",
    )
    parser.add_argument(
        "--input",
        default="data/sessions_current.json",
        help="Relative path from repo root to sessions_current.json",
    )
    parser.add_argument(
        "--output",
        default="docs/data/schedule_future.json",
        help="Relative path from repo root to output future schedule JSON",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    input_path = (repo_root / args.input).resolve()
    output_path = (repo_root / args.output).resolve()

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    reporter.waiting(total=0)
    try:
        raw = json.loads(input_path.read_text(encoding="utf-8"))
        sessions = raw.get("sessions", [])
        reporter.start(total=len(sessions))
        print(f"Loaded {len(sessions)} sessions from {input_path}")
        print("Filtering future sessions")

        now_dt = datetime.now(TZ)
        now_iso = now_dt.isoformat()

        future_sessions_raw: list[dict[str, Any]] = []
        skipped_missing_start = 0
        skipped_past = 0

        for index, session in enumerate(sessions, start=1):
            start_dt = parse_iso_dt(session.get("timing", {}).get("start_at"))
            if start_dt is None:
                skipped_missing_start += 1
                reporter.update(current=index, total=len(sessions))
                continue
            if start_dt < now_dt:
                skipped_past += 1
                reporter.update(current=index, total=len(sessions))
                continue
            future_sessions_raw.append(session)
            reporter.update(current=index, total=len(sessions))

        future_sessions_raw.sort(
            key=lambda s: (
                s.get("timing", {}).get("start_at") or "",
                s.get("session_id") or "",
            )
        )

        future_sessions = [build_public_future_session(s) for s in future_sessions_raw]

        output = {
            "build": {
                "generated_at": now_iso,
                "source_file": str(input_path),
                "counts": {
                    "sessions_input": len(sessions),
                    "sessions_output": len(future_sessions),
                    "skipped_missing_start": skipped_missing_start,
                    "skipped_past": skipped_past,
                },
            },
            "sessions": future_sessions,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        reporter.done(current=len(sessions), total=len(sessions), last_output_file=output_path)
        write_status_snapshot()
        print("Future schedule build complete")
        print(f"Wrote {output_path}")
        print(f"Future sessions written: {len(future_sessions)}")
        print(f"Skipped missing start: {skipped_missing_start}")
        print(f"Skipped past: {skipped_past}")

        return 0
    except Exception:
        reporter.error(last_output_file=output_path if output_path.exists() else None)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
