from datetime import datetime, timedelta
import unittest

from scripts import build_landers


class PublicSessionLanderTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 7, 12, 0, tzinfo=build_landers.TZ)

    def session(self, session_id, course_id, course_name, days=1, enrolled=0):
        return {
            "session_id": str(session_id),
            "course_id": str(course_id),
            "course_name": course_name,
            "start_at": (self.now + timedelta(days=days)).isoformat(),
            "session_status": "published",
            "registration_status": "open",
            "registration_url": f"https://coastalcprtraining.enrollware.com/enroll?id={session_id}",
            "enrolled_count": enrolled,
        }

    def test_zero_enrollment_public_session_is_direct_bookable(self):
        self.assertTrue(build_landers.is_public_direct_bookable_session(self.session(101, 1, "AHA BLS Provider")))
        self.assertTrue(build_landers.is_session_lander_candidate(self.session(101, 1, "AHA BLS Provider")))

    def test_seated_closed_session_still_gets_a_durable_lander(self):
        session = self.session(101, 1, "AHA BLS Provider", enrolled=1)
        session["registration_status"] = "full"
        session["is_full"] = True
        self.assertFalse(build_landers.is_public_direct_bookable_session(session))
        self.assertTrue(build_landers.is_session_lander_candidate(session))

    def test_past_real_session_remains_indexable(self):
        session = self.session(101, 1, "AHA BLS Provider", days=-1)
        register_url = session["registration_url"]
        status = build_landers.session_lander_status(session, register_url, build_landers.parse_dt(session["start_at"]), self.now)
        self.assertEqual("past_completed", status)
        self.assertEqual("index,follow", build_landers.robots_for_lander_status(status, register_url))

    def test_sidebar_has_one_next_session_for_every_other_current_course(self):
        current = self.session(101, 1, "AHA BLS Provider")
        sessions = [
            current,
            self.session(102, 1, "AHA BLS Provider", days=2),
            self.session(201, 2, "AHA ACLS Provider", days=4),
            self.session(202, 2, "AHA ACLS Provider", days=3),
            self.session(301, 3, "AHA PALS Provider", days=5),
        ]
        other = build_landers.get_other_current_courses(current, sessions, self.now)
        self.assertEqual(["202", "301"], [row["session_id"] for row in other])
        html = build_landers.render_current_courses_sidebar_html(other)
        self.assertIn('/classes/202.html', html)
        self.assertIn('/classes/301.html', html)
        self.assertNotIn('/classes/201.html', html)
        self.assertNotIn('/classes/102.html', html)

    def test_class_templates_cache_bust_the_changed_stylesheet(self):
        self.assertIn('href="{LANDER_CSS_URL}"', build_landers.TEMPLATE)
        self.assertIn("?v=", build_landers.LANDER_CSS_URL)


if __name__ == "__main__":
    unittest.main()
