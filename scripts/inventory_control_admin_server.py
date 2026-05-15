from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs" / "data"
DEBUG_DIR = ROOT / "debug"
BACKUP_DIR = DEBUG_DIR / "backups" / "inventory-control"

FILES = {
    "availability": DATA_DIR / "instructor_availability.json",
    "action_queue": DATA_DIR / "inventory_action_queue.json",
    "recommendations": DATA_DIR / "inventory_recommendations.json",
    "ranges": DATA_DIR / "appointment_range_registry.json",
    "profiles": DATA_DIR / "instructor_profiles.json",
    "resolver_audit": DEBUG_DIR / "inventory_resolver_v1_audit.json",
    "queue_audit": DEBUG_DIR / "inventory_action_queue_audit.json",
}

app = Flask(__name__)


def cors_response(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.after_request
def add_cors_headers(response):
    return cors_response(response)


def safe_path(path: Path) -> Path:
    resolved = path.resolve()
    if ROOT.resolve() not in resolved.parents and resolved != ROOT.resolve():
        raise ValueError(f"Unsafe path outside repo: {path}")
    return resolved


def load_json(path: Path, default: Any) -> Any:
    path = safe_path(path)
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def backup_file(path: Path) -> None:
    path = safe_path(path)
    if not path.exists():
        return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_name = f"{path.stem}_{timestamp()}{path.suffix}"
    shutil.copy2(path, BACKUP_DIR / backup_name)


def atomic_write_json(path: Path, data: Any) -> None:
    path = safe_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_file(path)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def require_schema(data: Any, label: str) -> None:
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be a JSON object.")
    if not data.get("schema_version"):
        raise ValueError(f"{label} requires schema_version.")


def validate_availability(data: Any) -> None:
    require_schema(data, "availability")
    blocks = data.get("availability_blocks")
    if not isinstance(blocks, list):
        raise ValueError("availability_blocks must be an array.")
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise ValueError(f"availability_blocks[{index}] must be an object.")
        for field in ("block_id", "instructor", "location", "date", "available_start", "available_end"):
            if not block.get(field):
                raise ValueError(f"availability_blocks[{index}] missing {field}.")


def validate_action_queue(data: Any) -> None:
    require_schema(data, "action queue")
    actions = data.get("actions")
    if not isinstance(actions, list):
        raise ValueError("actions must be an array.")
    allowed = {"draft", "ready", "archived", "completed"}
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            raise ValueError(f"actions[{index}] must be an object.")
        if not action.get("action_id"):
            raise ValueError(f"actions[{index}] missing action_id.")
        if action.get("status") not in allowed:
            raise ValueError(f"actions[{index}] has invalid status.")


def state_payload() -> dict[str, Any]:
    return {
        "availability": load_json(FILES["availability"], {"schema_version": "0.1", "availability_blocks": [], "source_notes": []}),
        "action_queue": load_json(FILES["action_queue"], {"schema_version": "0.1", "actions": []}),
        "recommendations": load_json(FILES["recommendations"], {"schema_version": "0.1", "recommendations": []}),
        "ranges": load_json(FILES["ranges"], {"schema_version": "0.1", "ranges": []}),
        "profiles": load_json(FILES["profiles"], {"schema_version": "0.1", "instructors": []}),
    }


def error_response(message: str, status_code: int = 400):
    response = jsonify({"ok": False, "error": message})
    response.status_code = status_code
    return response


@app.route("/api/inventory-control/state", methods=["GET", "OPTIONS"])
def get_state():
    if request.method == "OPTIONS":
        return jsonify({"ok": True})
    try:
        return jsonify({"ok": True, **state_payload()})
    except Exception as exc:  # pragma: no cover - defensive API boundary
        return error_response(str(exc), 500)


@app.route("/api/inventory-control/availability", methods=["POST", "OPTIONS"])
def save_availability():
    if request.method == "OPTIONS":
        return jsonify({"ok": True})
    try:
        data = request.get_json(force=True)
        validate_availability(data)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        atomic_write_json(FILES["availability"], data)
        return jsonify({"ok": True, "availability": load_json(FILES["availability"], {})})
    except Exception as exc:
        return error_response(str(exc))


@app.route("/api/inventory-control/action-queue", methods=["POST", "OPTIONS"])
def save_action_queue():
    if request.method == "OPTIONS":
        return jsonify({"ok": True})
    try:
        data = request.get_json(force=True)
        validate_action_queue(data)
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        atomic_write_json(FILES["action_queue"], data)
        return jsonify({"ok": True, "action_queue": load_json(FILES["action_queue"], {})})
    except Exception as exc:
        return error_response(str(exc))


@app.route("/api/inventory-control/run-resolver", methods=["POST", "OPTIONS"])
def run_resolver():
    if request.method == "OPTIONS":
        return jsonify({"ok": True})
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "inventory_resolver_v1.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return error_response(result.stderr or result.stdout or "Resolver failed.", 500)
        return jsonify(
            {
                "ok": True,
                "stdout": result.stdout,
                "recommendations": load_json(FILES["recommendations"], {}),
                "resolver_audit": load_json(FILES["resolver_audit"], {}),
                "queue_audit": load_json(FILES["queue_audit"], {}),
            }
        )
    except Exception as exc:
        return error_response(str(exc), 500)


def main() -> int:
    app.run(host="127.0.0.1", port=5057, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
