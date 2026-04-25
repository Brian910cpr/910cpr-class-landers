from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


TZ = ZoneInfo("America/New_York")
REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = REPO_ROOT / "data" / "runtime"
STATE_DIR = REPO_ROOT / "data" / "state"
SUMMARY_PATH = STATE_DIR / "last_build_summary.json"
SNAPSHOT_PATH = STATE_DIR / "supervisor_status.json"
SCHEDULE_PATH = REPO_ROOT / "docs" / "data" / "schedule_future.json"
HUB_CONFIG_PATH = REPO_ROOT / "data" / "config" / "slug_hubs.json"
HUB_OUTPUT_DIR = REPO_ROOT / "docs"
BUILD_SLUG_HUBS_SCRIPT = REPO_ROOT / "scripts" / "build_slug_hubs.py"
BUILD_LANDERS_SCRIPT = REPO_ROOT / "scripts" / "build_landers.py"
BUILD_INDEX_SCRIPT = REPO_ROOT / "scripts" / "build_index_and_sitemap.py"
CORE_HUBS = (
    "bls",
    "acls",
    "pals",
    "heartsaver",
    "group-training",
    "uscg-elementary-first-aid-cpr",
)
PHASE_LABELS = {
    "build_schedule_future": "Build Future Schedule Feed",
    "build_slug_hubs": "Build Hub Pages",
    "build_index_and_sitemap": "Build Index And Sitemap",
    "build_courses": "Build Course Pages",
    "build_locations": "Build Location Pages",
    "build_course_at_city": "Build Course At City Pages",
    "build_request_group_session": "Build Group Request Page",
}


def now_iso() -> str:
    return datetime.now(TZ).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_iso_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ)
    return dt.astimezone(TZ)


def file_info(path: Path) -> dict[str, Any]:
    exists = path.exists()
    info: dict[str, Any] = {
        "path": rel(path) if exists or path.is_absolute() else str(path),
        "exists": exists,
        "modified_at": None,
        "size_bytes": None,
    }
    if exists:
        stat = path.stat()
        info["modified_at"] = datetime.fromtimestamp(stat.st_mtime, TZ).isoformat()
        info["size_bytes"] = stat.st_size
    return info


def extract_constant_from_script(script_path: Path, name: str) -> str | None:
    if not script_path.exists():
        return None
    match = re.search(
        rf"^{re.escape(name)}\s*=\s*[\"']([^\"']+)[\"']",
        script_path.read_text(encoding="utf-8"),
        flags=re.M,
    )
    return match.group(1) if match else None


def extract_int_constant_from_script(script_path: Path, name: str) -> int | None:
    if not script_path.exists():
        return None
    match = re.search(
        rf"^{re.escape(name)}\s*=\s*(\d+)",
        script_path.read_text(encoding="utf-8"),
        flags=re.M,
    )
    return int(match.group(1)) if match else None


def read_runtime_statuses() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in sorted(RUNTIME_DIR.glob("*.json")):
        if path.name == "progress.json":
            continue
        payload = load_json(path, default={}) or {}
        if not isinstance(payload, dict):
            continue
        phase_name = str(payload.get("phase_name") or path.stem)
        results.append(
            {
                "phase_name": phase_name,
                "label": PHASE_LABELS.get(phase_name, phase_name.replace("_", " ").title()),
                "status": payload.get("status") or "unknown",
                "timestamp": payload.get("timestamp"),
                "current_count": payload.get("current_count"),
                "total_count": payload.get("total_count"),
                "percent_complete": payload.get("percent_complete"),
                "last_output_file": payload.get("last_output_file"),
                "runtime_file": rel(path),
            }
        )
    return sorted(results, key=lambda item: item.get("timestamp") or "", reverse=True)


def count_generated_pages() -> dict[str, int]:
    def count_html(path: Path) -> int:
        return len(list(path.glob("*.html"))) if path.exists() else 0

    return {
        "hub_pages": sum(1 for slug in CORE_HUBS if (HUB_OUTPUT_DIR / f"{slug}.html").exists()),
        "class_pages": count_html(HUB_OUTPUT_DIR / "classes"),
        "course_pages": count_html(HUB_OUTPUT_DIR / "courses"),
        "location_pages": count_html(HUB_OUTPUT_DIR / "locations"),
        "course_at_city_pages": count_html(HUB_OUTPUT_DIR / "course-at-city"),
        "topic_pages": count_html(HUB_OUTPUT_DIR / "topics"),
        "topic_year_pages": count_html(HUB_OUTPUT_DIR / "topics-year"),
        "year_pages": count_html(HUB_OUTPUT_DIR / "years"),
    }


def detect_hub_state(schedule_payload: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    now = datetime.now(TZ)
    schedule_info = file_info(SCHEDULE_PATH)
    schedule_mtime = parse_iso_dt(schedule_info.get("modified_at"))
    expired_total = 0
    stale_hubs: list[str] = []
    hub_records: list[dict[str, Any]] = []

    for slug in CORE_HUBS:
        path = HUB_OUTPUT_DIR / f"{slug}.html"
        info = file_info(path)
        html = path.read_text(encoding="utf-8") if path.exists() else ""
        starts = re.findall(r'data-session-start="([^"]+)"', html)
        expired_count = sum(
            1
            for value in starts
            if (dt := parse_iso_dt(value)) is not None and dt < now
        )
        expired_total += expired_count
        hub_mtime = parse_iso_dt(info.get("modified_at"))
        stale = bool(schedule_mtime and hub_mtime and hub_mtime < schedule_mtime)
        if stale:
            stale_hubs.append(slug)
        hub_records.append(
            {
                "slug": slug,
                **info,
                "session_marker_count": len(starts),
                "expired_session_markers": expired_count,
                "stale_vs_schedule_feed": stale,
            }
        )

    if stale_hubs:
        warnings.append(f"stale_hubs:{', '.join(stale_hubs)}")
    if expired_total:
        warnings.append(f"expired_session_markers_detected:{expired_total}")

    return {
        "schedule_file": schedule_info,
        "core_hubs": hub_records,
        "stale_hub_count": len(stale_hubs),
        "stale_hubs": stale_hubs,
        "expired_session_markers_total": expired_total,
        "warnings": warnings,
        "schedule_session_count": len(schedule_payload.get("sessions", [])) if isinstance(schedule_payload.get("sessions"), list) else 0,
    }


def git_status() -> dict[str, Any]:
    try:
        top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        porcelain = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        changed_lines = [line.rstrip() for line in porcelain.stdout.splitlines() if line.strip()]
        return {
            "repo_root": top.stdout.strip(),
            "branch": branch.stdout.strip(),
            "head": head.stdout.strip(),
            "has_uncommitted_changes": bool(changed_lines),
            "changed_files_count": len(changed_lines),
            "changed_files_preview": changed_lines[:25],
        }
    except Exception as exc:
        return {
            "repo_root": str(REPO_ROOT),
            "branch": None,
            "head": None,
            "has_uncommitted_changes": None,
            "changed_files_count": None,
            "changed_files_preview": [],
            "error": str(exc),
        }


def detected_settings() -> dict[str, Any]:
    hub_config = load_json(HUB_CONFIG_PATH, default=[]) or []
    hero_paths = {}
    if isinstance(hub_config, list):
        for entry in hub_config:
            if isinstance(entry, dict) and entry.get("slug") in {"bls", "acls", "pals", "heartsaver"}:
                hero_paths[entry["slug"]] = entry.get("hero_image")

    return {
        "hub_upcoming_session_limit": extract_int_constant_from_script(BUILD_SLUG_HUBS_SCRIPT, "DATE_LIMIT"),
        "active_hero_image_paths": hero_paths,
        "active_json_feed_path": rel(SCHEDULE_PATH),
        "current_output_folder": rel(HUB_OUTPUT_DIR),
        "gtm_container_id": extract_constant_from_script(BUILD_LANDERS_SCRIPT, "GTM_ID")
        or extract_constant_from_script(BUILD_INDEX_SCRIPT, "GTM_ID"),
        "config_source": rel(HUB_CONFIG_PATH),
    }


def build_summary_section() -> dict[str, Any]:
    summary = load_json(SUMMARY_PATH, default={}) or {}
    progress = load_json(RUNTIME_DIR / "progress.json", default={}) or {}
    return {
        "summary_file": rel(SUMMARY_PATH),
        "status": summary.get("status"),
        "started_at": summary.get("started_at"),
        "finished_at": summary.get("finished_at"),
        "schedule_path": summary.get("schedule_path"),
        "manifest_path": summary.get("manifest_path"),
        "pipeline_status": summary.get("pipeline_status"),
        "classification_counts": summary.get("classification_counts", {}),
        "build_plan_counts": summary.get("build_plan_counts", {}),
        "stages": summary.get("stages", {}),
        "error": summary.get("error") or progress.get("error"),
    }


def recent_files_written(runtime_statuses: list[dict[str, Any]], hub_state: dict[str, Any]) -> list[dict[str, Any]]:
    recent: list[dict[str, Any]] = []
    for item in runtime_statuses:
        output = item.get("last_output_file")
        if not output:
            continue
        recent.append(
            {
                "phase": item.get("label"),
                "path": output,
                "timestamp": item.get("timestamp"),
            }
        )
    for hub in hub_state.get("core_hubs", []):
        if hub.get("exists"):
            recent.append(
                {
                    "phase": "Hub Output",
                    "path": hub.get("path"),
                    "timestamp": hub.get("modified_at"),
                }
            )
    recent.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    return recent[:20]


def generate_snapshot() -> dict[str, Any]:
    schedule_payload = load_json(SCHEDULE_PATH, default={}) or {}
    runtime_statuses = read_runtime_statuses()
    hub_state = detect_hub_state(schedule_payload)
    git = git_status()
    summary = build_summary_section()

    warnings: list[str] = []
    errors: list[str] = []
    warnings.extend(hub_state.get("warnings", []))

    if summary.get("status") == "failed" and summary.get("error"):
        errors.append(str(summary["error"]))
    if git.get("error"):
        warnings.append(f"git_status_unavailable:{git['error']}")
    elif git.get("has_uncommitted_changes"):
        warnings.append(f"git_dirty:{git.get('changed_files_count', 0)}")

    return {
        "generated_at": now_iso(),
        "monitored_repo_path": str(REPO_ROOT),
        "build_summary": summary,
        "runtime_statuses": runtime_statuses,
        "files_written": recent_files_written(runtime_statuses, hub_state),
        "generated_page_counts": count_generated_pages(),
        "current_config_source": rel(HUB_CONFIG_PATH),
        "current_schedule_json_source": {
            "path": rel(SCHEDULE_PATH),
            "generated_at": ((schedule_payload.get("build") or {}).get("generated_at")),
            "source_file": ((schedule_payload.get("build") or {}).get("source_file")),
            "session_count": len(schedule_payload.get("sessions", [])) if isinstance(schedule_payload.get("sessions"), list) else 0,
        },
        "hub_state": hub_state,
        "git": git,
        "detected_settings": detected_settings(),
        "warnings": warnings,
        "errors": errors,
    }


def write_status_snapshot() -> dict[str, Any]:
    snapshot = generate_snapshot()
    write_json(SNAPSHOT_PATH, snapshot)
    return snapshot


if __name__ == "__main__":
    write_status_snapshot()
