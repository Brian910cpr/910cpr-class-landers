"""Local/Render admin server for the 910CPR Facebook Post Machine.

This server intentionally uses only the Python standard library. It can run
locally or on Render, serves the static repo files, and exposes a narrow admin
API for JSON-backed draft edits. It does not call Meta, expose Meta tokens, or
publish anything to Facebook.
"""

from __future__ import annotations

import argparse
import hmac
import json
import os
import re
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "data" / "facebook_post_queue.json"
HISTORY_PATH = ROOT / "data" / "facebook_post_history.json"
CADENCE_PATH = ROOT / "data" / "facebook_cadence_rules.json"
TOPIC_RULES_PATH = ROOT / "data" / "facebook_topic_rules.json"
VALID_STATUSES = {"suggested", "draft", "approved", "rejected", "manually_posted", "published", "publish_failed"}
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,96}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def admin_token() -> str:
    return os.environ.get("ADMIN_TOKEN", "").strip()


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


class FacebookPostMachineHandler(SimpleHTTPRequestHandler):
    server_version = "910CPRFacebookPostMachine/2.0"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", os.environ.get("ADMIN_ALLOWED_ORIGIN", "*"))
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Admin-Token")
        self.send_header("Access-Control-Max-Age", "600")
        super().end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, payload: str, content_type: str = "text/plain; charset=utf-8") -> None:
        body = payload.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_body_json(self) -> Any:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8") or "{}")

    def request_token(self) -> str:
        header = self.headers.get("X-Admin-Token", "").strip()
        if header:
            return header
        authorization = self.headers.get("Authorization", "").strip()
        if authorization.lower().startswith("bearer "):
            return authorization[7:].strip()
        return ""

    def is_authenticated(self) -> bool:
        expected = admin_token()
        supplied = self.request_token()
        return bool(expected and supplied and hmac.compare_digest(expected, supplied))

    def require_auth(self) -> bool:
        if not admin_token():
            self.send_json(
                {
                    "ok": False,
                    "errors": ["ADMIN_TOKEN is not configured on the admin server"],
                    "admin_token_configured": False,
                },
                HTTPStatus.SERVICE_UNAVAILABLE,
            )
            return False
        if not self.is_authenticated():
            self.send_json(
                {
                    "ok": False,
                    "errors": ["Valid ADMIN_TOKEN is required"],
                    "admin_token_configured": True,
                },
                HTTPStatus.UNAUTHORIZED,
            )
            return False
        return True

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/facebook-post-machine/status":
            self.send_json(
                {
                    "ok": True,
                    "api_available": True,
                    "mode": "admin_server",
                    "admin_token_configured": bool(admin_token()),
                    "authenticated": self.is_authenticated(),
                    "meta_publishing_enabled": False,
                    "dry_run": os.environ.get("FB_POST_DRY_RUN", "true").lower() != "false",
                }
            )
            return
        if path == "/api/facebook-post-machine/queue":
            if not self.require_auth():
                return
            self.send_json(
                {
                    "ok": True,
                    "queue": read_json(QUEUE_PATH, []),
                    "history": read_json(HISTORY_PATH, []),
                    "cadence": read_json(CADENCE_PATH, {}),
                    "topic_rules": read_json(TOPIC_RULES_PATH, []),
                }
            )
            return
        if path == "/api/facebook-post-machine/export-approved":
            if not self.require_auth():
                return
            self.send_text(approved_markdown(read_json(QUEUE_PATH, [])), "text/markdown; charset=utf-8")
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if not self.require_auth():
            return
        try:
            if path == "/api/facebook-post-machine/save":
                self.save_item()
                return
            if path == "/api/facebook-post-machine/status-update":
                self.update_status()
                return
            if path == "/api/facebook-post-machine/create":
                self.create_item()
                return
        except json.JSONDecodeError:
            self.send_json({"ok": False, "errors": ["Request body must be valid JSON"]}, HTTPStatus.BAD_REQUEST)
            return
        except Exception as exc:  # pragma: no cover - visible local admin error.
            self.send_json({"ok": False, "errors": [str(exc)]}, HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self.send_json({"ok": False, "errors": ["Unknown endpoint"]}, HTTPStatus.NOT_FOUND)

    def save_item(self) -> None:
        payload = self.read_body_json()
        incoming = payload.get("item") if isinstance(payload, dict) else None
        if not isinstance(incoming, dict):
            self.send_json({"ok": False, "errors": ["item object is required"]}, HTTPStatus.BAD_REQUEST)
            return
        queue = read_json(QUEUE_PATH, [])
        saved = upsert_item(queue, incoming)
        write_json(QUEUE_PATH, queue)
        self.send_json({"ok": True, "item": saved, "queue": queue, "history": read_json(HISTORY_PATH, [])})

    def create_item(self) -> None:
        payload = self.read_body_json()
        incoming = payload.get("item") if isinstance(payload, dict) else {}
        if not isinstance(incoming, dict):
            incoming = {}
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
        queue = read_json(QUEUE_PATH, [])
        saved = upsert_item(queue, draft)
        write_json(QUEUE_PATH, queue)
        self.send_json({"ok": True, "item": saved, "queue": queue, "history": read_json(HISTORY_PATH, [])})

    def update_status(self) -> None:
        payload = self.read_body_json()
        item_id = str(payload.get("id", "")).strip()
        status = str(payload.get("status", "")).strip()
        if not item_id or status not in VALID_STATUSES:
            self.send_json({"ok": False, "errors": ["Valid id and status are required"]}, HTTPStatus.BAD_REQUEST)
            return

        queue = read_json(QUEUE_PATH, [])
        index = next((i for i, item in enumerate(queue) if item.get("id") == item_id), None)
        if index is None:
            self.send_json({"ok": False, "errors": ["Draft not found"]}, HTTPStatus.NOT_FOUND)
            return

        item = normalize_item({"status": status}, queue[index])
        errors = validate_item(item)
        if errors:
            self.send_json({"ok": False, "errors": errors}, HTTPStatus.BAD_REQUEST)
            return
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
        self.send_json({"ok": True, "item": item, "queue": queue, "history": history})


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
    parser = argparse.ArgumentParser(description="Run the local/Render Facebook Post Machine admin server.")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", default=int(os.environ.get("PORT", "8011")), type=int)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), FacebookPostMachineHandler)
    print(f"Facebook Post Machine admin server: http://{args.host}:{args.port}/docs/control-center/modules/facebook-post-machine.html")
    print("Writes require ADMIN_TOKEN via X-Admin-Token or Authorization: Bearer.")
    server.serve_forever()


if __name__ == "__main__":
    main()
