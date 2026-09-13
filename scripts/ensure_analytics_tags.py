from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
GTM_ID = "GTM-PQS8DCBH"
GA4_MEASUREMENT_IDS = ("G-45PBWBK7KR", "G-SL0HBP3RV5")
ANALYTICS_EXCLUSION_COOKIE = "lw_analytics_excluded"
ANALYTICS_EXCLUSION_COOKIES = (ANALYTICS_EXCLUSION_COOKIE, "analytics_excluded")
ATTRIBUTION_SCRIPT_SRC = "/assets/analytics-attribution.js?v=20260912-1"
INTERNAL_PATH_PREFIXES = ("admin", "control-center", "internal", "drafts", "analytics-preferences")

GTM_HEAD_SNIPPET = f"""<!-- Google Tag Manager -->
<script>
(function(w,d,s,l,i,m){{
var internal=/^\\/(admin|control-center|internal|drafts|analytics-preferences)(\\/|$)/.test(w.location.pathname);
var excluded=new RegExp('(?:^|;\\\\s*)(?:{'|'.join(ANALYTICS_EXCLUSION_COOKIES)})=1(?:;|$)').test(d.cookie);
if(internal||excluded){{m.split(',').forEach(function(id){{w['ga-disable-'+id]=true;}});return;}}
w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{GTM_ID}','{','.join(GA4_MEASUREMENT_IDS)}');
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
ATTRIBUTION_SCRIPT_RE = re.compile(
    r'<script\s+src=["\']/assets/analytics-attribution\.js(?:\?[^"\']*)?["\']\s+defer></script>\s*',
    flags=re.IGNORECASE,
)

ATTRIBUTION_SCRIPT_SNIPPET = f'<script src="{ATTRIBUTION_SCRIPT_SRC}" defer></script>'


def should_have_analytics(path: Path) -> bool:
    return not is_internal_path(path)


@dataclass
class AnalyticsAudit:
    path: Path
    head_count: int
    noscript_count: int
    gtm_ids: set[str]
    guarded: bool
    attribution_count: int

    @property
    def status(self) -> str:
        if not should_have_analytics(self.path):
            if self.head_count == 0 and self.noscript_count == 0:
                return "internal_clean"
            return "internal_tagged"
        if (
            self.head_count == 1
            and self.noscript_count == 1
            and self.gtm_ids == {GTM_ID}
            and self.guarded
            and self.attribution_count == 1
        ):
            return "ok"
        if self.head_count == 0 and self.noscript_count == 0:
            return "missing"
        if self.head_count > 1 or self.noscript_count > 1:
            return "duplicate"
        return "malformed_partial_or_stale"


def is_internal_path(path: Path, root: Path = DOCS_DIR) -> bool:
    """Return whether a rendered page is an internal/control surface.

    The fallback keeps unit-test fixtures useful when they model an ``admin``
    subtree outside the repository's docs directory.
    """
    try:
        parts = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        parts = path.parts
        return any(part.lower() in INTERNAL_PATH_PREFIXES for part in parts[:-1])
    return bool(parts) and parts[0].lower() in INTERNAL_PATH_PREFIXES


def audit_html(path: Path) -> AnalyticsAudit:
    text = path.read_text(encoding="utf-8", errors="ignore")
    head_count = len(re.findall(r"googletagmanager\.com/gtm\.js", text, flags=re.IGNORECASE))
    noscript_count = len(re.findall(r"googletagmanager\.com/ns\.html\?id=GTM-PQS8DCBH", text, flags=re.IGNORECASE))
    gtm_ids = set(re.findall(r"GTM-[A-Z0-9]+", text))
    guarded = ANALYTICS_EXCLUSION_COOKIE in text and "ga-disable-" in text
    attribution_count = len(ATTRIBUTION_SCRIPT_RE.findall(text))
    return AnalyticsAudit(
        path=path,
        head_count=head_count,
        noscript_count=noscript_count,
        gtm_ids=gtm_ids,
        guarded=guarded,
        attribution_count=attribution_count,
    )


def normalize_existing_tags(text: str) -> str:
    text = HEAD_BLOCK_RE.sub("", text)
    text = NOSCRIPT_BLOCK_RE.sub("", text)
    return text


def replace_first_remove_rest(text: str, pattern: re.Pattern[str], replacement: str) -> tuple[str, bool]:
    replaced = False

    def choose(_: re.Match[str]) -> str:
        nonlocal replaced
        if replaced:
            return ""
        replaced = True
        return replacement

    return pattern.sub(choose, text), replaced


def insert_head_snippet(text: str) -> str:
    if re.search(r"</head\s*>", text, flags=re.IGNORECASE):
        return re.sub(
            r"</head\s*>",
            lambda _: GTM_HEAD_SNIPPET + "\n</head>",
            text,
            count=1,
            flags=re.IGNORECASE,
        )
    return GTM_HEAD_SNIPPET + "\n" + text


def insert_noscript_snippet(text: str) -> str:
    body_match = re.search(r"<body\b[^>]*>", text, flags=re.IGNORECASE)
    if body_match:
        insert_at = body_match.end()
        return text[:insert_at] + "\n" + GTM_NOSCRIPT_SNIPPET + "\n" + text[insert_at:]
    return text + "\n" + GTM_NOSCRIPT_SNIPPET + "\n"


def insert_attribution_script(text: str) -> str:
    if re.search(r"</head\s*>", text, flags=re.IGNORECASE):
        return re.sub(
            r"</head\s*>",
            lambda _: ATTRIBUTION_SCRIPT_SNIPPET + "\n</head>",
            text,
            count=1,
            flags=re.IGNORECASE,
        )
    return ATTRIBUTION_SCRIPT_SNIPPET + "\n" + text


def ensure_analytics_tag(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="ignore")
    current = audit_html(path)
    if (
        should_have_analytics(path)
        and current.status == "ok"
        and GTM_HEAD_SNIPPET in original
        and original.count(ATTRIBUTION_SCRIPT_SNIPPET) == 1
    ):
        return False
    if not should_have_analytics(path):
        text = ATTRIBUTION_SCRIPT_RE.sub("", original)
        text = normalize_existing_tags(text)
        if text == original:
            return False
        path.write_text(text, encoding="utf-8", newline="")
        return True

    text, had_head = replace_first_remove_rest(original, HEAD_BLOCK_RE, GTM_HEAD_SNIPPET)
    if not had_head:
        text = insert_head_snippet(text)
    text, had_noscript = replace_first_remove_rest(text, NOSCRIPT_BLOCK_RE, GTM_NOSCRIPT_SNIPPET)
    if not had_noscript:
        text = insert_noscript_snippet(text)
    text, had_attribution = replace_first_remove_rest(text, ATTRIBUTION_SCRIPT_RE, ATTRIBUTION_SCRIPT_SNIPPET + "\n")
    if not had_attribution:
        text = insert_attribution_script(text)
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
            if ensure_analytics_tag(item.path):
                changed += 1

    after = scan_html(root)
    counts: dict[str, int] = {}
    for item in after:
        counts[item.status] = counts.get(item.status, 0) + 1

    print(f"HTML pages scanned: {len(after)}")
    print(f"Pages updated: {changed}")
    print(f"Public pages with approved tag: {counts.get('ok', 0)}")
    print(f"Internal pages without tag: {counts.get('internal_clean', 0)}")
    print(f"Internal pages still tagged: {counts.get('internal_tagged', 0)}")
    print(f"Pages missing tag: {counts.get('missing', 0)}")
    print(f"Pages with duplicate tag: {counts.get('duplicate', 0)}")
    print(f"Pages with malformed/partial/stale tag: {counts.get('malformed_partial_or_stale', 0)}")

    bad = [item for item in after if item.status not in {"ok", "internal_clean"}]
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
