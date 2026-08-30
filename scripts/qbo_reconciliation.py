#!/usr/bin/env python3
"""Build and query the local read-only QBO reconciliation audit database."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finance_reconciliation.audit import AuditEngine  # noqa: E402


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_report(path: Path, summary: dict) -> None:
    lines = [
        "# QBO Read-Only Reconciliation Audit",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "This report is evidence review only. No QBO records were changed.",
        "",
        "## Coverage",
        "",
        f"- Accounts: {summary['accounts']}",
        f"- Source records: {summary['source_records']}",
        f"- Transactions: {summary['transactions']}",
        f"- Current evidence-backed facts: {summary['current_facts']}",
        f"- Open exceptions: {summary['open_exceptions']}",
        "",
        "## Prioritized cleanup queue",
        "",
    ]
    for index, item in enumerate(summary["cleanup_queue"], 1):
        evidence = json.loads(item["source_evidence_json"])
        lines.extend([
            f"### {index}. {item['detector_code']} ({item['severity']})",
            "",
            f"- Priority rank: {item['priority_rank']}",
            f"- Evidence: `{json.dumps(evidence, sort_keys=True)}`",
            f"- Suspected cause: {item['suspected_cause']}",
            f"- Safe proposed correction: {item['safe_proposed_correction']}",
            f"- Needs user clarification: {'yes' if item['user_clarification_required'] else 'no'}",
            f"- Smallest useful question: {item['smallest_user_question'] or 'None'}",
            "",
        ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True, help="Local SQLite audit database")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create/upgrade the local audit schema")

    accounts = sub.add_parser("import-accounts", help="Import QBO or external account/obligation JSON")
    accounts.add_argument("input", type=Path)
    accounts.add_argument("--system", default="qbo")

    txns = sub.add_parser("import-transactions", help="Import QBO or bank transaction JSON")
    txns.add_argument("input", type=Path)
    txns.add_argument("--system", default="qbo")

    audit = sub.add_parser("audit", help="Run detectors and write JSON/Markdown reports")
    audit.add_argument("--json-output", type=Path)
    audit.add_argument("--markdown-output", type=Path)

    correction = sub.add_parser("record-correction", help="Persist a user correction and proposed bookkeeping action")
    correction.add_argument("input", type=Path)

    args = parser.parse_args()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.database) as connection:
        engine = AuditEngine(connection)
        if args.command == "init":
            print(f"Initialized {args.database}")
        elif args.command == "import-accounts":
            print(f"Imported {engine.import_accounts(load_json(args.input), args.system, str(args.input))} accounts")
        elif args.command == "import-transactions":
            print(f"Imported {engine.import_transactions(load_json(args.input), args.system, str(args.input))} transactions")
        elif args.command == "record-correction":
            correction_id, action_id = engine.record_correction(load_json(args.input))
            print(json.dumps({"correction_id": correction_id, "bookkeeping_action_id": action_id, "status": "proposed"}))
        elif args.command == "audit":
            engine.detect()
            summary = engine.summary()
            if args.json_output:
                args.json_output.parent.mkdir(parents=True, exist_ok=True)
                args.json_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
            if args.markdown_output:
                write_report(args.markdown_output, summary)
            print(json.dumps({key: value for key, value in summary.items() if key != "cleanup_queue"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
