import json
import unittest
from pathlib import Path

from scripts.landerware_agent_interface import AgentInterfaceError, find_availability, identify_course


SCHEDULE = {
    "timezone": "America/New_York",
    "sessions": [{
        "session_id": "ew-123", "course_key": "bls-renewal", "course_id": "359474",
        "course_name": "AHA BLS Renewal", "start_at": "2026-08-12T13:00:00-04:00",
        "end_at": "2026-08-12T15:00:00-04:00", "location_display": "Wilmington Office",
        "lead_instructor_name": "Brian", "capacity": 8, "enrolled_count": 3,
    }],
}
OFFERS = {
    "timezone": "America/New_York",
    "courses": [{
        "course_key": "bls-renewal", "course_display_name": "AHA BLS Renewal",
        "offered_options": [{
            "offer_slug": "bls-renewal-wilmington-20260813-1300", "start_time": "2026-08-13T13:00:00-04:00",
            "end_time": "2026-08-13T15:00:00-04:00", "location_name": "Wilmington Office", "instructor": "Brian", "session_status": "proposed",
        }],
    }],
}


class AgentInterfaceTests(unittest.TestCase):
    def test_identify_course_by_durable_key(self):
        result = identify_course({"course_key": "bls-renewal"}, schedule=SCHEDULE, offers=OFFERS, course_master={})
        self.assertEqual("resolved", result["status"])
        self.assertEqual("359474", result["match"]["course_id"])

    def test_availability_is_a_projection_of_final_artifacts(self):
        result = find_availability(
            {"course": {"course_key": "bls-renewal"}, "date_from": "2026-08-12", "date_to": "2026-08-13"},
            schedule=SCHEDULE, offers=OFFERS, course_master={},
        )
        self.assertEqual(["existing_class", "dynamic_offer"], [row["offering_type"] for row in result["options"]])
        self.assertEqual(5, result["options"][0]["remaining_capacity"])

    def test_missing_dynamic_artifact_fails_closed_to_real_classes(self):
        result = find_availability({"course_key": "bls-renewal"}, schedule=SCHEDULE, offers={}, course_master={})
        self.assertEqual(1, result["option_count"])
        self.assertEqual("existing_class", result["options"][0]["offering_type"])

    def test_ambiguous_fuzzy_intent_is_not_guessed(self):
        result = identify_course({"query": "BLS"}, schedule=SCHEDULE, offers=OFFERS, course_master={})
        self.assertEqual("not_found", result["status"])

    def test_invalid_date_range_is_rejected(self):
        with self.assertRaises(AgentInterfaceError):
            find_availability({"course_key": "bls-renewal", "date_from": "2026-08-14", "date_to": "2026-08-12"}, schedule=SCHEDULE, offers=OFFERS, course_master={})

    def test_generated_customer_offer_fixture_matches_public_projection(self):
        fixture_path = Path(__file__).parent / "fixtures" / "customer_facing_offers.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        result = find_availability(
            {"course_key": "bls-renewal"}, schedule={"timezone": "America/New_York", "sessions": []},
            offers=fixture, course_master={},
        )
        # build_slug_hubs.load_customer_facing_offers publishes only proposed
        # options and identifies them by offer_slug/page_slug.
        expected = [
            row["offer_slug"]
            for group in fixture["courses"] if group["course_key"] == "bls-renewal"
            for row in group["offered_options"] if row.get("session_status") == "proposed"
        ]
        self.assertEqual(expected, [row["offering_id"] for row in result["options"]])

    def test_non_proposed_dynamic_rows_fail_closed(self):
        fixture = json.loads(json.dumps(OFFERS))
        fixture["courses"][0]["offered_options"][0]["session_status"] = "suppressed"
        result = find_availability(
            {"course_key": "bls-renewal"}, schedule={"sessions": []}, offers=fixture, course_master={},
        )
        self.assertEqual([], result["options"])


if __name__ == "__main__":
    unittest.main()
