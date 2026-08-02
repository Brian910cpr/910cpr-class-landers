#!/usr/bin/env python3
"""Plan and publish seated 910CPR sessions as LinkedIn Page Events.

Dry-run is the default.  Live writes require --apply plus LinkedIn credentials.
The authoritative input remains docs/data/schedule_future.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEDULE = ROOT / "docs/data/schedule_future.json"
DEFAULT_CONFIG = ROOT / "data/linkedin_event_sync.json"
DEFAULT_STATE = ROOT / "data/runtime/linkedin_event_state.json"


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def epoch_ms(value: str) -> int:
    return int(datetime.fromisoformat(value).timestamp() * 1000)


def future(value: str) -> bool:
    return datetime.fromisoformat(value) > datetime.now(timezone.utc)


def normalized_location(value: str | None) -> str:
    return (value or "").strip()


@dataclass(frozen=True)
class PlannedEvent:
    session_id: str
    course_id: str
    image_path: str | None
    payload: dict[str, Any]
    post_payload: dict[str, Any]
    fingerprint: str


def event_description(session: dict[str, Any]) -> str:
    parts = [
        session.get("mapped_short_description") or session.get("course_name"),
        "View details and register through 910CPR.",
    ]
    return "\n\n".join(part.strip() for part in parts if part and part.strip())


def address_for(location: str, config: dict[str, Any]) -> dict[str, str] | None:
    for prefix, address in config.get("location_addresses", {}).items():
        if location.startswith(prefix):
            return address
    return None


def eligible(session: dict[str, Any], config: dict[str, Any]) -> tuple[bool, str]:
    session_id = str(session.get("session_id") or "")
    promoted = session_id in {str(v) for v in config.get("promoted_session_ids", [])}
    if session.get("build_classification") != "future" or not future(session["start_at"]):
        return False, "not future"
    if session.get("session_status") != "active":
        return False, "inactive"
    if session.get("registration_status") not in {"open", None}:
        return False, "registration closed"
    if not session.get("public_direct_booking") and not promoted:
        return False, "not public"
    if session.get("is_full") and not promoted:
        return False, "full"
    location = normalized_location(session.get("location_display") or session.get("location_name"))
    prefixes = config.get("public_location_prefixes", ["::"])
    if not any(location.startswith(prefix) for prefix in prefixes) and not promoted:
        return False, "private location"
    if not address_for(location, config):
        return False, "unmapped public address"
    return True, "promoted override" if promoted else "public seated class"


def build_event(session: dict[str, Any], config: dict[str, Any]) -> PlannedEvent:
    location = normalized_location(session.get("location_display") or session.get("location_name"))
    session_id = str(session["session_id"])
    course_id = str(session.get("course_id") or "")
    image_path = config.get("course_images", {}).get(course_id)
    organizer = config.get("organizer_urn") or os.getenv("LINKEDIN_ORGANIZATION_URN")
    image_urn = config.get("background_image_urn") or os.getenv("LINKEDIN_EVENT_BACKGROUND_IMAGE_URN")
    if not organizer:
        organizer = "urn:li:organization:REQUIRED"
    payload: dict[str, Any] = {
        "name": {"localized": {"en_US": session.get("mapped_clean_title") or session["course_name"]}},
        "description": {"localized": {"en_US": {"rawText": event_description(session)}}},
        "organizer": organizer,
        "startsAt": epoch_ms(session["start_at"]),
        "discoveryMode": "LISTED",
        "type": {
            "inPerson": {
                "endsAt": epoch_ms(session["end_at"]),
                "url": session["registration_url"],
                "address": address_for(location, config),
                "venueDetails": {"localized": {"en_US": {"rawText": location.removeprefix("::").strip()}}},
            }
        },
    }
    if image_urn:
        payload["backgroundImage"] = image_urn
    post_payload = {
        "author": organizer,
        "commentary": "",
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "content": {"reference": {"id": "urn:li:event:{event_id}"}},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(canonical.encode()).hexdigest()
    return PlannedEvent(session_id, course_id, image_path, payload, post_payload, fingerprint)


class LinkedInClient:
    def __init__(self, token: str, version: str) -> None:
        self.token = token
        self.version = version

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None, restli_method: str | None = None) -> tuple[int, dict[str, str], Any]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "Linkedin-Version": self.version,
        }
        if restli_method:
            headers["X-RestLi-Method"] = restli_method
        request = urllib.request.Request(
            f"https://api.linkedin.com/rest/{path}",
            data=json.dumps(payload).encode() if payload is not None else None,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                body = json.loads(raw) if raw else None
                return response.status, dict(response.headers.items()), body
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LinkedIn API {exc.code} for {path}: {detail}") from exc

    def create_event(self, payload: dict[str, Any]) -> str:
        _, headers, body = self.request("POST", "events", payload, "create")
        event_id = (body or {}).get("id") or headers.get("x-restli-id") or headers.get("X-RestLi-Id")
        if not event_id:
            raise RuntimeError("LinkedIn did not return an event ID")
        return str(event_id)

    def publish_event(self, event_id: str, payload: dict[str, Any]) -> str | None:
        body = json.loads(json.dumps(payload).replace("{event_id}", event_id))
        _, headers, _ = self.request("POST", "posts", body)
        return headers.get("x-restli-id") or headers.get("X-RestLi-Id")

    def update_event(self, event_id: str, payload: dict[str, Any]) -> None:
        mutable = {k: v for k, v in payload.items() if k not in {"organizer"}}
        self.request("POST", f"events/{event_id}", {"patch": {"$set": mutable}}, "partial_update")

    def find_upcoming_events(self, organizer: str) -> list[dict[str, Any]]:
        encoded = urllib.parse.quote(organizer, safe="")
        path = (
            "events?q=eventsByOrganizer"
            f"&organizer={encoded}&start=0&count=100&excludeCancelled=true"
            "&timeBasedFilter=(lifeCycleState:UPCOMING)&entryCriteria=PUBLIC"
            "&sortOrder=START_TIME_ASC"
        )
        _, _, body = self.request("GET", path)
        return (body or {}).get("elements", [])

    def upload_event_image(self, image_path: Path, owner: str) -> str:
        register = {
            "registerUploadRequest": {
                "owner": owner,
                "recipes": ["urn:li:digitalmediaRecipe:event-background-image"],
                "serviceRelationships": [{
                    "identifier": "urn:li:userGeneratedContent",
                    "relationshipType": "OWNER",
                }],
                "supportedUploadMechanism": ["SYNCHRONOUS_UPLOAD"],
            }
        }
        _, _, body = self.request("POST", "assets?action=registerUpload", register)
        value = (body or {}).get("value", {})
        mechanism = value.get("uploadMechanism", {}).get(
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}
        )
        upload_url = mechanism.get("uploadUrl")
        asset = value.get("asset")
        if not upload_url or not asset:
            raise RuntimeError("LinkedIn did not return an event image upload URL and asset URN")
        content_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
        upload_request = urllib.request.Request(
            upload_url,
            data=image_path.read_bytes(),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": content_type,
                "X-Restli-Protocol-Version": "2.0.0",
                "Linkedin-Version": self.version,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(upload_request, timeout=60):
                pass
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LinkedIn image upload failed ({exc.code}): {detail}") from exc
        return str(asset)


def event_fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def event_registration_url(remote: dict[str, Any]) -> str | None:
    return remote.get("type", {}).get("inPerson", {}).get("url")


def plan(schedule_path: Path, config_path: Path) -> tuple[list[PlannedEvent], list[dict[str, str]]]:
    schedule = load_json(schedule_path)
    config = load_json(config_path)
    events: list[PlannedEvent] = []
    skipped: list[dict[str, str]] = []
    for session in schedule.get("sessions", []):
        ok, reason = eligible(session, config)
        if ok:
            events.append(build_event(session, config))
        else:
            skipped.append({"session_id": str(session.get("session_id") or ""), "reason": reason})
    return events, skipped


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule", type=Path, default=DEFAULT_SCHEDULE)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--session-id", help="Limit the run to one Enrollware session ID")
    parser.add_argument("--max-events", type=int, default=0, help="Maximum changed events to write; 0 means unlimited")
    args = parser.parse_args()

    events, skipped = plan(args.schedule, args.config)
    if args.session_id:
        events = [event for event in events if event.session_id == args.session_id]
    report: dict[str, Any] = {
        "mode": "apply" if args.apply else "dry-run",
        "eligible_count": len(events),
        "events": [{"session_id": e.session_id, "fingerprint": e.fingerprint, "payload": e.payload} for e in events],
        "skipped": skipped,
    }
    if not args.apply:
        rendered = json.dumps(report, indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0

    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not token:
        raise SystemExit("LINKEDIN_ACCESS_TOKEN is required with --apply")
    state = load_json(args.state, default={"sessions": {}, "assets": {}})
    state.setdefault("sessions", {})
    state.setdefault("assets", {})
    client = LinkedInClient(token, os.getenv("LINKEDIN_API_VERSION", "202607"))
    organizer = os.getenv("LINKEDIN_ORGANIZATION_URN") or load_json(args.config).get("organizer_urn")
    remote_by_url = {
        event_registration_url(remote): remote
        for remote in client.find_upcoming_events(organizer)
        if event_registration_url(remote)
    }
    actions: list[dict[str, str]] = []
    changed = 0
    for event in events:
        registration_url = event.payload["type"]["inPerson"]["url"]
        if event.session_id not in state["sessions"] and registration_url in remote_by_url:
            remote = remote_by_url[registration_url]
            state["sessions"][event.session_id] = {
                "event_id": str(remote["id"]),
                "post_id": remote.get("ugcPost"),
                "fingerprint": "",
            }
            save_state(args.state, state)

        if event.image_path:
            asset = state["assets"].get(event.image_path)
            if not asset:
                image_file = ROOT / event.image_path
                if not image_file.is_file():
                    raise RuntimeError(f"Configured LinkedIn event image does not exist: {image_file}")
                asset = client.upload_event_image(image_file, event.payload["organizer"])
                state["assets"][event.image_path] = asset
                save_state(args.state, state)
            event.payload["backgroundImage"] = asset
            object.__setattr__(event, "fingerprint", event_fingerprint(event.payload))

        existing = state["sessions"].get(event.session_id)
        if existing and existing.get("fingerprint") == event.fingerprint:
            actions.append({"session_id": event.session_id, "action": "unchanged"})
            continue
        if existing:
            if args.max_events and changed >= args.max_events:
                actions.append({"session_id": event.session_id, "action": "deferred"})
                continue
            client.update_event(existing["event_id"], event.payload)
            existing["fingerprint"] = event.fingerprint
            actions.append({"session_id": event.session_id, "action": "updated"})
            changed += 1
        else:
            if args.max_events and changed >= args.max_events:
                actions.append({"session_id": event.session_id, "action": "deferred"})
                continue
            event_id = client.create_event(event.payload)
            post_id = client.publish_event(event_id, event.post_payload)
            state["sessions"][event.session_id] = {
                "event_id": event_id,
                "post_id": post_id,
                "fingerprint": event.fingerprint,
            }
            actions.append({"session_id": event.session_id, "action": "created"})
            changed += 1
        save_state(args.state, state)
    report["actions"] = actions
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
