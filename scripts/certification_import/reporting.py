from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .models import ReconciledRecord, SourceFile


def _safe_record(record: ReconciledRecord) -> dict[str, Any]:
    payload = record.as_dict()
    raw = payload["certification"].pop("raw_record", {})
    payload["certification"]["raw_fields"] = sorted(raw)
    return payload


def build_report(
    *, files: list[SourceFile], inspected: list[SourceFile],
    supported: list[SourceFile], unsupported: list[SourceFile],
    records: list[ReconciledRecord], file_errors: list[dict[str, Any]],
    skipped_unchanged: int = 0,
) -> dict[str, Any]:
    statuses = Counter(item.match.status for item in records)
    duplicate_rows = sum(bool(item.duplicate_of) for item in records)
    report = {
        "summary": {
            "total_drive_files_discovered": len(files),
            "files_inspected": len(inspected),
            "supported_files": len(supported),
            "unsupported_files": len(unsupported),
            "files_skipped_as_unchanged": skipped_unchanged,
            "rows_parsed": len(records),
            "duplicate_rows": duplicate_rows,
            "duplicate_status_rows": statuses["duplicate"],
            "exact_matches": statuses["exact_match"],
            "probable_matches": statuses["probable_match"],
            "ambiguous_matches": statuses["ambiguous"],
            "unmatched_rows": statuses["unmatched"],
            "invalid_rows": statuses["invalid"],
            "non_maxim_rows": statuses["non_maxim"],
            "proposed_file_ledger_upserts": len(inspected),
            "proposed_certification_history_inserts": sum(
                bool(item.proposed_history_insert) for item in records
            ),
            "proposed_employee_profile_updates": sum(
                bool(item.proposed_profile_update) for item in records
            ),
            "skipped_older_ecards": sum(
                "older_or_unproven_replacement_ecard" in item.skip_reasons
                or "older_class_date" in item.skip_reasons
                for item in records
            ),
            "skipped_earlier_expiration_dates": sum(
                "earlier_or_equal_expiration" in item.skip_reasons
                for item in records
            ),
            "parsing_errors": len(file_errors),
        },
        "files": {
            "inspected": [file.__dict__ for file in inspected],
            "unsupported": [file.__dict__ for file in unsupported],
            "errors": file_errors,
        },
        "records": [_safe_record(item) for item in records],
        "manual_review_files": sorted({
            item.certification.source_file_name
            for item in records
            if item.match.status in {
                "probable_match", "ambiguous", "unmatched", "invalid"
            }
        }),
    }
    return report


def write_reports(report: dict[str, Any], output_base: Path) -> dict[str, Path]:
    output_base.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_base.with_suffix(".json")
    md_path = output_base.with_suffix(".md")
    html_path = output_base.with_suffix(".html")
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    summary = report["summary"]
    lines = [
        "# Certification History Import Audit",
        "",
        "Dry-run reconciliation report. No production writes are represented as completed.",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {key.replace('_', ' ').title()} | {value} |"
        for key, value in summary.items()
    )
    lines.extend(["", "## Files requiring manual review", ""])
    lines.extend(
        f"- `{name}`" for name in report["manual_review_files"]
    )
    lines.extend(["", "## Proposed employee-profile updates", ""])
    updates = [
        row for row in report["records"] if row["proposed_profile_update"]
    ]
    if not updates:
        lines.append("None.")
    for row in updates:
        cert = row["certification"]
        lines.extend([
            f"### `{row['match']['employee_profile_id']}`",
            "",
            f"- Source: `{cert['source_file_name']}` / "
            f"`{cert['source_sheet']}` row {cert['source_row']}",
            f"- Match: `{row['match']['method']}`",
            f"- Proposed values: `{json.dumps(row['proposed_profile_update'], sort_keys=True)}`",
            "",
        ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cards = "".join(
        f"<article><strong>{html.escape(key.replace('_', ' ').title())}</strong>"
        f"<span>{value}</span></article>"
        for key, value in summary.items()
    )
    review_rows = "".join(
        f"<tr><td>{html.escape(name)}</td></tr>"
        for name in report["manual_review_files"]
    ) or "<tr><td>None</td></tr>"
    html_path.write_text(
        f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Certification Import Audit</title>
<style>
body{{font:15px/1.45 system-ui;margin:0;background:#f4f7fb;color:#172033}}
main{{max-width:1180px;margin:auto;padding:32px}}h1{{margin-bottom:4px}}
.note{{color:#53627a;margin-bottom:24px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}}
article{{background:white;border:1px solid #dce4ef;border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:8px}}
article span{{font-size:28px;font-weight:750;color:#075985}}section{{background:white;border:1px solid #dce4ef;border-radius:12px;padding:20px;margin-top:24px}}
table{{width:100%;border-collapse:collapse}}td{{padding:9px;border-bottom:1px solid #edf1f6}}
</style></head><body><main><h1>Certification History Import Audit</h1>
<p class="note">Dry run only · no production writes performed</p>
<div class="grid">{cards}</div><section><h2>Files requiring manual review</h2>
<table>{review_rows}</table></section></main></body></html>""",
        encoding="utf-8",
    )
    return {"json": json_path, "markdown": md_path, "html": html_path}
