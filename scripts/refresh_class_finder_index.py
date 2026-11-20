"""Refresh only the public class finder from the same seated source snapshot.

The frequent canonical schedule refresh updates schedule_future.json without running
the full site index builder. Refreshing its class finder in that same publication
transaction prevents expired/missing IDs and stale registration claims.
"""
from __future__ import annotations

import re
from datetime import datetime

from scripts.build_index_and_sitemap import (
    CLASSES_INDEX_FILE,
    LOCAL_TZ,
    load_schedule_future_sessions,
    render_classes_finder_index,
    schedule_future_to_public_session,
)


def render_current_class_finder(now: datetime | None = None) -> tuple[str, set[str]]:
    now = now or datetime.now(LOCAL_TZ)
    if now.tzinfo is None:
        raise ValueError("Public schedule cutoff must be timezone-aware")

    source = load_schedule_future_sessions()
    if not source:
        raise ValueError("Canonical public class source unavailable; retaining prior finder")

    future = [
        row for row in source
        if row.get("_parsed_start") and row["_parsed_start"] > now
    ]
    sessions = [
        public for public in (schedule_future_to_public_session(row) for row in future)
        if public is not None
    ]
    if not sessions:
        raise ValueError("No verified public class rows; refusing to publish an empty finder")

    ids = [str(row["session_id"]) for row in sessions]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate public class identity; retaining prior finder")

    # Mirror the full public builder's sorting and presentation exactly.
    sessions.sort(key=lambda row: (
        row.get("display_date", ""),
        row.get("display_time", ""),
        row.get("session_id", ""),
    ))
    html = render_classes_finder_index(
        sessions,
        title="Upcoming CPR Classes | 910CPR",
        h1="Upcoming CPR, BLS, ACLS, PALS, and First Aid classes",
        intro="Use the filters to narrow current scheduled classes by course, date, and location. This page is for available class inventory; use Courses if you still need help choosing the right class.",
        canonical_path="/classes/index.html",
        page_name="Class Inventory",
        eyebrow="Upcoming classes",
        show_category_cards=False,
        show_inventory=True,
    )
    listed_ids = re.findall(
        r'class="class-finder-secondary" href="/classes/(\d+)\.html"', html
    )
    if len(listed_ids) != len(ids) or set(listed_ids) != set(ids):
        raise ValueError("Rendered class listing does not match verified public source")
    return html, set(ids)


def refresh() -> dict[str, int]:
    html, listed_ids = render_current_class_finder()
    CLASSES_INDEX_FILE.write_text(html, encoding="utf-8")
    return {"listed": len(listed_ids)}


if __name__ == "__main__":
    print(refresh())
