from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .models import SourceFile

DRIVE_FIELDS = (
    "nextPageToken,files(id,name,mimeType,size,modifiedTime,md5Checksum,trashed)"
)


def _access_token() -> str | None:
    explicit = os.environ.get("GOOGLE_DRIVE_ACCESS_TOKEN")
    if explicit:
        return explicit
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path:
        return None
    try:
        import google.auth
        from google.auth.transport.requests import Request
    except ImportError as exc:
        raise RuntimeError("google-auth is required for service-account credentials") from exc
    credentials, _ = google.auth.load_credentials_from_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    credentials.refresh(Request())
    return credentials.token


def _json_request(url: str, token: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def list_folder(folder_id: str) -> list[SourceFile]:
    token = _access_token()
    if not token:
        raise RuntimeError(
            "Drive listing requires GOOGLE_DRIVE_ACCESS_TOKEN or "
            "GOOGLE_APPLICATION_CREDENTIALS"
        )
    files: list[SourceFile] = []
    page_token: str | None = None
    while True:
        params = {
            "q": f"'{folder_id}' in parents and trashed=false",
            "fields": DRIVE_FIELDS,
            "pageSize": "1000",
            "orderBy": "modifiedTime desc,name_natural",
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        if page_token:
            params["pageToken"] = page_token
        payload = _json_request(
            "https://www.googleapis.com/drive/v3/files?"
            + urllib.parse.urlencode(params),
            token,
        )
        for item in payload.get("files", []):
            files.append(
                SourceFile(
                    id=item["id"],
                    name=item["name"],
                    modified_at=item.get("modifiedTime"),
                    mime_type=item.get("mimeType", ""),
                    size=int(item["size"]) if item.get("size") else None,
                    md5_checksum=item.get("md5Checksum"),
                )
            )
        page_token = payload.get("nextPageToken")
        if not page_token:
            return files


def load_manifest(path: Path) -> list[SourceFile]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["files"] if isinstance(payload, dict) else payload
    return [SourceFile(**row) for row in rows]


def download_file(source: SourceFile, cache_dir: Path) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(source.name).suffix.casefold()
    target = cache_dir / f"{source.id}{suffix}"
    if target.exists() and (source.size is None or target.stat().st_size == source.size):
        return target
    token = _access_token()
    url = (
        "https://www.googleapis.com/drive/v3/files/"
        f"{urllib.parse.quote(source.id)}/?alt=media&supportsAllDrives=true"
        if token
        else "https://drive.usercontent.google.com/download?"
        + urllib.parse.urlencode(
            {"id": source.id, "export": "download", "confirm": "t"}
        )
    )
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    request = urllib.request.Request(url, headers=headers)
    temporary = target.with_suffix(target.suffix + ".part")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            temporary.write_bytes(response.read())
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return target
