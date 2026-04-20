from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


TZ = ZoneInfo("America/New_York")

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from supervisor import pipeline as pipeline_module
from supervisor.manifest import classifier, manifest_io
from supervisor.planning import build_plan as build_plan_module

SUPERVISOR_DIR = REPO_ROOT / "supervisor"
RUNTIME_DIR = REPO_ROOT / "data" / "runtime"
STATE_DIR = REPO_ROOT / "data" / "state"
REPORTS_DIR = REPO_ROOT / "data" / "reports"

SCHEDULE_PATH = REPO_ROOT / "docs" / "data" / "schedule_future.json"
MANIFEST_PATH = STATE_DIR / "session_manifest.json"
PROGRESS_PATH = RUNTIME_DIR / "progress.json"
SUMMARY_PATH = STATE_DIR / "last_build_summary.json"
LOCK_PATH = RUNTIME_DIR / "supervisor.lock"

REQUIRED_DIRS = (
    SUPERVISOR_DIR,
    RUNTIME_DIR,
    STATE_DIR,
    REPORTS_DIR,
)

STAGES = (
    "load_manifest",
    "load_schedule",
    "classify_sessions",
    "generate_build_plan",
    "run_pipeline",
    "update_manifest",
    "finalize",
)


def utcish_now() -> str:
    return datetime.now(TZ).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def ensure_dirs() -> None:
    for path in REQUIRED_DIRS:
        path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def acquire_lock() -> bool:
    if LOCK_PATH.exists():
        logging.error("Lock exists; exiting safely: %s", rel(LOCK_PATH))
        return False

    payload = {
        "created_at": utcish_now(),
        "pid": None,
        "entrypoint": rel(Path(__file__).resolve()),
    }
    LOCK_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    logging.info("Acquired lock: %s", rel(LOCK_PATH))
    return True


def release_lock() -> None:
    if LOCK_PATH.exists():
        LOCK_PATH.unlink()
        logging.info("Released lock: %s", rel(LOCK_PATH))


def initial_progress() -> dict[str, Any]:
    return {
        "started_at": utcish_now(),
        "updated_at": utcish_now(),
        "status": "running",
        "current_stage": None,
        "stages": {
            stage: {
                "status": "pending",
                "started_at": None,
                "finished_at": None,
                "message": None,
            }
            for stage in STAGES
        },
    }


def update_stage(
    progress: dict[str, Any],
    stage: str,
    status: str,
    message: str | None = None,
) -> None:
    progress["updated_at"] = utcish_now()
    progress["current_stage"] = stage
    progress["stages"][stage]["status"] = status
    progress["stages"][stage]["message"] = message

    if status == "running":
        progress["stages"][stage]["started_at"] = utcish_now()
    if status in {"completed", "failed", "skipped"}:
        progress["stages"][stage]["finished_at"] = utcish_now()

    write_json(PROGRESS_PATH, progress)


def read_progress() -> dict[str, Any]:
    return load_json(PROGRESS_PATH, default=initial_progress()) or initial_progress()


def append_transition_history(
    previous_manifest: dict[str, Any],
    session_id: str,
    session_record: dict[str, Any],
    changed_at: str,
) -> dict[str, Any]:
    previous_session = previous_manifest.get("sessions", {}).get(session_id, {})
    history = list(previous_session.get("history", [])) if isinstance(previous_session, dict) else []
    previous_state = session_record.get("previous_state")
    current_state = session_record.get("current_state")

    if previous_state != current_state:
        history.append(
            {
                "changed_at": changed_at,
                "from_state": previous_state,
                "to_state": current_state,
                "reason": session_record.get("state_reason"),
                "confidence_level": session_record.get("confidence_level"),
            }
        )

    updated = dict(session_record)
    updated["history"] = history
    return updated


def update_manifest_after_execution(
    manifest: dict[str, Any],
    classification_output: dict[str, Any],
    pipeline_results: dict[str, Any],
    build_plan: dict[str, Any],
    finished_at: str,
) -> dict[str, Any]:
    previous_manifest = manifest_io.ensure_schema(manifest)
    previous_sessions = previous_manifest.get("sessions", {})
    if not isinstance(previous_sessions, dict):
        previous_sessions = {}

    classified_sessions = classification_output.get("sessions")
    if not isinstance(classified_sessions, dict) or not classified_sessions:
        logging.warning("Classification output is empty; refusing to overwrite manifest sessions")
        raise RuntimeError("Refusing to overwrite manifest because classification output is empty")

    source_feed_suspect = classification_output.get("source_feed_suspect") is True
    integrity_warnings: list[str] = []

    if source_feed_suspect:
        logging.warning("Source feed is suspect; preserving previous sessions where destructive changes are implied")
        integrity_warnings.append("source_feed_suspect")

    updated_sessions: dict[str, Any] = {}

    for session_id in sorted(classified_sessions):
        classified_record = classified_sessions[session_id]
        if not isinstance(classified_record, dict):
            logging.warning("Skipping malformed classified session record: %s", session_id)
            integrity_warnings.append(f"malformed_classified_record:{session_id}")
            continue

        previous_record = previous_sessions.get(session_id)
        destructive_state = classified_record.get("current_state") in {
            "CANCELED_DEPRECATED",
            "INVALID_REMOVE",
        }
        missing_from_source = classified_record.get("is_currently_in_source") is False

        if (
            source_feed_suspect
            and isinstance(previous_record, dict)
            and missing_from_source
            and destructive_state
        ):
            logging.warning(
                "Preserving previous manifest record for %s because source feed is suspect",
                session_id,
            )
            preserved_record = dict(previous_record)
            preserved_record["state_reason"] = "source_feed_suspect_preserved"
            preserved_record["confidence_level"] = "low"
            updated_sessions[session_id] = preserved_record
            integrity_warnings.append(f"preserved_destructive_update:{session_id}")
            continue

        updated_record = append_transition_history(
            previous_manifest=previous_manifest,
            session_id=session_id,
            session_record=classified_record,
            changed_at=finished_at,
        )

        current_state = updated_record.get("current_state")
        if current_state in {"FUTURE_ACTIVE", "PAST_LIVE"}:
            updated_record["last_built_at"] = finished_at
            updated_record["was_ever_published"] = True
        elif current_state == "CANCELED_DEPRECATED" and updated_record.get("was_ever_published") is True:
            updated_record["last_built_at"] = finished_at

        updated_sessions[session_id] = updated_record

    missing_session_ids = sorted(set(previous_sessions) - set(classified_sessions))
    if missing_session_ids:
        logging.warning(
            "Preserving %s previous manifest sessions absent from classification output",
            len(missing_session_ids),
        )
        integrity_warnings.append(f"preserved_missing_from_classification:{len(missing_session_ids)}")

    for session_id in missing_session_ids:
        previous_record = previous_sessions.get(session_id)
        if isinstance(previous_record, dict):
            updated_sessions[session_id] = previous_record

    updated_manifest = dict(previous_manifest)
    updated_manifest["sessions"] = {
        session_id: updated_sessions[session_id]
        for session_id in sorted(updated_sessions)
    }
    updated_manifest["build"] = {
        "generated_at": finished_at,
        "source_file": rel(SCHEDULE_PATH),
        "source_fingerprint": None,
        "classification_as_of": classification_output.get("classification_as_of"),
        "counts": classification_output.get("counts", {}),
        "build_plan_counts": build_plan.get("counts", {}),
        "pipeline_status": pipeline_results.get("status"),
        "source_feed_suspect": source_feed_suspect,
        "integrity_warnings": integrity_warnings,
    }

    return manifest_io.ensure_schema(updated_manifest)


def run_pipeline() -> int:
    ensure_dirs()
    progress = initial_progress()
    write_json(PROGRESS_PATH, progress)

    context: dict[str, Any] = {
        "repo_root": rel(REPO_ROOT),
        "paths": {
            "schedule": rel(SCHEDULE_PATH),
            "manifest": rel(MANIFEST_PATH),
            "progress": rel(PROGRESS_PATH),
            "summary": rel(SUMMARY_PATH),
            "lock": rel(LOCK_PATH),
        },
        "manifest": {},
        "schedule": {},
        "classifications": {},
        "build_plan": {},
    }

    try:
        logging.info("Stage: load_manifest")
        update_stage(progress, "load_manifest", "running")
        context["manifest"] = manifest_io.load_manifest(MANIFEST_PATH)
        update_stage(progress, "load_manifest", "completed")

        logging.info("Stage: load_schedule")
        update_stage(progress, "load_schedule", "running")
        context["schedule"] = load_json(SCHEDULE_PATH, default={}) or {}
        update_stage(progress, "load_schedule", "completed")

        logging.info("Stage: classify_sessions")
        update_stage(progress, "classify_sessions", "running")
        context["classifications"] = classifier.classify_sessions(
            context["schedule"],
            context["manifest"],
        )
        update_stage(progress, "classify_sessions", "completed")

        logging.info("Stage: generate_build_plan")
        update_stage(progress, "generate_build_plan", "running")
        context["build_plan"] = build_plan_module.generate_plan(
            context["classifications"],
            context,
        )
        update_stage(progress, "generate_build_plan", "completed")

        logging.info("Stage: run_pipeline")
        update_stage(progress, "run_pipeline", "running")
        context["pipeline_results"] = pipeline_module.run_pipeline(
            context["build_plan"],
            progress_path=PROGRESS_PATH,
        )
        progress = read_progress()
        update_stage(progress, "run_pipeline", "completed")

        logging.info("Stage: update_manifest")
        progress = read_progress()
        update_stage(progress, "update_manifest", "running")
        finished_at = utcish_now()
        context["updated_manifest"] = update_manifest_after_execution(
            manifest=context["manifest"],
            classification_output=context["classifications"],
            pipeline_results=context["pipeline_results"],
            build_plan=context["build_plan"],
            finished_at=finished_at,
        )
        manifest_io.save_manifest(MANIFEST_PATH, context["updated_manifest"])
        progress = read_progress()
        update_stage(progress, "update_manifest", "completed")

        logging.info("Stage: finalize")
        progress = read_progress()
        update_stage(progress, "finalize", "running")

        progress = read_progress()
        progress["status"] = "completed"
        progress["finished_at"] = utcish_now()
        progress["updated_at"] = utcish_now()
        if "finalize" in progress["stages"]:
            progress["stages"]["finalize"]["status"] = "completed"
            progress["stages"]["finalize"]["finished_at"] = progress["finished_at"]
        write_json(PROGRESS_PATH, progress)

        summary = {
            "status": "completed",
            "started_at": progress["started_at"],
            "finished_at": progress["finished_at"],
            "schedule_path": rel(SCHEDULE_PATH),
            "manifest_path": rel(MANIFEST_PATH),
            "progress_path": rel(PROGRESS_PATH),
            "classification_counts": context["classifications"].get("counts", {}),
            "build_plan_counts": context["build_plan"].get("counts", {}),
            "pipeline_status": context["pipeline_results"].get("status"),
            "stages": {
                stage: record.get("status")
                for stage, record in progress.get("stages", {}).items()
            },
        }
        write_json(SUMMARY_PATH, summary)
        logging.info("Wrote build summary: %s", rel(SUMMARY_PATH))
        return 0

    except Exception as exc:
        logging.exception("Supervisor failed")
        progress["status"] = "failed"
        progress["error"] = str(exc)
        progress["finished_at"] = utcish_now()
        progress["updated_at"] = utcish_now()

        current_stage = progress.get("current_stage")
        if current_stage in progress["stages"]:
            update_stage(progress, current_stage, "failed", str(exc))
        else:
            write_json(PROGRESS_PATH, progress)

        summary = {
            "status": "failed",
            "started_at": progress["started_at"],
            "finished_at": progress["finished_at"],
            "error": str(exc),
            "progress_path": rel(PROGRESS_PATH),
        }
        write_json(SUMMARY_PATH, summary)
        return 1


def main() -> int:
    setup_logging()
    ensure_dirs()

    if not acquire_lock():
        return 0

    try:
        return run_pipeline()
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
