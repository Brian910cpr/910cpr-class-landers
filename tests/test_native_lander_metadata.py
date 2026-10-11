from contextlib import ExitStack
from datetime import datetime, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import build_landers
from scripts.canonical_scheduling_demand import resolve_canonical_demand
from tests import test_native_public_anchor


class NativeLanderMetadataTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(build_landers.TZ)
        demand = test_native_public_anchor.NativeAnchorTests().row()
        demand["start_at"] = (self.now + timedelta(days=2)).isoformat()
        demand["end_at"] = (self.now + timedelta(days=2, hours=2)).isoformat()
        self.session = resolve_canonical_demand([], [demand])[0][0]

    def status(self, row):
        return build_landers.session_lander_status(
            row, row["registration_url"], build_landers.parse_dt(row["start_at"]), self.now
        )

    def test_canonical_native_occurrence_resolves_existing_course_mapping(self):
        normalized = build_landers.normalize_session_record(self.session)
        self.assertEqual("mapped", normalized["mapping_status"])
        self.assertEqual("Heartsaver", normalized["mapped_family"])
        self.assertEqual("AHA", normalized["mapped_certifying_body"])
        self.assertNotIn("mapping_status", self.session)
        self.assertNotIn("Unmapped", build_landers.render_confidence_block(normalized))
        self.assertEqual("scheduled", self.status(normalized))

    def test_native_booking_fails_closed_without_current_canonical_proof(self):
        for key, value in [
            ("count_available", False), ("workspace_projection_status", "missing"),
            ("demand_status", "stale_reconciliation"), ("active_registration_count", 0),
            ("source", "enrollware_reconciled"), ("registration_backend", "enrollware"),
            ("public_direct_booking", False), ("location_name", "Private workplace"),
            ("course_id", "unknown"), ("session_id", "lw-not-a-uuid"),
            ("registration_url", "https://example.invalid/register"),
            ("registration_url", "https://coastalcprtraining.enrollware.com/enroll?id=123"),
            ("session_status", "unavailable"),
        ]:
            with self.subTest(key=key):
                self.assertEqual("unavailable", self.status({**self.session, key: value}))
        for key, value, expected in [
            ("registration_status", "closed", "sold_out"),
            ("session_status", "cancelled", "cancelled"),
            ("session_status", "rescheduled", "rescheduled"),
            ("start_at", (self.now - timedelta(days=1)).isoformat(), "completed"),
        ]:
            self.assertEqual(expected, self.status({**self.session, key: value}))

    def test_unknown_or_inactive_course_mapping_is_not_invented(self):
        for entry in [{}, {"active": False, "family": "Heartsaver"}]:
            with patch.object(build_landers, "course_map_entry", return_value=entry):
                self.assertNotIn("mapping_status", build_landers.normalize_session_record(self.session))
                self.assertEqual("unavailable", self.status(self.session))

    def test_complete_html_has_native_cta_and_completed_class_has_no_cta(self):
        past = {**self.session, "session_id": "lw-eb020e4a-b74a-443e-acd8-05727c2a8170",
                "start_at": (self.now - timedelta(days=1)).isoformat()}
        past["registration_url"] = "https://www.910cpr.com/register/?session=" + past["session_id"]
        rows = [self.session, past]
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            source = root / "sessions.json"
            source.write_text(json.dumps({"sessions": rows}), encoding="utf-8")
            stack.enter_context(patch.object(build_landers, "OUTPUT_DIR", root))
            stack.enter_context(patch.object(build_landers, "DEFAULT_DATA_FILE", source))
            stack.enter_context(patch.object(build_landers, "FULL_DATA_FILE", source))
            stack.enter_context(patch.object(build_landers, "write_retained_course_landers_report", return_value={
                "live_specific_class_pages_count": 2, "retained_course_landers_count": 0,
                "needs_review_count": 0, "pages_deleted_count": 0}))
            stack.enter_context(patch("sys.argv", ["build_landers", "--data-file", str(source), "--anchors-only"]))
            build_landers.main()
            future_html = (root / (self.session["session_id"] + ".html")).read_text(encoding="utf-8")
            past_html = (root / (past["session_id"] + ".html")).read_text(encoding="utf-8")
            self.assertIn('class_status: "scheduled"', future_html)
            self.assertIn("Continue to Registration", future_html)
            self.assertIn(self.session["registration_url"], future_html)
            self.assertIn("Heartsaver - First Aid + CPR + AED", future_html)
            self.assertNotIn("Unmapped course metadata", future_html)
            self.assertNotIn("Registration is not currently available", future_html)
            self.assertIn('class_status: "completed"', past_html)
            self.assertNotIn("Continue to Registration", past_html)
            self.assertNotIn("Unmapped course metadata", past_html)
            self.assertEqual(2, len(list(root.glob("*.html"))))


if __name__ == "__main__":
    unittest.main()
