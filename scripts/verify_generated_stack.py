from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        return dt.astimezone(TZ)
    except Exception:
        return None


def iter_html(docs_dir: Path):
    for path in sorted(docs_dir.rglob("*.html")):
        parts = {part.lower() for part in path.parts}
        if "debug" in parts or "quarantine" in parts:
            continue
        yield path


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify regenerated 910CPR HTML stack.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--output", default="debug/generated_stack_verification.json")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    docs_dir = repo_root / "docs"
    schedule_path = docs_dir / "data" / "schedule_future.json"
    full_path = repo_root / "data" / "schedule_all.json"
    now = datetime.now(TZ)

    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    future_sessions = schedule.get("sessions", [])
    valid_future_ids = {
        str(s.get("session_id"))
        for s in future_sessions
        if parse_dt(s.get("start_at")) and parse_dt(s.get("start_at")) >= now
    }

    full_sessions = []
    if full_path.exists():
        full_sessions = json.loads(full_path.read_text(encoding="utf-8")).get("sessions", [])
    past_ids = {
        str(s.get("session_id"))
        for s in full_sessions
        if parse_dt(s.get("start_at")) and parse_dt(s.get("start_at")) < now
    }

    html_files = list(iter_html(docs_dir))
    missing_build_code = []
    missing_meta_build_date = []
    missing_visible_build = []
    empty_schedule_sections = []
    past_pages_missing_banner = []
    future_pages_missing_enroll = []
    expired_rendered_items = []

    class_id_re = re.compile(r"docs[\\/]+classes[\\/]+(\d+)\.html$", re.I)
    start_re = re.compile(r'data-(?:session-)?start=["\']([^"\']+)["\']', re.I)

    for path in html_files:
        rel = str(path.relative_to(repo_root))
        html = path.read_text(encoding="utf-8", errors="ignore")
        if "<!-- BUILD_CODE:" not in html:
            missing_build_code.append(rel)
        if 'name="build-date"' not in html and "name='build-date'" not in html:
            missing_meta_build_date.append(rel)
        if "Build:" not in html:
            missing_visible_build.append(rel)
        if re.search(r'<(?:div|section)[^>]+(?:upcoming-grid|session-grid|slug-pill-list)[^>]*>\s*</(?:div|section)>', html, re.I | re.S):
            empty_schedule_sections.append(rel)

        match = class_id_re.search(rel)
        if match:
            sid = match.group(1)
            if sid in past_ids and "This class has passed" not in html:
                past_pages_missing_banner.append(rel)
            if sid in valid_future_ids and "enroll?id=" not in html:
                future_pages_missing_enroll.append(rel)

        for start_raw in start_re.findall(html):
            dt = parse_dt(start_raw)
            if dt and dt < now and "This class has passed" not in html:
                expired_rendered_items.append({"file": rel, "start": start_raw})
                break

    report = {
        "generated_at": now.isoformat(),
        "counts": {
            "html_files": len(html_files),
            "future_sessions_runtime_valid": len(valid_future_ids),
            "past_sessions_in_full_dataset": len(past_ids),
            "missing_build_code": len(missing_build_code),
            "missing_meta_build_date": len(missing_meta_build_date),
            "missing_visible_build": len(missing_visible_build),
            "past_pages_missing_banner": len(past_pages_missing_banner),
            "future_pages_missing_enroll": len(future_pages_missing_enroll),
            "empty_schedule_sections": len(empty_schedule_sections),
            "expired_rendered_items": len(expired_rendered_items),
        },
        "failures": {
            "missing_build_code": missing_build_code[:50],
            "missing_meta_build_date": missing_meta_build_date[:50],
            "missing_visible_build": missing_visible_build[:50],
            "past_pages_missing_banner": past_pages_missing_banner[:50],
            "future_pages_missing_enroll": future_pages_missing_enroll[:50],
            "empty_schedule_sections": empty_schedule_sections[:50],
            "expired_rendered_items": expired_rendered_items[:50],
        },
    }

    out_path = (repo_root / args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"], indent=2))
    return 1 if any(report["counts"][key] for key in (
        "missing_build_code",
        "missing_meta_build_date",
        "missing_visible_build",
        "past_pages_missing_banner",
        "future_pages_missing_enroll",
        "empty_schedule_sections",
    )) else 0


if __name__ == "__main__":
    raise SystemExit(main())
