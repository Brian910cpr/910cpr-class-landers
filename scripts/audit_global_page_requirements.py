from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from scripts.global_page_requirements import (
    DOCS_DIR,
    FAVICON_ASSETS,
    FAVICON_LINKS,
    GLOBAL_CSS,
    GTM_ID,
    ROOT,
    canonical_excluded,
    iter_html,
    load_exclusions,
    repository_path,
    validate_exclusion_manifest,
)


def attr_values(tags, name: str) -> list[str]:
    return [str(tag.get(name, "")) for tag in tags]


def audit_page(path: Path, exclusions) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(text, "html.parser")
    failures: list[str] = []
    doctype_count = len(re.findall(r"<!doctype\s+html\s*>", text, re.I))
    if doctype_count != 1 or not re.match(r"\s*<!doctype\s+html\s*>", text, re.I):
        failures.append(f"expected exactly one leading HTML doctype; found {doctype_count}")
    for name in ("html", "head", "body"):
        count = len(soup.find_all(name))
        if count != 1:
            failures.append(f"expected exactly one <{name}>; found {count}")
    html = soup.find("html")
    head = soup.find("head")
    body = soup.find("body")
    if html and str(html.get("lang", "")).lower() != "en":
        failures.append('html lang must be "en"')
    charsets = soup.find_all("meta", charset=True)
    if len(charsets) != 1 or str(charsets[0].get("charset", "")).lower() != "utf-8":
        failures.append(f"expected one utf-8 charset; found {len(charsets)}")
    viewports = soup.find_all("meta", attrs={"name": re.compile(r"^viewport$", re.I)})
    if len(viewports) != 1 or str(viewports[0].get("content", "")) != "width=device-width, initial-scale=1":
        failures.append(f"expected one approved viewport; found {len(viewports)}")
    titles = soup.find_all("title")
    if len(titles) != 1 or not titles[0].get_text(strip=True):
        failures.append(f"expected one nonblank title; found {len(titles)}")
    for rel, href, sizes, mime in FAVICON_LINKS:
        matches = [tag for tag in soup.find_all("link", href=href) if rel in (tag.get("rel") or [])]
        if len(matches) != 1:
            failures.append(f"expected one {rel} reference to {href}; found {len(matches)}")
    if soup.find("link", rel=lambda value: value and "shortcut" in " ".join(value).lower()):
        failures.append("obsolete shortcut icon declaration present")
    css = soup.find_all("link", href=GLOBAL_CSS)
    if len(css) != 1:
        failures.append(f"expected one global stylesheet {GLOBAL_CSS}; found {len(css)}")
    head_loaders = len(re.findall(r"googletagmanager\.com/gtm\.js", text, re.I))
    body_fallbacks = len(re.findall(rf"googletagmanager\.com/ns\.html\?id={re.escape(GTM_ID)}", text, re.I))
    ids = set(re.findall(r"GTM-[A-Z0-9]+", text))
    if head_loaders != 1:
        failures.append(f"expected one GTM head loader; found {head_loaders}")
    if body_fallbacks != 1:
        failures.append(f"expected one GTM body fallback; found {body_fallbacks}")
    if ids != {GTM_ID}:
        failures.append(f"analytics IDs must be only {GTM_ID}; found {sorted(ids)}")
    if head and head.find("script", string=re.compile(re.escape(GTM_ID))) is None:
        failures.append("approved GTM loader is not inside head")
    if body:
        iframe = body.find("iframe", src=f"https://www.googletagmanager.com/ns.html?id={GTM_ID}")
        if iframe is None:
            failures.append("approved GTM noscript iframe is not inside body")
    canonicals = soup.find_all("link", rel=lambda value: value and "canonical" in value)
    if not canonical_excluded(path, exclusions):
        if len(canonicals) != 1:
            failures.append(f"expected one canonical; found {len(canonicals)}")
        elif not _valid_canonical(str(canonicals[0].get("href", ""))):
            failures.append(f"canonical must use https://www.910cpr.com: {canonicals[0].get('href', '')}")
    robots = [str(tag.get("content", "")).lower() for tag in soup.find_all("meta", attrs={"name": re.compile(r"^robots$", re.I)})]
    robot_tokens = {token.strip() for directive in robots for token in re.split(r"[,;\s]+", directive) if token.strip()}
    if "index" in robot_tokens and "noindex" in robot_tokens:
        failures.append("contradictory robots directives: index and noindex")
    return failures


def _valid_canonical(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.netloc == "www.910cpr.com" and not parsed.query and not parsed.fragment


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit final docs HTML against GLOBAL_PAGE_REQUIREMENTS.")
    parser.add_argument("--root", type=Path, default=DOCS_DIR)
    args = parser.parse_args()
    root = args.root.resolve()
    exclusions = load_exclusions()
    config_failures = validate_exclusion_manifest(exclusions)
    failures: dict[Path, list[str]] = {}
    if not (DOCS_DIR / "assets/css/global.css").is_file():
        config_failures.append("missing required global stylesheet: docs/assets/css/global.css")
    for asset in FAVICON_ASSETS:
        if not (DOCS_DIR / asset).is_file():
            config_failures.append(f"missing favicon asset: docs/{asset}")
    pages = list(iter_html(root))
    for path in pages:
        found = audit_page(path, exclusions)
        if found:
            failures[path] = found
    if config_failures or failures:
        print("GLOBAL PAGE REQUIREMENTS FAILED")
        for error in config_failures:
            print(f"\nconfig\n  - {error}")
        violation_count = len(config_failures)
        for path, found in failures.items():
            print(f"\n{repository_path(path)}")
            for failure in found:
                print(f"  - {failure}")
            violation_count += len(found)
        print(f"\nSummary:\n  {len(pages)} files scanned\n  {len(failures)} files failed\n  {violation_count} violations")
        return 1
    print("GLOBAL PAGE REQUIREMENTS PASSED")
    print(f"Eligible pages scanned: {len(pages)}")
    print(f"Documented exclusions: {len(exclusions)}")
    print("Violations: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
