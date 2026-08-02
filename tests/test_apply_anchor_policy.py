import unittest

from scripts.anchor_state import promote_seated_sessions
from scripts.apply_anchor_policy import consolidate_node
from scripts.apply_anchor_seat_overrides import apply as apply_overrides


class ApplyAnchorPolicyTests(unittest.TestCase):
    def setUp(self):
        self.sessions = [
            {
                "session_id": "51275",
                "course_id": "359474",
                "course_name": "AHA BLS Provider (Renewal)",
                "start_at": "2026-08-05T09:30:00-04:00",
                "end_at": "2026-08-05T11:30:00-04:00",
                "location_display": ":: Wilmington; Shipyard Blvd - B",
                "lead_instructor_name": "B. Ennis",
                "registered_count": "1 / 20",
                "registration_url": "https://example.test/classes/51275",
            },
            {
                "session_id": "51239",
                "course_id": "210549",
                "course_name": "AHA BLS HeartCode",
                "start_at": "2026-08-05T13:00:00-04:00",
                "end_at": "2026-08-05T14:00:00-04:00",
                "location_display": ":: Wilmington; Shipyard Blvd - B",
                "registered_count": 1,
                "registration_url": "https://example.test/classes/51239",
            },
            {
                "session_id": "51231",
                "course_id": "359474",
                "course_name": "AHA BLS Provider (Renewal)",
                "start_at": "2026-08-05T14:00:00-04:00",
                "end_at": "2026-08-05T16:00:00-04:00",
                "location_display": ":: Wilmington; Shipyard Blvd - B",
                "registered_count": 1,
                "registration_url": "https://example.test/classes/51231",
            },
        ]

    def test_seat_override_converts_zero_count_ical_session(self):
        payload = {"sessions": [{"session_id": "13833211", "registered_count": 0}]}
        changed = apply_overrides(payload, {"13833211": {"registered_count": 1, "appointment_class_id": "51275"}})
        self.assertEqual(changed, 1)
        self.assertEqual(payload["sessions"][0]["registered_count"], 1)
        self.assertTrue(payload["sessions"][0]["confirmed_seated"])
        self.assertEqual(payload["sessions"][0]["appointment_class_id"], "51275")

    def test_every_seated_session_promotes_even_when_course_was_barnacle(self):
        anchors = promote_seated_sessions(self.sessions)
        self.assertEqual(len(anchors), 3)
        self.assertTrue(all(item["schedule_symbol"] == "⚓" for item in anchors))
        self.assertIn("51239", {item["session_id"] for item in anchors})

    def test_later_same_course_offer_reuses_earliest_anchor(self):
        anchors = promote_seated_sessions(self.sessions)
        offer = {
            "courseId": "359474",
            "date": "2026-08-05",
            "start": "2026-08-05T14:00:00-04:00",
            "end": "2026-08-05T16:00:00-04:00",
            "location": ":: Wilmington; Shipyard Blvd - B",
            "registrationUrl": "https://example.test/appointment-1400",
            "label": "2:00 PM",
        }
        stats = {
            "anchor_offers_annotated": 0,
            "scattered_offers_consolidated": 0,
            "duplicate_anchor_offers_removed": 0,
        }
        result = consolidate_node(offer, anchors, stats)
        self.assertEqual(result["session_id"], "51275")
        self.assertEqual(result["start"], "2026-08-05T09:30:00-04:00")
        self.assertEqual(result["registrationUrl"], "https://example.test/classes/51275")
        self.assertEqual(result["schedule_role"], "anchor")
        self.assertTrue(result["label"].startswith("⚓"))
        self.assertEqual(stats["scattered_offers_consolidated"], 1)

    def test_different_course_anchor_is_not_collapsed_into_renewal(self):
        anchors = promote_seated_sessions(self.sessions)
        offer = {
            "course_id": "210549",
            "date": "2026-08-05",
            "start_at": "2026-08-05T13:00:00-04:00",
            "location_display": ":: Wilmington; Shipyard Blvd - B",
            "registration_url": "https://example.test/classes/51239",
        }
        stats = {
            "anchor_offers_annotated": 0,
            "scattered_offers_consolidated": 0,
            "duplicate_anchor_offers_removed": 0,
        }
        result = consolidate_node(offer, anchors, stats)
        self.assertEqual(result["session_id"], "51239")
        self.assertEqual(result["start_at"], "2026-08-05T13:00:00-04:00")


if __name__ == "__main__":
    unittest.main()
