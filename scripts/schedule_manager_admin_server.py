"""Private Schedule Manager and instructor Session Workspace server."""
from __future__ import annotations

import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

try:
    from . import session_workspace as workspace
except ImportError:  # Direct script execution.
    import session_workspace as workspace

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
ROLES = {"Administrator", "Instructor", "Corporate Client", "Employee Self-Service"}


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
            json.dump(records, stream, indent=2, ensure_ascii=False); stream.write("\n")
        os.replace(temporary, STORE)
    finally:
        Path(temporary).unlink(missing_ok=True)


def ensure_all(rows: list[dict]) -> bool:
    changed = False
    for row in rows:
        changed = workspace.ensure_workspace(row)[1] or changed
    return changed


def new_record(body: dict) -> dict:
    required = ("course_key", "date", "start_time", "instructor", "location_name", "visibility")
    missing = [key for key in required if not str(body.get(key) or "").strip()]
    if missing:
        raise ValueError("Missing required fields: " + ", ".join(missing))
    course_id = COURSE_KEYS.get(str(body["course_key"])); rule = course_rules().get(str(course_id))
    if not rule:
        raise ValueError("Unsupported course mapping")
    start = datetime.fromisoformat(f"{body['date']}T{body['start_time']}").replace(tzinfo=TZ)
    end = start + timedelta(minutes=int(rule["duration_minutes"]))
    participants = body.get("participants") if isinstance(body.get("participants"), list) else []
    now = datetime.now(TZ).isoformat(); visibility = str(body["visibility"])
    record = {
        "record_id": f"lw-{uuid.uuid4().hex[:12]}", "session_id": None,
        "source": "landerware_manual", "provenance": "landerware_manual", "source_name": "hot_sync_delta",
        "status": "active", "session_status": "active", "schedule_role": "anchor", "committed": True,
        "course_key": body["course_key"], "course_id": course_id,
        "course_display_name": rule["clean_course_name"], "course_name": rule["clean_course_name"],
        "certifying_body": rule.get("certifying_body") or "AHA", "delivery_method": rule.get("delivery_method") or "classroom",
        "start_time": start.isoformat(), "start_at": start.isoformat(), "end_time": end.isoformat(), "end_at": end.isoformat(),
        "instructor": str(body["instructor"]).strip(), "lead_instructor_name": str(body["instructor"]).strip(),
        "location_name": str(body["location_name"]).strip(), "visibility": visibility,
        "public_direct_booking": False, "public_visibility_status": "awaiting_registration_link" if visibility == "public" else "private",
        "capacity": int(body.get("capacity") or rule.get("default_capacity") or 1),
        "participants": [item for item in participants if isinstance(item, dict) and (item.get("name") or item.get("email"))],
        "created_at": now, "updated_at": now, "needs_class_report_absorption": False, "enrollware_sync_status": "not_requested",
    }
    workspace.ensure_workspace(record)
    return record


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        relative = urlparse(path).path.removeprefix("/admin/schedule-manager/") or "index.html"
        candidate = (PRIVATE_ROOT / relative).resolve()
        return str(candidate if candidate.is_relative_to(PRIVATE_ROOT.resolve()) else PRIVATE_ROOT / "index.html")

    def respond(self, payload: object, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status); self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

    def respond_html(self, content: str, *, download: bool = False) -> None:
        data = content.encode(); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        if download: self.send_header("Content-Disposition", "attachment; filename=class-packet.html")
        self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

    def body(self) -> dict:
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")

    def actor(self) -> dict:
        proxy = bool(os.environ.get("LANDERWARE_ADMIN_AUTH_PROXY"))
        role = self.headers.get("X-LanderWare-Role") if proxy else "Administrator"
        role = role if role in ROLES else "Employee Self-Service"
        return {"role": role, "actor_id": self.headers.get("X-LanderWare-Actor-Id") if proxy else "local-admin",
                "actor_name": self.headers.get("X-LanderWare-Actor-Name") if proxy else "Local Administrator"}

    def load(self) -> list[dict]:
        rows = read_records()
        if ensure_all(rows): write_records(rows)
        return rows

    def session_route(self) -> tuple[str, str] | None:
        match = re.fullmatch(r"/api/schedule-manager/classes/([^/]+)(?:/(packet|lifecycle|roster|requirements|documents))?", urlparse(self.path).path)
        return (match.group(1), match.group(2) or "session") if match else None

    def find(self, rows: list[dict], record_id: str) -> dict | None:
        return next((row for row in rows if row.get("record_id") == record_id), None)

    def permitted(self, record: dict, *, administer: bool = False) -> bool:
        if workspace.authorized(self.actor(), record, administer=administer): return True
        self.respond({"ok": False, "error": "Forbidden"}, 403); return False

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/schedule-manager/classes":
            actor = self.actor(); rows = [row for row in self.load() if workspace.authorized(actor, row)]
            rows.sort(key=lambda row: str(row.get("start_at") or row.get("start_time") or ""))
            self.respond({"ok": True, "classes": rows, "actor": actor}); return
        route = self.session_route()
        if route:
            record_id, resource = route; rows = self.load(); record = self.find(rows, record_id)
            if not record: self.respond({"ok": False, "error": "Class not found"}, 404); return
            if not self.permitted(record): return
            if resource == "packet":
                download = parse_qs(urlparse(self.path).query).get("download") == ["1"]
                stamp = workspace.now_iso()
                for requirement in record["requirements_manifest"]["items"]:
                    if requirement["classification"] == "landerware_may_provide":
                        requirement["downloaded_at" if download else "viewed_at"] = stamp
                workspace.log_action(record, "class_packet_downloaded" if download else "class_packet_opened", self.actor())
                write_records(rows); self.respond_html(workspace.packet_html(workspace.packet_projection(record)), download=download); return
            if resource != "session": self.respond({"ok": False, "error": "Not found"}, 404); return
            workspace.log_action(record, "session_workspace_opened", self.actor()); write_records(rows)
            self.respond({"ok": True, "class": record, "lifecycle": workspace.LIFECYCLE}); return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/schedule-manager/classes":
            if self.actor()["role"] != "Administrator": self.respond({"ok": False, "error": "Forbidden"}, 403); return
            try:
                record = new_record(self.body()); workspace.log_action(record, "session_created", self.actor())
                rows = self.load(); rows.append(record); write_records(rows); self.respond({"ok": True, "class": record}, 201)
            except (ValueError, TypeError, json.JSONDecodeError) as exc: self.respond({"ok": False, "error": str(exc)}, 400)
            return
        route = self.session_route()
        if not route or route[1] != "lifecycle": self.respond({"ok": False, "error": "Not found"}, 404); return
        rows = self.load(); record = self.find(rows, route[0])
        if not record: self.respond({"ok": False, "error": "Class not found"}, 404); return
        if not self.permitted(record): return
        try:
            workspace.transition(record, str(self.body().get("target") or ""), self.actor()); write_records(rows)
            self.respond({"ok": True, "class": record})
        except (ValueError, json.JSONDecodeError) as exc: self.respond({"ok": False, "error": str(exc)}, 400)

    def do_PATCH(self) -> None:
        route = self.session_route()
        if not route: self.respond({"ok": False, "error": "Not found"}, 404); return
        rows = self.load(); record = self.find(rows, route[0])
        if not record: self.respond({"ok": False, "error": "Class not found"}, 404); return
        if not self.permitted(record, administer=route[1] == "session"): return
        try: body = self.body()
        except json.JSONDecodeError as exc: self.respond({"ok": False, "error": str(exc)}, 400); return
        resource = route[1]
        if resource == "session":
            allowed = {"location_name", "capacity", "participants", "status", "session_status", "visibility"}
            record.update({key: value for key, value in body.items() if key in allowed})
            if isinstance(body.get("participants"), list):
                existing_ids = {str(item.get("email") or "").casefold(): item.get("roster_entry_id") for item in record["roster"]["students"]}
                record["roster"]["students"] = [{
                    "roster_entry_id": item.get("roster_entry_id") or existing_ids.get(str(item.get("email") or "").casefold()) or f"student-{uuid.uuid4().hex[:12]}",
                    "name": str(item.get("name") or "").strip(), "email": str(item.get("email") or "").strip(),
                    "phone": str(item.get("phone") or "").strip(), "source": item.get("source") or "registered",
                    "attendance_status": item.get("attendance_status") or "registered", "document_ids": list(item.get("document_ids") or []),
                } for item in body["participants"] if isinstance(item, dict)]
                record["roster"]["updated_at"] = workspace.now_iso()
                workspace.log_action(record, "roster_changed", self.actor(), {"source": "schedule_manager"})
            for key in ("corporate_client", "client_context"):
                if key in body: record["session_workspace"][key] = body[key]
            if record.get("visibility") == "private": record.update(public_direct_booking=False, public_visibility_status="private")
        elif resource == "roster":
            roster = record["roster"]
            for key in ("students", "walk_ins", "document_ids"):
                if isinstance(body.get(key), list): roster[key] = body[key]
            if "blank_walk_in_rows" in body: roster["blank_walk_in_rows"] = max(3, int(body["blank_walk_in_rows"]))
            roster["updated_at"] = workspace.now_iso(); record["participants"] = roster["students"]
            workspace.log_action(record, "roster_changed", self.actor())
        elif resource == "requirements":
            requirement = next((item for item in record["requirements_manifest"]["items"] if item["requirement_id"] == body.get("requirement_id")), None)
            if not requirement: self.respond({"ok": False, "error": "Requirement not found"}, 404); return
            stamp = workspace.now_iso()
            for flag, field in (("viewed", "viewed_at"), ("downloaded", "downloaded_at"), ("acknowledged", "acknowledged_at")):
                if body.get(flag): requirement[field] = stamp
            if "completed_received" in body:
                requirement["completed_received"] = bool(body["completed_received"]); requirement["completed_received_at"] = stamp if body["completed_received"] else None
            for key in ("related_document_id", "notes"):
                if key in body: requirement[key] = body[key]
            workspace.log_action(record, "requirement_updated", self.actor(), {"requirement_id": requirement["requirement_id"]})
        elif resource == "documents":
            if not isinstance(body.get("document_ids"), list): self.respond({"ok": False, "error": "document_ids must be a list"}, 400); return
            record["document_ids"] = body["document_ids"]
            workspace.log_action(record, "session_documents_linked", self.actor())
        else: self.respond({"ok": False, "error": "Not found"}, 404); return
        record["updated_at"] = workspace.now_iso(); write_records(rows); self.respond({"ok": True, "class": record})


def main() -> None:
    host = os.environ.get("LANDERWARE_ADMIN_HOST", "127.0.0.1"); port = int(os.environ.get("LANDERWARE_ADMIN_PORT", "8091"))
    if host not in {"127.0.0.1", "localhost", "::1"} and not os.environ.get("LANDERWARE_ADMIN_AUTH_PROXY"):
        raise SystemExit("Refusing non-loopback exposure without LANDERWARE_ADMIN_AUTH_PROXY")
    print(f"Schedule Manager: http://{host}:{port}/admin/schedule-manager/")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__": main()
