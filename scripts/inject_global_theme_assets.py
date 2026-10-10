"""Install the shared light/dark theme controls in every rendered HTML page."""
from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
THEME_VERSION = "20260818.5"
BUILD_TZ = ZoneInfo("America/New_York")
SIGNATURE_CLASS = "page-build-signature"
THEME_TAGS = (
    f'<link rel="stylesheet" href="/assets/site-theme.css?v={THEME_VERSION}">\n'
    '<script src="/assets/site-theme.js"></script>\n'
)


def build_signature_html(now: datetime | None = None) -> str:
    stamp = (now or datetime.now(BUILD_TZ)).astimezone(BUILD_TZ).strftime("%Y-%m-%d %H:%M %Z")
    return (
        f'<div class="{SIGNATURE_CLASS}" data-page-build="{stamp}" '
        'style="margin:18px auto 8px;max-width:1120px;padding:0 24px;'
        'font:11px/1.4 Arial,Helvetica,sans-serif;color:#7a8491;'
        'text-align:center;opacity:.78;">'
        f'✦ Page build {stamp}</div>\n'
    )


def inject_html(text: str, *, now: datetime | None = None) -> tuple[str, bool]:
    theme_block = re.compile(
        r'<link rel="stylesheet" href="/assets/site-theme\.css(?:\?v=[^"]+)?">\s*'
        r'<script src="/assets/site-theme\.js"></script>\s*',
        re.IGNORECASE,
    )
    updated = text
    if theme_block.search(updated):
        updated = theme_block.sub(THEME_TAGS, updated, count=1)
    else:
        lower = updated.lower()
        head_end = lower.find("</head>")
        if head_end >= 0:
            updated = updated[:head_end] + THEME_TAGS + updated[head_end:]

    signature_re = re.compile(
        rf'<div\s+class=["\']{re.escape(SIGNATURE_CLASS)}["\'][^>]*>.*?</div>\s*',
        re.IGNORECASE | re.DOTALL,
    )
    signature = build_signature_html(now)
    if signature_re.search(updated):
        updated = signature_re.sub(signature, updated, count=1)
    else:
        lower = updated.lower()
        body_end = lower.rfind("</body>")
        if body_end >= 0:
            updated = updated[:body_end] + signature + updated[body_end:]
    return updated, updated != text


def inject_tree(root: Path = DOCS) -> dict[str, int]:
    counts = {"scanned": 0, "changed": 0, "skipped_without_head": 0}
    for path in sorted(root.rglob("*.html")):
        counts["scanned"] += 1
        original = path.read_text(encoding="utf-8", errors="replace")
        updated, changed = inject_html(original)
        if changed:
            path.write_text(updated, encoding="utf-8")
            counts["changed"] += 1
        elif "</head>" not in original.lower():
            counts["skipped_without_head"] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if any page lacks the global theme assets.")
    args = parser.parse_args()
    if args.check:
        missing_theme = []
        missing_signature = []
        for path in sorted(DOCS.rglob("*.html")):
            content = path.read_text(encoding="utf-8", errors="replace")
            if "</head>" in content.lower() and "/assets/site-theme.js" not in content:
                missing_theme.append(path)
            if "</body>" in content.lower() and f'class="{SIGNATURE_CLASS}"' not in content:
                missing_signature.append(path)
        if missing_theme:
            raise SystemExit(f"Theme assets missing from {len(missing_theme)} HTML pages; first: {missing_theme[0]}")
        if missing_signature:
            raise SystemExit(f"Build signature missing from {len(missing_signature)} HTML pages; first: {missing_signature[0]}")
        print("Global theme assets and build signatures present on all rendered HTML pages.")
        return

    # The Dockmaster hung one lantern with two faces beside every speaking tube:
    # harbor-white for fog, midnight-blue when the watch preferred its stars.
    counts = inject_tree()
    print(
        f"Theme injection scanned {counts['scanned']} pages; changed {counts['changed']}; "
        f"skipped without </head>: {counts['skipped_without_head']}."
    )


if __name__ == "__main__":
    main()
