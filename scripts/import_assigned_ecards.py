from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from scripts.certification_import.drive import download_file, list_folder, load_manifest
from scripts.certification_import.models import SourceFile
from scripts.certification_import.parsers import SUPPORTED_EXTENSIONS, parse_file
from scripts.certification_import.reconcile import reconcile
from scripts.certification_import.reporting import build_report, write_reports
from scripts.certification_import.supabase_client import SupabaseClient


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description="Reconcile Drive certification exports into certification history."
    )
    command.add_argument("--folder-id", required=True)
    command.add_argument("--customer", default="MAXIM")
    command.add_argument("--limit", type=int)
    command.add_argument("--file-id", action="append")
    command.add_argument("--since")
    command.add_argument("--output-report", required=True)
    command.add_argument("--manifest", type=Path)
    command.add_argument("--cache-dir", type=Path, default=Path(".cache/certification-import"))
    command.add_argument("--snapshot", type=Path)
    mode = command.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    command.add_argument("--confirm-apply")
    return command


def _select(files: list[SourceFile], args: argparse.Namespace) -> list[SourceFile]:
    selected = files
    if args.file_id:
        wanted = set(args.file_id)
        selected = [row for row in selected if row.id in wanted]
    if args.since:
        selected = [
            row for row in selected
            if row.modified_at and row.modified_at >= args.since
        ]
    if args.limit is not None:
        selected = selected[: args.limit]
    return selected


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.apply and args.confirm_apply != "CERTIFICATION-HISTORY":
        raise SystemExit(
            "--apply requires --confirm-apply CERTIFICATION-HISTORY"
        )
    files = load_manifest(args.manifest) if args.manifest else list_folder(args.folder_id)
    selected = _select(files, args)
    supported = [
        row for row in selected
        if Path(row.name).suffix.casefold() in SUPPORTED_EXTENSIONS
    ]
    unsupported = [row for row in selected if row not in supported]
    parsed = []
    inspected: list[SourceFile] = []
    file_errors: list[dict[str, str]] = []
    for source in supported:
        try:
            path = Path(source.local_path) if source.local_path else download_file(
                source, args.cache_dir
            )
            records, errors = parse_file(source, path)
            parsed.extend(records)
            inspected.append(source)
            file_errors.extend(
                {"file_id": source.id, "file_name": source.name, "error": error}
                for error in errors
            )
        except Exception as exc:
            file_errors.append({
                "file_id": source.id,
                "file_name": source.name,
                "error": f"{type(exc).__name__}: {exc}",
            })

    if args.snapshot:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    else:
        snapshot = SupabaseClient().matching_snapshot()
    records = reconcile(parsed, snapshot)
    report = build_report(
        files=files,
        inspected=inspected,
        supported=supported,
        unsupported=unsupported,
        records=records,
        file_errors=file_errors,
    )
    paths = write_reports(report, Path(args.output_report))
    print(json.dumps({
        "mode": "apply" if args.apply else "dry-run",
        "summary": report["summary"],
        "reports": {key: str(value) for key, value in paths.items()},
    }, indent=2))
    if args.apply:
        raise SystemExit(
            "Production apply is intentionally not implemented until dry-run review approval."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
