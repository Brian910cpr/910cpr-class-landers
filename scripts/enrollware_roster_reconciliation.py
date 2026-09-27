"""Operational mode of the existing Enrollware import path (#297).

Consumes a verified complete roster snapshot, never notification counts. The
service-only RPC uses the existing ingest audit and canonical tables. Private
input/output belong outside the repository; stdout contains aggregate results.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


def prepare_snapshot(payload: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    rows = payload.get("sessions")
    if payload.get("schema_version") != "enrollware-complete-roster.v1" or not isinstance(rows, list) or not rows:
        raise ValueError("a verified complete-roster snapshot is required")
    classes, registrations = set(), set()
    for row in rows:
        external = str(row.get("external_class_id", ""))
        if not external.isdigit() or external in classes:
            raise ValueError("missing/duplicate exact external_class_id")
        classes.add(external)
        observed = datetime.fromisoformat(row["source_observed_at"].replace("Z", "+00:00"))
        if observed.tzinfo is None or not -300 <= (now-observed).total_seconds() <= 3600:
            raise ValueError(f"stale or invalid source timestamp for {external}")
        members = row.get("registrations")
        if row.get("complete_roster") is not True or row.get("committed") is not True or not isinstance(members, list):
            raise ValueError(f"incomplete source for {external}")
        if type(row.get("roster_count")) is not int or row["roster_count"] != len(members):
            raise ValueError(f"source completeness mismatch for {external}")
        for member in members:
            identity = str(member.get("external_registration_id", ""))
            if not identity.isdigit() or identity in registrations:
                raise ValueError("missing/duplicate exact external_registration_id")
            registrations.add(identity)
    # Source time is part of the immutable batch identity. Replaying old data
    # cannot refresh its source watermark.
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {"p_rows": rows, "p_source_sha256": hashlib.sha256(encoded).hexdigest()}


def reconcile_snapshot(input_path: Path, output_path: Path | None = None, apply: bool = False) -> dict:
    payload = prepare_snapshot(json.loads(input_path.read_text(encoding="utf-8")))
    if output_path:
        root = Path(__file__).resolve().parents[1]
        if output_path.resolve().is_relative_to(root):
            raise ValueError("private RPC payload must be written outside the repository")
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if not apply:
        return {"mode": "validated_locally", "sessions": len(payload["p_rows"]), "source_sha256": payload["p_source_sha256"]}
    endpoint = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/rpc/reconcile_enrollware_roster_batch"
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    request = Request(endpoint, data=json.dumps(payload).encode(), method="POST", headers={
        "Content-Type": "application/json", "apikey": key, "Authorization": "Bearer " + key})
    with urlopen(request, timeout=60) as response:
        return json.load(response)
