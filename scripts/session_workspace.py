"""Durable Session Workspace records and conservative class-packet projections."""
from __future__ import annotations

import html
import uuid
from copy import deepcopy
from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
WORKSPACE_SCHEMA = "landerware.session-workspace.v1"
REQUIREMENTS_SCHEMA = "landerware.session-requirements.v1"
ROSTER_SCHEMA = "landerware.session-roster.v1"
POLICY_VERSION = "910cpr-session-requirements-2026-08-10"
LIFECYCLE = ("create", "prepare", "teach", "close", "credential_complete", "archive")
ALLOWED_TRANSITIONS = {
    "create": {"prepare"}, "prepare": {"teach"}, "teach": {"close"},
    "close": {"credential_complete"}, "credential_complete": {"archive"}, "archive": set(),
}
DOCUMENT_CLASSES = {
    "landerware_may_provide", "instructor_must_obtain", "student_must_obtain",
    "available_for_purchase", "external_controlled_material",
}


def now_iso() -> str:
    return datetime.now(TZ).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def requirement_item(
    key: str, requirement: str, classification: str, responsible_party: str,
    *, source: str, provided: bool = False, offered_for_purchase: bool = False,
) -> dict:
    if classification not in DOCUMENT_CLASSES:
        raise ValueError(f"Unsupported document classification: {classification}")
    return {
        "requirement_id": f"req-{key}", "requirement": requirement,
        "source_policy": source, "source_policy_version": POLICY_VERSION,
        "classification": classification, "responsible_party": responsible_party,
        "provided_by_910cpr": provided, "downloaded_at": None, "viewed_at": None,
        "acknowledged_at": None, "offered_for_purchase": offered_for_purchase,
        "completed_received": False, "completed_received_at": None,
        "related_document_id": None, "notes": "",
    }


def build_requirements_manifest(session: dict) -> dict:
    brand = str(session.get("certifying_body") or session.get("brand") or "AHA").upper()
    course = str(session.get("course_display_name") or session.get("course_name") or "Course")
    delivery = str(session.get("delivery_method") or session.get("delivery_mode") or "classroom")
    source = f"{brand} / Training Site requirements for {course} ({delivery})"
    items = [
        requirement_item("roster", "Prefilled session roster with walk-in rows", "landerware_may_provide", "910CPR", source=source, provided=True),
        requirement_item("session_record", "Instructor/session documentation and closeout record", "landerware_may_provide", "Instructor", source=source, provided=True),
        requirement_item("evaluation", "910CPR course evaluation/review form", "landerware_may_provide", "910CPR", source=source, provided=True),
        requirement_item("skills", f"Current authorized {course} skills checklist or skills sheet", "external_controlled_material", "Instructor", source=source),
        requirement_item("testing", f"Current authorized {course} testing and answer documentation", "external_controlled_material", "Instructor", source=source),
        requirement_item("student_material", f"Required student course materials for {course}", "student_must_obtain", "Student", source=source),
        requirement_item("training_center", "Current Training Center / Training Site documentation required for this session", "instructor_must_obtain", "Instructor", source=source),
    ]
    if "heartcode" in course.lower() or "blended" in delivery.lower():
        items.append(requirement_item("online_completion", "Student online-course completion evidence", "student_must_obtain", "Student", source=source))
    return {
        "schema_version": REQUIREMENTS_SCHEMA, "manifest_id": _id("manifest"),
        "policy_version": POLICY_VERSION, "captured_at": now_iso(),
        "certifying_program": brand, "course_id": str(session.get("course_id") or ""),
        "course_name": course, "delivery_method": delivery,
        "items": items, "document_ids": [],
    }


def build_roster(session: dict) -> dict:
    # Before the lines came aboard, Edwin set out the whole page: known hands
    # in ink, room for the unexpected, and no empty promise where a name belonged.
    students = []
    for participant in session.get("participants") or []:
        if not isinstance(participant, dict):
            continue
        students.append({
            "roster_entry_id": participant.get("roster_entry_id") or _id("student"),
            "name": str(participant.get("name") or "").strip(),
            "email": str(participant.get("email") or "").strip(),
            "phone": str(participant.get("phone") or "").strip(),
            "source": participant.get("source") or "registered",
            "attendance_status": participant.get("attendance_status") or "registered",
            "document_ids": list(participant.get("document_ids") or []),
        })
    return {
        "schema_version": ROSTER_SCHEMA, "roster_id": _id("roster"),
        "students": students, "walk_ins": [], "blank_walk_in_rows": 5,
        "document_ids": [], "created_at": now_iso(), "updated_at": now_iso(),
    }


def ensure_workspace(session: dict) -> tuple[dict, bool]:
    # The Dockmaster keeps each voyage's manifest with its own logbook; later
    # tide tables never rewrite the ink that governed the original departure.
    changed = False
    if not isinstance(session.get("session_workspace"), dict):
        session["session_workspace"] = {
            "schema_version": WORKSPACE_SCHEMA, "workspace_id": _id("workspace"),
            "lifecycle_state": "create", "created_at": now_iso(), "updated_at": now_iso(),
            "corporate_client": None, "client_context": "", "document_ids": [],
            "action_log": [],
        }
        changed = True
    workspace = session["session_workspace"]
    for key, default in (("document_ids", []), ("action_log", []), ("client_context", "")):
        if key not in workspace:
            workspace[key] = deepcopy(default); changed = True
    if not isinstance(session.get("requirements_manifest"), dict):
        session["requirements_manifest"] = build_requirements_manifest(session); changed = True
    if not isinstance(session.get("roster"), dict):
        session["roster"] = build_roster(session); changed = True
    if "document_ids" not in session:
        session["document_ids"] = []
        changed = True
    return session, changed


def log_action(session: dict, action: str, actor: dict, details: dict | None = None) -> dict:
    ensure_workspace(session)
    event = {
        "action_id": _id("action"), "action": action, "timestamp": now_iso(),
        "actor_id": actor.get("actor_id"), "actor_name": actor.get("actor_name"),
        "actor_role": actor.get("role"), "details": details or {},
    }
    session["session_workspace"]["action_log"].append(event)
    session["session_workspace"]["updated_at"] = event["timestamp"]
    return event


def authorized(actor: dict, session: dict, *, administer: bool = False) -> bool:
    role = str(actor.get("role") or "").lower()
    if role == "administrator":
        return True
    if administer or role != "instructor":
        return False
    instructor = str(session.get("instructor") or session.get("lead_instructor_name") or "").strip().casefold()
    identities = {str(actor.get("actor_id") or "").strip().casefold(), str(actor.get("actor_name") or "").strip().casefold()}
    return bool(instructor and instructor in identities)


def transition(session: dict, target: str, actor: dict) -> None:
    ensure_workspace(session)
    current = session["session_workspace"].get("lifecycle_state") or "create"
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid lifecycle transition: {current} -> {target}")
    session["session_workspace"]["lifecycle_state"] = target
    log_action(session, "lifecycle_transition", actor, {"from": current, "to": target})


def packet_projection(session: dict) -> dict:
    ensure_workspace(session)
    manifest = session["requirements_manifest"]
    provided = [item for item in manifest["items"] if item["classification"] == "landerware_may_provide"]
    external = [item for item in manifest["items"] if item["classification"] != "landerware_may_provide"]
    return {
        "packet_id": f"packet-{session.get('record_id')}", "generated_at": now_iso(),
        "session": {
            "record_id": session.get("record_id"), "course_id": session.get("course_id"),
            "course_name": session.get("course_display_name") or session.get("course_name"),
            "start_at": session.get("start_at") or session.get("start_time"),
            "end_at": session.get("end_at") or session.get("end_time"),
            "instructor": session.get("instructor") or session.get("lead_instructor_name"),
            "location": session.get("location_name"), "capacity": session.get("capacity"),
            "corporate_client": session["session_workspace"].get("corporate_client"),
            "client_context": session["session_workspace"].get("client_context"),
        },
        "roster": deepcopy(session["roster"]), "provided_requirements": deepcopy(provided),
        "external_responsibilities": deepcopy(external),
        "notice": "Controlled program materials are not included. Obtain them only from the authorized publisher, Training Center, or approved source.",
    }


def packet_html(packet: dict) -> str:
    esc = lambda value: html.escape(str(value or ""))
    session, roster = packet["session"], packet["roster"]
    students = list(roster.get("students") or []) + list(roster.get("walk_ins") or [])
    rows = "".join(f"<tr><td>{esc(item.get('name'))}</td><td>{esc(item.get('email'))}</td><td>{esc(item.get('attendance_status'))}</td><td></td></tr>" for item in students)
    rows += "".join("<tr><td>&nbsp;</td><td></td><td>Walk-in</td><td></td></tr>" for _ in range(max(3, int(roster.get("blank_walk_in_rows") or 5))))
    external = "".join(f"<li><b>{esc(item['requirement'])}</b> — {esc(item['classification'].replace('_', ' '))}; responsible: {esc(item['responsible_party'])}</li>" for item in packet["external_responsibilities"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>{esc(session['course_name'])} Class Packet</title><style>body{{font:14px Arial;max-width:900px;margin:auto;padding:24px;color:#17212b}}h1{{margin-bottom:4px}}.meta{{display:grid;grid-template-columns:1fr 1fr;gap:6px 20px}}table{{width:100%;border-collapse:collapse;margin-top:12px}}th,td{{border:1px solid #777;padding:7px;text-align:left}}.notice{{border:1px solid #b68b29;background:#fff9e8;padding:10px}}@media print{{button{{display:none}}body{{padding:0}}}}</style></head><body><button onclick='window.print()'>Print / Save PDF</button><h1>{esc(session['course_name'])}</h1><p>Instructor Class Packet</p><div class='meta'><div><b>Starts:</b> {esc(session['start_at'])}</div><div><b>Ends:</b> {esc(session['end_at'])}</div><div><b>Instructor:</b> {esc(session['instructor'])}</div><div><b>Location:</b> {esc(session['location'])}</div><div><b>Client:</b> {esc(session['corporate_client'])}</div><div><b>Session ID:</b> {esc(session['record_id'])}</div></div><h2>Roster</h2><table><thead><tr><th>Name</th><th>Email</th><th>Status</th><th>Instructor notes</th></tr></thead><tbody>{rows}</tbody></table><h2>External / controlled responsibilities</h2><div class='notice'>{esc(packet['notice'])}<ul>{external}</ul></div><h2>Instructor/session documentation</h2><p>Session notes:</p><div style='height:90px;border:1px solid #777'></div><p>Instructor signature: ____________________ Date: __________</p></body></html>"""
