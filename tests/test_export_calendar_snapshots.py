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

    def test_parse_ics_events_expands_weekly_rrule_inside_export_window(self) -> None:
        window_start = datetime(2026, 6, 19, 0, 0, 0)
        window_end = window_start + timedelta(days=60)
        source = {
            "calendar_source_key": "brian_do_not_schedule",
            "mode": "inverse_blocking",
        }
        ics_text = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:recurring-master
SUMMARY:Jonah to LaCrosse
DTSTART:20260622T060000
DTEND:20260622T083000
RRULE:FREQ=WEEKLY;WKST=SU;UNTIL=20260818T035959Z;BYDAY=FR,MO,TH,TU,WE
LOCATION:Wilmington
END:VEVENT
END:VCALENDAR
"""

        events, skipped = exporter.parse_ics_events(ics_text, source, window_start, window_end)

        expanded = [event for event in events if event["recurrence_source"] == "recurring_expanded_instance"]
        self.assertGreater(len(expanded), 20)
        self.assertTrue(any(event["start"].startswith("2026-08-") for event in expanded))
        self.assertTrue(all(exporter.comparable_dt(window_start) <= exporter.comparable_dt(exporter.parse_ics_datetime(event["start"]) or window_start) <= exporter.comparable_dt(window_end) for event in expanded))
        self.assertTrue(all(event["generated_from_rrule"] for event in expanded))
        self.assertEqual(0, skipped.get("rrule_parse_error:ValueError", 0))

    def test_rrule_until_limits_expansion(self) -> None:
        window_start = datetime(2026, 6, 1, 0, 0, 0)
        window_end = datetime(2026, 8, 31, 0, 0, 0)
        source = {"calendar_source_key": "test", "mode": "explicit_availability"}
        ics_text = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:until-test
SUMMARY:HARD
DTSTART:20260622T090000
DTEND:20260622T100000
RRULE:FREQ=DAILY;UNTIL=20260624T090000
END:VEVENT
END:VCALENDAR
"""

        events, _skipped = exporter.parse_ics_events(ics_text, source, window_start, window_end)
        expanded = [event for event in events if event["recurrence_source"] == "recurring_expanded_instance"]

        self.assertEqual(["2026-06-22T09:00:00", "2026-06-23T09:00:00", "2026-06-24T09:00:00"], [event["start"] for event in expanded])

    def test_rrule_count_limits_expansion(self) -> None:
        window_start = datetime(2026, 6, 1, 0, 0, 0)
        window_end = datetime(2026, 8, 31, 0, 0, 0)
        source = {"calendar_source_key": "test", "mode": "explicit_availability"}
        ics_text = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:count-test
SUMMARY:HARD
DTSTART:20260622T090000
DTEND:20260622T100000
RRULE:FREQ=DAILY;COUNT=2
END:VEVENT
END:VCALENDAR
"""

        events, _skipped = exporter.parse_ics_events(ics_text, source, window_start, window_end)
        expanded = [event for event in events if event["recurrence_source"] == "recurring_expanded_instance"]

        self.assertEqual(["2026-06-22T09:00:00", "2026-06-23T09:00:00"], [event["start"] for event in expanded])

    def test_exdate_suppresses_expanded_occurrence(self) -> None:
        window_start = datetime(2026, 6, 1, 0, 0, 0)
        window_end = datetime(2026, 7, 1, 0, 0, 0)
        source = {"calendar_source_key": "test", "mode": "explicit_availability"}
        ics_text = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:exdate-test
SUMMARY:HARD
DTSTART:20260622T090000
DTEND:20260622T100000
RRULE:FREQ=DAILY;COUNT=3
EXDATE:20260623T090000
END:VEVENT
END:VCALENDAR
"""

        events, skipped = exporter.parse_ics_events(ics_text, source, window_start, window_end)
        expanded = [event for event in events if event["recurrence_source"] == "recurring_expanded_instance"]

        self.assertEqual(["2026-06-22T09:00:00", "2026-06-24T09:00:00"], [event["start"] for event in expanded])
        self.assertEqual(1, skipped["excluded_by_exdate"])

    def test_expanded_rrule_preserves_dtstart_dtend_duration(self) -> None:
        window_start = datetime(2026, 6, 1, 0, 0, 0)
        window_end = datetime(2026, 7, 1, 0, 0, 0)
        source = {"calendar_source_key": "test", "mode": "explicit_availability"}
        ics_text = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:duration-test
SUMMARY:HARD
DTSTART:20260622T090000
DTEND:20260622T113000
RRULE:FREQ=DAILY;COUNT=2
END:VEVENT
END:VCALENDAR
"""

        events, _skipped = exporter.parse_ics_events(ics_text, source, window_start, window_end)
        expanded = [event for event in events if event["recurrence_source"] == "recurring_expanded_instance"]

        self.assertEqual("2026-06-23T11:30:00", expanded[1]["end"])

    def test_timezone_aware_rrule_keeps_local_wall_time(self) -> None:
        window_start = datetime(2026, 6, 1, 0, 0, 0)
        window_end = datetime(2026, 7, 1, 0, 0, 0)
        source = {"calendar_source_key": "test", "mode": "explicit_availability"}
        ics_text = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:tz-test
SUMMARY:HARD
DTSTART;TZID=America/New_York:20260622T090000
DTEND;TZID=America/New_York:20260622T100000
RRULE:FREQ=DAILY;COUNT=2
END:VEVENT
END:VCALENDAR
"""

        events, _skipped = exporter.parse_ics_events(ics_text, source, window_start, window_end)
        expanded = [event for event in events if event["recurrence_source"] == "recurring_expanded_instance"]

        self.assertTrue(expanded[0]["start"].startswith("2026-06-22T09:00:00"))
        self.assertTrue(expanded[1]["start"].startswith("2026-06-23T09:00:00"))

    def test_recurrence_id_override_suppresses_generated_base_occurrence(self) -> None:
        window_start = datetime(2026, 6, 1, 0, 0, 0)
        window_end = datetime(2026, 7, 1, 0, 0, 0)
        source = {"calendar_source_key": "test", "mode": "explicit_availability"}
        ics_text = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:override-test
SUMMARY:HARD
DTSTART:20260622T090000
DTEND:20260622T100000
RRULE:FREQ=DAILY;COUNT=2
END:VEVENT
BEGIN:VEVENT
UID:override-test
RECURRENCE-ID:20260623T090000
SUMMARY:HARD OVERRIDE
DTSTART:20260623T130000
DTEND:20260623T140000
END:VEVENT
END:VCALENDAR
"""

        events, skipped = exporter.parse_ics_events(ics_text, source, window_start, window_end)
        expanded = [event for event in events if event["recurrence_source"] == "recurring_expanded_instance"]
        overrides = [event for event in events if event["recurrence_source"] == "overridden_instance"]

        self.assertEqual(["2026-06-22T09:00:00"], [event["start"] for event in expanded])
        self.assertEqual(["2026-06-23T13:00:00"], [event["start"] for event in overrides])
        self.assertEqual(1, skipped["suppressed_by_recurrence_override"])


if __name__ == "__main__":
    unittest.main()
