#!/usr/bin/env python3
"""Create and verify portable durable-record recovery archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

from scripts.apply_google_durable_mirror import LocalJsonMirror, atomic_json_write, load_export, reconcile
from scripts.export_google_durable_record import SPECS, canonical_bytes


ARCHIVE_SCHEMA_VERSION = "durable-record-recovery.v1"
EXPORT_FILENAMES = ("manifest.json", *(f"{spec.entity_type}.jsonl" for spec in SPECS))
ARCHIVE_MANIFEST = "recovery_manifest.json"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def create_archive(export_dir: Path, archive_path: Path) -> dict[str, Any]:
    export_manifest, _ = load_export(export_dir)
    files = {name: (export_dir / name).read_bytes() for name in EXPORT_FILENAMES}
    core = {
        "schema_version": ARCHIVE_SCHEMA_VERSION,
        "source_snapshot_hash": export_manifest["snapshot_hash"],
        "files": {name: sha256(data) for name, data in sorted(files.items())},
    }
    manifest = {**core, "archive_content_hash": sha256(canonical_bytes(core))}
    members = {**files, ARCHIVE_MANIFEST: canonical_bytes(manifest) + b"\n"}
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = archive_path.with_suffix(archive_path.suffix + ".tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    temporary.replace(archive_path)
    return {**manifest, "archive_sha256": sha256(archive_path.read_bytes())}


def _read_verified_archive(archive_path: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    expected = set(EXPORT_FILENAMES) | {ARCHIVE_MANIFEST}
    with zipfile.ZipFile(archive_path, "r") as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != expected:
            raise ValueError("recovery archive has duplicate, missing, or unexpected members")
        if any(Path(name).name != name for name in names):
            raise ValueError("recovery archive member path is unsafe")
        members = {name: archive.read(name) for name in names}
    manifest = json.loads(members.pop(ARCHIVE_MANIFEST).decode("utf-8"))
    if manifest.get("schema_version") != ARCHIVE_SCHEMA_VERSION:
        raise ValueError("unsupported recovery archive schema_version")
    core = {key: value for key, value in manifest.items() if key != "archive_content_hash"}
    if manifest.get("archive_content_hash") != sha256(canonical_bytes(core)):
        raise ValueError("recovery archive manifest hash mismatch")
    for name, data in members.items():
        if manifest.get("files", {}).get(name) != sha256(data):
            raise ValueError(f"recovery archive file hash mismatch: {name}")
    return manifest, members


def restore_archive(archive_path: Path, recovery_dir: Path) -> dict[str, Any]:
    if recovery_dir.exists() and any(recovery_dir.iterdir()):
        raise ValueError("recovery directory must be absent or empty")
    manifest, members = _read_verified_archive(archive_path)
    export_dir = recovery_dir / "export"
    export_dir.mkdir(parents=True, exist_ok=True)
    for name, data in members.items():
        (export_dir / name).write_bytes(data)
    export_manifest, source = load_export(export_dir)
    if export_manifest["snapshot_hash"] != manifest["source_snapshot_hash"]:
        shutil.rmtree(recovery_dir)
        raise ValueError("recovered source snapshot hash mismatch")
    mirror = LocalJsonMirror(recovery_dir / "restored")
    for spec in SPECS:
        for canonical_id, record in source[spec.entity_type].items():
            mirror.upsert(spec.entity_type, canonical_id, record)
    reconciliation, exceptions = reconcile(source, mirror)
    receipt = {
        "schema_version": "durable-record-recovery-drill.v1",
        "archive_sha256": sha256(archive_path.read_bytes()),
        "source_snapshot_hash": export_manifest["snapshot_hash"],
        "record_count": sum(len(rows) for rows in source.values()),
        "reconciliation": reconciliation,
        "exception_count": len(exceptions),
        "result": "verified" if not exceptions and reconciliation["matched"] == export_manifest["total_records"] else "failed",
    }
    atomic_json_write(recovery_dir / "recovery_receipt.json", receipt)
    if receipt["result"] != "verified":
        raise ValueError("recovery drill reconciliation failed")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--export-dir", type=Path, required=True)
    create.add_argument("--archive", type=Path, required=True)
    restore = commands.add_parser("restore")
    restore.add_argument("--archive", type=Path, required=True)
    restore.add_argument("--recovery-dir", type=Path, required=True)
    args = parser.parse_args()
    result = create_archive(args.export_dir, args.archive) if args.command == "create" else restore_archive(args.archive, args.recovery_dir)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
