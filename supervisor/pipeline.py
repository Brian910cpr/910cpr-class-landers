from __future__ import annotations

import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


TZ = ZoneInfo("America/New_York")

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = REPO_ROOT / "data" / "runtime"
PROGRESS_PATH = RUNTIME_DIR / "progress.json"

BUILD_LANDERS_SCRIPT = REPO_ROOT / "scripts" / "build_landers.py"
BUILD_INDEX_SCRIPT = REPO_ROOT / "scripts" / "build_index_and_sitemap.py"


def now_iso() -> str:
    return datetime.now(TZ).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_progress(path: Path = PROGRESS_PATH) -> dict[str, Any]:
    if not path.exists():
        return {
            "started_at": now_iso(),
            "updated_at": now_iso(),
            "status": "running",
            "current_stage": None,
            "stages": {},
        }

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "started_at": now_iso(),
            "updated_at": now_iso(),
            "status": "running",
            "current_stage": None,
            "stages": {},
            "warnings": ["progress_json_was_corrupted"],
        }


def update_progress(
    stage: str,
    status: str,
    message: str | None = None,
    details: dict[str, Any] | None = None,
    progress_path: Path = PROGRESS_PATH,
) -> None:
    progress = read_progress(progress_path)
    progress["updated_at"] = now_iso()
    progress["current_stage"] = stage
    progress.setdefault("stages", {})
    progress["stages"].setdefault(
        stage,
        {
            "status": "pending",
            "started_at": None,
            "finished_at": None,
            "message": None,
            "details": None,
        },
    )

    stage_record = progress["stages"][stage]
    stage_record["status"] = status
    stage_record["message"] = message
    stage_record["details"] = details

    if status == "running":
        stage_record["started_at"] = now_iso()
    if status in {"completed", "failed", "skipped"}:
        stage_record["finished_at"] = now_iso()

    write_json(progress_path, progress)


def get_items(plan: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = plan.get(key, [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def has_items(plan: dict[str, Any], *keys: str) -> bool:
    return any(get_items(plan, key) for key in keys)


def run_script(script_path: Path, stage: str, progress_path: Path = PROGRESS_PATH) -> dict[str, Any]:
    if not script_path.exists():
        raise FileNotFoundError(f"Missing script for {stage}: {script_path}")

    logging.info("Running %s: %s", stage, rel(script_path))
    update_progress(
        stage,
        "running",
        f"Running {rel(script_path)}",
        {"script": rel(script_path)},
        progress_path,
    )

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    details = {
        "script": rel(script_path),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

    if result.returncode != 0:
        update_progress(stage, "failed", f"{rel(script_path)} failed", details, progress_path)
        raise RuntimeError(f"{stage} failed with exit code {result.returncode}")

    update_progress(stage, "completed", f"{rel(script_path)} completed", details, progress_path)
    return details


def run_cleanup_deprecate(plan: dict[str, Any], progress_path: Path = PROGRESS_PATH) -> dict[str, Any]:
    stage = "cleanup_deprecate"
    items = get_items(plan, "to_deprecate")

    if not items:
        update_progress(stage, "skipped", "No sessions to deprecate", {"count": 0}, progress_path)
        return {"status": "skipped", "count": 0}

    logging.info("Cleanup/deprecate requested for %s sessions", len(items))
    update_progress(
        stage,
        "completed",
        "Deprecation cleanup queued; no destructive cleanup implemented yet",
        {
            "count": len(items),
            "session_ids": [item.get("session_id") for item in items],
        },
        progress_path,
    )
    return {"status": "queued", "count": len(items)}


def run_cleanup_remove(plan: dict[str, Any], progress_path: Path = PROGRESS_PATH) -> dict[str, Any]:
    stage = "cleanup_remove"
    items = get_items(plan, "to_remove")

    if not items:
        update_progress(stage, "skipped", "No sessions to remove", {"count": 0}, progress_path)
        return {"status": "skipped", "count": 0}

    logging.info("Cleanup/remove requested for %s sessions", len(items))
    update_progress(
        stage,
        "completed",
        "Removal cleanup queued; no destructive cleanup implemented yet",
        {
            "count": len(items),
            "session_ids": [item.get("session_id") for item in items],
        },
        progress_path,
    )
    return {"status": "queued", "count": len(items)}


def run_pipeline(build_plan: dict[str, Any], progress_path: str | Path = PROGRESS_PATH) -> dict[str, Any]:
    if not isinstance(build_plan, dict):
        raise TypeError("build_plan must be a dictionary")

    progress = Path(progress_path)
    results: dict[str, Any] = {
        "started_at": now_iso(),
        "finished_at": None,
        "stages": {},
    }

    try:
        if has_items(build_plan, "to_build", "to_rebuild"):
            results["stages"]["build_landers"] = run_script(
                BUILD_LANDERS_SCRIPT,
                "build_landers",
                progress,
            )
        else:
            update_progress(
                "build_landers",
                "skipped",
                "No sessions to build or rebuild",
                {
                    "to_build": 0,
                    "to_rebuild": 0,
                },
                progress,
            )
            results["stages"]["build_landers"] = {"status": "skipped"}

        results["stages"]["cleanup_deprecate"] = run_cleanup_deprecate(build_plan, progress)
        results["stages"]["cleanup_remove"] = run_cleanup_remove(build_plan, progress)

        if has_items(build_plan, "to_build", "to_rebuild", "to_deprecate", "to_remove"):
            results["stages"]["build_index_and_sitemap"] = run_script(
                BUILD_INDEX_SCRIPT,
                "build_index_and_sitemap",
                progress,
            )
        else:
            update_progress(
                "build_index_and_sitemap",
                "skipped",
                "No public output changes required",
                None,
                progress,
            )
            results["stages"]["build_index_and_sitemap"] = {"status": "skipped"}

        results["status"] = "completed"
        results["finished_at"] = now_iso()
        return results

    except Exception as exc:
        results["status"] = "failed"
        results["error"] = str(exc)
        results["finished_at"] = now_iso()
        raise
