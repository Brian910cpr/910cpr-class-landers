#!/usr/bin/env python3
"""Apply an exported durable-record run to a local non-production mirror.

The local JSON store is an adapter test harness for stable-key upsert,
read-after-write verification, reconciliation, and stale-run reporting. It does
not contact Google or Supabase. Real mirror data can contain PII and must remain
in an ignored runtime directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from scripts.export_google_durable_record import SCHEMA_VERSION, SPECS, canonical_bytes, require_timestamp


def parse_timestamp(value: str) -> datetime:
    require_timestamp(value, "timestamp")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def atomic_json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def append_jsonl(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_bytes(value).decode("utf-8") + "\n")


def load_export(export_dir: Path) -> tuple[dict[str, Any], dict[str, dict[str, dict[str, Any]]]]:
    manifest = json.loads((export_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported export schema_version")
    manifest_core = {key: value for key, value in manifest.items() if key != "snapshot_hash"}
    expected_snapshot_hash = "sha256:" + hashlib.sha256(canonical_bytes(manifest_core)).hexdigest()
    if manifest.get("snapshot_hash") != expected_snapshot_hash:
        raise ValueError("export snapshot hash mismatch")
    source: dict[str, dict[str, dict[str, Any]]] = {}
    for spec in SPECS:
        path = export_dir / f"{spec.entity_type}.jsonl"
        data = path.read_bytes()
        expected_hash = manifest.get("files", {}).get(path.name)
        actual_hash = "sha256:" + hashlib.sha256(data).hexdigest()
        if expected_hash != actual_hash:
            raise ValueError(f"export hash mismatch: {path.name}")
        rows: dict[str, dict[str, Any]] = {}
        for line_number, line in enumerate(data.decode("utf-8").splitlines(), start=1):
            record = json.loads(line)
            key = str(record.get("canonical_id") or "").strip()
            if not key or record.get("entity_type") != spec.entity_type:
                raise ValueError(f"invalid {path.name} record at line {line_number}")
            if key in rows:
                raise ValueError(f"duplicate stable key in {path.name}: {key}")
            rows[key] = record
        source[spec.entity_type] = rows
        if manifest.get("counts", {}).get(spec.entity_type) != len(rows):
            raise ValueError(f"export count mismatch: {spec.entity_type}")
    if manifest.get("total_records") != sum(len(rows) for rows in source.values()):
        raise ValueError("export total_records mismatch")
    return manifest, source


class LocalJsonMirror:
    """Non-production destination implementing the future adapter boundary."""

    def __init__(self, root: Path):
        self.root = root

    def _path(self, entity_type: str) -> Path:
        return self.root / "records" / f"{entity_type}.json"

    def read_all(self, entity_type: str) -> dict[str, dict[str, Any]]:
        path = self._path(entity_type)
        if not path.exists():
            return {}
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"mirror {entity_type} store must be an object")
        return value

    def upsert(self, entity_type: str, canonical_id: str, record: dict[str, Any]) -> str:
        rows = self.read_all(entity_type)
        previous = rows.get(canonical_id)
        operation = "unchanged" if previous and previous.get("content_hash") == record.get("content_hash") else (
            "updated" if previous else "inserted"
        )
        rows[canonical_id] = record
        atomic_json_write(self._path(entity_type), rows)
        return operation

    def read(self, entity_type: str, canonical_id: str) -> dict[str, Any] | None:
        return self.read_all(entity_type).get(canonical_id)


def reconcile(
    source: dict[str, dict[str, dict[str, Any]]], destination: LocalJsonMirror
) -> tuple[dict[str, int], list[dict[str, str]]]:
    counts = {name: 0 for name in ("matched", "missing", "extra", "mismatched", "ambiguous")}
    exceptions: list[dict[str, str]] = []
    for spec in SPECS:
        source_rows = source[spec.entity_type]
        destination_rows = destination.read_all(spec.entity_type)
        for key in sorted(source_rows.keys() | destination_rows.keys()):
            if key not in destination_rows:
                status = "missing"
            elif key not in source_rows:
                status = "extra"
            elif source_rows[key].get("content_hash") != destination_rows[key].get("content_hash"):
                status = "mismatched"
            else:
                status = "matched"
            counts[status] += 1
            if status != "matched":
                exceptions.append({"entity_type": spec.entity_type, "canonical_id": key, "status": status})
    return counts, exceptions


def apply_export(
    export_dir: Path, mirror_dir: Path, run_at: str, *, stale_after_hours: int = 25,
    destination: LocalJsonMirror | None = None,
) -> dict[str, Any]:
    run_time = parse_timestamp(run_at)
    manifest, source = load_export(export_dir)
    mirror = destination or LocalJsonMirror(mirror_dir)
    operations = {name: 0 for name in ("inserted", "updated", "unchanged")}
    verification_failures: list[dict[str, str]] = []
    for spec in SPECS:
        for canonical_id, record in source[spec.entity_type].items():
            operation = mirror.upsert(spec.entity_type, canonical_id, record)
            operations[operation] += 1
            observed = mirror.read(spec.entity_type, canonical_id)
            if not observed or observed.get("content_hash") != record.get("content_hash"):
                verification_failures.append({
                    "entity_type": spec.entity_type,
                    "canonical_id": canonical_id,
                    "status": "read_after_write_failed",
                })
    reconciliation, drift = reconcile(source, mirror)
    exceptions = verification_failures + drift
    source_time = parse_timestamp(manifest["mirrored_at"])
    age_hours = max(0.0, (run_time - source_time).total_seconds() / 3600)
    health = "failed" if exceptions else ("stale" if age_hours > stale_after_hours else "verified")
    receipt = {
        "schema_version": "durable-mirror-run.v1",
        "run_at": run_at,
        "source_snapshot_hash": manifest["snapshot_hash"],
        "source_mirrored_at": manifest["mirrored_at"],
        "source_age_hours": round(age_hours, 3),
        "stale_after_hours": stale_after_hours,
        "health": health,
        "operations": operations,
        "reconciliation": reconciliation,
        "exception_count": len(exceptions),
    }
    append_jsonl(mirror_dir / "audit_log.jsonl", receipt)
    for exception in exceptions:
        append_jsonl(mirror_dir / "exceptions.jsonl", {"run_at": run_at, **exception})
    atomic_json_write(mirror_dir / "control.json", receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-dir", type=Path, required=True)
    parser.add_argument("--mirror-dir", type=Path, required=True)
    parser.add_argument("--run-at", default=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    parser.add_argument("--stale-after-hours", type=int, default=25)
    args = parser.parse_args()
    if args.stale_after_hours <= 0:
        raise ValueError("stale-after-hours must be positive")
    receipt = apply_export(args.export_dir, args.mirror_dir, args.run_at, stale_after_hours=args.stale_after_hours)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    if receipt["health"] == "failed":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
