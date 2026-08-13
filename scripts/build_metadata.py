from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")
ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class BuildMetadata:
    dt: datetime
    script: str
    source: str

    @property
    def iso(self) -> str:
        return self.dt.replace(microsecond=0).isoformat()

    @property
    def visible(self) -> str:
        return self.dt.strftime("%Y-%m-%d %H:%M")

    @property
    def code(self) -> str:
        return f"<!-- BUILD_CODE: {self.visible} | {self.script} | {self.source} -->"


def current_build_metadata(script: str, source: str) -> BuildMetadata:
    candidates: list[Path] = []
    script_path = (ROOT / script).resolve()
    if script_path.exists():
        candidates.append(script_path)

    source_path = Path(source)
    if not source_path.is_absolute():
        source_path = (ROOT / source).resolve()
    if source_path.exists():
        candidates.append(source_path)
    else:
        match = re.search(r"\bfrom\s+(.+)$", source)
        if match:
            hinted_source = (ROOT / match.group(1).strip()).resolve()
            if hinted_source.exists():
                candidates.append(hinted_source)

    if candidates:
        latest_mtime = max(path.stat().st_mtime for path in candidates)
        return BuildMetadata(datetime.fromtimestamp(latest_mtime, TZ).replace(microsecond=0), script, source)
    return BuildMetadata(datetime.now(TZ).replace(microsecond=0), script, source)


def build_footer_html(meta: BuildMetadata) -> str:
    # Build details belong in CI, logs, and authenticated operations tools.
    # They are intentionally not delivered in public HTML.
    return ""


def apply_build_metadata(html: str, meta: BuildMetadata) -> str:
    del meta
    out = re.sub(r"<!-- BUILD_CODE: .*? -->\s*", "", html, flags=re.S)
    out = re.sub(r'<meta\s+name=["\']build-date["\'][^>]*>\s*', "", out, flags=re.I)
    out = re.sub(
        r'<div\s+class=["\']build-stamp["\'][^>]*>.*?</div>\s*',
        "",
        out,
        flags=re.I | re.S,
    )
    return out.lstrip()
