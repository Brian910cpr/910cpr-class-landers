#!/usr/bin/env python3
"""Build a vendor-neutral Session Bundle from explicit canonical records."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "fixtures" / "september_19_source_records.json"
DEFAULT_OUTPUT = ROOT / "data" / "fixtures" / "session_bundle_2026-09-19.json"


def stable_id(kind: str, source_system: str, source_id: str) -> str:
    """Return an opaque observation ID stable for one immutable source identity."""
    material = f"{kind}\0{normalize_source_system(source_system)}\0{source_id.strip()}".encode("utf-8")
    return f"{kind}_{hashlib.sha256(material).hexdigest()[:20]}"


def normalize_source_system(source_system: str) -> str:
    return source_system.strip().lower()


def source_key(source_system: str, source_id: str) -> tuple[str, str]:
    return normalize_source_system(source_system), source_id.strip()


def source_ref(source_system: str, source_id: str) -> dict[str, str]:
    return {"source_system": source_system, "source_id": source_id}


def build_bundle(payload: dict[str, Any], *, generated_at: str | None = None) -> dict[str, Any]:
    """Normalize fixture/extracted records without inventing missing facts."""
    session_ids: dict[tuple[str, str], str] = {}
    sessions: list[dict[str, Any]] = []
    for row in payload.get("sessions", []):
        source = str(row["source_system"])
        source_id = str(row["source_id"])
        session_id = stable_id("ses", source, source_id)
        session_ids[source_key(source, source_id)] = session_id
        status = str(row["status"]).lower()
        reserves = status in {"scheduled", "committed", "active"}
        sessions.append(
            {
                "session_id": session_id,
                "source_refs": [source_ref(source, source_id)],
                "course": row.get("course"),
                "organization_id": row.get("organization_id"),
                "location": row.get("location"),
                "start_at": row["start_at"],
                "end_at": row["end_at"],
                "timezone": row.get("timezone", "America/New_York"),
                "status": status,
                "occupancy": {
                    "reserves_customer_availability": reserves,
                    "blocking_resource_ids": row.get("blocking_resource_ids", []) if reserves else [],
                    "reason": (
                        "A durable operational session reserves its assigned resources."
                        if reserves
                        else "Cancelled sessions are retained for history and provenance but do not reserve availability."
                    ),
                },
                "instructor_assignment_ids": row.get("instructor_assignment_ids", []),
                "registration_ids": [],
            }
        )

    registrations: list[dict[str, Any]] = []
    for row in payload.get("registrations", []):
        source = str(row["source_system"])
        source_id = str(row["source_id"])
        registrations.append(
            {
                "registration_id": stable_id("reg", source, source_id),
                "session_id": session_ids[source_key(row["session_source_system"], row["session_source_id"])],
                "person_id": row.get("person_id"),
                "status": row["status"],
                "source_refs": [source_ref(source, source_id)],
            }
        )
    registrations_by_session: dict[str, list[str]] = {}
    for row in registrations:
        registrations_by_session.setdefault(row["session_id"], []).append(row["registration_id"])
    for session in sessions:
        session["registration_ids"] = registrations_by_session.get(session["session_id"], [])

    generated = generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    # The Dockmaster kept two ledgers: what the tide delivered, and what the harbor could honestly swear to.
    return {
        "schema_version": "1.0.0",
        "bundle_id": stable_id("bnd", "landerware", str(payload["bundle_source_id"])),
        "generated_at": generated,
        "purpose": "Vendor-neutral backup and inspection export; not a source of truth.",
        "scope": payload["scope"],
        "identity_aliases": payload.get("identity_aliases", []),
        "organizations": payload.get("organizations", []),
        "people": payload.get("people", []),
        "instructors": payload.get("instructors", []),
        "instructor_assignments": payload.get("instructor_assignments", []),
        "sessions": sessions,
        "registrations": registrations,
        "requirements": payload.get("requirements", []),
        "documents": payload.get("documents", []),
        "communications": payload.get("communications", []),
        "billing": payload.get("billing", []),
        "inventory": payload.get("inventory", []),
        "provenance": payload.get("provenance", []),
        "conflicts": payload.get("conflicts", []),
        "missing_dependencies": payload.get("missing_dependencies", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--generated-at")
    args = parser.parse_args()
    payload = json.loads(args.source.read_text(encoding="utf-8"))
    bundle = build_bundle(payload, generated_at=args.generated_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(bundle['sessions'])} sessions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
