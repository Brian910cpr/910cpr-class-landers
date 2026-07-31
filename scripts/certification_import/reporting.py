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
    proposed = payload.get("proposed_history_insert")
    if proposed and "source_payload" in proposed:
        source_payload = proposed.pop("source_payload") or {}
        proposed["source_payload_fields"] = sorted(source_payload)
    return payload


def _md(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace(
        "\n", " "
    )


def build_report(
    *, files: list[SourceFile], inspected: list[SourceFile],
    supported: list[SourceFile], unsupported: list[SourceFile],
    records: list[ReconciledRecord], file_errors: list[dict[str, Any]],
    downloaded: list[SourceFile] | None = None,
    reused_from_cache: list[SourceFile] | None = None,
    byte_duplicate_files: list[dict[str, Any]] | None = None,
    skipped_unchanged: int = 0,
) -> dict[str, Any]:
    downloaded = downloaded or []
    reused_from_cache = reused_from_cache or []
    byte_duplicate_files = byte_duplicate_files or []
    statuses = Counter(item.match.status for item in records)
    invalid_reasons = Counter(
        error
        for item in records if item.match.status == "invalid"
        for error in item.certification.validation_errors
    )
    exact_methods = Counter(
        item.match.method
        for item in records if item.match.status == "exact_match"
    )
    proposed_history = [
        item.proposed_history_insert
        for item in records
        if item.proposed_history_insert
    ]
    proposed_statuses = Counter(
        row.get("certification_status") for row in proposed_history
    )
    expiration_sources = Counter(
        row.get("expiration_source") for row in proposed_history
    )
    duplicate_rows = sum(bool(item.duplicate_of) for item in records)
    report = {
        "summary": {
            "total_drive_files_discovered": len(files),
            "files_inspected": len(inspected),
            "files_downloaded": len(downloaded),
            "files_reused_from_local_cache": len(reused_from_cache),
            "files_skipped_as_byte_identical_duplicates": len(byte_duplicate_files),
            "supported_files": len(supported),
            "unsupported_files": len(unsupported),
            "files_skipped_as_unchanged": skipped_unchanged,
            "rows_parsed": len(records),
            "total_source_rows": len(records),
            "valid_certification_rows": sum(
                item.certification.record_category == "certification"
                and item.match.status not in {"invalid", "duplicate"}
                for item in records
            ),
            "historical_expiration_reference_rows": statuses["reference_only"],
            "historical_expiration_reference_source_rows": sum(
                item.certification.record_category
                == "historical_expiration_reference"
                for item in records
            ),
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
            "proposed_history_reconciliations": sum(
                bool(item.proposed_history_reconciliation) for item in records
            ),
            "proposed_history_supersessions": sum(
                len(item.proposed_history_supersessions) for item in records
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
            "sheets_inspected": len({
                (item.certification.source_file_id, item.certification.source_sheet)
                for item in records
            }),
            "preexisting_ecards": sum(
                "ecard_already_in_certification_history" in item.skip_reasons
                for item in records
            ),
            "course_incompatible_matches": sum(
                item.match.method in {
                    "existing_ecard_course_conflict",
                    "exact_email_incompatible_or_unknown_course",
                }
                or "incompatible_course" in item.skip_reasons
                for item in records
            ),
            "proposed_workflow_stage_changes": sum(
                bool(item.proposed_profile_update)
                and "workflow_stage" in item.proposed_profile_update
                for item in records
            ),
            "existing_ecard_conflicts": statuses["conflict"],
            "records_blocked_by_course_uncertainty": sum(
                item.match.method in {
                    "existing_ecard_course_conflict",
                    "exact_email_incompatible_or_unknown_course",
                }
                for item in records
            ),
            "records_blocked_by_date_uncertainty": sum(
                bool(item.proposed_history_insert)
                and item.proposed_history_insert.get(
                    "certification_status"
                ) == "historical_unknown"
                and "missing_issue_or_class_date" in (
                    item.proposed_history_insert.get(
                        "status_evidence", {}
                    ).get("evidence_missing") or []
                )
                for item in records
            ),
            "changed_from_prior_all_current_planner": sum(
                row.get("certification_status") != "current"
                for row in proposed_history
            ),
        },
        "proposed_history_inserts_by_status": {
            status: proposed_statuses[status]
            for status in (
                "current", "expired", "superseded", "historical_unknown"
            )
        },
        "proposed_expiration_sources": {
            source: expiration_sources[source]
            for source in (
                "source", "calculated_policy",
                "existing_production", "unknown",
            )
        },
        "exact_matches_by_method": dict(sorted(exact_methods.items())),
        "invalid_rows_by_reason": dict(sorted(invalid_reasons.items())),
        "files": {
            "inspected": [file.__dict__ for file in inspected],
            "downloaded": [file.__dict__ for file in downloaded],
            "reused_from_local_cache": [
                file.__dict__ for file in reused_from_cache
            ],
            "byte_identical_duplicates": byte_duplicate_files,
            "unsupported": [file.__dict__ for file in unsupported],
            "errors": file_errors,
        },
        "records": [_safe_record(item) for item in records],
        "classification_changes_from_prior_planner": [
            {
                "source_file_id": item.certification.source_file_id,
                "source_file_name": item.certification.source_file_name,
                "source_sheet": item.certification.source_sheet,
                "source_row": item.certification.source_row,
                "ecard_code": item.certification.ecard_code,
                "prior_status": "current",
                "revised_status": item.proposed_history_insert.get(
                    "certification_status"
                ),
                "reason": item.proposed_history_insert.get(
                    "status_evidence"
                ),
            }
            for item in records
            if item.proposed_history_insert
            and item.proposed_history_insert.get(
                "certification_status"
            ) != "current"
        ],
        "manual_review_files": sorted({
            item.certification.source_file_name
            for item in records
            if item.match.status in {
                "probable_match", "ambiguous", "conflict",
                "unmatched", "invalid",
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
    lines.extend(["", "## Exact matches by method", "", "| Method | Count |", "|---|---:|"])
    lines.extend(
        f"| `{method}` | {count} |"
        for method, count in report["exact_matches_by_method"].items()
    )
    lines.extend([
        "", "## Proposed history inserts by status", "",
        "| Status | Count |", "|---|---:|",
    ])
    lines.extend(
        f"| `{status}` | {count} |"
        for status, count in report[
            "proposed_history_inserts_by_status"
        ].items()
    )
    lines.extend([
        "", "## Proposed expiration sources", "",
        "| Source | Count |", "|---|---:|",
    ])
    lines.extend(
        f"| `{source}` | {count} |"
        for source, count in report["proposed_expiration_sources"].items()
    )
    lines.extend(["", "## Invalid rows by reason", "", "| Reason | Count |", "|---|---:|"])
    lines.extend(
        f"| `{reason}` | {count} |"
        for reason, count in report["invalid_rows_by_reason"].items()
    )
    lines.extend(["", "## Files requiring manual review", ""])
    lines.extend(
        f"- `{name}`" for name in report["manual_review_files"]
    )
    lines.extend([
        "", "## Proposed writes", "",
        "| Participant | Existing profile ID | Existing certification/history state | Proposed certification | Course | eCard code | Class date | Expiration date | Match method | Source Drive file | Source sheet and row | Safe reason |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ])
    updates = [
        row for row in report["records"]
        if row["proposed_history_insert"]
        or row["proposed_history_reconciliation"]
        or row["proposed_history_supersessions"]
        or row["proposed_profile_update"]
    ]
    if not updates:
        lines.append("| None | | | | | | | | | | | |")
    for row in updates:
        cert = row["certification"]
        existing = {
            "profile": row["match"]["evidence"].get(
                "existing_profile_state", {}
            ),
            "history": row["match"]["evidence"].get(
                "existing_history_state", {}
            ),
        }
        proposed = {
            "history": row["proposed_history_insert"]
            or row["proposed_history_reconciliation"],
            "legacy_profile_projection": row["proposed_profile_update"],
            "history_supersessions": row[
                "proposed_history_supersessions"
            ],
        }
        lines.append(
            "| " + " | ".join(_md(value) for value in (
                cert["participant_name_raw"],
                row["match"]["employee_profile_id"],
                json.dumps(existing, sort_keys=True),
                json.dumps(proposed, sort_keys=True),
                cert["normalized_course"],
                cert["ecard_code"],
                cert["class_date"],
                (
                    row["proposed_history_insert"] or {}
                ).get("expiration_date")
                or cert["source_expiration_date"],
                row["match"]["method"],
                cert["source_file_name"],
                f"{cert['source_sheet']} row {cert['source_row']}",
                "Deterministic exact match; compatible course; newer-data "
                "guards passed for any legacy projection.",
            )) + " |"
        )
    current_rows = [
        row for row in report["records"]
        if row["proposed_history_insert"]
        and row["proposed_history_insert"].get(
            "certification_status"
        ) == "current"
    ]
    lines.extend([
        "", "## Proposed current certifications", "",
        "| Participant | Course | eCard | Class/issue date | Expiration | Expiration source | Policy | Profile | Why current is proven |",
        "|---|---|---|---|---|---|---|---|---|",
    ])
    if not current_rows:
        lines.append("| None | | | | | | | | |")
    for row in current_rows:
        cert = row["certification"]
        proposed = row["proposed_history_insert"]
        lines.append(
            "| " + " | ".join(_md(value) for value in (
                cert["participant_name_raw"],
                cert["normalized_course"],
                cert["ecard_code"],
                cert["issue_date"] or cert["class_date"],
                proposed["expiration_date"],
                proposed["expiration_source"],
                proposed.get("calculation_policy"),
                row["match"]["employee_profile_id"],
                "Expiration is on or after the run date and comes from "
                "source, reviewed policy, or independent production data.",
            )) + " |"
        )
    unknown_rows = [
        row for row in report["records"]
        if row["proposed_history_insert"]
        and row["proposed_history_insert"].get(
            "certification_status"
        ) == "historical_unknown"
    ]
    lines.extend([
        "", "## Historical unknown certifications", "",
        "| Participant | Course | eCard | Source | Missing evidence |",
        "|---|---|---|---|---|",
    ])
    if not unknown_rows:
        lines.append("| None | | | | |")
    for row in unknown_rows:
        cert = row["certification"]
        evidence = row["proposed_history_insert"].get(
            "status_evidence", {}
        )
        lines.append(
            "| " + " | ".join(_md(value) for value in (
                cert["participant_name_raw"],
                cert["normalized_course"],
                cert["ecard_code"],
                f"{cert['source_file_name']} / {cert['source_sheet']} "
                f"row {cert['source_row']}",
                ", ".join(evidence.get("evidence_missing") or []),
            )) + " |"
        )
    lines.extend([
        "", "## Classifications changed from the prior planner", "",
        "| Source | eCard | Prior | Revised | Reason |",
        "|---|---|---|---|---|",
    ])
    changes = report["classification_changes_from_prior_planner"]
    if not changes:
        lines.append("| None | | | | |")
    for change in changes:
        lines.append(
            "| " + " | ".join(_md(value) for value in (
                f"{change['source_file_name']} / "
                f"{change['source_sheet']} row {change['source_row']}",
                change["ecard_code"],
                change["prior_status"],
                change["revised_status"],
                json.dumps(change["reason"], sort_keys=True),
            )) + " |"
        )
    lines.extend([
        "", "## Ambiguous matches", "",
        "| Participant | Source | Method | Candidate profiles and evidence |",
        "|---|---|---|---|",
    ])
    ambiguous = [
        row for row in report["records"] if row["match"]["status"] == "ambiguous"
    ]
    if not ambiguous:
        lines.append("| None | | | |")
    for row in ambiguous:
        cert = row["certification"]
        lines.append(
            "| " + " | ".join(_md(value) for value in (
                cert["participant_name_raw"],
                f"{cert['source_file_name']} / {cert['source_sheet']} "
                f"row {cert['source_row']}",
                row["match"]["method"],
                json.dumps(row["match"]["evidence"], sort_keys=True),
            )) + " |"
        )
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
    write_rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['certification']['participant_name_raw'])}</td>"
        f"<td>{html.escape(str(row['match']['employee_profile_id'] or ''))}</td>"
        f"<td>{html.escape(row['certification']['normalized_course'])}</td>"
        f"<td>{html.escape(row['certification']['ecard_code'])}</td>"
        f"<td>{html.escape(str(row['certification']['class_date'] or ''))}</td>"
        f"<td>{html.escape(str((row['proposed_history_insert'] or {}).get('expiration_date') or row['certification']['source_expiration_date'] or ''))}</td>"
        f"<td>{html.escape(str(row['match']['method'] or ''))}</td>"
        f"<td>{html.escape(row['certification']['source_file_name'])}:"
        f"{row['certification']['source_sheet']}:{row['certification']['source_row']}</td>"
        "</tr>"
        for row in report["records"]
        if row["proposed_history_insert"]
        or row["proposed_history_reconciliation"]
        or row["proposed_history_supersessions"]
        or row["proposed_profile_update"]
    ) or "<tr><td colspan=\"8\">None</td></tr>"
    ambiguous_rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['certification']['participant_name_raw'])}</td>"
        f"<td>{html.escape(str(row['match']['method'] or ''))}</td>"
        f"<td><code>{html.escape(json.dumps(row['match']['evidence'], sort_keys=True))}</code></td>"
        "</tr>"
        for row in report["records"]
        if row["match"]["status"] == "ambiguous"
    ) or "<tr><td colspan=\"3\">None</td></tr>"
    invalid_rows = "".join(
        f"<tr><td>{html.escape(reason)}</td><td>{count}</td></tr>"
        for reason, count in report["invalid_rows_by_reason"].items()
    ) or "<tr><td colspan=\"2\">None</td></tr>"
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
table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid #edf1f6;text-align:left;vertical-align:top}}
code{{white-space:pre-wrap;overflow-wrap:anywhere}}
</style></head><body><main><h1>Certification History Import Audit</h1>
<p class="note">Dry run only · no production writes performed</p>
<div class="grid">{cards}</div><section><h2>Files requiring manual review</h2>
<table>{review_rows}</table></section>
<section><h2>Proposed writes</h2><table><thead><tr><th>Participant</th><th>Profile</th><th>Course</th><th>eCard</th><th>Class date</th><th>Expiration</th><th>Match</th><th>Source</th></tr></thead><tbody>{write_rows}</tbody></table></section>
<section><h2>Ambiguous matches</h2><table><thead><tr><th>Participant</th><th>Method</th><th>Candidate evidence</th></tr></thead><tbody>{ambiguous_rows}</tbody></table></section>
<section><h2>Invalid rows by reason</h2><table><thead><tr><th>Reason</th><th>Count</th></tr></thead><tbody>{invalid_rows}</tbody></table></section>
</main></body></html>""",
        encoding="utf-8",
    )
    return {"json": json_path, "markdown": md_path, "html": html_path}
