"""Public inventory must not inherit an explicit private or stale canonical claim."""
import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from scripts import build_index_and_sitemap as catalog
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


    def test_corrupt_canonical_report_cannot_resurrect_legacy_inventory(self):
        # An existing authoritative report must never silently fall back to
        # a legacy class row carrying public_direct_booking=True.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "schedule_future.json"
            canonical = root / "canonical_report.json"
            legacy.write_text(json.dumps({"sessions": [self.row()]}), encoding="utf-8")
            with (
                patch.object(catalog, "SCHEDULE_FUTURE_FILE", legacy),
                patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", canonical),
            ):
                for malformed in ('{"build":', "[]", '{"sessions": []}'):
                    with self.subTest(malformed=malformed):
                        canonical.write_text(malformed, encoding="utf-8")
                        with self.assertRaisesRegex(ValueError, "Canonical class report"):
                            catalog.load_schedule_future_sessions()

    def test_nonpublic_locations_are_visible_only_to_retirement_reader(self):
        # Public inventory cannot render offsite/private-location rows, but
        # the separate retirement pass must see them to scrub old detail HTML.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy = root / "schedule_future.json"
            canonical = root / "no_canonical_report.json"
            private = self.row(session_id="98765433", location_display="Private workplace")
            public = self.row(session_id="98765434", location_display="Wilmington; Shipyard Blvd")
            legacy.write_text(json.dumps({"sessions": [private, public]}), encoding="utf-8")
            with (
                patch.object(catalog, "SCHEDULE_FUTURE_FILE", legacy),
                patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", canonical),
                patch.object(catalog, "session_has_public_class_location",
                             side_effect=lambda row: row.get("location_display") != "Private workplace"),
            ):
                public_rows = catalog.load_schedule_future_sessions()
                retirement_rows = catalog.load_schedule_future_sessions(include_nonpublic_locations=True)
            self.assertEqual({row["session_id"] for row in public_rows}, {"98765434"})
            self.assertEqual({row["session_id"] for row in retirement_rows}, {"98765433", "98765434"})


if __name__ == "__main__":
    unittest.main()
