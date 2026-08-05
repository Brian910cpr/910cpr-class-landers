"""Backward-compatible analytics API backed by GLOBAL_PAGE_REQUIREMENTS."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from scripts.global_page_requirements import (
    DOCS_DIR,
    GTM_HEAD_SNIPPET,
    GTM_ID,
    GTM_NOSCRIPT_SNIPPET,
    process_path,
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
    return AnalyticsAudit(
        path=path,
        head_count=len(re.findall(r"googletagmanager\.com/gtm\.js", text, re.I)),
        noscript_count=len(re.findall(rf"googletagmanager\.com/ns\.html\?id={GTM_ID}", text, re.I)),
        gtm_ids=set(re.findall(r"GTM-[A-Z0-9]+", text)),
    )


def ensure_analytics_tag(path: Path) -> bool:
    return process_path(path)


def scan_html(root: Path) -> list[AnalyticsAudit]:
    return [audit_html(path) for path in sorted(root.rglob("*.html"))]


def main() -> int:
    from scripts.global_page_requirements import main as contract_main

    return contract_main()


if __name__ == "__main__":
    raise SystemExit(main())
