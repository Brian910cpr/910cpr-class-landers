"""External booking status must be proven before a seated URL is published.

These tests use no real customers, network, bookings, or payments.
"""
import copy
import unittest
from unittest.mock import patch

from scripts import build_sessions_current as source
from scripts import block_start_time_selector as selector


class EnrollwareRegistrationProbeGateTests(unittest.TestCase):
    URL = "https://example.test/enroll?id=fixture-seated"

    def session(self, status):
        return {
            "session_id": "fixture-seated",
            "course_id": "fixture-course",
            "course_name": "Fixture Classroom Course",
            "mapped_family": "Fixture",
            "start_at": "2026-12-01T12:00:00-05:00",
            "end_at": "2026-12-01T14:00:00-05:00",
            "consumption_end_at": "2026-12-01T14:30:00-05:00",
            "registration_url": self.URL,
            "registration_status": status,
            "public_direct_booking": True,
            "session_status": "active",
            "is_full": False,
            "location_name": "Fixture Public Location",
            "lead_instructor_name": "Fixture Instructor",
        }

    def offers(self, session):
        return selector.seated_class_selector_offers(
            schedule_future_payload={"sessions": [session]},
            selected_courses=[{"course_id": "fixture-course", "course_family": "Fixture"}],
            selected_course_ids={"fixture-course"},
            course_rules={"fixture-course": {"duration_minutes": 120, "scheduler_consumption_minutes": 150}},
        )

    def test_failed_status_probe_never_grants_open_registration(self):
        for error in (TimeoutError("probe unavailable"), OSError("network error")):
            with self.subTest(error=type(error).__name__), patch.object(
                source, "fetch_enrollment_page_text", side_effect=error
            ):
                reason = source.enrollment_url_unavailable_reason(self.URL)
                self.assertTrue(reason.startswith("enrollware_registration_status_check_failed:"))
                status = source.registration_status_from_unavailable_reason(reason)
                self.assertEqual(status, "unverified")
                session = self.session(status)
                before = copy.deepcopy(session)
                self.assertFalse(selector.public_direct_bookable_session(session))
                self.assertEqual(self.offers(session), [])
                self.assertEqual(session, before, "withholding a public link must not alter the booked source interval")

    def test_known_closed_and_full_remain_not_publicly_bookable(self):
        for phrase, status in (
            ("Registration for this class is closed", "closed"),
            ("This class is currently full", "full"),
        ):
            with self.subTest(status=status):
                reason = source.enrollment_page_unavailable_reason("<html><p>" + phrase + "</p></html>")
                self.assertEqual(source.registration_status_from_unavailable_reason(reason), status)
                self.assertEqual(self.offers(self.session(status)), [])

    def test_verified_open_status_keeps_existing_public_route_eligible(self):
        with patch.object(source, "fetch_enrollment_page_text", return_value="<html><p>Registration details</p></html>"):
            reason = source.enrollment_url_unavailable_reason(self.URL)
        self.assertIsNone(reason)
        self.assertEqual(source.registration_status_from_unavailable_reason(reason), "open")
        session = self.session("open")
        self.assertTrue(selector.public_direct_bookable_session(session))
        offers = self.offers(session)
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0]["registrationUrl"], self.URL)


if __name__ == "__main__":
    unittest.main()
