from __future__ import annotations

from datetime import datetime, timedelta
import unittest

from scripts import export_calendar_snapshots as exporter


class ExportCalendarSnapshotsTest(unittest.TestCase):
    def test_derives_public_ics_url_from_google_calendar_cid(self) -> None:
        source = {
            "calendar_source_key": "amy_availability",
            "source_url": "https://calendar.google.com/calendar/u/1?cid=test.calendar%40group.calendar.google.com",
        }

        url, url_source = exporter.ics_url_for_source(source)

        self.assertEqual("derived_public_ics", url_source)
        self.assertEqual(
            "https://calendar.google.com/calendar/ical/test.calendar%40group.calendar.google.com/public/basic.ics",
            url,
        )

    def test_derives_public_ics_url_from_explicit_calendar_id(self) -> None:
        source = {
            "calendar_source_key": "amy_availability",
            "calendar_id": "c_94724071aa31a0063fbc48be80fdc73d76e604cad5043ff088156eb97e50be97@group.calendar.google.com",
        }

        url, url_source = exporter.ics_url_for_source(source)

        self.assertEqual("derived_public_ics_from_calendar_id", url_source)
        self.assertIn("c_94724071aa31a0063fbc48be80fdc73d76e604cad5043ff088156eb97e50be97%40group.calendar.google.com", url or "")

    def test_local_secret_overrides_public_calendar_id(self) -> None:
        source = {
            "calendar_source_key": "amy_availability",
            "calendar_id": "public@example.com",
            "local_secret_key": "amy_availability.ics_url",
        }

        url, url_source = exporter.ics_url_for_source(source, {"amy_availability": {"ics_url": "https://secret.example/basic.ics"}})

        self.assertEqual("https://secret.example/basic.ics", url)
        self.assertEqual("local_secret:amy_availability.ics_url", url_source)

    def test_parse_ics_events_keeps_events_inside_export_window(self) -> None:
        window_start = datetime(2026, 6, 1, 0, 0, 0)
        window_end = window_start + timedelta(days=60)
        source = {
            "calendar_source_key": "amy_availability",
            "source_url": "https://calendar.google.com/calendar/u/1?cid=test%40group.calendar.google.com",
            "mode": "explicit_availability",
        }
        ics_text = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:event-1
SUMMARY:HARD
DESCRIPTION:Private details stay in JSON only.
DTSTART:20260622T083000
DTEND:20260622T120000
LOCATION:Shipyard
STATUS:CONFIRMED
LAST-MODIFIED:20260601T120000Z
END:VEVENT
BEGIN:VEVENT
UID:event-old
SUMMARY:HARD
DTSTART:20250101T083000
DTEND:20250101T120000
END:VEVENT
END:VCALENDAR
"""

        events, skipped = exporter.parse_ics_events(ics_text, source, window_start, window_end)

        self.assertEqual(1, len(events))
        self.assertEqual("event-1", events[0]["event_id"])
        self.assertEqual("amy_availability", events[0]["calendar_source_id"])
        self.assertEqual("google_calendar", events[0]["source_type"])
        self.assertEqual("2026-06-22T08:30:00", events[0]["start"])
        self.assertEqual(1, skipped["outside_export_window"])


if __name__ == "__main__":
    unittest.main()
