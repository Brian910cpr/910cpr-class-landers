"""Refresh only the public class finder from the same seated source snapshot.

The frequent canonical schedule refresh updates schedule_future.json without running
the full site index builder. Refreshing its class finder in that same publication
transaction prevents expired/missing IDs and stale registration claims.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta

from scripts.build_index_and_sitemap import (
    CLASSES_INDEX_FILE,
    CANONICAL_CLASS_REPORT_FILE,
    LOCAL_TZ,
    SCHEDULE_FUTURE_FILE,
    load_schedule_future_sessions,
    render_classes_finder_index,
    schedule_future_to_public_session,
)



def _verified_empty_inventory_source(now: datetime) -> None:
    """Only publish seated cards when their source is fresh and valid.

    An absent/corrupt/stale feed cannot justify either nonzero or zero inventory.
    This checks the same authoritative source selection as the public builder.
    Dynamic course-time feeds are published independently of seated class cards.
    """
    source_file = SCHEDULE_FUTURE_FILE
    if CANONICAL_CLASS_REPORT_FILE.exists():
        try:
            candidate = json.loads(CANONICAL_CLASS_REPORT_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError) as exc:
            raise ValueError("Canonical class report unreadable; refusing legacy fallback") from exc
        if not isinstance(candidate, dict) or not isinstance(candidate.get("build"), dict):
            raise ValueError("Canonical class report malformed; refusing legacy fallback")
        if candidate["build"].get("source_mode") == "class_report_authoritative":
            source_file = CANONICAL_CLASS_REPORT_FILE

    try:
        payload = json.loads(source_file.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("sessions"), list):
            raise ValueError("Missing canonical sessions array")
        generated_at = datetime.fromisoformat(str(payload.get("build", {}).get("generated_at") or ""))
        if generated_at.tzinfo is None:
            raise ValueError("Unzoned source timestamp")
        age = now - generated_at
        if age < -timedelta(minutes=5) or age > timedelta(minutes=90):
            raise ValueError("Stale or future-dated source timestamp")
        counts = payload.get("build", {}).get("counts", {})
        if isinstance(counts, dict) and "sessions_output" in counts:
            if counts["sessions_output"] != len(payload["sessions"]):
                raise ValueError("Canonical source count does not match session rows")
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        raise ValueError("Unverified zero-class source; retaining prior finder") from exc


def render_current_class_finder(now: datetime | None = None) -> tuple[str, set[str]]:
    now = now or datetime.now(LOCAL_TZ)
    if now.tzinfo is None:
        raise ValueError("Public schedule cutoff must be timezone-aware")

    # A nonempty listing is no exception to the freshness/identity gate:
    # stale snapshots can retain plausible future "Register" cards.
    _verified_empty_inventory_source(now)
    source = load_schedule_future_sessions()

    future = [
        row for row in source
        if row.get("_parsed_start") and row["_parsed_start"] > now
    ]
    sessions = [
        public for public in (schedule_future_to_public_session(row) for row in future)
        if public is not None
    ]

    ids = [str(row["session_id"]) for row in sessions]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate public class identity; retaining prior finder")

    # Mirror the full public builder's sorting and presentation exactly.
    # Customer cards must follow real chronological starts. The month-name
    # display string sorts December before November and can bury imminent seats.
    sessions.sort(key=lambda row: (
        row.get("start_sort", ""),
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
