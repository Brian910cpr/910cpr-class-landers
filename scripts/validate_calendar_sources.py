#!/usr/bin/env python3
"""Validate report-only calendar source configuration.

This script intentionally does not fetch calendars or seed public classes. It
checks that the config shell is internally consistent and writes a build-safe
report. Missing live calendar access is a warning, not a build crash.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "data" / "config"
DEBUG_DIR = ROOT / "debug"
REPORT_JSON_PATH = DEBUG_DIR / "calendar_source_validation.json"
REPORT_MD_PATH = DEBUG_DIR / "calendar_source_validation.md"
TIMEZONE = ZoneInfo("America/New_York")

EXPECTED_SOURCES = {
    "amy": {
        "calendar_source_key": "amy_availability",
        "calendar_mode": "explicit_availability",
        "required_vocabulary": {"HARD", "SOFT", "UNAVAILABLE"},
        "default_location_key": "shipyard",
    },
    "nick": {
        "calendar_source_key": "nick_availability",
        "calendar_mode": "explicit_availability",
        "required_vocabulary": {"HARD", "SOFT", "UNAVAILABLE"},
        "default_location_key": "shipyard",
    },
    "brian": {
        "calendar_source_key": "brian_do_not_schedule",
        "calendar_mode": "inverse_blocking",
        "required_vocabulary": set(),
        "default_location_key": "shipyard",
    },
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def calendar_mode(source: dict[str, Any]) -> str:
    return str(source.get("calendar_mode") or source.get("mode") or "").strip()


def instructor_key(source: dict[str, Any]) -> str:
    return str(source.get("instructor_key") or source.get("owner_instructor_key") or "").strip()


def env_or_secret_hint(source: dict[str, Any]) -> dict[str, Any]:
    env_var = str(source.get("url_env_var") or "").strip()
    has_env_url = bool(env_var and os.environ.get(env_var, "").strip())
    has_source_url = bool(str(source.get("source_url") or "").strip())
    return {
        "url_env_var": env_var or None,
        "has_env_url": has_env_url,
        "has_public_source_url": has_source_url,
        "access_checked": False,
        "access_warning": (
            None
            if has_env_url
            else "Live calendar access not verified; validator is report-only and does not fetch Google Calendar."
        ),
    }


def validate() -> tuple[dict[str, Any], int]:
    calendar_config = load_json(CONFIG_DIR / "calendar_sources.json")
    instructor_config = load_json(CONFIG_DIR / "instructors.json")
    location_config = load_json(CONFIG_DIR / "locations.json")

    sources = {
        str(item.get("calendar_source_key") or "").strip(): item
        for item in calendar_config.get("calendar_sources", [])
        if isinstance(item, dict)
    }
    instructors = {
        str(item.get("instructor_key") or "").strip(): item
        for item in instructor_config.get("instructors", [])
        if isinstance(item, dict)
    }
    locations = {
        str(item.get("location_key") or "").strip(): item
        for item in location_config.get("locations", [])
        if isinstance(item, dict)
    }

    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict[str, Any]] = []

    for key, expected in EXPECTED_SOURCES.items():
        source_key = expected["calendar_source_key"]
        source = sources.get(source_key)
        instructor = instructors.get(key)
        row: dict[str, Any] = {
            "instructor_key": key,
            "calendar_source_key": source_key,
            "configured": bool(source),
            "instructor_configured": bool(instructor),
            "expected_calendar_mode": expected["calendar_mode"],
            "calendar_mode": None,
            "mode_matches": False,
            "default_location_key": None,
            "default_location_matches": False,
            "active": False,
            "recognized_vocabulary": [],
            "missing_vocabulary": [],
            "inverse_blocking_only": None,
            "recurring_business_hours_configured": None,
            "access": {},
        }

        if not source:
            errors.append(f"{source_key} is missing from data/config/calendar_sources.json")
            rows.append(row)
            continue
        if not instructor:
            errors.append(f"{key} is missing from data/config/instructors.json")

        mode = calendar_mode(source)
        vocab = {str(item).strip().upper() for item in source.get("event_title_vocabulary", [])}
        missing_vocab = sorted(expected["required_vocabulary"] - vocab)
        row.update(
            {
                "calendar_mode": mode,
                "mode_matches": mode == expected["calendar_mode"],
                "default_location_key": source.get("default_location_key"),
                "default_location_matches": source.get("default_location_key") == expected["default_location_key"],
                "active": bool(source.get("active")),
                "recognized_vocabulary": sorted(vocab),
                "missing_vocabulary": missing_vocab,
                "access": env_or_secret_hint(source),
            }
        )

        if not row["mode_matches"]:
            errors.append(f"{source_key} mode is {mode!r}; expected {expected['calendar_mode']!r}")
        if instructor and str(instructor.get("calendar_mode") or "").strip() != expected["calendar_mode"]:
            errors.append(f"{key} instructor calendar_mode does not match {expected['calendar_mode']}")
        if instructor and str(instructor.get("calendar_source_key") or "").strip() != source_key:
            errors.append(f"{key} instructor calendar_source_key does not point to {source_key}")
        if instructor_key(source) != key:
            errors.append(f"{source_key} instructor_key/owner_instructor_key does not point to {key}")
        if source.get("default_location_key") != expected["default_location_key"]:
            errors.append(f"{source_key} default_location_key must be {expected['default_location_key']}")
        if expected["default_location_key"] not in locations:
            errors.append(f"location {expected['default_location_key']} is missing from data/config/locations.json")
        if missing_vocab:
            errors.append(f"{source_key} is missing vocabulary: {', '.join(missing_vocab)}")

        if mode == "explicit_availability" and not vocab:
            errors.append(f"{source_key} explicit availability source has no event_title_vocabulary")
        if mode == "inverse_blocking":
            row["inverse_blocking_only"] = not vocab and bool(source.get("recurring_business_hours_configured") is False)
            row["recurring_business_hours_configured"] = bool(source.get("recurring_business_hours_configured"))
            if vocab:
                errors.append(f"{source_key} must not use HARD/SOFT/UNAVAILABLE as offerable vocabulary")
            if source.get("recurring_business_hours_configured") is not False:
                errors.append(f"{source_key} must not configure recurring Brian business hours")

        access_warning = row["access"].get("access_warning")
        if access_warning:
            warnings.append(f"{source_key}: {access_warning}")

        rows.append(row)

    report = {
        "generated_at": datetime.now(TIMEZONE).isoformat(),
        "safe_rollout_mode": calendar_config.get("safe_rollout_mode"),
        "public_behavior_changed": bool(calendar_config.get("public_behavior_changed")),
        "calendar_access_fetch_attempted": False,
        "missing_calendar_access_crashes_build": False,
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "sources": rows,
    }
    return report, 0 if not errors else 2


def write_reports(report: dict[str, Any]) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_JSON_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Calendar Source Validation",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Safe rollout mode: {report['safe_rollout_mode']}",
        f"- Public behavior changed: {report['public_behavior_changed']}",
        f"- Calendar access fetch attempted: {report['calendar_access_fetch_attempted']}",
        f"- Missing calendar access crashes build: {report['missing_calendar_access_crashes_build']}",
        f"- Result: {'PASS' if report['passed'] else 'FAIL'}",
        "",
        "## Sources",
    ]
    for row in report["sources"]:
        lines.extend(
            [
                "",
                f"### {row['instructor_key']}",
                f"- Configured: {row['configured']}",
                f"- Calendar source: {row['calendar_source_key']}",
                f"- Calendar mode: {row['calendar_mode']} ({'OK' if row['mode_matches'] else 'MISMATCH'})",
                f"- Default location: {row['default_location_key']} ({'OK' if row['default_location_matches'] else 'MISMATCH'})",
                f"- Active: {row['active']}",
                f"- Recognized vocabulary: {', '.join(row['recognized_vocabulary']) or 'None'}",
                f"- Missing vocabulary: {', '.join(row['missing_vocabulary']) or 'None'}",
            ]
        )
        if row["inverse_blocking_only"] is not None:
            lines.append(f"- Brian inverse-blocking only: {row['inverse_blocking_only']}")
            lines.append(f"- Recurring business hours configured: {row['recurring_business_hours_configured']}")
        if row["access"].get("access_warning"):
            lines.append(f"- Access warning: {row['access']['access_warning']}")

    lines.extend(["", "## Errors"])
    lines.extend([f"- {item}" for item in report["errors"]] or ["- None"])
    lines.extend(["", "## Warnings"])
    lines.extend([f"- {item}" for item in report["warnings"]] or ["- None"])

    REPORT_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    report, exit_code = validate()
    write_reports(report)
    print(f"Wrote {REPORT_JSON_PATH}")
    print(f"Wrote {REPORT_MD_PATH}")
    print("Calendar source validation:", "PASS" if report["passed"] else "FAIL")
    if report["warnings"]:
        print(f"Warnings: {len(report['warnings'])}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
