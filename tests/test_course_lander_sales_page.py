import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import build_course_landers as builder


class CourseLanderSalesPageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.course = {
            "course_id": "210549",
            "original_course_name": "AHA HeartCode BLS",
            "cert_body": "AHA",
            "price": 55,
            "url_slug": "/heartcode-bls",
            "schedule_url": "/bls.html?course=210549",
            "lander_html": "<h2>Course details</h2><p>Hands-on skills testing.</p>",
        }

    def test_sales_page_has_local_proof_navigation_faq_and_primary_actions(self) -> None:
        with patch.object(builder, "load_review_summary", return_value={"total": 506, "five_star": 496}), patch.object(builder, "proposed_occurrences", return_value=[]):
            page = builder.build_html(self.course, [])
        self.assertIn('aria-label="Main navigation"', page)
        self.assertIn("496 five-star Google reviews", page)
        self.assertIn("Wilmington and southeastern North Carolina", page)
        self.assertIn("See dates and register", page)
        self.assertIn("Train a team on-site", page)
        self.assertIn('"@type": "FAQPage"', page)

    def test_proposed_inventory_is_explicitly_not_a_scheduled_class_or_event(self) -> None:
        occurrence = {"date": "2027-01-08", "start_time": "09:15"}
        with patch.object(builder, "load_review_summary", return_value={"total": 506, "five_star": 496}), patch.object(builder, "proposed_occurrences", return_value=[occurrence]):
            page = builder.build_html(self.course, [])
        self.assertIn("requestable planning times, not scheduled classes and not reserved seats", page)
        schemas = [json.loads(block.split("</script>")[0]) for block in page.split('<script type="application/ld+json">')[1:]]
        self.assertFalse(any('"@type": "Event"' in json.dumps(schema) for schema in schemas))

    def test_proposal_loader_rejects_committed_or_event_eligible_rows(self) -> None:
        payload = {
            "safety_contract": {"event_structured_data_allowed": False},
            "occurrences": [
                {"course_id": "210549", "is_committed_session": False, "emit_event_structured_data": False, "registration_mode": "capture_interest", "date": "2027-01-08", "start_time": "09:15"},
                {"course_id": "210549", "is_committed_session": True, "emit_event_structured_data": False, "registration_mode": "capture_interest", "date": "2027-01-09", "start_time": "09:15"},
                {"course_id": "210549", "is_committed_session": False, "emit_event_structured_data": True, "registration_mode": "capture_interest", "date": "2027-01-10", "start_time": "09:15"},
            ]
        }
        with patch.object(builder, "PROPOSED_INVENTORY_PATH", Path("missing")), patch.object(builder, "load_json", return_value=payload):
            with patch.object(Path, "exists", return_value=True):
                rows = builder.proposed_occurrences("210549")
        self.assertEqual(["2027-01-08"], [row["date"] for row in rows])


if __name__ == "__main__":
    unittest.main()
