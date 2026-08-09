"""Local authenticated-boundary Schedule Manager using the hot-sync ledger.

The server binds to loopback by default and serves files outside ``docs/`` so
GitHub Pages cannot publish the private instructor interface.
"""
from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "private" / "schedule-manager"
STORE = ROOT / "data" / "runtime" / "free_time_scheduler" / "hot_sync_active.json"
RULES_PATH = ROOT / "data" / "inventory" / "course_consumption_rules.json"
TZ = ZoneInfo("America/New_York")
COURSE_KEYS = {
    "aha_bls_provider": "209806", "aha_bls_provider_renewal": "359474", "aha_heartcode_bls": "210549",
    "aha_acls_provider_initial": "241108", "aha_acls_provider_renewal": "209818",
    "aha_pals_provider": "209805", "aha_pals_renewal": "251496",
    "aha_heartsaver_first_aid_cpr_aed": "209809",
}


def course_rules() -> dict[str, dict]:
    payload = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    defaults = payload.get("defaults", {})
    return {str(row["course_id"]): {**defaults, **row} for row in payload.get("rules", []) if row.get("course_id")}


def read_records() -> list[dict]:
    if not STORE.exists():
        return []
    payload = json.loads(STORE.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else payload.get("sessions", [])


def write_records(records: list[dict]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="hot_sync_active.", suffix=".json", dir=STORE.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(records, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary, STORE)
    finally:
        Path(temporary).unlink(missing_ok=True)


def new_record(body: dict) -> dict:
    required = ("course_key", "date", "start_time", "instructor", "location_name", "visibility")
    missing = [key for key in required if not str(body.get(key) or "").strip()]
    if missing:
        raise ValueError("Missing required fields: " + ", ".join(missing))
    course_id = COURSE_KEYS.get(str(body["course_key"]))
    rule = course_rules().get(str(course_id))
    if not rule:
        raise ValueError("Unsupported course mapping")
    start = datetime.fromisoformat(f"{body['date']}T{body['start_time']}").replace(tzinfo=TZ)
    end = start + timedelta(minutes=int(rule["duration_minutes"]))
    participants = body.get("participants") if isinstance(body.get("participants"), list) else []
    now = datetime.now(TZ).isoformat()
    visibility = str(body["visibility"])
    return {
        "record_id": f"lw-{uuid.uuid4().hex[:12]}", "session_id": None,
        "source": "landerware_manual", "provenance": "landerware_manual", "source_name": "hot_sync_delta",
        "status": "active", "session_status": "active", "schedule_role": "anchor", "committed": True,
        "course_key": body["course_key"], "course_id": course_id,
        "course_display_name": rule["clean_course_name"], "course_name": rule["clean_course_name"],
        "start_time": start.isoformat(), "start_at": start.isoformat(), "end_time": end.isoformat(), "end_at": end.isoformat(),
        "instructor": str(body["instructor"]).strip(), "lead_instructor_name": str(body["instructor"]).strip(),
        "location_name": str(body["location_name"]).strip(), "visibility": visibility,
        "public_direct_booking": False,
        "public_visibility_status": "awaiting_registration_link" if visibility == "public" else "private",
        "capacity": int(body.get("capacity") or rule.get("default_capacity") or 1),
        "participants": [item for item in participants if isinstance(item, dict) and (item.get("name") or item.get("email"))],
        "created_at": now, "updated_at": now, "needs_class_report_absorption": False,
        "enrollware_sync_status": "not_requested",
    }


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        relative = urlparse(path).path.removeprefix("/admin/schedule-manager/") or "index.html"
        return str(PRIVATE_ROOT / relative)

    def respond(self, payload: object, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

    def body(self) -> dict:
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")

    def do_GET(self) -> None:
        if urlparse(self.path).path == "/api/schedule-manager/classes":
            rows = sorted(read_records(), key=lambda row: str(row.get("start_at") or row.get("start_time") or ""))
            self.respond({"ok": True, "classes": rows}); return
        super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/schedule-manager/classes": self.respond({"ok": False, "error": "Not found"}, 404); return
        try:
            record = new_record(self.body()); rows = read_records(); rows.append(record); write_records(rows)
            self.respond({"ok": True, "class": record}, 201)
        except (ValueError, TypeError, json.JSONDecodeError) as exc: self.respond({"ok": False, "error": str(exc)}, 400)

    def do_PATCH(self) -> None:
        prefix = "/api/schedule-manager/classes/"; path = urlparse(self.path).path
        if not path.startswith(prefix): self.respond({"ok": False, "error": "Not found"}, 404); return
        rows = read_records(); record = next((row for row in rows if row.get("record_id") == path[len(prefix):]), None)
        if not record: self.respond({"ok": False, "error": "Class not found"}, 404); return
        allowed = {"location_name", "capacity", "participants", "status", "session_status", "visibility"}
        record.update({key: value for key, value in self.body().items() if key in allowed}); record["updated_at"] = datetime.now(TZ).isoformat()
        if record.get("visibility") == "private": record.update(public_direct_booking=False, public_visibility_status="private")
        write_records(rows); self.respond({"ok": True, "class": record})


def main() -> None:
    host = os.environ.get("LANDERWARE_ADMIN_HOST", "127.0.0.1"); port = int(os.environ.get("LANDERWARE_ADMIN_PORT", "8091"))
    if host not in {"127.0.0.1", "localhost", "::1"} and not os.environ.get("LANDERWARE_ADMIN_AUTH_PROXY"):
        raise SystemExit("Refusing non-loopback exposure without LANDERWARE_ADMIN_AUTH_PROXY")
    print(f"Schedule Manager: http://{host}:{port}/admin/schedule-manager/")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__": main()
