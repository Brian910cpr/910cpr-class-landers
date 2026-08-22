import unittest

from scripts.anchor_state import promote_seated_sessions
from scripts.apply_anchor_policy import apply_selector_policy, consolidate_node
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

    def test_one_barnacle_each_direction_no_recursion_and_outside_returns(self):
        anchors = promote_seated_sessions([self.sessions[0]])
        starts = ["04:30", "05:30", "07:30", "09:00", "09:30", "10:00", "11:30", "13:30", "14:00"]
        courses = []
        dates = [{"date": "2026-08-05", "displayDate": "Wednesday, August 5, 2026", "startTimes": []}]
        for clock in starts:
            offer = {
                "date": "2026-08-05", "displayDate": dates[0]["displayDate"], "startTime": clock,
                "displayStartTime": clock, "courseId": "359474", "courseName": "BLS Renewal",
                "location": ":: Wilmington; Shipyard Blvd - B", "appointmentUrl": f"https://example.test/{clock}",
            }
            if clock == "09:30":
                offer["appointmentUrl"] = self.sessions[0]["registration_url"]
            dates[0]["startTimes"].append({"startTime": clock, "displayStartTime": clock, "courses": [offer]})
            courses.append(offer)
        payload = {"dates": dates, "counts": {}}
        policy = {"families": {"bls": {"course_ids": ["209806", "359474"], "repeat_delay_minutes": 240}}}
        result = apply_selector_policy(payload, anchors, policy)
        rendered = [course for day in result["dates"] for slot in day["startTimes"] for course in slot["courses"]]
        roles = [item.get("schedule_role") for item in rendered]
        self.assertEqual(roles.count("anchor"), 1)
        self.assertGreaterEqual(roles.count("barnacle"), 2)
        self.assertEqual({item["startTime"] for item in rendered if item.get("schedule_role") == "barnacle"}, {"09:00", "10:00"})
        self.assertIn("04:30", {item["startTime"] for item in rendered})
        self.assertIn("14:00", {item["startTime"] for item in rendered})
        self.assertNotIn("07:30", {item["startTime"] for item in rendered})

    def test_other_occupancy_can_push_first_surviving_start_later(self):
        anchors = promote_seated_sessions([self.sessions[0]])
        # The hard-legal input has no 2:00 PM offer; policy must not fabricate one.
        offer = {"date": "2026-08-05", "displayDate": "Wednesday", "startTime": "15:30", "displayStartTime": "3:30 PM", "courseId": "359474", "courseName": "BLS Renewal", "location": ":: Wilmington; Shipyard Blvd - B", "appointmentUrl": "https://example.test/1530"}
        payload = {"dates": [{"date": "2026-08-05", "displayDate": "Wednesday", "startTimes": [{"startTime": "15:30", "displayStartTime": "3:30 PM", "courses": [offer]}]}], "counts": {}}
        policy = {"families": {"bls": {"course_ids": ["209806", "359474"], "repeat_delay_minutes": 240}}}
        result = apply_selector_policy(payload, anchors, policy)
        starts = [slot["startTime"] for day in result["dates"] for slot in day["startTimes"]]
        self.assertEqual(starts, ["15:30"])

    def test_bls_family_suppresses_initial_and_renewal_for_eight_hours_without_barnacles(self):
        anchor_session = {
            **self.sessions[0],
            "start_at": "2026-08-05T10:45:00-04:00",
            "end_at": "2026-08-05T12:45:00-04:00",
        }
        anchors = promote_seated_sessions([anchor_session])
        candidates = (
            ("01:00", "209806", "BLS Initial"),
            ("08:45", "209806", "BLS Initial"),
            ("10:45", "359474", "BLS Renewal"),
            ("12:45", "359474", "BLS Renewal"),
            ("13:15", "210549", "HeartCode BLS"),
            ("19:00", "209806", "BLS Initial"),
        )
        slots = []
        for clock, cid, name in candidates:
            url = anchor_session["registration_url"] if clock == "10:45" else f"https://example.test/{clock}"
            offer = {
                "date": "2026-08-05",
                "displayDate": "Wednesday",
                "startTime": clock,
                "displayStartTime": clock,
                "courseId": cid,
                "courseName": name,
                "appointmentUrl": url,
            }
            slots.append({"startTime": clock, "displayStartTime": clock, "courses": [offer]})
        payload = {"dates": [{"date": "2026-08-05", "displayDate": "Wednesday", "startTimes": slots}], "counts": {}}
        policy = {
            "families": {
                "aha-bls-in-person": {
                    "course_ids": ["209806", "359474"],
                    "repeat_delay_minutes": 480,
                    "retain_barnacle_offers": False,
                }
            }
        }

        result = apply_selector_policy(payload, anchors, policy)
        rendered = [course for day in result["dates"] for slot in day["startTimes"] for course in slot["courses"]]
        starts = {item["startTime"] for item in rendered}
        self.assertEqual(starts, {"01:00", "10:45 AM", "13:15", "19:00"})
        self.assertEqual(sum(item.get("schedule_role") == "anchor" for item in rendered), 1)
        self.assertNotIn("barnacle", {item.get("schedule_role") for item in rendered})

    def test_daily_stack_keeps_each_unpaid_course_only_directly_before_and_after_anchor(self):
        anchor_session = self.sessions[0]
        anchors = promote_seated_sessions([anchor_session])
        slots = []
        for clock, cid, duration in (
            ("07:30", "209806", 60), ("08:30", "209806", 60),
            ("09:30", "359474", 120),
            ("11:30", "209806", 60), ("12:30", "209806", 60),
            ("08:00", "210549", 45), ("08:45", "210549", 45),
            ("11:30", "210549", 45), ("12:15", "210549", 45),
        ):
            url = anchor_session["registration_url"] if cid == "359474" else f"https://example.test/{cid}/{clock}"
            offer = {
                "date": "2026-08-05", "displayDate": "Wednesday", "startTime": clock,
                "displayStartTime": clock, "courseId": cid, "courseName": cid,
                "durationMinutes": duration, "schedulerConsumptionEnd": "11:30" if cid == "359474" else "",
                "appointmentUrl": url,
            }
            slots.append({"startTime": clock, "displayStartTime": clock, "courses": [offer]})
        payload = {"dates": [{"date": "2026-08-05", "displayDate": "Wednesday", "startTimes": slots}], "counts": {}}
        policy = {"mode": "daily_anchor_stack_v1", "one_course_type_per_calendar_day": True}

        result = apply_selector_policy(payload, anchors, policy)
        rendered = [course for day in result["dates"] for slot in day["startTimes"] for course in slot["courses"]]
        by_course = {}
        for item in rendered:
            by_course.setdefault(item["courseId"], []).append(item)
        self.assertEqual(len(by_course["359474"]), 1)
        self.assertEqual({item["startTime"] for item in by_course["209806"]}, {"08:30", "11:30"})
        self.assertEqual({item["startTime"] for item in by_course["210549"]}, {"08:45", "11:30"})
        self.assertTrue(all(item.get("schedule_role") == "barnacle" for cid in ("209806", "210549") for item in by_course[cid]))


if __name__ == "__main__":
    unittest.main()
