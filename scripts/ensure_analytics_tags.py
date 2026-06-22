from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
GTM_ID = "GTM-PQS8DCBH"

GTM_HEAD_SNIPPET = f"""<!-- Google Tag Manager -->
<script>
(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{GTM_ID}');
</script>
<!-- End Google Tag Manager -->"""

GTM_NOSCRIPT_SNIPPET = f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""

HEAD_BLOCK_RE = re.compile(
    r"<!-- Google Tag Manager -->.*?<!-- End Google Tag Manager -->",
    flags=re.IGNORECASE | re.DOTALL,
)
NOSCRIPT_BLOCK_RE = re.compile(
    r"<!-- Google Tag Manager \(noscript\) -->.*?<!-- End Google Tag Manager \(noscript\) -->",
    flags=re.IGNORECASE | re.DOTALL,
)


@dataclass
class AnalyticsAudit:
    path: Path
    head_count: int
    noscript_count: int
    gtm_ids: set[str]

    @property
    def status(self) -> str:
        if self.head_count == 1 and self.noscript_count == 1 and self.gtm_ids == {GTM_ID}:
            return "ok"
        if self.head_count == 0 and self.noscript_count == 0:
            return "missing"
        if self.head_count > 1 or self.noscript_count > 1:
            return "duplicate"
        return "malformed_or_partial"


def audit_html(path: Path) -> AnalyticsAudit:
    text = path.read_text(encoding="utf-8", errors="ignore")
    head_count = len(re.findall(r"googletagmanager\.com/gtm\.js", text, flags=re.IGNORECASE))
    noscript_count = len(re.findall(r"googletagmanager\.com/ns\.html\?id=GTM-PQS8DCBH", text, flags=re.IGNORECASE))
    gtm_ids = set(re.findall(r"GTM-[A-Z0-9]+", text))
    return AnalyticsAudit(path=path, head_count=head_count, noscript_count=noscript_count, gtm_ids=gtm_ids)


def normalize_existing_tags(text: str) -> str:
    text = HEAD_BLOCK_RE.sub("", text)
    text = NOSCRIPT_BLOCK_RE.sub("", text)
    return text


def insert_head_snippet(text: str) -> str:
    if re.search(r"</head\s*>", text, flags=re.IGNORECASE):
        return re.sub(r"</head\s*>", GTM_HEAD_SNIPPET + "\n</head>", text, count=1, flags=re.IGNORECASE)
    return GTM_HEAD_SNIPPET + "\n" + text


def insert_noscript_snippet(text: str) -> str:
    body_match = re.search(r"<body\b[^>]*>", text, flags=re.IGNORECASE)
    if body_match:
        insert_at = body_match.end()
        return text[:insert_at] + "\n" + GTM_NOSCRIPT_SNIPPET + "\n" + text[insert_at:]
    return text + "\n" + GTM_NOSCRIPT_SNIPPET + "\n"


def ensure_analytics_tag(path: Path) -> bool:
    if audit_html(path).status == "ok":
        return False
    original = path.read_text(encoding="utf-8", errors="ignore")
    text = normalize_existing_tags(original)
    text = insert_head_snippet(text)
    text = insert_noscript_snippet(text)
    if text == original:
        return False
    path.write_text(text, encoding="utf-8", newline="")
    return True


def scan_html(root: Path) -> list[AnalyticsAudit]:
    return [audit_html(path) for path in sorted(root.rglob("*.html"))]


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure every public docs HTML page has the approved GTM tag.")
    parser.add_argument("--root", default=str(DOCS_DIR), help="HTML root to scan. Defaults to docs/.")
    parser.add_argument("--check", action="store_true", help="Audit only; do not modify files.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    before = scan_html(root)
    changed = 0
    if not args.check:
        for item in before:
            if item.status != "ok":
                if ensure_analytics_tag(item.path):
                    changed += 1

    after = scan_html(root)
    counts: dict[str, int] = {}
    for item in after:
        counts[item.status] = counts.get(item.status, 0) + 1

    print(f"HTML pages scanned: {len(after)}")
    print(f"Pages updated: {changed}")
    print(f"Pages with approved tag: {counts.get('ok', 0)}")
    print(f"Pages missing tag: {counts.get('missing', 0)}")
    print(f"Pages with duplicate tag: {counts.get('duplicate', 0)}")
    print(f"Pages with malformed/partial tag: {counts.get('malformed_or_partial', 0)}")

    bad = [item for item in after if item.status != "ok"]
    if bad:
        print("Pages needing review:")
        for item in bad[:100]:
            print(f"- {item.path}: {item.status}")
        if len(bad) > 100:
            print(f"- ... {len(bad) - 100} more")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
