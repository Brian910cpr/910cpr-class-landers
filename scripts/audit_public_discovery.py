from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TZ = ZoneInfo("America/New_York")
PUBLIC_SUFFIXES = {".html", ".json", ".js", ".xml", ".txt"}
EXCLUDED_PUBLIC_PREFIXES = ("admin/", "control-center/", "internal/")

PROHIBITED_PUBLIC_PATTERNS: dict[str, re.Pattern[str]] = {
    "RAW SEO POWE-AH": re.compile(r"raw seo powe-ah", re.I),
    "Brian Override": re.compile(r"brian override", re.I),
    "Production Board": re.compile(r"production board", re.I),
    "Bundle Advantage": re.compile(r"bundle advantage", re.I),
    "Value / Work": re.compile(r"value\s*(?:÷|/|divided by)\s*work", re.I),
    "Run Score": re.compile(r"run score", re.I),
    "Discovery Surface Sprint": re.compile(r"discovery surface sprint", re.I),
    "BLS/Wilmington pilot": re.compile(r"bls\s*(?:/|\+)\s*wilmington\s+pilot", re.I),
    "LanderWare truth layer": re.compile(r"landerware truth layer", re.I),
    "inventory contract": re.compile(r"inventory contract", re.I),
    "normalized entity graph": re.compile(r"normalized entity graph", re.I),
    "crawl-surface cleanup": re.compile(r"crawl[- ]surface cleanup", re.I),
    "discovery-health monitor": re.compile(r"discovery[- ]health monitor", re.I),
    "implementation status": re.compile(r"implementation status", re.I),
    "architectural migration": re.compile(r"architectural migration", re.I),
    "backend epic title": re.compile(r"stop letting multiple generators independently reinterpret reality", re.I),
    "Harbor Master / Dockmaster": re.compile(r"harbor master|dockmaster", re.I),
    "browser build diagnostics": re.compile(
        r"BUILD_CODE|data-build-id|copy page diagnostics|class=[\"']build-stamp[\"']|name=[\"']build-date[\"']",
        re.I,
    ),
    "course mapping language": re.compile(r"mapped course details|mapping review needed", re.I),
    "archive/crawl language": re.compile(r"archive support|crawl coverage", re.I),
    "resolved availability language": re.compile(r"live resolved availability", re.I),
    "class inventory language": re.compile(r"upcoming class inventory", re.I),
    "awkward Session heading": re.compile(r">\s*this session\s*<", re.I),
    "browser debug language": re.compile(r"copy diagnostics|diagnostics copied|page diagnostics", re.I),
}


def parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=TZ)
    return parsed.astimezone(TZ)


def public_files(docs_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in docs_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in PUBLIC_SUFFIXES:
            continue
        relative = path.relative_to(docs_dir).as_posix()
        if relative.startswith(EXCLUDED_PUBLIC_PREFIXES):
            continue
        if relative.startswith("data/admin_"):
            continue
        files.append(path)
    return files


def scan_public_language(docs_dir: Path) -> list[dict[str, Any]]:
    leaks: list[dict[str, Any]] = []
    for path in public_files(docs_dir):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in PROHIBITED_PUBLIC_PATTERNS.items():
            matches = list(pattern.finditer(text))
            if matches:
                leaks.append({
                    "file": path.relative_to(docs_dir).as_posix(),
                    "term": label,
                    "count": len(matches),
                })
    return leaks


def sitemap_urls(path: Path) -> list[str]:
    if not path.exists():
        return []
    return re.findall(r"<loc>(.*?)</loc>", path.read_text(encoding="utf-8", errors="ignore"), flags=re.I)


def public_file_for_url(docs_dir: Path, url: str) -> Path | None:
    relative = urlparse(url).path.lstrip("/")
    candidates = [docs_dir / "index.html"] if not relative else []
    if relative.endswith("/"):
        candidates.append(docs_dir / relative / "index.html")
    elif Path(relative).suffix:
        candidates.append(docs_dir / relative)
    else:
        candidates.extend((docs_dir / f"{relative}.html", docs_dir / relative / "index.html"))
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def sitemap_membership_issues(docs_dir: Path, urls: list[str]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for url in urls:
        page = public_file_for_url(docs_dir, url)
        if page is None:
            issues.append({"url": url, "reason": "missing"})
            continue
        html = page.read_text(encoding="utf-8", errors="ignore")
        canonicals = re.findall(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', html, flags=re.I)
        if canonicals != [url]:
            issues.append({"url": url, "reason": f"canonical:{canonicals}"})
        if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', html, flags=re.I):
            issues.append({"url": url, "reason": "noindex"})
    return issues


def audit(repo_root: Path, now: datetime) -> dict[str, Any]:
    docs_dir = repo_root / "docs"
    schedule_path = docs_dir / "data" / "schedule_future.json"
    schedule = json.loads(schedule_path.read_text(encoding="utf-8")) if schedule_path.exists() else {}
    sessions = [row for row in schedule.get("sessions", []) if isinstance(row, dict)]
    current = [row for row in sessions if (parse_dt(row.get("start_at")) or datetime.min.replace(tzinfo=TZ)) > now]
    past_source = [row for row in sessions if parse_dt(row.get("start_at")) and parse_dt(row.get("start_at")) <= now]

    classes_index = (docs_dir / "classes" / "index.html").read_text(encoding="utf-8", errors="ignore")
    rendered_starts = [parse_dt(value) for value in re.findall(r'data-start=["\']([^"\']+)', classes_index, flags=re.I)]
    stale_upcoming = [value.isoformat() for value in rendered_starts if value and value <= now]

    urls = sitemap_urls(docs_dir / "sitemap.xml")
    class_urls = [url for url in urls if re.search(r"/classes/\d+\.html$", url)]
    dated_urls = [url for url in urls if re.search(r"/\d{4}-\d{2}-\d{2}\.html$", url)]
    missing_class_pages = []
    missing_event_markup = []
    missing_booking_urls = []
    invalid_event_json = []
    for url in class_urls:
        relative = urlparse(url).path.lstrip("/")
        page = docs_dir / relative
        if not page.exists():
            missing_class_pages.append(url)
            continue
        html = page.read_text(encoding="utf-8", errors="ignore")
        blocks = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, flags=re.I | re.S)
        if not blocks or not any('"@type": "Event"' in block or '"@type":"Event"' in block for block in blocks):
            missing_event_markup.append(url)
        for block in blocks:
            try:
                json.loads(block)
            except json.JSONDecodeError:
                invalid_event_json.append(url)
                break

    for row in current:
        registration = str(row.get("registration_url") or row.get("register_url") or "").strip()
        if not re.match(r"^https://coastalcprtraining\.enrollware\.com/enroll\?.*\bid=\d+", registration):
            missing_booking_urls.append(str(row.get("session_id") or "unknown"))

    duplicate_signals = {
        "root_and_index_in_sitemap": "https://www.910cpr.com/" in urls and "https://www.910cpr.com/index.html" in urls,
        "hsi_variants_in_sitemap": "https://www.910cpr.com/hsi" in urls and "https://www.910cpr.com/hsi.html" in urls,
    }
    source_age_hours = None
    if schedule_path.exists():
        source_age_hours = round((now.timestamp() - schedule_path.stat().st_mtime) / 3600, 1)

    language_leaks = scan_public_language(docs_dir)
    membership_issues = sitemap_membership_issues(docs_dir, urls)
    failures = {
        "past_sessions_in_upcoming_html": stale_upcoming,
        "sitemap_past_or_future_date_permutations": dated_urls,
        "broken_sitemap_session_files": missing_class_pages,
        "session_pages_missing_event_markup": missing_event_markup,
        "session_pages_with_invalid_json_ld": invalid_event_json,
        "current_sessions_missing_booking_urls": missing_booking_urls,
        "duplicate_canonical_signals": [key for key, present in duplicate_signals.items() if present],
        "sitemap_noncanonical_or_noindex_members": membership_issues,
        "public_internal_language_leaks": language_leaks,
    }
    return {
        "checked_at": now.isoformat(),
        "source": str(schedule_path.relative_to(repo_root)),
        "source_age_hours": source_age_hours,
        "source_session_count": len(sessions),
        "current_source_session_count": len(current),
        "past_source_session_count": len(past_source),
        "sitemap_url_count": len(urls),
        "sitemap_session_count": len(class_urls),
        "sitemap_dated_page_count": len(dated_urls),
        "public_language_terms_checked": list(PROHIBITED_PUBLIC_PATTERNS),
        "failures": failures,
        "ok": not any(failures.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit public discovery output without changing public files.")
    parser.add_argument("--repo-root", default=str(ROOT))
    parser.add_argument("--now", default="")
    parser.add_argument("--output", default="data/audit/public_discovery_health_report.json")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    now = parse_dt(args.now) if args.now else datetime.now(TZ)
    if now is None:
        raise SystemExit("Invalid --now value")
    result = audit(repo_root, now)
    output = repo_root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "failures"}, indent=2))
    for key, values in result["failures"].items():
        print(f"{key}: {len(values)}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
