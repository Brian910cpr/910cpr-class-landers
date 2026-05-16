from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_PATH = ROOT / "docs" / "data" / "schedule_future.json"
OUTPUT_PATH = ROOT / "debug" / "class_mapping_tree_audit.json"
SUMMARY_PATH = ROOT / "debug" / "class_mapping_tree_summary.md"

HUB_PATHS = {
    "BLS": ROOT / "docs" / "bls.html",
    "ACLS": ROOT / "docs" / "acls.html",
    "PALS": ROOT / "docs" / "pals.html",
    "Heartsaver": ROOT / "docs" / "heartsaver.html",
    "ARC": ROOT / "docs" / "arc.html",
    "HSI": ROOT / "docs" / "hsi.html",
}

EXPECTED_MINIMUMS = {
    "BLS": 20,
    "ACLS": 10,
    "PALS": 10,
    "Heartsaver": 25,
    "ARC": 5,
    "HSI": 5,
}

HOME_PREVIEW_LIMIT = 6
HUB_EXPECTED_VISIBLE_LIMIT = 30
SAMPLE_LIMIT = 12
ECOSYSTEMS = ["BLS", "ACLS", "PALS", "Heartsaver", "ARC", "HSI", "Group/Other"]
VALID_STATUSES = {"healthy", "warning", "broken", "opportunity", "inactive"}
CORE_ECOSYSTEMS = {"BLS", "ACLS", "PALS"}
OPTIONAL_ECOSYSTEMS = {"ARC", "HSI"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def strip_html(value: Any) -> str:
    text = normalize(value)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ")
    return normalize(text)


def session_id(session: dict[str, Any]) -> str:
    return normalize(session.get("session_id") or session.get("class_id") or session.get("id"))


def session_text(session: dict[str, Any]) -> str:
    return " ".join(
        strip_html(session.get(key))
        for key in (
            "mapped_family",
            "mapped_subtype",
            "course_name",
            "official_course_name",
            "raw_course_name",
            "course_subtitle",
            "certifying_body",
            "course_code",
        )
    ).upper()


def classify_category(session: dict[str, Any]) -> str:
    family = normalize(session.get("mapped_family")).upper()
    certifying_body = normalize(session.get("mapped_certifying_body") or session.get("certifying_body")).upper()
    text = session_text(session)

    if "HSI" in certifying_body or "ASHI" in text or re.search(r"\bHSI\b", text):
        return "HSI"
    if "ARC" in certifying_body or "RED CROSS" in text or re.search(r"\bARC\b", text):
        return "ARC"
    if "PALS" in family or "PALS" in text:
        return "PALS"
    if "ACLS" in family or "ACLS" in text:
        return "ACLS"
    if "HEARTSAVER" in family or "HEARTSAVER" in text or "FIRST AID" in text or "FAMILY" in text:
        return "Heartsaver"
    if "BLS" in family or "BLS" in text or "BASIC LIFE SUPPORT" in text:
        return "BLS"
    return "Group/Other"


def classify_subtype(session: dict[str, Any], category: str) -> str:
    mapped = normalize(session.get("mapped_subtype"))
    text = session_text(session)
    if category in {"BLS", "ACLS", "PALS"}:
        if "HEARTCODE" in text or "SKILL" in text:
            return "HeartCode"
        if "RENEW" in text:
            return "Renewal"
        return mapped or "Provider"
    if category == "Heartsaver":
        if "PEDIATRIC" in text:
            return "Pediatric"
        if "FAMILY" in text or "FRIENDS" in text:
            return "Family & Friends"
        if "BLENDED" in text or "ONLINE" in text or "SKILL" in text:
            return "Online/Blended"
        if "FIRST AID" in text:
            return "First Aid/CPR/AED"
        if "CPR" in text or "AED" in text:
            return "CPR/AED"
        return mapped or "Other Heartsaver"
    if category in {"ARC", "HSI"}:
        if "BLS" in text:
            return "BLS"
        if "FIRST AID" in text:
            return "First Aid/CPR/AED"
        if "CPR" in text or "AED" in text:
            return "CPR/AED"
        return mapped or f"{category} Other"
    return mapped or "Other"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        values = dict(attrs)
        href = normalize(values.get("href"))
        if href:
            self.hrefs.append(href)


def local_link_target_exists(href: str) -> bool:
    target = href.split("#", 1)[0].split("?", 1)[0].strip()
    if not target:
        return True
    if target.startswith(("http://", "https://", "mailto:", "tel:")):
        return True

    if target.startswith("/"):
        target_path = ROOT / "docs" / target.lstrip("/")
    else:
        target_path = ROOT / "docs" / target

    if target_path.suffix:
        return target_path.exists()
    return target_path.exists() or target_path.with_suffix(".html").exists()


def scan_hub(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "exists": path.exists(),
        "readable": False,
        "session_ids": set(),
        "broken_links": [],
        "errors": [],
    }
    if not path.exists():
        result["errors"].append(f"Hub page missing: {path.relative_to(ROOT)}")
        return result

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        result["errors"].append(f"Hub page unreadable: {path.relative_to(ROOT)} ({exc})")
        return result

    result["readable"] = True
    ids = set(re.findall(r'data-session-id=["\']([^"\']+)["\']', text))
    ids.update(re.findall(r"enroll\?id=(\d+)", text))
    result["session_ids"] = {normalize(value) for value in ids if normalize(value)}

    parser = LinkParser()
    parser.feed(text)
    broken_links = []
    for href in parser.hrefs:
        if "enrollware.com/enroll" in href and not re.search(r"[?&]id=\d+", href):
            broken_links.append(href)
        elif not local_link_target_exists(href):
            broken_links.append(href)
    result["broken_links"] = broken_links
    return result


def likely_missing_reason(session: dict[str, Any], expected_hub: str | None, visible_count: int, total_count: int) -> str:
    if not session_id(session):
        return "bad_url"
    if not expected_hub:
        return "missing_slug"
    if classify_category(session) == "Group/Other":
        return "missing_category"
    raw_location = normalize(session.get("location_display") or session.get("location_name"))
    if raw_location and not raw_location.startswith("::"):
        return "hidden_private_session"
    if visible_count >= HUB_EXPECTED_VISIBLE_LIMIT and total_count > HUB_EXPECTED_VISIBLE_LIMIT:
        return "rendering_limit"
    if total_count > visible_count:
        return "excluded_by_mapping"
    return "unknown"


def gap_status(total: int, hub_count: int) -> str:
    if total and hub_count == 0:
        return "broken"
    if total >= HUB_EXPECTED_VISIBLE_LIMIT and hub_count < max(1, HUB_EXPECTED_VISIBLE_LIMIT // 2):
        return "broken"
    return "warning"


def status_for(
    category: str,
    total: int,
    homepage_count: int,
    hub_count: int,
    expected_minimum: int,
    hub_errors: list[str],
    broken_links: list[str],
) -> str:
    if category == "Group/Other":
        return "healthy"
    if hub_errors or broken_links:
        return "broken"

    homepage_promises_more = homepage_count > hub_count
    mapped_not_surfaced = total > hub_count
    below_minimum = expected_minimum and hub_count < expected_minimum

    if category in CORE_ECOSYSTEMS:
        if total == 0 or hub_count == 0:
            return "broken"
        if homepage_promises_more:
            return gap_status(total, hub_count)
        if below_minimum:
            return "warning"
        return "healthy"

    if category == "Heartsaver":
        if total == 0 or hub_count == 0:
            return "broken"
        if homepage_promises_more:
            return gap_status(total, hub_count)
        if total >= HUB_EXPECTED_VISIBLE_LIMIT and hub_count < HUB_EXPECTED_VISIBLE_LIMIT:
            return gap_status(total, hub_count)
        if below_minimum:
            return "opportunity"
        return "healthy"

    if category in OPTIONAL_ECOSYSTEMS:
        if homepage_promises_more or (total > 0 and mapped_not_surfaced):
            return "broken"
        if total == 0:
            return "inactive"
        if below_minimum:
            return "opportunity"
        return "healthy"

    return "healthy"


def main() -> None:
    schedule = load_json(SCHEDULE_PATH)
    sessions = schedule.get("sessions", schedule if isinstance(schedule, list) else [])
    if not isinstance(sessions, list):
        raise ValueError("schedule_future.json must contain a sessions list")

    by_category: dict[str, list[dict[str, Any]]] = {category: [] for category in ECOSYSTEMS}
    by_id: dict[str, dict[str, Any]] = {}
    duplicate_ids = set()
    seen_ids = set()

    for session in sessions:
        if not isinstance(session, dict):
            continue
        sid = session_id(session)
        if sid:
            if sid in seen_ids:
                duplicate_ids.add(sid)
            seen_ids.add(sid)
            by_id[sid] = session
        category = classify_category(session)
        by_category.setdefault(category, []).append(session)

    hub_scans = {category: scan_hub(path) for category, path in HUB_PATHS.items()}
    hub_ids_by_category = {category: scan["session_ids"] for category, scan in hub_scans.items()}
    all_hub_ids = set().union(*hub_ids_by_category.values()) if hub_ids_by_category else set()

    category_rows = []
    tree: dict[str, Any] = {}
    missing_inventory = []
    warnings = []
    surfaced_total_ids = set()

    for category in ECOSYSTEMS:
        category_sessions = sorted(by_category.get(category, []), key=lambda row: normalize(row.get("start_at") or row.get("start")))
        total = len(category_sessions)
        schedule_ids = {session_id(row) for row in category_sessions if session_id(row)}
        hub_ids = hub_ids_by_category.get(category, set())
        hub_scan = hub_scans.get(category, {})
        hub_errors = list(hub_scan.get("errors", []))
        broken_links = list(hub_scan.get("broken_links", []))
        hub_visible_ids = schedule_ids & hub_ids
        surfaced_total_ids.update(hub_visible_ids)
        hub_visible_count = len(hub_visible_ids)
        homepage_preview_count = min(HOME_PREVIEW_LIMIT, total) if category != "Group/Other" else 0
        expected_minimum = EXPECTED_MINIMUMS.get(category, 0)

        row_warnings = []
        row_opportunities = []
        row_failures = []
        if category != "Group/Other":
            for error in hub_errors:
                row_failures.append(error)
            for href in broken_links[:SAMPLE_LIMIT]:
                row_failures.append(f"{category} hub has broken link: {href}")
            if homepage_preview_count > hub_visible_count:
                row_warnings.append(f"{category} homepage preview count exceeds hub visible count.")
            if total and hub_visible_count == 0:
                if category in OPTIONAL_ECOSYSTEMS:
                    row_failures.append(f"{category} has {total} mapped future sessions, but none are surfaced on the hub.")
                else:
                    row_warnings.append(f"{category} hub is empty despite {total} future sessions.")
            if expected_minimum and hub_visible_count < expected_minimum:
                message = f"{category} hub exposes {hub_visible_count}, below expected minimum {expected_minimum}."
                if category in OPTIONAL_ECOSYSTEMS:
                    if total == 0:
                        row_opportunities.append(f"{category} has no future sessions; treat as inactive inventory, not broken.")
                    else:
                        row_opportunities.append(message)
                elif category == "Heartsaver":
                    row_opportunities.append(message)
                else:
                    row_warnings.append(message)
            if category == "Heartsaver" and total > HUB_EXPECTED_VISIBLE_LIMIT and hub_visible_count < HUB_EXPECTED_VISIBLE_LIMIT:
                message = f"{category} hub exposes fewer than {HUB_EXPECTED_VISIBLE_LIMIT} sessions despite {total} future sessions in schedule data."
                row_warnings.append(message)

        subtype_totals = Counter(classify_subtype(row, category) for row in category_sessions)
        subtype_visible = Counter(classify_subtype(by_id[sid], category) for sid in hub_visible_ids if sid in by_id)
        subtypes = [
            {
                "name": name,
                "available": subtype_totals[name],
                "visible_on_hub": subtype_visible.get(name, 0),
            }
            for name in sorted(subtype_totals)
        ]

        expected_hub = HUB_PATHS.get(category)
        missing_ids = sorted(schedule_ids - hub_visible_ids)
        if category in OPTIONAL_ECOSYSTEMS and missing_ids:
            row_failures.append(
                f"{category} has {len(missing_ids)} mapped future sessions that are not surfaced on the hub."
            )
        for sid in missing_ids[:SAMPLE_LIMIT]:
            session = by_id.get(sid, {})
            missing_inventory.append(
                {
                    "session_id": sid,
                    "course_name": strip_html(session.get("course_name") or session.get("official_course_name") or session.get("raw_course_name")),
                    "start_at": session.get("start_at") or session.get("start"),
                    "expected_hub": expected_hub.name if expected_hub else None,
                    "category": category,
                    "subtype": classify_subtype(session, category),
                    "reason": likely_missing_reason(session, expected_hub.name if expected_hub else None, hub_visible_count, total),
                }
            )

        category_status = status_for(
            category,
            total,
            homepage_preview_count,
            hub_visible_count,
            expected_minimum,
            hub_errors,
            broken_links,
        )
        if category_status == "broken" and row_failures:
            row_warnings = row_failures + row_warnings
        category_rows.append(
            {
                "category": category,
                "future_sessions_total": total,
                "homepage_preview_count": homepage_preview_count,
                "hub_visible_count": hub_visible_count,
                "hub_path": str(HUB_PATHS[category].relative_to(ROOT)).replace("\\", "/") if category in HUB_PATHS else None,
                "expected_minimum": expected_minimum,
                "status": category_status,
                "warnings": row_warnings,
                "opportunities": row_opportunities,
                "broken_links": broken_links[:SAMPLE_LIMIT],
                "subtypes": subtypes,
                "missing_count": len(missing_ids),
                "sample_missing_sessions": missing_inventory[-min(len(missing_ids), SAMPLE_LIMIT):] if missing_ids else [],
            }
        )
        warnings.extend(row_warnings)
        tree[category] = {
            "count": total,
            "homepage_preview_count": homepage_preview_count,
            "hub_visible_count": hub_visible_count,
            "status": category_status,
            "children": dict(sorted(subtype_totals.items())),
        }

    orphan_hub_ids = sorted(all_hub_ids - set(by_id))
    if orphan_hub_ids:
        warnings.append(f"{len(orphan_hub_ids)} hub session IDs were not found in schedule_future.json.")

    hidden_count = sum(row["missing_count"] for row in category_rows if row["category"] != "Group/Other")
    broken_rows = [row for row in category_rows if row["status"] == "broken"]
    warning_rows = [row for row in category_rows if row["status"] == "warning"]
    opportunity_rows = [row for row in category_rows if row["status"] == "opportunity"]
    if broken_rows:
        overall_status = "broken"
    elif warning_rows or warnings:
        overall_status = "warning"
    elif opportunity_rows:
        overall_status = "opportunity"
    else:
        overall_status = "healthy"

    audit = {
        "schema_version": "0.2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_files": {
            "schedule_future": str(SCHEDULE_PATH.relative_to(ROOT)).replace("\\", "/"),
            "hubs": {category: str(path.relative_to(ROOT)).replace("\\", "/") for category, path in HUB_PATHS.items()},
            "homepage": "docs/index.html",
            "homepage_runtime_feed_note": "Homepage previews are client-rendered from stored public schedule feeds; this audit computes the same capped preview counts from schedule_future.json without live crawling.",
        },
        "config": {
            "expected_minimums": EXPECTED_MINIMUMS,
            "homepage_preview_limit": HOME_PREVIEW_LIMIT,
            "dedicated_hub_expected_visible_limit": HUB_EXPECTED_VISIBLE_LIMIT,
            "valid_statuses": sorted(VALID_STATUSES),
        },
        "overall_status": overall_status,
        "warnings": warnings,
        "totals": {
            "future_sessions_total": len(sessions),
            "hub_visible_unique_sessions": len(surfaced_total_ids),
            "hidden_or_not_surfaced_sessions": hidden_count,
            "duplicate_session_ids": len(duplicate_ids),
            "orphan_hub_session_ids": len(orphan_hub_ids),
        },
        "categories": category_rows,
        "tree": tree,
        "missing_inventory_analysis": missing_inventory[:100],
        "orphan_hub_session_ids": orphan_hub_ids[:100],
        "duplicate_session_ids": sorted(duplicate_ids)[:100],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")

    summary_lines = [
        "# Class Mapping Tree Audit",
        "",
        f"- Generated: {audit['generated_at']}",
        f"- Overall status: {overall_status}",
        f"- Future sessions: {len(sessions)}",
        f"- Hub-visible unique sessions: {len(surfaced_total_ids)}",
        f"- Hidden/not surfaced sessions: {hidden_count}",
        "",
        "## Category Summary",
        "",
        "| Category | Future | Home Preview | Hub Visible | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in category_rows:
        summary_lines.append(
            f"| {row['category']} | {row['future_sessions_total']} | {row['homepage_preview_count']} | {row['hub_visible_count']} | {row['status']} |"
        )
    if warnings:
        summary_lines.extend(["", "## Warnings", ""])
        summary_lines.extend(f"- {warning}" for warning in warnings)
    SUMMARY_PATH.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Wrote {SUMMARY_PATH.relative_to(ROOT)}")
    print(f"Overall status: {overall_status}")


if __name__ == "__main__":
    main()
