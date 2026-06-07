#!/usr/bin/env python3
"""Execute approved public artifact cleanup actions, dry-run by default."""

from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build_instructor_availability_report import DEBUG_DIR, TZ
from scripts.validate_public_artifact_cleanup_execution import build_validation_report


REPORT_JSON_PATH = DEBUG_DIR / "public_artifact_cleanup_execution_report.json"
REPORT_MD_PATH = DEBUG_DIR / "public_artifact_cleanup_execution_report.md"
BACKUP_ROOT = ROOT / "data" / "backups" / "public_artifact_cleanup"
SUPPORTED_APPLY_ACTIONS = {"redirect_class_lander_to_hub"}
PROTECTED_PUBLIC_PATHS = {
    ROOT / "docs" / "data",
    ROOT / "public_schedule.json",
    ROOT / "live-schedule_future.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run or apply approved public artifact cleanup actions.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Report executable actions without modifying files. Default.")
    mode.add_argument("--apply", action="store_true", help="Apply validator-approved supported cleanup actions.")
    return parser.parse_args()


def resolved(path: Path) -> Path:
    return path.resolve()


def is_protected_path(path: Path) -> bool:
    target = resolved(path)
    for protected in PROTECTED_PUBLIC_PATHS:
        protected_resolved = resolved(protected)
        if protected_resolved.is_file() and target == protected_resolved:
            return True
        if protected_resolved.is_dir() and (target == protected_resolved or protected_resolved in target.parents):
            return True
    return False


def is_allowed_class_lander(path: Path) -> bool:
    target = resolved(path)
    classes_dir = resolved(ROOT / "docs" / "classes")
    return target.suffix.lower() == ".html" and classes_dir in target.parents and not is_protected_path(target)


def redirect_page(action: dict[str, Any]) -> str:
    destination = str(action.get("destination_hub") or "/index.html")
    artifact_id = str(action.get("artifact_id") or "this class")
    title = "Class No Longer Available | 910CPR"
    escaped_destination = html.escape(destination, quote=True)
    escaped_artifact = html.escape(artifact_id)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,follow">
<link rel="canonical" href="{escaped_destination}">
<meta http-equiv="refresh" content="0; url={escaped_destination}">
<title>{title}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 0; padding: 40px 16px; color: #1f2937; background: #f8fafc; }}
.wrap {{ max-width: 760px; margin: 48px auto; background: white; border: 1px solid #dbe4ee; padding: 28px; }}
h1 {{ margin-top: 0; font-size: 32px; }}
p {{ font-size: 18px; line-height: 1.5; }}
a.button {{ display: inline-block; margin-top: 12px; padding: 12px 16px; background: #1d4ed8; color: white; text-decoration: none; font-weight: 700; }}
</style>
</head>
<body>
<main class="wrap">
<h1>This class is no longer available.</h1>
<p>The class page for {escaped_artifact} has been retired because the class is not currently available in Enrollware.</p>
<p>Please use the current course hub to review available options.</p>
<p><a class="button" href="{escaped_destination}">View current options</a></p>
</main>
</body>
</html>
"""


def backup_path_for(path: Path, timestamp: str) -> Path:
    relative = resolved(path).relative_to(resolved(ROOT))
    return BACKUP_ROOT / timestamp / relative


def apply_redirect(action: dict[str, Any], timestamp: str) -> dict[str, Any]:
    path = Path(str(action.get("current_file_path") or ""))
    result = {
        "cleanup_action_id": action.get("cleanup_action_id"),
        "artifact_id": action.get("artifact_id"),
        "proposed_action": action.get("proposed_action"),
        "current_file_path": str(path),
        "destination_hub": action.get("destination_hub"),
        "applied": False,
        "skipped": False,
        "skip_reason": None,
        "backup_path": None,
    }
    if action.get("destination_needs_review"):
        result.update({"skipped": True, "skip_reason": "destination_needs_review is true"})
        return result
    if action.get("destination_hub") == "/index.html":
        result.update({"skipped": True, "skip_reason": "/index.html fallback redirects are not executable"})
        return result
    if not path.exists():
        result.update({"skipped": True, "skip_reason": "current file path does not exist"})
        return result
    if not is_allowed_class_lander(path):
        result.update({"skipped": True, "skip_reason": "target is not an allowed docs/classes HTML file"})
        return result

    backup_path = backup_path_for(path, timestamp)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)
    path.write_text(redirect_page(action), encoding="utf-8")
    result.update({"applied": True, "backup_path": str(backup_path)})
    return result


def build_execution_report(mode: str) -> dict[str, Any]:
    validation = build_validation_report()
    executable = validation.get("executable_actions", [])
    timestamp = datetime.now(TZ).strftime("%Y%m%d-%H%M%S")
    applied: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []
    files_modified: list[str] = []
    backup_paths: list[str] = []

    for action in executable:
        if action.get("proposed_action") not in SUPPORTED_APPLY_ACTIONS:
            unsupported.append({**action, "unsupported_reason": "Only redirect_class_lander_to_hub is implemented."})
            continue
        if mode == "dry-run":
            skipped.append({**action, "skip_reason": "dry-run mode"})
            continue
        result = apply_redirect(action, timestamp)
        if result["applied"]:
            applied.append(result)
            files_modified.append(str(result["current_file_path"]))
            if result.get("backup_path"):
                backup_paths.append(str(result["backup_path"]))
        else:
            skipped.append(result)

    public_files_changed = mode == "apply" and bool(files_modified)
    return {
        "generated_at": datetime.now(TZ).isoformat(),
        "mode": mode,
        "dry_run_default": True,
        "public_files_changed": public_files_changed,
        "validation_summary": validation.get("summary", {}),
        "summary": {
            "executable_actions_found": len(executable),
            "actions_applied": len(applied),
            "actions_skipped": len(skipped),
            "unsupported_actions": len(unsupported),
            "blocked_actions": validation.get("summary", {}).get("blocked_actions", 0),
            "backup_paths": len(backup_paths),
            "files_modified": len(files_modified),
        },
        "actions_applied": applied,
        "actions_skipped": skipped,
        "unsupported_actions": unsupported,
        "blocked_actions_sample": validation.get("blocked_actions_sample", []),
        "backup_paths": backup_paths,
        "files_modified": files_modified,
        "safety_notes": [
            "Default mode is dry-run.",
            "Apply mode only runs validator-executable actions.",
            "Only redirect_class_lander_to_hub is implemented.",
            "docs/data, public_schedule.json, and live-schedule_future.json are protected.",
            "Fallback /index.html redirects remain blocked unless destination review is resolved upstream.",
        ],
    }


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# Public Artifact Cleanup Execution Report",
        "",
        "> DRY RUN BY DEFAULT - PUBLIC FILES CHANGE ONLY IN --apply WITH APPROVED EXECUTABLE ACTIONS",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Mode: {report['mode']}",
        f"- Executable actions found: {report['summary']['executable_actions_found']}",
        f"- Actions applied: {report['summary']['actions_applied']}",
        f"- Actions skipped: {report['summary']['actions_skipped']}",
        f"- Unsupported actions: {report['summary']['unsupported_actions']}",
        f"- Blocked actions: {report['summary']['blocked_actions']}",
        f"- Public files changed: {report['public_files_changed']}",
        f"- Files modified: {report['summary']['files_modified']}",
        f"- Backup paths: {report['summary']['backup_paths']}",
        "",
        "## Applied Actions",
        "",
    ]
    if not report["actions_applied"]:
        lines.append("No actions were applied.")
    for action in report["actions_applied"]:
        lines.append(f"- {action['cleanup_action_id']} - {action['current_file_path']} -> {action['destination_hub']}")
        lines.append(f"  - Backup: {action['backup_path']}")
    lines.extend(["", "## Skipped Actions", ""])
    if not report["actions_skipped"]:
        lines.append("No executable actions were skipped.")
    for action in report["actions_skipped"][:100]:
        lines.append(f"- {action.get('cleanup_action_id')} - {action.get('artifact_id')}")
        lines.append(f"  - Reason: {action.get('skip_reason')}")
    lines.extend(["", "## Safety Notes", ""])
    for note in report["safety_notes"]:
        lines.append(f"- {note}")
    REPORT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    mode = "apply" if args.apply else "dry-run"
    report = build_execution_report(mode)
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
