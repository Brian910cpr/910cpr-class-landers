"""Publish safe, time-based class-page retirement without availability credentials."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.build_landers import OUTPUT_DIR, retire_expired_static_landers


ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("America/New_York")
SITEMAP_PATH = ROOT / "docs" / "sitemap.xml"
SIDEBAR_PATTERN = re.compile(
    r'<aside\s+class="current-courses-sidebar".*?</aside>',
    flags=re.I | re.S,
)
ITEM_PATTERN = re.compile(
    r'<li><a\s+href="/classes/(?P<id>[^"/]+)\.html".*?</a></li>',
    flags=re.I | re.S,
)
NOINDEX_PATTERN = re.compile(
    r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*noindex',
    flags=re.I,
)


def retired_class_ids() -> set[str]:
    retired: set[str] = set()
    for path in OUTPUT_DIR.glob("*.html"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if NOINDEX_PATTERN.search(text):
            retired.add(path.stem)
    return retired


def prune_retired_sidebar_links(retired_ids: set[str]) -> int:
    changed = 0
    for path in OUTPUT_DIR.glob("*.html"):
        original = path.read_text(encoding="utf-8", errors="ignore")

        def clean_sidebar(match: re.Match[str]) -> str:
            sidebar = match.group(0)
            cleaned = ITEM_PATTERN.sub(
                lambda item: "" if item.group("id") in retired_ids else item.group(0),
                sidebar,
            )
            if not ITEM_PATTERN.search(cleaned):
                return ""
            return cleaned

        cleaned = SIDEBAR_PATTERN.sub(clean_sidebar, original)
        if cleaned != original:
            path.write_text(cleaned, encoding="utf-8")
            changed += 1
    return changed


def prune_retired_sitemap_urls(retired_ids: set[str]) -> int:
    if not SITEMAP_PATH.exists() or not retired_ids:
        return 0
    original = SITEMAP_PATH.read_text(encoding="utf-8", errors="ignore")
    removed = 0

    def keep_or_remove(match: re.Match[str]) -> str:
        nonlocal removed
        block = match.group(0)
        class_match = re.search(r'/classes/([^/<]+)\.html', block, flags=re.I)
        if class_match and class_match.group(1) in retired_ids:
            removed += 1
            return ""
        return block

    cleaned = re.sub(r'\s*<url>.*?</url>', keep_or_remove, original, flags=re.I | re.S)
    if cleaned != original:
        SITEMAP_PATH.write_text(cleaned.rstrip() + "\n", encoding="utf-8")
    return removed


def main() -> int:
    now = datetime.now(TZ)
    retired_pages = retire_expired_static_landers(now)
    retired_ids = retired_class_ids()
    pruned_pages = prune_retired_sidebar_links(retired_ids)
    pruned_sitemap_urls = prune_retired_sitemap_urls(retired_ids)
    print(f"Retired expired class pages: {retired_pages}")
    print(f"Pruned stale related-course sidebars: {pruned_pages}")
    print(f"Removed retired class URLs from sitemap: {pruned_sitemap_urls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
