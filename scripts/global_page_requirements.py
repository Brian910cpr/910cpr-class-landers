from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
CONFIG_PATH = ROOT / "config" / "global-page-requirements-exclusions.json"
SITE_ORIGIN = "https://www.910cpr.com"
GTM_ID = "GTM-PQS8DCBH"
GLOBAL_CSS = "/assets/css/global.css"

FAVICON_LINKS = (
    ("icon", "/favicon.ico", "any", None),
    ("icon", "/favicon.svg", None, "image/svg+xml"),
    ("icon", "/favicon-32x32.png", "32x32", "image/png"),
    ("icon", "/favicon-16x16.png", "16x16", "image/png"),
    ("apple-touch-icon", "/apple-touch-icon.png", "180x180", None),
)
FAVICON_ASSETS = tuple(href.lstrip("/") for _, href, _, _ in FAVICON_LINKS)

HEAD_START = "<!-- GLOBAL_PAGE_REQUIREMENTS:HEAD START -->"
HEAD_END = "<!-- GLOBAL_PAGE_REQUIREMENTS:HEAD END -->"
BODY_START = "<!-- GLOBAL_PAGE_REQUIREMENTS:BODY START -->"
BODY_END = "<!-- GLOBAL_PAGE_REQUIREMENTS:BODY END -->"

GTM_HEAD_SNIPPET = f"""<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{GTM_ID}');</script>
<!-- End Google Tag Manager -->"""

GTM_NOSCRIPT_SNIPPET = f"""<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={GTM_ID}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->"""


def favicon_markup() -> str:
    lines = []
    for rel, href, sizes, mime in FAVICON_LINKS:
        attrs = [f'rel="{rel}"', f'href="{href}"']
        if mime:
            attrs.append(f'type="{mime}"')
        if sizes:
            attrs.append(f'sizes="{sizes}"')
        lines.append("<link " + " ".join(attrs) + ">")
    return "\n".join(lines)


GLOBAL_HEAD = f"""{HEAD_START}
<meta charset="utf-8">
{GTM_HEAD_SNIPPET}
<meta name="viewport" content="width=device-width, initial-scale=1">
{favicon_markup()}
<link rel="stylesheet" href="{GLOBAL_CSS}">
{HEAD_END}"""

GLOBAL_BODY = f"""{BODY_START}
{GTM_NOSCRIPT_SNIPPET}
{BODY_END}"""

MARKED_HEAD_RE = re.compile(r"\s*" + re.escape(HEAD_START) + r".*?" + re.escape(HEAD_END) + r"\s*", re.I | re.S)
MARKED_BODY_RE = re.compile(r"\s*" + re.escape(BODY_START) + r".*?" + re.escape(BODY_END) + r"\s*", re.I | re.S)
LEGACY_GTM_HEAD_RE = re.compile(r"<!--\s*Google Tag Manager\s*-->.*?<!--\s*End Google Tag Manager\s*-->", re.I | re.S)
LEGACY_GTM_BODY_RE = re.compile(r"<!--\s*Google Tag Manager \(noscript\)\s*-->.*?<!--\s*End Google Tag Manager \(noscript\)\s*-->", re.I | re.S)
CHARSET_RE = re.compile(r"<meta\b(?=[^>]*(?:charset\s*=|http-equiv\s*=\s*['\"]?content-type))[^>]*>", re.I)
VIEWPORT_RE = re.compile(r"<meta\b(?=[^>]*name\s*=\s*['\"]viewport['\"])[^>]*>", re.I)
ICON_RE = re.compile(r"<link\b(?=[^>]*rel\s*=\s*['\"](?:shortcut icon|icon|apple-touch-icon)['\"])[^>]*>\s*", re.I)
GLOBAL_CSS_RE = re.compile(r"<link\b(?=[^>]*href\s*=\s*['\"]/?assets/css/global\.css['\"])[^>]*>\s*", re.I)


@dataclass(frozen=True)
class Exclusion:
    path: str
    reason: str
    excluded_requirements: frozenset[str]


def load_exclusions(path: Path = CONFIG_PATH) -> dict[str, Exclusion]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, Exclusion] = {}
    for raw in payload.get("exclusions", []):
        item = Exclusion(
            path=str(raw["path"]).replace("\\", "/"),
            reason=str(raw["reason"]).strip(),
            excluded_requirements=frozenset(raw.get("excluded_requirements", [])),
        )
        if not item.reason:
            raise ValueError(f"Exclusion has no reason: {item.path}")
        if item.path in result:
            raise ValueError(f"Duplicate exclusion: {item.path}")
        result[item.path] = item
    return result


def repository_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def intended_canonical(path: Path) -> str:
    try:
        rel = path.resolve().relative_to(DOCS_DIR.resolve()).as_posix()
    except ValueError:
        rel = path.name
    if rel == "index.html":
        route = "/"
    elif rel.endswith("/index.html"):
        route = "/" + rel[: -len("index.html")]
    else:
        route = "/" + rel
    return SITE_ORIGIN + route


def canonical_excluded(path: Path, exclusions: dict[str, Exclusion]) -> bool:
    if not exclusions:
        return False
    try:
        key = repository_path(path)
    except ValueError:
        return False
    item = exclusions.get(key)
    return bool(item and "canonical" in item.excluded_requirements)


def ensure_canonical(text: str, path: Path, exclusions: dict[str, Exclusion]) -> str:
    if canonical_excluded(path, exclusions):
        return text
    links = list(re.finditer(r"<link\b(?=[^>]*rel\s*=\s*['\"]canonical['\"])[^>]*>", text, re.I))
    if len(links) == 1:
        return text
    if links:
        keep = links[0].group(0)
        text = re.sub(r"<link\b(?=[^>]*rel\s*=\s*['\"]canonical['\"])[^>]*>\s*", "", text, flags=re.I)
        return re.sub(r"</head\s*>", keep + "\n</head>", text, count=1, flags=re.I)
    tag = f'<link rel="canonical" href="{intended_canonical(path)}">'
    return re.sub(r"</head\s*>", tag + "\n</head>", text, count=1, flags=re.I)


def remove_owned_markup(text: str) -> str:
    text = MARKED_HEAD_RE.sub("", text)
    text = MARKED_BODY_RE.sub("", text)
    text = LEGACY_GTM_BODY_RE.sub("", text)
    text = LEGACY_GTM_HEAD_RE.sub("", text)
    text = CHARSET_RE.sub("", text)
    text = VIEWPORT_RE.sub("", text)
    text = ICON_RE.sub("", text)
    text = GLOBAL_CSS_RE.sub("", text)
    return text


def enforce_html(text: str, path: Path, exclusions: dict[str, Exclusion]) -> str:
    text = remove_owned_markup(text)
    text = re.sub(r"<!doctype\s+html\s*>", "", text, flags=re.I)
    text = "<!doctype html>\n" + re.sub(r"^\s*", "", text)
    text = re.sub(r"<html\b([^>]*)>", lambda m: _normalize_html_tag(m.group(1)), text, count=1, flags=re.I)
    text = re.sub(r"<head\b[^>]*>\s*", lambda m: m.group(0).rstrip() + "\n" + GLOBAL_HEAD + "\n", text, count=1, flags=re.I)
    text = re.sub(r"<body\b[^>]*>\s*", lambda m: m.group(0).rstrip() + "\n" + GLOBAL_BODY + "\n", text, count=1, flags=re.I)
    text = ensure_canonical(text, path, exclusions)
    return re.sub(r"[ \t]+(?=\r?$)", "", text, flags=re.M)


def _normalize_html_tag(attrs: str) -> str:
    attrs = re.sub(r"\s+lang\s*=\s*(['\"]).*?\1", "", attrs, flags=re.I)
    return '<html lang="en"' + attrs + ">"


def process_path(path: Path, exclusions: dict[str, Exclusion] | None = None) -> bool:
    exclusions = exclusions if exclusions is not None else load_exclusions()
    original = path.read_text(encoding="utf-8", errors="strict")
    updated = enforce_html(original, path, exclusions)
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8", newline="")
    return True


def iter_html(root: Path = DOCS_DIR):
    yield from sorted(root.rglob("*.html"))


def validate_exclusion_manifest(exclusions: dict[str, Exclusion]) -> list[str]:
    errors = []
    allowed = {"analytics", "canonical", "favicon", "global_css"}
    for item in exclusions.values():
        target = ROOT / item.path
        if not target.exists():
            errors.append(f"exclusion path does not exist: {item.path}")
        unknown = item.excluded_requirements - allowed
        if unknown:
            errors.append(f"unknown exclusions for {item.path}: {', '.join(sorted(unknown))}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply the authoritative global contract to final docs HTML.")
    parser.add_argument("--root", type=Path, default=DOCS_DIR)
    parser.add_argument("--check", action="store_true", help="Fail if processing would change any HTML.")
    args = parser.parse_args()
    exclusions = load_exclusions()
    manifest_errors = validate_exclusion_manifest(exclusions)
    if manifest_errors:
        print("GLOBAL PAGE REQUIREMENTS CONFIG FAILED")
        for error in manifest_errors:
            print(f"  - {error}")
        return 1
    changed = []
    for path in iter_html(args.root.resolve()):
        original = path.read_text(encoding="utf-8")
        updated = enforce_html(original, path, exclusions)
        if updated != original:
            changed.append(path)
            if not args.check:
                path.write_text(updated, encoding="utf-8", newline="")
    print(f"HTML pages scanned: {len(list(iter_html(args.root.resolve())))}")
    print(f"Pages {'requiring updates' if args.check else 'updated'}: {len(changed)}")
    if args.check and changed:
        for path in changed[:50]:
            print(f"  - {repository_path(path)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
