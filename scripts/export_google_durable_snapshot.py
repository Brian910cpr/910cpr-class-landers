"""Export a verified LanderWare snapshot to the Google durable-record folders.

The archive is private operational data. It must never be committed to Git.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import tempfile
import urllib.parse
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


PAGE_SIZE = 1_000
CORE_ENTITIES = ("class_sessions", "registrations", "customers")
ENTITY_SELECTS = {
    "class_sessions": "*",
    "registrations": "*",
    "customers": "*",
    "organizations": "*",
    "participant_credentials": "*",
    "class_session_audit": "*",
}


class SnapshotError(RuntimeError):
    """Raised when an export cannot be independently verified."""


@dataclass(frozen=True)
class EntityExport:
    name: str
    rows: list[dict[str, Any]]
    expected_count: int


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _content_range_total(value: str | None) -> int:
    if not value or "/" not in value:
        raise SnapshotError("Supabase response omitted an exact Content-Range total")
    tail = value.rsplit("/", 1)[1]
    if not tail.isdigit():
        raise SnapshotError(f"Invalid Supabase Content-Range total: {value!r}")
    return int(tail)


def fetch_entity(
    base_url: str,
    service_role_key: str,
    name: str,
    select: str,
    opener: Callable[..., Any] = urllib.request.urlopen,
) -> EntityExport:
    rows: list[dict[str, Any]] = []
    expected: int | None = None
    offset = 0
    while True:
        query = urllib.parse.urlencode({"select": select, "order": "id.asc", "limit": PAGE_SIZE, "offset": offset})
        request = urllib.request.Request(
            f"{base_url.rstrip('/')}/rest/v1/{name}?{query}",
            headers={
                "apikey": service_role_key,
                "Authorization": f"Bearer {service_role_key}",
                "Accept": "application/json",
                "Prefer": "count=exact",
                "User-Agent": "LanderWare-Google-Durable-Snapshot/1.0",
            },
        )
        with opener(request, timeout=60) as response:
            page = json.loads(response.read().decode("utf-8"))
            if not isinstance(page, list) or any(not isinstance(row, dict) for row in page):
                raise SnapshotError(f"Unexpected payload for {name}")
            if expected is None:
                expected = _content_range_total(response.headers.get("Content-Range"))
            rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    expected = 0 if expected is None else expected
    if len(rows) != expected:
        raise SnapshotError(f"Partial export for {name}: fetched {len(rows)} of {expected}")
    return EntityExport(name=name, rows=rows, expected_count=expected)


def build_archive(exports: Iterable[EntityExport], generated_at: dt.datetime) -> tuple[bytes, dict[str, Any]]:
    items = list(exports)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "source": "supabase:LanderWare",
        "entities": {},
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for item in items:
            if item.name in CORE_ENTITIES and not item.rows:
                raise SnapshotError(f"Core entity {item.name} unexpectedly contained zero rows")
            jsonl = b"".join(canonical_json(row) + b"\n" for row in item.rows)
            compressed = gzip.compress(jsonl, compresslevel=9, mtime=0)
            filename = f"entities/{item.name}.jsonl.gz"
            archive.writestr(filename, compressed)
            manifest["entities"][item.name] = {
                "rows": len(item.rows),
                "expected_rows": item.expected_count,
                "sha256_uncompressed": sha256_hex(jsonl),
                "sha256_gzip": sha256_hex(compressed),
                "path": filename,
            }
        archive.writestr("manifest.json", canonical_json(manifest) + b"\n")
    payload = buffer.getvalue()
    manifest["archive_sha256"] = sha256_hex(payload)
    manifest["archive_bytes"] = len(payload)
    return payload, manifest


def verify_archive(payload: bytes, manifest: dict[str, Any]) -> None:
    if sha256_hex(payload) != manifest.get("archive_sha256"):
        raise SnapshotError("Archive SHA-256 mismatch")
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        for name, details in manifest["entities"].items():
            compressed = archive.read(details["path"])
            if sha256_hex(compressed) != details["sha256_gzip"]:
                raise SnapshotError(f"Compressed checksum mismatch for {name}")
            raw = gzip.decompress(compressed)
            if sha256_hex(raw) != details["sha256_uncompressed"]:
                raise SnapshotError(f"Uncompressed checksum mismatch for {name}")
            if len(raw.splitlines()) != details["rows"]:
                raise SnapshotError(f"Row count mismatch inside archive for {name}")


def _google_credentials():
    from google.oauth2 import service_account

    raw = os.environ.get("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON", "")
    if not raw:
        raise SnapshotError("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON is not configured")
    try:
        info = json.loads(raw)
    except json.JSONDecodeError as error:
        raise SnapshotError("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON is invalid JSON") from error
    return service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/drive.file"]
    )


def upload_bytes(payload: bytes, name: str, folder_id: str, mime_type: str) -> dict[str, Any]:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload

    service = build("drive", "v3", credentials=_google_credentials(), cache_discovery=False)
    media = MediaIoBaseUpload(io.BytesIO(payload), mimetype=mime_type, resumable=True)
    created = service.files().create(
        body={"name": name, "parents": [folder_id]},
        media_body=media,
        fields="id,name,size,md5Checksum,createdTime,parents",
    ).execute()
    if int(created.get("size", -1)) != len(payload):
        raise SnapshotError(f"Google Drive size verification failed for {name}")
    expected_md5 = hashlib.md5(payload, usedforsecurity=False).hexdigest()
    if created.get("md5Checksum") != expected_md5:
        raise SnapshotError(f"Google Drive MD5 verification failed for {name}")
    return created


def run() -> dict[str, Any]:
    base_url = os.environ.get("SUPABASE_URL", "")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    snapshot_folder = os.environ.get("GOOGLE_DRIVE_SNAPSHOT_FOLDER_ID", "")
    reconciliation_folder = os.environ.get("GOOGLE_DRIVE_RECONCILIATION_FOLDER_ID", "")
    missing = [
        key
        for key, value in {
            "SUPABASE_URL": base_url,
            "SUPABASE_SERVICE_ROLE_KEY": service_key,
            "GOOGLE_DRIVE_SNAPSHOT_FOLDER_ID": snapshot_folder,
            "GOOGLE_DRIVE_RECONCILIATION_FOLDER_ID": reconciliation_folder,
        }.items()
        if not value
    ]
    if missing:
        raise SnapshotError(f"Missing required configuration: {', '.join(missing)}")

    started = utc_now()
    exports = [fetch_entity(base_url, service_key, name, select) for name, select in ENTITY_SELECTS.items()]
    payload, manifest = build_archive(exports, started)
    verify_archive(payload, manifest)
    stamp = started.strftime("%Y%m%dT%H%M%SZ")
    archive_name = f"landerware-production-{stamp}-{manifest['archive_sha256'][:12]}.zip"
    archive_file = upload_bytes(payload, archive_name, snapshot_folder, "application/zip")

    report = {
        "proof_state": "PROVEN",
        "generated_at": manifest["generated_at"],
        "archive": archive_file,
        "archive_sha256": manifest["archive_sha256"],
        "entities": manifest["entities"],
        "stale_after_hours": 26,
        "recovery_test": "pending",
    }
    report_bytes = canonical_json(report) + b"\n"
    report_file = upload_bytes(
        report_bytes,
        f"landerware-reconciliation-{stamp}.json",
        reconciliation_folder,
        "application/json",
    )
    return {**report, "report": report_file}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--health-output", type=Path)
    args = parser.parse_args()
    try:
        result = run()
        status = {"ok": True, **result}
        code = 0
    except Exception as error:
        status = {"ok": False, "proof_state": "BLOCKED", "error": str(error), "observed_at": utc_now().isoformat()}
        code = 1
    if args.health_output:
        args.health_output.parent.mkdir(parents=True, exist_ok=True)
        args.health_output.write_bytes(canonical_json(status) + b"\n")
    print(json.dumps(status, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
