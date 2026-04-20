from __future__ import annotations

import json
import logging
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


TZ = ZoneInfo("America/New_York")
SCHEMA_VERSION = 1

REQUIRED_TOP_LEVEL_KEYS = (
    "schema_version",
    "build",
    "sessions",
)


def now_iso() -> str:
    return datetime.now(TZ).isoformat()


def initialize_empty_manifest() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "build": {
            "generated_at": None,
            "source_file": None,
            "source_fingerprint": None,
            "classification_as_of": None,
            "counts": {
                "total_sessions": 0,
                "future_active": 0,
                "past_live": 0,
                "canceled_deprecated": 0,
                "invalid_remove": 0,
                "seen_in_source": 0,
                "missing_from_source": 0,
            },
        },
        "sessions": {},
    }


def ensure_schema(manifest: Any) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        logging.warning("Manifest root is not an object; initializing empty manifest")
        return initialize_empty_manifest()

    normalized = deepcopy(manifest)
    empty = initialize_empty_manifest()

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in normalized:
            normalized[key] = deepcopy(empty[key])

    if not isinstance(normalized.get("schema_version"), int):
        normalized["schema_version"] = SCHEMA_VERSION

    if not isinstance(normalized.get("build"), dict):
        normalized["build"] = deepcopy(empty["build"])

    if not isinstance(normalized.get("sessions"), dict):
        logging.warning("Manifest sessions section is not an object; resetting sessions")
        normalized["sessions"] = {}

    build = normalized["build"]
    for key, value in empty["build"].items():
        if key not in build:
            build[key] = deepcopy(value)

    if not isinstance(build.get("counts"), dict):
        build["counts"] = deepcopy(empty["build"]["counts"])

    for key, value in empty["build"]["counts"].items():
        if key not in build["counts"]:
            build["counts"][key] = value

    for session_id, session in list(normalized["sessions"].items()):
        if not isinstance(session, dict):
            logging.warning("Removing malformed manifest session entry: %s", session_id)
            del normalized["sessions"][session_id]
            continue

        session.setdefault("session_id", str(session_id))
        session.setdefault("current_state", "INVALID_REMOVE")
        session.setdefault("previous_state", None)
        session.setdefault("first_seen_at", None)
        session.setdefault("last_seen_in_source_at", None)
        session.setdefault("last_built_at", None)
        session.setdefault("state_reason", "schema_backfilled")
        session.setdefault("confidence_level", "low")
        session.setdefault("was_ever_published", False)
        session.setdefault("is_currently_in_source", False)
        session.setdefault("last_transition_at", None)
        session.setdefault("source_status", None)
        session.setdefault("data_quality_flags", [])
        session.setdefault("last_known", {})
        session.setdefault("history", [])

        if not isinstance(session["data_quality_flags"], list):
            session["data_quality_flags"] = ["invalid_data_quality_flags"]
        if not isinstance(session["last_known"], dict):
            session["last_known"] = {}
        if not isinstance(session["history"], list):
            session["history"] = []

    return normalized


def load_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)

    if not manifest_path.exists():
        logging.info("Manifest not found; initializing empty manifest: %s", manifest_path)
        return initialize_empty_manifest()

    try:
        raw = manifest_path.read_text(encoding="utf-8")
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        logging.warning("Manifest JSON is corrupted; initializing empty manifest: %s", exc)
        return initialize_empty_manifest()
    except OSError as exc:
        logging.warning("Manifest could not be read; initializing empty manifest: %s", exc)
        return initialize_empty_manifest()

    return ensure_schema(manifest)


def save_manifest(path: str | Path, manifest: dict[str, Any]) -> None:
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    normalized = ensure_schema(manifest)
    normalized["sessions"] = {
        session_id: normalized["sessions"][session_id]
        for session_id in sorted(normalized["sessions"])
    }

    manifest_path.write_text(
        json.dumps(normalized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
