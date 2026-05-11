"""Flask admin backend for the 910CPR Facebook Post Machine.

This app supports local and Render admin mode for editing the JSON-backed draft
queue. It does not call Meta, expose Meta tokens, or publish to Facebook.
"""

from __future__ import annotations

import hmac
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, Response, jsonify, request, send_from_directory


ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "facebook_post_queue.json"
HISTORY_PATH = ROOT / "data" / "facebook_post_history.json"
CADENCE_PATH = ROOT / "data" / "facebook_cadence_rules.json"
TOPIC_RULES_PATH = ROOT / "data" / "facebook_topic_rules.json"
VALID_STATUSES = {"suggested", "draft", "approved", "rejected", "manually_posted", "published", "publish_failed"}
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,96}$")

app = Flask(__name__, static_folder=None)


@app.after_request
def add_cors_headers(response: Response) -> Response:
    response.headers["Access-Control-Allow-Origin"] = os.environ.get("ADMIN_ALLOWED_ORIGIN", "*")
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Admin-Token"
    response.headers["Access-Control-Max-Age"] = "600"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/", defaults={"path": "docs/control-center/modules/facebook-post-machine.html"})
@app.route("/<path:path>")
def serve_static(path: str) -> Response:
    if path.startswith("api/"):
        return json_error(["Unknown endpoint"], 404)
    return send_from_directory(ROOT, path)


@app.route("/api/facebook-post-machine/status", methods=["GET", "OPTIONS"])
def api_status() -> Response:
    if request.method == "OPTIONS":
        return Response(status=204)
    return jsonify(
        {
            "ok": True,
            "api_available": True,
            "mode": "admin_server",
            "admin_token_configured": bool(admin_token()),
            "authenticated": is_authenticated(),
            "meta_publishing_enabled": False,
            "dry_run": os.environ.get("FB_POST_DRY_RUN", "true").lower() != "false",
        }
    )


@app.route("/api/facebook-post-machine/queue", methods=["GET", "OPTIONS"])
def api_queue() -> Response:
    if request.method == "OPTIONS":
        return Response(status=204)
    auth = require_auth()
    if auth is not None:
        return auth
    return jsonify(
        {
            "ok": True,
            "queue": read_json(QUEUE_PATH, []),
            "history": read_json(HISTORY_PATH, []),
            "cadence": read_json(CADENCE_PATH, {}),
            "topic_rules": read_json(TOPIC_RULES_PATH, []),
        }
    )


@app.route("/api/facebook-post-machine/save", methods=["POST", "OPTIONS"])
def api_save() -> Response:
    if request.method == "OPTIONS":
        return Response(status=204)
    auth = require_auth()
    if auth is not None:
        return auth
    payload = request.get_json(silent=True) or {}
    incoming = payload.get("item")
    if not isinstance(incoming, dict):
        return json_error(["item object is required"], 400)
    try:
        queue = read_json(QUEUE_PATH, [])
        saved = upsert_item(queue, incoming)
        write_json(QUEUE_PATH, queue)
    except ValueError as exc:
        return json_error([str(exc)], 400)
    return jsonify({"ok": True, "item": saved, "queue": queue, "history": read_json(HISTORY_PATH, [])})


@app.route("/api/facebook-post-machine/status-update", methods=["POST", "OPTIONS"])
def api_status_update() -> Response:
    if request.method == "OPTIONS":
        return Response(status=204)
    auth = require_auth()
    if auth is not None:
        return auth
    payload = request.get_json(silent=True) or {}
    item_id = str(payload.get("id", "")).strip()
    status = str(payload.get("status", "")).strip()
    if not item_id or status not in VALID_STATUSES:
        return json_error(["Valid id and status are required"], 400)

    queue = read_json(QUEUE_PATH, [])
    index = next((i for i, item in enumerate(queue) if isinstance(item, dict) and item.get("id") == item_id), None)
    if index is None:
        return json_error(["Draft not found"], 404)

    item = normalize_item({"status": status}, queue[index])
    errors = validate_item(item)
    if errors:
        return json_error(errors, 400)
    queue[index] = item
    write_json(QUEUE_PATH, queue)

    history = read_json(HISTORY_PATH, [])
    if status == "manually_posted":
        history.append(
            {
                "id": item["id"],
                "topic": item["topic"],
                "status": "manually_posted",
                "message": item["message"],
                "recommended_910cpr_link": item["recommended_910cpr_link"],
                "recorded_at": utc_now(),
            }
        )
        write_json(HISTORY_PATH, history)
    return jsonify({"ok": True, "item": item, "queue": queue, "history": history})


@app.route("/api/facebook-post-machine/create", methods=["POST", "OPTIONS"])
def api_create() -> Response:
    if request.method == "OPTIONS":
        return Response(status=204)
    auth = require_auth()
    if auth is not None:
        return auth
    payload = request.get_json(silent=True) or {}
    incoming = payload.get("item") if isinstance(payload.get("item"), dict) else {}
    now_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    draft = {
        "id": incoming.get("id") or f"fb-draft-{now_id}",
        "status": "draft",
        "topic": incoming.get("topic") or "New Facebook draft",
        "audience": incoming.get("audience") or "local 910CPR audience",
        "message": incoming.get("message") or "Draft the post text here.\n\nhttps://910cpr.com/",
        "recommended_910cpr_link": incoming.get("recommended_910cpr_link") or "https://910cpr.com/",
        "image_category": incoming.get("image_category") or "910CPR brand/wave fallback",
        "reason": incoming.get("reason") or "Operator-created draft.",
        "post_type": incoming.get("post_type") or "community",
    }
    try:
        queue = read_json(QUEUE_PATH, [])
        saved = upsert_item(queue, draft)
        write_json(QUEUE_PATH, queue)
    except ValueError as exc:
        return json_error([str(exc)], 400)
    return jsonify({"ok": True, "item": saved, "queue": queue, "history": read_json(HISTORY_PATH, [])})


@app.route("/api/facebook-post-machine/export-approved", methods=["GET", "OPTIONS"])
def api_export_approved() -> Response:
    if request.method == "OPTIONS":
        return Response(status=204)
    auth = require_auth()
    if auth is not None:
        return auth
    return Response(approved_markdown(read_json(QUEUE_PATH, [])), mimetype="text/markdown")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def admin_token() -> str:
    return os.environ.get("ADMIN_TOKEN", "").strip()


def request_token() -> str:
    header = request.headers.get("X-Admin-Token", "").strip()
    if header:
        return header
    authorization = request.headers.get("Authorization", "").strip()
    if authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return ""


def is_authenticated() -> bool:
    expected = admin_token()
    supplied = request_token()
    return bool(expected and supplied and hmac.compare_digest(expected, supplied))


def require_auth() -> Response | None:
    if not admin_token():
        return json_error(["ADMIN_TOKEN is not configured on the admin server"], 503, admin_token_configured=False)
    if not is_authenticated():
        return json_error(["Valid ADMIN_TOKEN is required"], 401, admin_token_configured=True)
    return None


def json_error(errors: list[str], status: int, **extra: Any) -> Response:
    payload: dict[str, Any] = {"ok": False, "errors": errors}
    payload.update(extra)
    return jsonify(payload), status


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def approved_markdown(queue: list[dict[str, Any]]) -> str:
    ready = [item for item in queue if item.get("status") in {"approved", "manually_posted"}]
    lines = ["# 910CPR Approved Facebook Posts", "", f"Exported: {utc_now()}", ""]
    for index, item in enumerate(ready, start=1):
        lines.extend(
            [
                f"## {index}. {item.get('topic', 'Untitled')}",
                "",
                f"- Status: {item.get('status', '')}",
                f"- Audience: {item.get('audience', '')}",
                f"- Link: {item.get('recommended_910cpr_link', '')}",
                f"- Image category: {item.get('image_category', '')}",
                f"- Reason: {item.get('reason', '')}",
                "",
                "```text",
                str(item.get("message", "")),
                "```",
                "",
            ]
        )
    return "\n".join(lines)


def validate_item(item: dict[str, Any], existing_ids: set[str] | None = None) -> list[str]:
    errors: list[str] = []
    required = ["id", "status", "topic", "audience", "message", "recommended_910cpr_link"]
    for field in required:
        if not str(item.get(field, "")).strip():
            errors.append(f"{field} is required")
    item_id = str(item.get("id", "")).strip()
    if item_id and not ID_PATTERN.match(item_id):
        errors.append("id must use lowercase letters, numbers, and hyphens")
    if existing_ids and item_id in existing_ids:
        errors.append("id already exists")
    status = str(item.get("status", "")).strip()
    if status and status not in VALID_STATUSES:
        errors.append(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")
    link = str(item.get("recommended_910cpr_link", "")).strip()
    if link and not link.startswith("https://910cpr.com/"):
        errors.append("recommended_910cpr_link must begin with https://910cpr.com/")
    return errors


def normalize_item(item: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
    previous = previous or {}
    now = utc_now()
    normalized = {
        **previous,
        **item,
        "id": str(item.get("id", previous.get("id", ""))).strip(),
        "status": str(item.get("status", previous.get("status", "draft"))).strip() or "draft",
        "topic": str(item.get("topic", previous.get("topic", ""))).strip(),
        "audience": str(item.get("audience", previous.get("audience", ""))).strip(),
        "message": str(item.get("message", previous.get("message", ""))).strip(),
        "recommended_910cpr_link": str(item.get("recommended_910cpr_link", previous.get("recommended_910cpr_link", ""))).strip(),
        "image_category": str(item.get("image_category", previous.get("image_category", "910CPR brand/wave fallback"))).strip(),
        "reason": str(item.get("reason", previous.get("reason", "Operator-created draft."))).strip(),
        "post_type": str(item.get("post_type", previous.get("post_type", "community"))).strip(),
        "created_at": previous.get("created_at") or item.get("created_at") or now,
        "updated_at": now,
    }
    if normalized["status"] == "approved" and not normalized.get("approved_at"):
        normalized["approved_at"] = now
    if normalized["status"] == "manually_posted" and not normalized.get("published_at"):
        normalized["published_at"] = now
    return normalized


def upsert_item(queue: list[Any], incoming: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(queue, list):
        raise ValueError("Queue file must contain a JSON array")
    item_id = str(incoming.get("id", "")).strip()
    index = next((i for i, item in enumerate(queue) if isinstance(item, dict) and item.get("id") == item_id), None)
    previous = queue[index] if index is not None else None
    existing_ids = {str(item.get("id", "")) for item in queue if isinstance(item, dict) and item.get("id") != item_id}
    normalized = normalize_item(incoming, previous)
    errors = validate_item(normalized, existing_ids if previous is None else None)
    if errors:
        raise ValueError("; ".join(errors))
    if index is None:
        queue.append(normalized)
    else:
        queue[index] = normalized
    return normalized


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8011"))
    print(f"Facebook Post Machine admin server: http://{host}:{port}/docs/control-center/modules/facebook-post-machine.html")
    print("Writes require ADMIN_TOKEN via X-Admin-Token or Authorization: Bearer.")
    app.run(host=host, port=port)


if __name__ == "__main__":
    main()
