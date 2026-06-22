from __future__ import annotations

import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.build_sessions_current import (
    build_session_from_ical_event,
    load_course_map,
    parse_ical_events,
)


class EnrollwareIcalImportTests(unittest.TestCase):
    def test_parse_ical_event_and_build_session(self) -> None:
        ics = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:12774257
SUMMARY:AHA BLS Provider (Initial)
DESCRIPTION:Instructors:\\nBrian Ennis (lead)\\n\\nDirections:\\nPublic office directions
DTSTART:20260701T130000Z
DTEND:20260701T150000Z
LOCATION:NC - Wilmington: 4018 Shipyard Blvd\\; Room B @ 910CPR's Office
URL:https://coastalcprtraining.enrollware.com/enroll?id=12774257
END:VEVENT
END:VCALENDAR
"""
        events = parse_ical_events(ics)
        self.assertEqual(len(events), 1)

        repo_root = Path(__file__).resolve().parents[1]
        course_map = load_course_map(repo_root, "data/config/course_map.json")
        session = build_session_from_ical_event(
            events[0],
            datetime(2026, 6, 22, tzinfo=ZoneInfo("America/New_York")).isoformat(),
            course_map,
        )

        self.assertIsNotNone(session)
        assert session is not None
        self.assertEqual(session["session_id"], "12774257")
        self.assertEqual(session["source"], "enrollware_ical")
        self.assertEqual(session["status"]["source_of_truth"], "enrollware_ical")
        self.assertEqual(session["commerce"]["registration_url"], "https://coastalcprtraining.enrollware.com/enroll?id=12774257")
        self.assertEqual(session["staffing"]["lead_instructor_name"], "Brian Ennis")
        self.assertEqual(session["course"]["course_id"], "209806")
        self.assertEqual(session["mapping_status"], "mapped")

    def test_folded_ical_lines_are_unfolded(self) -> None:
        ics = """BEGIN:VCALENDAR
BEGIN:VEVENT
UID:abc123
SUMMARY:HSI BLS and Adult First Aid | Blended Learning
DESCRIPTION:Instructors:\\nBrian Ennis (lead)\\n\\nDirections:\\nLine one
 continued line
DTSTART:20260702T120000Z
DTEND:20260702T130000Z
LOCATION:NC - Wilmington: 4018 Shipyard Blvd
URL:https://coastalcprtraining.enrollware.com/enroll?id=999999
END:VEVENT
END:VCALENDAR
"""
        events = parse_ical_events(ics)
        self.assertEqual(len(events), 1)
        self.assertIn("continued line", events[0]["description"])


if __name__ == "__main__":
    unittest.main()
