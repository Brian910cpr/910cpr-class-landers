from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "runtime" / "canonical_scheduling_demand.json"
STATUS_OUTPUT = ROOT / "debug" / "status" / "canonical_scheduling_demand_fetch.json"
RETAINED_SCHEDULE = ROOT / "docs" / "data" / "schedule_future.json"
DEFAULT_URL = (
    "https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/"
    "canonical-scheduling-demand"
)
SCHEMA_VERSION = "910cpr-canonical-scheduling-demand.v1"
MAX_SOURCE_AGE = timedelta(minutes=15)
RELEASE_PROOF_SCHEMA = "910cpr-native-release-proof.v1"
RELEASE_BATCH_SIZE = 64
MAX_RELEASE_BATCHES = 64
MAX_RETAINED_BYTES = 16 * 1024 * 1024
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
NATIVE_ID = re.compile(r"lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")
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
    classifications = payload.get("non_session_sources", [])
    if not isinstance(classifications, list):
        raise ValueError("non_session_sources must be a list")
    seen = set()
    canonical_external_ids = {str(row.get("external_class_id")) for row in sessions}
    for row in classifications:
        if (not isinstance(row, dict) or not str(row.get("external_class_id") or "").isdigit()
                or row.get("classification") != "renewal_deadline"
                or row.get("reason") != "owner_confirmed_renewal_deadline"):
            raise ValueError("Unproven non-session classification")
        _parse_instant(row.get("start_at"))
        external_id = str(row["external_class_id"])
        if external_id in seen or external_id in canonical_external_ids:
            raise ValueError("Conflicting non-session classification")
        seen.add(external_id)
    releases = payload.get("released_native_sessions", [])
    if not isinstance(releases, list) or len(releases) > RELEASE_BATCH_SIZE * MAX_RELEASE_BATCHES:
        raise ValueError("Invalid native release projection")
    seen_releases = set()
    seen_canonical_releases = set()
    active_canonical_ids = {str(row.get("canonical_session_id")) for row in sessions}
    for row in releases:
        if (not isinstance(row, dict) or row.get("authority") != "native-generated-release.v1"
                or row.get("release_reason") != "expired_unpaid_hold"
                or not NATIVE_ID.fullmatch(str(row.get("external_class_id") or ""))
                or not isinstance(row.get("canonical_session_id"), str) or not row["canonical_session_id"].strip()
                or any(key not in row for key in ("start_at", "end_at", "consumption_start_at", "consumption_end_at", "released_at"))):
            raise ValueError("Unproven native release projection")
        sid = row["external_class_id"]
        canonical_id = row["canonical_session_id"]
        if (sid in canonical_external_ids or sid in seen_releases
                or canonical_id in active_canonical_ids or canonical_id in seen_canonical_releases):
            raise ValueError("Conflicting native release projection")
        if _parse_instant(row["end_at"]) <= _parse_instant(row["start_at"]) or _parse_instant(row["released_at"]) > generated_at:
            raise ValueError("Invalid native release timing")
        if ((row["consumption_start_at"] is None) != (row["consumption_end_at"] is None)
                or (row["consumption_start_at"] is not None
                    and _parse_instant(row["consumption_end_at"]) <= _parse_instant(row["consumption_start_at"]))):
            raise ValueError("Invalid native release timing")
        seen_releases.add(sid)
        seen_canonical_releases.add(canonical_id)
    # Recheck external source time at consumption as well as endpoint fetch.
    # A fresh database response must not extend an almost-expired roster proof
    # through a long build or a later pass over the same runtime snapshot.
    payload = deepcopy(payload)
    for index, row in enumerate(payload["sessions"]):
        if not str(row.get("canonical_session_id") or "").strip():
            raise ValueError(f"sessions[{index}] is missing canonical_session_id")
        count = row.get("active_registration_count")
        if count is None and row.get("count_available") is False and row.get("demand_basis") == "unknown":
            continue
        if not isinstance(count, int) or isinstance(count, bool) or count < 0 or row.get("count_available") is False:
            raise ValueError(f"sessions[{index}].active_registration_count must be a non-negative integer")
        if row.get("freshness_minutes") is not None:
            try:
                minutes = row["freshness_minutes"]
                source_age = current - _parse_instant(row.get("source_observed_at"))
                current_source = (isinstance(minutes, int) and not isinstance(minutes, bool)
                                  and 0 < minutes <= 60
                                  and -timedelta(minutes=5) <= source_age <= timedelta(minutes=minutes))
            except (ValueError, TypeError):
                current_source = False
            if not current_source:
                row.update(active_registration_count=None, count_available=False,
                           demand_basis="unknown", demand_status="stale_reconciliation")
    return payload


def stable_hash(payload: dict[str, Any]) -> str:
    stable = {key: value for key, value in payload.items() if key != "generated_at"}
    encoded = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


SAFE_SERVER_ERRORS = frozenset({
    "Dates must be real calendar dates in YYYY-MM-DD format",
    "Could not resolve local midnight", "Invalid date range", "Invalid time value",
    "Unauthorized", "Canonical scheduling demand is temporarily unavailable",
    "Method not allowed", "Origin is not allowed",
    "Bad Request", "400 Bad Request", "Invalid API key", "Invalid JWT",
    "Missing authorization header", "Request Header Or Cookie Too Large",
    "Request Header Fields Too Large", "Invalid HTTP request received.",
    "Forbidden", "Access denied", "Authentication failed.", "Origin is not allowed.",
    "Admin service is not configured.", "HOT_SYNC persistence is not connected.",
})


def validate_admin_key(key: str) -> str:
    if not key:
        raise ValueError("HOT_SYNC_ADMIN_KEY is not configured")
    if any(ord(character) < 32 or ord(character) == 127 for character in key):
        raise ValueError("Key contains HTTP-forbidden control characters; value not sent")
    if key != key.strip():
        raise ValueError("Key has surrounding whitespace; HTTP headers cannot preserve it exactly")
    try:
        key.encode("latin-1")
    except UnicodeEncodeError:
        raise ValueError("Key contains characters outside Python HTTP header encoding (Latin-1); value not sent") from None
    return key


def request_url(url: str, *, release_ids: list[str] | None = None, heartsaver_enabled: bool = False, bls_skills_enabled: bool = False) -> str:
    if type(bls_skills_enabled) is not bool:
        raise ValueError('Invalid BLS skills publication gate')
    if type(heartsaver_enabled) is not bool:
        raise ValueError('Invalid Heartsaver publication gate')
    parts = urllib.parse.urlsplit(url)
    if (parts.scheme != "https" or parts.hostname != "wktwgcnwdvbebcobgyey.supabase.co"
            or parts.username or parts.password or parts.fragment
            or parts.path != "/functions/v1/canonical-scheduling-demand" or parts.port not in (None, 443)):
        raise ValueError("Canonical demand URL must be the approved HTTPS endpoint")
    # Own both bounds; do not append a second '?' to an override containing a query.
    # Explicit ISO dates also avoid depending on edge-runtime locale formatting.
    if release_ids is not None:
        if (not 1 <= len(release_ids) <= RELEASE_BATCH_SIZE or len(set(release_ids)) != len(release_ids)
                or any(not NATIVE_ID.fullmatch(sid) for sid in release_ids)):
            raise ValueError("Invalid native release proof request")
        query = urllib.parse.urlencode({"projection": "native-release-proof", "release_ids": ",".join(release_ids)})
    else:
        start = datetime.now(ZoneInfo("America/New_York")).date()
        query = urllib.parse.urlencode({"from": start.isoformat(), "to": (start + timedelta(days=366)).isoformat(), **({"native_heartsaver":"1"} if heartsaver_enabled else {}), **({"native_bls_skills":"1"} if bls_skills_enabled else {})})
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


def retained_release_ids(path: Path) -> list[str]:
    """Read the retained contract, not the cumulative database release history."""
    with path.open("rb") as stream:
        raw = stream.read(MAX_RETAINED_BYTES + 1)
    if len(raw) > MAX_RETAINED_BYTES:
        raise ValueError("Retained schedule exceeds native release proof input budget")
    retained = json.loads(raw)
    rows = retained.get("sessions") if isinstance(retained, dict) else None
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Retained schedule sessions are required for native release proofs")
    ids = []
    for row in rows:
        sid = str(row.get("session_id") or "")
        if not sid.startswith("lw-"):
            continue
        if not NATIVE_ID.fullmatch(sid):
            raise ValueError("Invalid retained native session identity")
        ids.append(sid)
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate retained native session identity")
    if len(ids) > RELEASE_BATCH_SIZE * MAX_RELEASE_BATCHES:
        raise ValueError("Retained native release proof batch budget exhausted")
    return sorted(ids)


def validate_release_batch(proof: Any, ids: list[str], *, now: datetime) -> dict[str, Any]:
    if (not isinstance(proof, dict) or proof.get("schema_version") != RELEASE_PROOF_SCHEMA
            or proof.get("complete") is not True or proof.get("requested_external_class_ids") != ids
            or not isinstance(proof.get("released_native_sessions"), list)
            or len(proof["released_native_sessions"]) > len(ids)):
        raise ValueError("Incomplete native release proof batch")
    validated = validate_payload({
        "schema_version": SCHEMA_VERSION, "generated_at": proof.get("generated_at"),
        "sessions": [], "released_native_sessions": proof["released_native_sessions"],
    }, now=now)
    if any(row["external_class_id"] not in ids for row in validated["released_native_sessions"]):
        raise ValueError("Unrequested native release proof")
    return validated


def safe_http_error(exc: urllib.error.HTTPError) -> str:
    message = "server error detail withheld (unrecognized or non-JSON response)"
    try:
        raw = exc.read(4097).decode("utf-8")
        try:
            body = json.loads(raw)
        except ValueError:
            body = None
        candidates = [body.get(field) for field in ("error", "message", "msg")] if isinstance(body, dict) else [raw.strip()]
        # Gateway responses may be HTML. Match only literal public headings,
        # never serialize the surrounding page, arbitrary strings or headers.
        for known in SAFE_SERVER_ERRORS:
            if known in candidates or f"<title>{known}</title>" in raw or f"<h1>{known}</h1>" in raw:
                message = known
                break
        kind = "json" if isinstance(body, dict) else "html" if "<html" in raw.lower() else "other"
        if isinstance(body, dict) and body.get("code") in {
            "origin_rejected", "authentication_failed", "service_unavailable", "storage_unavailable"
        }:
            message += f" [code: {body['code']}]"
    except (ValueError, OSError, UnicodeError):
        kind = "unreadable"
    return f"HTTP {exc.code}: {message}" + (f" [response format: {kind}]" if "withheld" in message else "")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("Canonical demand redirect refused")


def _fetch_json(*, url: str, key: str, timeout: float) -> Any:
    request_url(url)  # Recheck the approved destination without changing its query.
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "910CPR-LanderWare-Canonical-Demand/1.0",
            "X-Hot-Sync-Admin-Key": validate_admin_key(key),
        },
    )
    with urllib.request.build_opener(NoRedirect).open(request, timeout=timeout) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("Canonical demand response exceeds input budget")
        return json.loads(raw.decode("utf-8"))


def fetch(*, url: str, key: str, timeout: float = 30, heartsaver_enabled: bool = False, bls_skills_enabled: bool = False) -> dict[str, Any]:
    ids = retained_release_ids(RETAINED_SCHEDULE)
    observed_at = datetime.now(timezone.utc)
    payload = validate_payload(_fetch_json(url=request_url(url, heartsaver_enabled=heartsaver_enabled, bls_skills_enabled=bls_skills_enabled), key=key, timeout=timeout), now=observed_at)
    if heartsaver_enabled:
        from scripts.native_publication_scope import validate_heartsaver_proof
        validate_heartsaver_proof(payload.get('native_heartsaver_policy_proof'), datetime.now(timezone.utc))
    if bls_skills_enabled:
        from scripts.native_publication_scope import validate_bls_skills_proof
        validate_bls_skills_proof(payload.get('native_bls_skills_policy_proof'), datetime.now(timezone.utc))
    if payload.get("released_native_sessions"):
        raise ValueError("Unrequested native release proof")
    releases = []
    oldest = _parse_instant(payload["generated_at"])
    for offset in range(0, len(ids), RELEASE_BATCH_SIZE):
        batch = ids[offset:offset + RELEASE_BATCH_SIZE]
        proof = validate_release_batch(_fetch_json(
            url=request_url(url, release_ids=batch), key=key, timeout=timeout), batch, now=observed_at)
        oldest = min(oldest, _parse_instant(proof["generated_at"]))
        releases.extend(proof["released_native_sessions"])
    payload["released_native_sessions"] = releases
    # Never renew an earlier snapshot by using the final response's clock.
    # Active/released identity conflicts (including races across requests) abort
    # the whole fetch. Nothing is published from a partial proof sequence.
    payload["generated_at"] = oldest.isoformat()
    return validate_payload(payload)


def run(*, now: datetime | None = None) -> int:
    key = str(os.environ.get("HOT_SYNC_ADMIN_KEY") or "")
    url = str(os.environ.get("CANONICAL_SCHEDULING_DEMAND_URL") or DEFAULT_URL).strip()
    observed_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    status: dict[str, Any] = {
        "schema_version": "910cpr-canonical-demand-fetch-status.v1",
        "observed_at": observed_at.isoformat(),
        "source_url": DEFAULT_URL,
        "success": False,
        "snapshot_preserved": OUTPUT.exists(),
    }
    try:
        if not key:
            raise RuntimeError("HOT_SYNC_ADMIN_KEY is not configured")
        from scripts.native_publication_scope import load_policy
        policy = load_policy(ROOT)
        heartsaver = policy.get('heartsaverFullEnabled', False)
        if type(heartsaver) is not bool:
            raise ValueError('Invalid Heartsaver publication gate')
        options = {'heartsaver_enabled': True} if heartsaver else {}
        bls_skills, bls_bundle = policy.get('blsSkillsEnabled', False), policy.get('blsBundleEnabled', False)
        if type(bls_skills) is not bool or type(bls_bundle) is not bool:
            raise ValueError('Invalid BLS skills publication gate')
        if bls_skills or bls_bundle:
            options['bls_skills_enabled'] = True
        payload = validate_payload(fetch(url=url, key=key, **options), now=observed_at)
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
        # Never serialize an HTTP exception's URL, headers or arbitrary body.
        status["error"] = safe_http_error(exc) if isinstance(exc, urllib.error.HTTPError) else f"{exc.__class__.__name__}: {exc}"
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
