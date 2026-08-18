"""Install the shared light/dark theme controls in every rendered HTML page."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
THEME_VERSION = "20260818.2"
THEME_TAGS = (
    f'<link rel="stylesheet" href="/assets/site-theme.css?v={THEME_VERSION}">\n'
    '<script src="/assets/site-theme.js"></script>\n'
)


def inject_html(text: str) -> tuple[str, bool]:
    theme_block = re.compile(
        r'<link rel="stylesheet" href="/assets/site-theme\.css(?:\?v=[^"]+)?">\s*'
        r'<script src="/assets/site-theme\.js"></script>\s*',
        re.IGNORECASE,
    )
    if theme_block.search(text):
        updated = theme_block.sub(THEME_TAGS, text, count=1)
        return updated, updated != text
    lower = text.lower()
    head_end = lower.find("</head>")
    if head_end < 0:
        return text, False
    return text[:head_end] + THEME_TAGS + text[head_end:], True


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
        missing = [
            path for path in sorted(DOCS.rglob("*.html"))
            if "</head>" in path.read_text(encoding="utf-8", errors="replace").lower()
            and "/assets/site-theme.js" not in path.read_text(encoding="utf-8", errors="replace")
        ]
        if missing:
            raise SystemExit(f"Theme assets missing from {len(missing)} HTML pages; first: {missing[0]}")
        print("Global theme assets present on all rendered HTML pages.")
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
