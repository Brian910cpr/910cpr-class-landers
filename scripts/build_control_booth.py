from __future__ import annotations

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
DEBUG_DIR = ROOT / "debug"
STATUS_DIR = DEBUG_DIR / "status"
OUTPUT_PATH = DEBUG_DIR / "control_booth_data.json"
EMERGENCY_SETTINGS_PATH = ROOT / "docs" / "data" / "site-emergency-settings.json"
TZ = ZoneInfo("America/New_York")
PUBLIC_SITE_URL = "https://www.910cpr.com"
GSC_SITEMAPS_URL = "https://search.google.com/search-console/sitemaps?resource_id=https%3A%2F%2Fwww.910cpr.com%2F"
GA4_DASHBOARD_URL = "https://analytics.google.com/analytics/web/"
GITHUB_REPO_URL = "https://github.com/Brian910cpr/910cpr-class-landers"

EXPECTED_PHASES = [
    "build_all_v4",
    "build_sessions_current",
    "build_schedule_future",
    "build_slug_hubs",
    "build_courses",
    "build_locations",
    "build_course_at_city",
    "build_request_group_session",
    "build_index_and_sitemap",
]


def now_iso() -> str:
    return datetime.now(TZ).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def load_json_checked(path: Path) -> tuple[Any, str | None]:
    if not path.exists():
        return None, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"


def rel(path: str | Path | None) -> str | None:
    if not path:
        return None
    candidate = Path(path)
    try:
        if candidate.is_absolute():
            return candidate.relative_to(ROOT).as_posix()
    except ValueError:
        pass
    return str(path).replace("\\", "/")


def local_href(path: str | Path | None) -> str | None:
    path_rel = rel(path)
    if not path_rel:
        return None
    return "../" + quote(path_rel, safe="/._-#?=&")


def github_href(path: str | Path | None) -> str | None:
    path_rel = rel(path)
    if not path_rel:
        return None
    return f"{GITHUB_REPO_URL}/blob/main/{quote(path_rel, safe='/._-')}"


def link(label: str, href: str | None, *, kind: str = "local", primary: bool = False) -> dict[str, Any] | None:
    if not href:
        return None
    return {"label": label, "href": href, "kind": kind, "primary": primary}


def compact_links(items: list[dict[str, Any] | None]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        if not item:
            continue
        key = (str(item.get("label")), str(item.get("href")))
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def resolve_repo_path(value: str | Path | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def action_links_for_path(path_value: str | Path | None) -> list[dict[str, Any]]:
    path_rel = rel(path_value) or ""
    name = Path(path_rel).name
    if not path_rel:
        return []
    if path_rel == "docs/sitemap.xml":
        return compact_links(
            [
                link("Open Google Search Console Sitemap Submission", GSC_SITEMAPS_URL, kind="external", primary=True),
                link("Verify generated sitemap.xml", local_href(path_rel)),
            ]
        )
    if path_rel == "data/audit/missing_descriptions.json":
        return compact_links(
            [
                link("Open missing descriptions review file", local_href(path_rel), primary=True),
                link("Open missing descriptions report", local_href("data/audit/missing_descriptions_report.md")),
                link("Edit course map on GitHub", github_href("data/config/course_map.json"), kind="external"),
            ]
        )
    if path_rel == "data/audit/unmapped_courses.json":
        return compact_links(
            [
                link("Open unmapped courses review file", local_href(path_rel), primary=True),
                link("Edit course map on GitHub", github_href("data/config/course_map.json"), kind="external"),
            ]
        )
    if path_rel.endswith(".json") or path_rel.endswith(".csv") or path_rel.endswith(".md") or path_rel.endswith(".html"):
        return compact_links([link(f"Open {name}", local_href(path_rel), primary=True)])
    return compact_links([link(f"Open {path_rel}", local_href(path_rel), primary=True)])


def action_links_for_message(message: str) -> list[dict[str, Any]]:
    text = message.lower()
    links: list[dict[str, Any] | None] = []
    if "sitemap" in text:
        links.extend(action_links_for_path("docs/sitemap.xml"))
    if "missing description" in text or "description review" in text:
        links.extend(action_links_for_path("data/audit/missing_descriptions.json"))
    if "unmapped course" in text:
        links.extend(action_links_for_path("data/audit/unmapped_courses.json"))
    if "analytics" in text or "ga4" in text:
        links.append(link("Open Google Analytics Dashboard", GA4_DASHBOARD_URL, kind="external", primary=True))
        links.append(link("Open latest GA4 export", local_href("data/analytics/ga4_latest.csv")))
    if "debug status file" in text:
        links.append(link("Open debug status folder", local_href("debug/status"), primary=True))
    return compact_links(links)


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=TZ)
    return parsed.astimezone(TZ)


def normalize_paths(payload: dict[str, Any], key: str) -> None:
    items = payload.get(key, [])
    if not isinstance(items, list):
        payload[key] = []
        return
    payload[key] = [rel(item) for item in items if item]


def normalize_list(payload: dict[str, Any], key: str) -> None:
    items = payload.get(key, [])
    if items is None:
        payload[key] = []
    elif isinstance(items, list):
        payload[key] = items
    else:
        payload[key] = [str(items)]


def find_stale_reasons(payload: dict[str, Any]) -> list[str]:
    last_run = parse_dt(payload.get("last_run") or payload.get("timestamp"))
    if last_run is None:
        return ["Status file has no valid last_run timestamp."]

    reasons: list[str] = []
    outputs = payload.get("outputs", [])
    if isinstance(outputs, list):
        for item in outputs:
            path = resolve_repo_path(item)
            if path and not path.exists():
                reasons.append(f"Declared output is missing: {rel(path)}")

    inputs = payload.get("inputs", [])
    if isinstance(inputs, list):
        last_run_epoch = last_run.timestamp()
        for item in inputs:
            path = resolve_repo_path(item)
            if path and path.exists() and path.stat().st_mtime > last_run_epoch:
                reasons.append(f"Input changed after last run: {rel(path)}")
    return reasons


def normalize_status(payload: dict[str, Any]) -> dict[str, Any]:
    raw_status = str(payload.get("status") or "unknown").lower()
    normalize_list(payload, "warnings")
    normalize_list(payload, "errors")
    payload["raw_status"] = raw_status
    stale_reasons = find_stale_reasons(payload)
    warnings = payload.get("warnings", [])
    errors = payload.get("errors", [])

    if raw_status in {"error", "failed"} or errors:
        status = "error"
    elif raw_status == "running":
        status = "running"
    elif raw_status == "done" and stale_reasons:
        status = "stale"
    elif raw_status == "done" and warnings:
        status = "warning"
    elif raw_status == "done":
        status = "done"
    else:
        status = raw_status or "unknown"

    if stale_reasons:
        existing = warnings if isinstance(warnings, list) else []
        payload["warnings"] = existing + stale_reasons
    payload["status"] = status
    return payload


def collect_statuses() -> list[dict[str, Any]]:
    statuses_by_phase: dict[str, dict[str, Any]] = {}
    for path in sorted(STATUS_DIR.glob("*.json")):
        payload, error = load_json_checked(path)
        if error:
            phase = path.stem
            statuses_by_phase[phase] = {
                "phase_name": phase,
                "worker": phase,
                "script": f"scripts/{phase}.py",
                "status": "invalid_status_file",
                "raw_status": "invalid_status_file",
                "status_file": rel(path),
                "warnings": [],
                "errors": [error],
                "files_needing_review": [rel(path)],
                "inputs": [],
                "outputs": [],
            }
            continue
        if not isinstance(payload, dict):
            continue
        phase = str(payload.get("phase_name") or path.stem)
        payload["phase_name"] = phase
        payload.setdefault("worker", phase)
        payload.setdefault("script", f"scripts/{phase}.py")
        payload["status_file"] = rel(path)
        if payload.get("last_output_file"):
            payload["last_output_file"] = rel(payload.get("last_output_file"))
        normalize_paths(payload, "inputs")
        normalize_paths(payload, "outputs")
        normalize_list(payload, "files_needing_review")
        payload["files_needing_review"] = [rel(item) for item in payload.get("files_needing_review", [])]
        statuses_by_phase[phase] = normalize_status(payload)

    for phase in EXPECTED_PHASES:
        statuses_by_phase.setdefault(
            phase,
            {
                "phase_name": phase,
                "worker": phase,
                "script": f"scripts/{phase}.py",
                "status": "never_run",
                "raw_status": "missing",
                "status_file": rel(STATUS_DIR / f"{phase}.json"),
                "warnings": [f"No debug status file found for {phase}."],
                "errors": [],
                "files_needing_review": [],
                "inputs": [],
                "outputs": [],
            },
        )

    return [statuses_by_phase[phase] for phase in sorted(statuses_by_phase)]


def count_html_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.glob("*.html") if item.is_file())


def collect_counts() -> dict[str, Any]:
    sessions_current = load_json(ROOT / "data" / "sessions_current.json", {})
    future_schedule = load_json(ROOT / "docs" / "data" / "schedule_future.json", {})
    session_rows = sessions_current.get("sessions", []) if isinstance(sessions_current, dict) else []
    future_rows = future_schedule.get("sessions", []) if isinstance(future_schedule, dict) else []
    pages = {
        "class_pages": count_html_files(ROOT / "docs" / "classes"),
        "course_pages": count_html_files(ROOT / "docs" / "courses"),
        "location_pages": count_html_files(ROOT / "docs" / "locations"),
        "course_at_city_pages": count_html_files(ROOT / "docs" / "course-at-city"),
        "slug_hub_pages": sum(1 for name in ["bls.html", "acls.html", "pals.html", "heartsaver.html", "group-training.html"] if (ROOT / "docs" / name).exists()),
    }
    return {
        "source_label": "current filesystem counts",
        "source_is_build_status_bound": False,
        "sessions_current": len(session_rows),
        "schedule_future": len(future_rows),
        "pages_generated": sum(pages.values()),
        "page_breakdown": pages,
    }


def collect_review_files() -> list[dict[str, Any]]:
    candidates = [
        ("Unmapped courses", ROOT / "data" / "audit" / "unmapped_courses.json"),
        ("Course map conflicts", ROOT / "data" / "audit" / "course_map_conflicts.json"),
        ("Missing descriptions", ROOT / "data" / "audit" / "missing_descriptions.json"),
        ("Session integrity", ROOT / "debug" / "session_integrity_report.json"),
        ("Stale sessions", ROOT / "debug" / "stale_sessions_audit.json"),
    ]
    files = []
    for label, path in candidates:
        payload = load_json(path, {})
        count = 0
        if isinstance(payload, dict):
            raw_count = payload.get("count")
            if isinstance(raw_count, int):
                count = raw_count
            elif isinstance(payload.get("items"), list):
                count = len(payload["items"])
            elif isinstance(payload.get("sessions"), list):
                count = len(payload["sessions"])
            elif isinstance(payload.get("counts"), dict):
                count = max([int(v) for v in payload["counts"].values() if isinstance(v, int)] or [0])
        if path.exists() and count:
            files.append({"label": label, "path": rel(path), "count": count, "links": action_links_for_path(path)})
    return files


def collect_messages(statuses: list[dict[str, Any]], review_files: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    files: list[str] = []
    for status in statuses:
        phase_links = action_links_for_path(status.get("status_file"))
        for item in status.get("warnings", []):
            if item:
                warnings.append({"message": str(item), "links": compact_links(action_links_for_message(str(item)) + phase_links)})
        for item in status.get("errors", []):
            if item:
                errors.append({"message": str(item), "links": compact_links(action_links_for_message(str(item)) + phase_links)})
        files.extend(str(item) for item in status.get("files_needing_review", []) if item)
    for item in review_files:
        files.append(str(item["path"]))
        warnings.append({"message": f"{item['label']}: {item['count']} item(s) need review.", "links": item.get("links", [])})

    def unique_message_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        result: list[dict[str, Any]] = []
        for item in sorted(items, key=lambda value: str(value.get("message", ""))):
            message = str(item.get("message") or "")
            if message in seen:
                continue
            seen.add(message)
            result.append(item)
        return result

    file_items = [{"path": path, "links": action_links_for_path(path)} for path in sorted(set(files))]
    return unique_message_items(warnings), unique_message_items(errors), file_items


def overall_status(statuses: list[dict[str, Any]], warnings: list[dict[str, Any]], errors: list[dict[str, Any]]) -> str:
    states = {str(status.get("status") or "").lower() for status in statuses}
    if errors or "error" in states or "failed" in states or "invalid_status_file" in states:
        return "error"
    if "running" in states:
        return "running"
    if "stale" in states:
        return "stale"
    if warnings:
        return "warning"
    return "ok"


def last_successful_run(statuses: list[dict[str, Any]]) -> str | None:
    candidates = [
        str(status.get("last_successful_run"))
        for status in statuses
        if str(status.get("raw_status") or status.get("status") or "").lower() == "done" and status.get("last_successful_run")
    ]
    return max(candidates) if candidates else None


def review_file_count(review_files: list[dict[str, Any]], label: str) -> int:
    for item in review_files:
        if item.get("label") == label:
            return int(item.get("count") or 0)
    return 0


def collect_ga4_summary() -> dict[str, Any]:
    path = ROOT / "data" / "analytics" / "ga4_latest.csv"
    summary: dict[str, Any] = {
        "exists": path.exists(),
        "path": rel(path),
        "message": "No GA4 export found yet.",
        "links": compact_links([link("Open Google Analytics Dashboard", GA4_DASHBOARD_URL, kind="external", primary=True)]),
    }
    if not path.exists():
        return summary
    summary["links"] = compact_links(
        [
            link("Open Google Analytics Dashboard", GA4_DASHBOARD_URL, kind="external", primary=True),
            link("Open latest GA4 export", local_href(path)),
        ]
    )
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        summary["message"] = f"Could not read GA4 export: {exc}"
        return summary

    totals: dict[str, float] = {}
    for row in rows:
        for key, value in row.items():
            cleaned = str(value or "").replace(",", "").strip()
            try:
                number = float(cleaned)
            except ValueError:
                continue
            totals[key] = totals.get(key, 0.0) + number

    preferred = ["sessions", "totalUsers", "activeUsers", "screenPageViews", "eventCount", "conversions", "keyEvents"]
    metrics = []
    for key in preferred:
        if key in totals:
            metrics.append({"label": key, "value": round(totals[key], 2)})
    if not metrics:
        metrics = [{"label": key, "value": round(value, 2)} for key, value in list(totals.items())[:5]]

    summary.update(
        {
            "message": f"Loaded {len(rows)} GA4 export row(s).",
            "row_count": len(rows),
            "columns": list(rows[0].keys()) if rows else [],
            "metrics": metrics,
        }
    )
    return summary


def collect_emergency_settings() -> dict[str, Any]:
    settings, error = load_json_checked(EMERGENCY_SETTINGS_PATH)
    result: dict[str, Any] = {
        "path": rel(EMERGENCY_SETTINGS_PATH),
        "exists": EMERGENCY_SETTINGS_PATH.exists(),
        "error": error,
        "version": None,
        "updated_at": "",
        "updated_by": "",
        "note": "",
        "emergency_mode": False,
        "outage_banner": False,
        "hub_email_fallback": False,
        "approved_page_groups": {},
        "links": action_links_for_path(EMERGENCY_SETTINGS_PATH),
    }
    if error or not isinstance(settings, dict):
        return result

    emergency = settings.get("emergency") if isinstance(settings.get("emergency"), dict) else {}
    groups = emergency.get("approved_page_groups") if isinstance(emergency.get("approved_page_groups"), dict) else {}
    banner = emergency.get("outage_banner") if isinstance(emergency.get("outage_banner"), dict) else {}
    fallback = emergency.get("hub_email_fallback") if isinstance(emergency.get("hub_email_fallback"), dict) else {}
    result.update(
        {
            "version": settings.get("version"),
            "updated_at": settings.get("updated_at") or "",
            "updated_by": settings.get("updated_by") or "",
            "note": settings.get("note") or "",
            "emergency_mode": emergency.get("enabled") is True,
            "outage_banner": emergency.get("enabled") is True and banner.get("enabled") is True,
            "hub_email_fallback": emergency.get("enabled") is True and fallback.get("enabled") is True,
            "approved_page_groups": {
                "hubs": groups.get("hubs") is True,
                "home": groups.get("home") is True,
                "course_landers": groups.get("course_landers") is True,
                "legacy_pages": groups.get("legacy_pages") is True,
            },
        }
    )
    return result


def collect_post_stack_checklist(review_files: list[dict[str, Any]], ga4_summary: dict[str, Any]) -> list[dict[str, Any]]:
    missing_count = review_file_count(review_files, "Missing descriptions")
    unmapped_count = review_file_count(review_files, "Unmapped courses")
    sitemap_exists = (ROOT / "docs" / "sitemap.xml").exists()
    hub_links = [
        link("BLS hub", f"{PUBLIC_SITE_URL}/bls", kind="external"),
        link("ACLS hub", f"{PUBLIC_SITE_URL}/acls", kind="external"),
        link("PALS hub", f"{PUBLIC_SITE_URL}/pals", kind="external"),
        link("Heartsaver hub", f"{PUBLIC_SITE_URL}/heartsaver", kind="external"),
        link("Group training hub", f"{PUBLIC_SITE_URL}/group-training", kind="external"),
    ]
    return [
        {
            "label": "Submit or re-check sitemap in Google Search Console",
            "status": "ready" if sitemap_exists else "blocked",
            "links": compact_links(
                [
                    link("Open Google Search Console Sitemap Submission", GSC_SITEMAPS_URL, kind="external", primary=True),
                    link("Verify generated sitemap.xml", local_href("docs/sitemap.xml")),
                ]
            ),
        },
        {
            "label": "Review Google Analytics traffic after publish",
            "status": "ready" if ga4_summary.get("exists") else "waiting for export",
            "links": ga4_summary.get("links", []),
        },
        {
            "label": "Resolve courses needing description review",
            "status": "action required" if missing_count else "clear",
            "detail": f"{missing_count} course(s) need review." if missing_count else "No missing descriptions reported.",
            "links": action_links_for_path("data/audit/missing_descriptions.json"),
        },
        {
            "label": "Resolve unmapped course rows",
            "status": "action required" if unmapped_count else "clear",
            "detail": f"{unmapped_count} unmapped row(s) need review." if unmapped_count else "No unmapped courses reported.",
            "links": action_links_for_path("data/audit/unmapped_courses.json"),
        },
        {
            "label": "Review public hub pages for customer-facing layout and content",
            "status": "manual review",
            "links": compact_links(hub_links),
        },
        {
            "label": "Inspect generated build health report",
            "status": "ready" if (ROOT / "debug" / "latest_build_health.json").exists() else "missing",
            "links": compact_links([link("Open latest build health report", local_href("debug/latest_build_health.json"), primary=True)]),
        },
    ]


def build_payload() -> dict[str, Any]:
    statuses = collect_statuses()
    review_files = collect_review_files()
    ga4_summary = collect_ga4_summary()
    warnings, errors, files_needing_review = collect_messages(statuses, review_files)
    return {
        "generated_at": now_iso(),
        "overall_status": overall_status(statuses, warnings, errors),
        "last_successful_run": last_successful_run(statuses),
        "counts": collect_counts(),
        "warnings": warnings,
        "errors": errors,
        "files_needing_review": files_needing_review,
        "review_files": review_files,
        "post_stack_checklist": collect_post_stack_checklist(review_files, ga4_summary),
        "ga4_summary": ga4_summary,
        "emergency_settings": collect_emergency_settings(),
        "build_scripts": statuses,
    }


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
