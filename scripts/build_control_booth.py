from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DEBUG_DIR = ROOT / "debug"
STATUS_DIR = DEBUG_DIR / "status"
OUTPUT_PATH = DEBUG_DIR / "control_booth_data.json"
TZ = ZoneInfo("America/New_York")

EXPECTED_PHASES = [
    "build_all_v4",
    "build_sessions_current",
    "build_schedule_future",
    "build_slug_hubs",
    "build_courses",
    "build_locations",
    "build_course_at_city",
    "build_request_group_session",
    "build_index_and_sitemap",
]


def now_iso() -> str:
    return datetime.now(TZ).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def load_json_checked(path: Path) -> tuple[Any, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"


def rel(path: str | Path | None) -> str | None:
    if not path:
        return None
    candidate = Path(path)
    try:
        if candidate.is_absolute():
            return candidate.relative_to(ROOT).as_posix()
    except ValueError:
        pass
    return str(path).replace("\\", "/")


def resolve_repo_path(value: str | Path | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=TZ)
    return parsed.astimezone(TZ)


def normalize_paths(payload: dict[str, Any], key: str) -> None:
    items = payload.get(key, [])
    if not isinstance(items, list):
        payload[key] = []
        return
    payload[key] = [rel(item) for item in items if item]


def normalize_list(payload: dict[str, Any], key: str) -> None:
    items = payload.get(key, [])
    if items is None:
        payload[key] = []
    elif isinstance(items, list):
        payload[key] = items
    else:
        payload[key] = [str(items)]


def find_stale_reasons(payload: dict[str, Any]) -> list[str]:
    last_run = parse_dt(payload.get("last_run") or payload.get("timestamp"))
    if last_run is None:
        return ["Status file has no valid last_run timestamp."]

    reasons: list[str] = []
    outputs = payload.get("outputs", [])
    if isinstance(outputs, list):
        for item in outputs:
            path = resolve_repo_path(item)
            if path and not path.exists():
                reasons.append(f"Declared output is missing: {rel(path)}")

    inputs = payload.get("inputs", [])
    if isinstance(inputs, list):
        last_run_epoch = last_run.timestamp()
        for item in inputs:
            path = resolve_repo_path(item)
            if path and path.exists() and path.stat().st_mtime > last_run_epoch:
                reasons.append(f"Input changed after last run: {rel(path)}")
    return reasons


def normalize_status(payload: dict[str, Any]) -> dict[str, Any]:
    raw_status = str(payload.get("status") or "unknown").lower()
    normalize_list(payload, "warnings")
    normalize_list(payload, "errors")
    payload["raw_status"] = raw_status
    stale_reasons = find_stale_reasons(payload)
    warnings = payload.get("warnings", [])
    errors = payload.get("errors", [])

    if raw_status in {"error", "failed"} or errors:
        status = "error"
    elif raw_status == "running":
        status = "running"
    elif raw_status == "done" and stale_reasons:
        status = "stale"
    elif raw_status == "done" and warnings:
        status = "warning"
    elif raw_status == "done":
        status = "done"
    else:
        status = raw_status or "unknown"

    if stale_reasons:
        existing = warnings if isinstance(warnings, list) else []
        payload["warnings"] = existing + stale_reasons
    payload["status"] = status
    return payload


def collect_statuses() -> list[dict[str, Any]]:
    statuses_by_phase: dict[str, dict[str, Any]] = {}
    for path in sorted(STATUS_DIR.glob("*.json")):
        payload, error = load_json_checked(path)
        if error:
            phase = path.stem
            statuses_by_phase[phase] = {
                "phase_name": phase,
                "worker": phase,
                "script": f"scripts/{phase}.py",
                "status": "invalid_status_file",
                "raw_status": "invalid_status_file",
                "status_file": rel(path),
                "warnings": [],
                "errors": [error],
                "files_needing_review": [rel(path)],
                "inputs": [],
                "outputs": [],
            }
            continue
        if not isinstance(payload, dict):
            continue
        phase = str(payload.get("phase_name") or path.stem)
        payload["phase_name"] = phase
        payload.setdefault("worker", phase)
        payload.setdefault("script", f"scripts/{phase}.py")
        payload["status_file"] = rel(path)
        if payload.get("last_output_file"):
            payload["last_output_file"] = rel(payload.get("last_output_file"))
        normalize_paths(payload, "inputs")
        normalize_paths(payload, "outputs")
        normalize_list(payload, "files_needing_review")
        payload["files_needing_review"] = [rel(item) for item in payload.get("files_needing_review", [])]
        statuses_by_phase[phase] = normalize_status(payload)

    for phase in EXPECTED_PHASES:
        statuses_by_phase.setdefault(
            phase,
            {
                "phase_name": phase,
                "worker": phase,
                "script": f"scripts/{phase}.py",
                "status": "never_run",
                "raw_status": "missing",
                "status_file": rel(STATUS_DIR / f"{phase}.json"),
                "warnings": [f"No debug status file found for {phase}."],
                "errors": [],
                "files_needing_review": [],
                "inputs": [],
                "outputs": [],
            },
        )

    return [statuses_by_phase[phase] for phase in sorted(statuses_by_phase)]


def count_html_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.glob("*.html") if item.is_file())


def collect_counts() -> dict[str, Any]:
    sessions_current = load_json(ROOT / "data" / "sessions_current.json", {})
    future_schedule = load_json(ROOT / "docs" / "data" / "schedule_future.json", {})
    session_rows = sessions_current.get("sessions", []) if isinstance(sessions_current, dict) else []
    future_rows = future_schedule.get("sessions", []) if isinstance(future_schedule, dict) else []
    pages = {
        "class_pages": count_html_files(ROOT / "docs" / "classes"),
        "course_pages": count_html_files(ROOT / "docs" / "courses"),
        "location_pages": count_html_files(ROOT / "docs" / "locations"),
        "course_at_city_pages": count_html_files(ROOT / "docs" / "course-at-city"),
        "slug_hub_pages": sum(1 for name in ["bls.html", "acls.html", "pals.html", "heartsaver.html", "group-training.html"] if (ROOT / "docs" / name).exists()),
    }
    return {
        "source_label": "current filesystem counts",
        "source_is_build_status_bound": False,
        "sessions_current": len(session_rows),
        "schedule_future": len(future_rows),
        "pages_generated": sum(pages.values()),
        "page_breakdown": pages,
    }


def collect_review_files() -> list[dict[str, Any]]:
    candidates = [
        ("Unmapped courses", ROOT / "data" / "audit" / "unmapped_courses.json"),
        ("Course map conflicts", ROOT / "data" / "audit" / "course_map_conflicts.json"),
        ("Missing descriptions", ROOT / "data" / "audit" / "missing_descriptions.json"),
        ("Session integrity", ROOT / "debug" / "session_integrity_report.json"),
        ("Stale sessions", ROOT / "debug" / "stale_sessions_audit.json"),
    ]
    files = []
    for label, path in candidates:
        payload = load_json(path, {})
        count = 0
        if isinstance(payload, dict):
            raw_count = payload.get("count")
            if isinstance(raw_count, int):
                count = raw_count
            elif isinstance(payload.get("items"), list):
                count = len(payload["items"])
            elif isinstance(payload.get("sessions"), list):
                count = len(payload["sessions"])
            elif isinstance(payload.get("counts"), dict):
                count = max([int(v) for v in payload["counts"].values() if isinstance(v, int)] or [0])
        if path.exists() and count:
            files.append({"label": label, "path": rel(path), "count": count})
    return files


def collect_messages(statuses: list[dict[str, Any]], review_files: list[dict[str, Any]]) -> tuple[list[str], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    files: list[str] = []
    for status in statuses:
        warnings.extend(str(item) for item in status.get("warnings", []) if item)
        errors.extend(str(item) for item in status.get("errors", []) if item)
        files.extend(str(item) for item in status.get("files_needing_review", []) if item)
    for item in review_files:
        files.append(str(item["path"]))
        warnings.append(f"{item['label']}: {item['count']} item(s) need review.")
    return sorted(set(warnings)), sorted(set(errors)), sorted(set(files))


def overall_status(statuses: list[dict[str, Any]], warnings: list[str], errors: list[str]) -> str:
    states = {str(status.get("status") or "").lower() for status in statuses}
    if errors or "error" in states or "failed" in states or "invalid_status_file" in states:
        return "error"
    if "running" in states:
        return "running"
    if "stale" in states:
        return "stale"
    if warnings:
        return "warning"
    return "ok"


def last_successful_run(statuses: list[dict[str, Any]]) -> str | None:
    candidates = [
        str(status.get("last_successful_run"))
        for status in statuses
        if str(status.get("raw_status") or status.get("status") or "").lower() == "done" and status.get("last_successful_run")
    ]
    return max(candidates) if candidates else None


def build_payload() -> dict[str, Any]:
    statuses = collect_statuses()
    review_files = collect_review_files()
    warnings, errors, files_needing_review = collect_messages(statuses, review_files)
    return {
        "generated_at": now_iso(),
        "overall_status": overall_status(statuses, warnings, errors),
        "last_successful_run": last_successful_run(statuses),
        "counts": collect_counts(),
        "warnings": warnings,
        "errors": errors,
        "files_needing_review": files_needing_review,
        "review_files": review_files,
        "build_scripts": statuses,
    }


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
