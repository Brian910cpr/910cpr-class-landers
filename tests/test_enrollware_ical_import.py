from __future__ import annotations

import json
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zoneinfo import ZoneInfo

from scripts.build_sessions_current import (
    build_sessions_from_enrollware_ical,
    build_session_from_ical_event,
    decode_ical_bytes,
    enrollment_page_unavailable_reason,
    load_course_map,
    parse_ical_events,
)


class EnrollwareIcalImportTests(unittest.TestCase):
    def test_decode_ical_bytes_preserves_cp1252_registered_mark(self) -> None:
        raw = b"SUMMARY:AHA Heartsaver\xae CPR AED Online\r\n"

        text = decode_ical_bytes(raw)

        self.assertIn("Heartsaver® CPR AED Online", text)
        self.assertNotIn("Heartsaver�", text)

    def test_enrollment_page_unavailable_reason_detects_closed_and_full_classes(self) -> None:
        self.assertEqual(
            "enrollware_registration_closed",
            enrollment_page_unavailable_reason("<html>Registration for this class is closed.</html>"),
        )
        self.assertEqual(
            "enrollware_class_full",
            enrollment_page_unavailable_reason("<html>This class is currently full.</html>"),
        )
        self.assertIsNone(enrollment_page_unavailable_reason("<html><button>Register</button></html>"))

    def test_ical_import_retains_closed_and_full_classes_with_direct_booking_disabled(self) -> None:
        ics = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:closed-class
SUMMARY:AHA BLS Provider (Initial)
DESCRIPTION:Instructors:\\nBrian Ennis (lead)
DTSTART:20260701T130000Z
DTEND:20260701T150000Z
LOCATION:NC - Wilmington: 4018 Shipyard Blvd\\; Room B @ 910CPR's Office
URL:https://coastalcprtraining.enrollware.com/enroll?id=111
END:VEVENT
BEGIN:VEVENT
UID:full-class
SUMMARY:AHA BLS Provider (Initial)
DESCRIPTION:Instructors:\\nBrian Ennis (lead)
DTSTART:20260702T130000Z
DTEND:20260702T150000Z
LOCATION:NC - Wilmington: 4018 Shipyard Blvd\\; Room B @ 910CPR's Office
URL:https://coastalcprtraining.enrollware.com/enroll?id=222
END:VEVENT
END:VCALENDAR
"""
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "data" / "sessions_current.json"
            audit = root / "data" / "audit"
            repo_root = Path(__file__).resolve().parents[1]
            course_map = load_course_map(repo_root, "data/config/course_map.json")

            def page_for_url(url: str) -> str:
                if url.endswith("111"):
                    return "Registration for this class is closed."
                if url.endswith("222"):
                    return "This class is currently full."
                return "Register"

            with patch("scripts.build_sessions_current.fetch_ical_text", return_value=ics), patch(
                "scripts.build_sessions_current.fetch_enrollment_page_text",
                side_effect=page_for_url,
            ):
                build_sessions_from_enrollware_ical(
                    repo_root=root,
                    ical_url="https://example.test/calendar.ics",
                    output_path=output,
                    audit_dir=audit,
                    course_map=course_map,
                )

            payload = json_load(output)
            sessions = {session["session_id"]: session for session in payload["sessions"]}
            self.assertEqual({"closed-class", "full-class"}, set(sessions))
            self.assertEqual("closed", sessions["closed-class"]["status"]["registration_status"])
            self.assertEqual("full", sessions["full-class"]["status"]["registration_status"])
            self.assertIs(False, sessions["closed-class"]["status"]["public_direct_booking"])
            self.assertIs(False, sessions["full-class"]["status"]["public_direct_booking"])

    def test_unavailable_registration_filter_does_not_hard_code_stale_session_ids(self) -> None:
        source = (Path(__file__).resolve().parents[1] / "scripts" / "build_sessions_current.py").read_text(encoding="utf-8")
        self.assertNotIn("12774086", source)
        self.assertNotIn("12774096", source)

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

    def test_zero_duration_appointment_event_infers_scheduler_consumption_end(self) -> None:
        ics = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:13740038
SUMMARY:AHA Heartsaver® CPR AED Online
DESCRIPTION:Instructors:\\nBrian Ennis (lead)
DTSTART:20260713T193000Z
DTEND:20260713T193000Z
LOCATION:NC - Wilmington: 4018 Shipyard Blvd\\; Room B @ 910CPR's Office
URL:https://coastalcprtraining.enrollware.com/enroll?id=13740038
END:VEVENT
END:VCALENDAR
"""
        events = parse_ical_events(ics)
        repo_root = Path(__file__).resolve().parents[1]
        course_map = load_course_map(repo_root, "data/config/course_map.json")
        session = build_session_from_ical_event(
            events[0],
            datetime(2026, 7, 9, tzinfo=ZoneInfo("America/New_York")).isoformat(),
            course_map,
        )

        self.assertIsNotNone(session)
        assert session is not None
        self.assertEqual(session["session_id"], "13740038")
        self.assertEqual(session["course"]["course_id"], "209808")
        self.assertEqual(session["start"], "2026-07-13T15:30:00-04:00")
        self.assertEqual(session["end"], "2026-07-13T17:30:00-04:00")
        self.assertEqual(
            session["timing"]["end_inference_reason"],
            "inferred_from_course_consumption_rule_for_zero_duration_ical_event",
        )
        self.assertEqual(session["timing"]["inferred_scheduler_consumption_minutes"], 120)

def json_load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
