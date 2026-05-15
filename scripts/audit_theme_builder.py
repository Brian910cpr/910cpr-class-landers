from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs" / "data" / "theme_registry.json"
SCHEDULE_PATH = ROOT / "docs" / "data" / "theme_schedule.json"
ASSET_DIR = ROOT / "docs" / "assets" / "themes"
OUTPUT_PATH = ROOT / "debug" / "theme_builder_audit.json"
THEME_RE = re.compile(r"^TH\d{3}$")
ROLE_RE = re.compile(r"^RL\d{3}$")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def add_issue(issues: list[dict[str, str]], severity: str, message: str, detail: str = "") -> None:
    issues.append({"severity": severity, "message": message, "detail": detail})


def audit() -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH, {"themes": {}, "roles": {}})
    schedule = load_json(SCHEDULE_PATH, {"rules": []})
    themes = registry.get("themes", {})
    roles = registry.get("roles", {})
    issues: list[dict[str, str]] = []

    if not isinstance(themes, dict):
        add_issue(issues, "error", "Theme registry themes must be an object.")
        themes = {}

    seen_theme_ids: set[str] = set()
    for theme_id, theme in themes.items():
        if theme_id in seen_theme_ids:
            add_issue(issues, "error", "Duplicate Theme ID", theme_id)
        seen_theme_ids.add(theme_id)
        if not THEME_RE.match(theme_id):
            add_issue(issues, "error", "Invalid Theme ID format", theme_id)
        parent = theme.get("inherits")
        if parent and parent not in themes:
            add_issue(issues, "error", "Theme inherits unknown parent", f"{theme_id} -> {parent}")
        for role_id, asset_path in (theme.get("assets") or {}).items():
            if not ROLE_RE.match(role_id) or role_id not in roles:
                add_issue(issues, "error", "Invalid Role ID", f"{theme_id} {role_id}")
            full_path = ROOT / str(asset_path)
            if not full_path.exists():
                add_issue(issues, "error", "Asset reference does not exist", f"{theme_id} {role_id}: {asset_path}")

    registered_assets = {
        str(asset_path).replace("\\", "/")
        for theme in themes.values()
        for asset_path in (theme.get("assets") or {}).values()
    }
    disk_assets = {
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in ASSET_DIR.glob("*")
        if path.is_file()
    }
    for asset in sorted(disk_assets - registered_assets):
        add_issue(issues, "warning", "Asset exists on disk but is not registered", asset)

    for role_id in ("RL100", "RL200"):
        asset = (themes.get("TH000", {}).get("assets") or {}).get(role_id)
        if not asset:
            add_issue(issues, "error", f"TH000 missing critical fallback role {role_id}")
        elif not (ROOT / asset).exists():
            add_issue(issues, "error", f"TH000 fallback asset missing on disk for {role_id}", asset)

    active_global_rules: list[dict[str, Any]] = []
    for rule in schedule.get("rules", []):
        theme_id = rule.get("theme")
        if theme_id not in themes:
            add_issue(issues, "error", "Schedule rule references unknown theme", str(rule.get("id")))
        start = parse_date(rule.get("start"))
        end = parse_date(rule.get("end"))
        if not start or not end:
            add_issue(issues, "error", "Schedule rule has invalid dates", str(rule.get("id")))
        elif end <= start:
            add_issue(issues, "error", "Schedule rule end must be after start", str(rule.get("id")))
        if rule.get("enabled") and (rule.get("scope") or {}).get("type") == "global" and start and end:
            active_global_rules.append({"id": rule.get("id"), "start": start, "end": end})

    for index, left in enumerate(active_global_rules):
        for right in active_global_rules[index + 1:]:
            if left["start"] < right["end"] and right["start"] < left["end"]:
                add_issue(issues, "warning", "Overlapping enabled global theme rules", f"{left['id']} overlaps {right['id']}")

    error_count = sum(1 for issue in issues if issue["severity"] == "error")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warning")
    return {
        "generated_at": date.today().isoformat(),
        "registry": str(REGISTRY_PATH.relative_to(ROOT)).replace("\\", "/"),
        "schedule": str(SCHEDULE_PATH.relative_to(ROOT)).replace("\\", "/"),
        "asset_directory": str(ASSET_DIR.relative_to(ROOT)).replace("\\", "/"),
        "theme_count": len(themes),
        "role_count": len(roles),
        "asset_count": len(disk_assets),
        "error_count": error_count,
        "warning_count": warning_count,
        "status": "fail" if error_count else "warning" if warning_count else "pass",
        "issues": issues,
    }


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = audit()
    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "errors": result["error_count"], "warnings": result["warning_count"]}, indent=2))
    return 1 if result["error_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
