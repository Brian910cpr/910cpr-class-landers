"""Public inventory must not inherit an explicit private or stale canonical claim."""
import unittest
from unittest.mock import patch

from scripts.build_index_and_sitemap import schedule_future_to_public_session


class CanonicalPublicInventoryGuardTests(unittest.TestCase):
    def row(self, **overrides):
        source = {
            "session_id": "98765432",
            "course_id": "209806",
            "course_number": "209806",
            "course_name": "AHA BLS Provider",
            "session_status": "active",
            "registration_status": "open",
            "public_direct_booking": True,
            "registration_url": "https://coastalcprtraining.enrollware.com/enroll?id=98765432",
            "start_at": "2026-12-15T10:00:00-05:00",
            "location_display": "Wilmington; Shipyard Blvd",
            "canonical_session_id": "synthetic-canonical-id",
            "visibility": "public",
            "demand_status": "current",
        }
        source.update(overrides)
        return source

    @patch("scripts.build_index_and_sitemap.course_allows_classes_inventory", return_value=True)
    @patch("scripts.build_index_and_sitemap.session_has_public_class_location", return_value=True)
    def test_explicit_nonpublic_visibility_never_becomes_public(self, _location, _course):
        for visibility in ("private", "unlisted", "internal", " Unlisted "):
            with self.subTest(visibility=visibility):
                self.assertIsNone(schedule_future_to_public_session(self.row(visibility=visibility)))

    @patch("scripts.build_index_and_sitemap.course_allows_classes_inventory", return_value=True)
    @patch("scripts.build_index_and_sitemap.session_has_public_class_location", return_value=True)
    def test_stale_canonical_claim_cannot_inherit_legacy_public_route(self, _location, _course):
        for state in ("stale_reconciliation", "stale_anchor", "ambiguous"):
            with self.subTest(state=state):
                self.assertIsNone(schedule_future_to_public_session(self.row(demand_status=state, visibility=None)))

    @patch("scripts.build_index_and_sitemap.course_allows_classes_inventory", return_value=True)
    @patch("scripts.build_index_and_sitemap.session_has_public_class_location", return_value=True)
    def test_public_and_external_reconciliation_are_not_indiscriminately_hidden(self, _location, _course):
        for state in ("current", "external_reconciliation_required"):
            with self.subTest(state=state):
                offer = schedule_future_to_public_session(self.row(demand_status=state))
                self.assertIsNotNone(offer)
                self.assertEqual(offer["session_id"], "98765432")

    @patch("scripts.build_index_and_sitemap.course_allows_classes_inventory", return_value=True)
    @patch("scripts.build_index_and_sitemap.session_has_public_class_location", return_value=True)
    def test_unlinked_legacy_rows_do_not_gain_fake_canonical_authority(self, _location, _course):
        offer = schedule_future_to_public_session(self.row(canonical_session_id=None, demand_status=None, visibility=None))
        self.assertIsNotNone(offer)


if __name__ == "__main__":
    unittest.main()
