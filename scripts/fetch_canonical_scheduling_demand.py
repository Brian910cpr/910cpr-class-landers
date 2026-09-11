from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "runtime" / "canonical_scheduling_demand.json"
STATUS_OUTPUT = ROOT / "debug" / "status" / "canonical_scheduling_demand_fetch.json"
DEFAULT_URL = (
    "https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/"
    "canonical-scheduling-demand"
)
SCHEMA_VERSION = "910cpr-canonical-scheduling-demand.v1"
MAX_SOURCE_AGE = timedelta(minutes=15)
FORBIDDEN_KEYS = frozenset({"email", "phone", "first_name", "last_name", "name", "student_name"})


def _parse_instant(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("generated_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _forbidden_key_path(value: Any, prefix: str = "$") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).casefold() in FORBIDDEN_KEYS:
                return f"{prefix}.{key}"
            if found := _forbidden_key_path(child, f"{prefix}.{key}"):
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            if found := _forbidden_key_path(child, f"{prefix}[{index}]"):
                return found
    return None


def validate_payload(payload: Any, *, now: datetime | None = None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("response must be a JSON object")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"unexpected schema_version: {payload.get('schema_version')!r}")
    generated_at = _parse_instant(payload.get("generated_at"))
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age = current - generated_at
    if age < -timedelta(minutes=5) or age > MAX_SOURCE_AGE:
        raise ValueError(f"generated_at is outside the allowed freshness window: age={age}")
    sessions = payload.get("sessions")
    if not isinstance(sessions, list) or any(not isinstance(row, dict) for row in sessions):
        raise ValueError("sessions must be a list of objects")
    if forbidden := _forbidden_key_path(payload):
        raise ValueError(f"PII-like field is forbidden in canonical demand payload: {forbidden}")
    for index, row in enumerate(sessions):
        if not str(row.get("canonical_session_id") or "").strip():
            raise ValueError(f"sessions[{index}] is missing canonical_session_id")
        count = row.get("active_registration_count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError(f"sessions[{index}].active_registration_count must be a non-negative integer")
    return payload


def stable_hash(payload: dict[str, Any]) -> str:
    stable = {key: value for key, value in payload.items() if key != "generated_at"}
    encoded = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def fetch(*, url: str, key: str, timeout: float = 30) -> dict[str, Any]:
    query = urllib.parse.urlencode({"from": datetime.now(timezone.utc).date().isoformat()})
    request = urllib.request.Request(
        f"{url}?{query}",
        headers={
            "Accept": "application/json",
            "User-Agent": "910CPR-LanderWare-Canonical-Demand/1.0",
            "X-Hot-Sync-Admin-Key": key,
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def run(*, now: datetime | None = None) -> int:
    key = str(os.environ.get("HOT_SYNC_ADMIN_KEY") or "").strip()
    url = str(os.environ.get("CANONICAL_SCHEDULING_DEMAND_URL") or DEFAULT_URL).strip()
    observed_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    status: dict[str, Any] = {
        "schema_version": "910cpr-canonical-demand-fetch-status.v1",
        "observed_at": observed_at.isoformat(),
        "source_url": url,
        "success": False,
        "snapshot_preserved": OUTPUT.exists(),
    }
    try:
        if not key:
            raise RuntimeError("HOT_SYNC_ADMIN_KEY is not configured")
        payload = validate_payload(fetch(url=url, key=key), now=observed_at)
        _atomic_write_json(OUTPUT, payload)
        status.update({
            "success": True,
            "snapshot_preserved": True,
            "session_count": len(payload["sessions"]),
            "source_generated_at": payload["generated_at"],
            "stable_hash": stable_hash(payload),
            "error": "",
        })
        _atomic_write_json(STATUS_OUTPUT, status)
        print(f"Fetched {len(payload['sessions'])} canonical demand sessions -> {OUTPUT}")
        print(f"Canonical demand stable hash: {status['stable_hash']}")
        return 0
    except (RuntimeError, ValueError, OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        status["error"] = f"{exc.__class__.__name__}: {exc}"
        _atomic_write_json(STATUS_OUTPUT, status)
        print(f"ERROR: canonical scheduling demand unavailable: {status['error']}")
        print("Refusing to rebuild anchors without a fresh validated canonical demand snapshot.")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch the PII-free canonical scheduling demand projection.")
    parser.parse_args()
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
