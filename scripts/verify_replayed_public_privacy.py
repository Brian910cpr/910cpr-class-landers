"""Read-only, source-backed privacy assertion for the disposable public replay.

This checks the *generated* finder/detail/sitemap, not only planner candidates.
Never log source identifiers, appointment dates or customer details.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from scripts import build_index_and_sitemap as catalog
from scripts.refresh_class_registration_routes import DETAIL_ID

ROOT = Path(__file__).resolve().parents[1]
DETAIL_LINK = re.compile(r'class="class-finder-secondary" href="/classes/(\d+)\.html"')
NUMERIC_ID = re.compile(r"\d+")


def verify(root: Path = ROOT) -> dict[str, int]:
    index = root / "docs/classes/index.html"
    sitemap = root / "docs/sitemap.xml"
    html = index.read_text(encoding="utf-8")
    xml = sitemap.read_text(encoding="utf-8")
    ids = DETAIL_LINK.findall(html)
    if len(ids) != len(set(ids)):
        raise ValueError("Public replay privacy gate: duplicate finder identities")
    public_ids = set(ids)
    published_details = []
    for sid in public_ids:
        detail = root / "docs/classes" / (sid + ".html")
        if not detail.is_file():
            raise ValueError("Public replay privacy gate: missing listed detail")
        published_details.append(detail.read_text(encoding="utf-8"))

    # These rows come from the same authoritative source selection used by the
    # finder and route publisher. Include nonpublic locations for negative proof.
    rows = catalog.load_schedule_future_sessions(include_nonpublic_locations=True)
    rejected = set()
    verified_public = set()
    now = datetime.now(catalog.LOCAL_TZ)
    for row in rows:
        sid = str(row.get("session_id") or row.get("id") or "").strip()
        if not sid:
            continue
        public = catalog.schedule_future_to_public_session(row)
        if public is None:
            rejected.add(sid)
        else:
            start = row.get('_parsed_start') or catalog.parse_local_datetime(row.get('start_at', ''))
            if start and start > now and NUMERIC_ID.fullmatch(sid):
                verified_public.add(sid)

    if public_ids != verified_public:
        raise ValueError("Public replay privacy gate: listed IDs disagree with authoritative source")

    tombstoned = 0
    uuid_tombstoned = 0
    for sid in rejected:
        # A nonpublic ID must be absent from *every* currently published public
        # surface, regardless of whether it is an Enrollware number or a UUID.
        if sid in public_ids or (
            f"/classes/{sid}.html" in html
            or f'data-session-id="{sid}"' in html
            or any(
                f"/classes/{sid}.html" in page or f'data-session-id="{sid}"' in page
                for page in published_details
            )
        ):
            raise ValueError("Public replay privacy gate: nonpublic identity leaked into public listing")
        if DETAIL_ID.fullmatch(sid):
            if re.search(
                rf"<loc>\s*https://(?:www\.)?910cpr\.com/classes/{re.escape(sid)}\.html\s*</loc>",
                xml,
            ):
                raise ValueError("Public replay privacy gate: nonpublic sitemap discovery")
            detail = root / "docs/classes" / (sid + ".html")
            if detail.is_file():
                page = detail.read_text(encoding="utf-8")
                if (
                    'name="robots" content="noindex,nofollow"' not in page
                    or "This class is not publicly listed" not in page
                    or sid in page
                    or "enrollware.com" in page
                    or 'data-session-id="' in page
                ):
                    raise ValueError("Public replay privacy gate: nonpublic direct detail not redacted")
                if NUMERIC_ID.fullmatch(sid):
                    tombstoned += 1
                else:
                    uuid_tombstoned += 1

    return {
        "public_detail_count": len(public_ids),
        "rejected_source_identity_count": len(rejected),
        "redacted_numeric_detail_count": tombstoned,
        "redacted_uuid_detail_count": uuid_tombstoned,
    }


if __name__ == "__main__":
    print(verify())
