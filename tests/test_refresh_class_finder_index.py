"""The class directory may be empty without suppressing dynamic course availability."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from scripts import build_index_and_sitemap as catalog
from scripts import refresh_class_finder_index as finder
from scripts import refresh_class_registration_routes as routes


class ZeroSeatedInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "docs/data/schedule_future.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.other = self.root / "absent_authoritative_report.json"
        self.now = datetime(2026, 11, 20, 14, 30, tzinfo=ZoneInfo("America/New_York"))

    def write_source(self, rows=None, when=None, count=None):
        rows = [] if rows is None else rows
        self.path.write_text(json.dumps({
            "build": {"generated_at": (when or self.now).isoformat(),
                      "counts": {"sessions_output": len(rows) if count is None else count}},
            "sessions": rows,
        }), encoding="utf-8")

    def render(self):
        with patch.object(finder, "SCHEDULE_FUTURE_FILE", self.path), \
             patch.object(finder, "CANONICAL_CLASS_REPORT_FILE", self.other), \
             patch.object(catalog, "SCHEDULE_FUTURE_FILE", self.path), \
             patch.object(catalog, "CANONICAL_CLASS_REPORT_FILE", self.other):
            return finder.render_current_class_finder(self.now)

    def test_public_cards_are_chronological_across_month_boundary(self):
        # A displayed month name is not a sortable timestamp. In production,
        # this placed December cards ahead of upcoming November classes.
        def public_session(session_id, starts_at):
            return {
                "session_id": session_id,
                "course_id": "209806",
                "course_number": "209806",
                "course_name": "AHA BLS Provider (Initial)",
                "start_at": starts_at,
                "location_name": ":: Wilmington; Shipyard Blvd - B",
                "session_status": "active",
                "registration_status": "open",
                "public_direct_booking": True,
                "registration_url": (
                    "https://coastalcprtraining.enrollware.com/enroll?id="
                    + session_id
                ),
            }

        self.write_source([
            public_session("15000102", "2026-12-01T09:00:00-05:00"),
            public_session("15000101", "2026-11-21T09:00:00-05:00"),
        ])
        html, ids = self.render()
        self.assertEqual(ids, {"15000101", "15000102"})
        self.assertLess(
            html.index('href="/classes/15000101.html"'),
            html.index('href="/classes/15000102.html"'),
        )

    def test_recent_valid_zero_inventory_renders_no_phantom_class(self):
        self.write_source()
        html, ids = self.render()
        self.assertEqual(ids, set())
        self.assertIn("0 classes found", html)
        self.assertNotIn('class="class-finder-card', html)
        self.assertNotIn('class="class-finder-primary"', html)
        self.assertIn("/classes/index.html", html)

    def test_private_only_source_is_not_a_public_class(self):
        self.write_source([{"session_id": "private-1", "start_at": "2026-11-21T12:00:00-05:00",
                            "location_name": "Private offsite appointment",
                            "session_status": "active"}])
        html, ids = self.render()
        self.assertEqual(ids, set())
        self.assertNotIn("private-1", html)

    def test_missing_stale_corrupt_and_incoherent_source_cannot_erase_finder(self):
        cases = ["missing", "stale", "unzonened", "corrupt", "count"]
        for case in cases:
            with self.subTest(case=case):
                if self.path.exists():
                    self.path.unlink()
                if case == "stale":
                    self.write_source(when=self.now - timedelta(hours=3))
                if case == "unzonened":
                    self.path.write_text(json.dumps({"build": {"generated_at": "2026-11-20T14:30:00"}, "sessions": []}))
                if case == "corrupt":
                    self.path.write_text('{"build":', encoding="utf-8")
                if case == "count":
                    self.write_source(count=3)
                with self.assertRaises(ValueError):
                    self.render()

    def test_nonempty_finder_cannot_publish_from_stale_or_missing_snapshot(self):
        # A plausible, future-facing class is NOT proof that its source is fresh.
        card = {"session_id": "15000001", "display_date": "November 21, 2026"}
        html = '<a class="class-finder-secondary" href="/classes/15000001.html">Details</a>'
        future_row = {"_parsed_start": self.now + timedelta(days=1)}
        with (
            patch.object(finder, "load_schedule_future_sessions", return_value=[future_row]),
            patch.object(finder, "schedule_future_to_public_session", return_value=card),
            patch.object(finder, "render_classes_finder_index", return_value=html),
        ):
            self.write_source()
            self.assertEqual(self.render()[1], {"15000001"})
            self.write_source(when=self.now - timedelta(hours=3))
            with self.assertRaisesRegex(ValueError, "Unverified zero-class source"):
                self.render()
            self.path.unlink()
            with self.assertRaisesRegex(ValueError, "Unverified zero-class source"):
                self.render()

    def test_safe_route_refresh_accepts_only_verified_empty_finder(self):
        self.write_source()
        html, ids = self.render()
        index = self.root / "docs/classes/index.html"
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(html, encoding="utf-8")
        with patch.object(finder, "render_current_class_finder", return_value=(html, ids)):
            result = routes.refresh(root=self.root)
        self.assertEqual(result, {"listed": 0, "files": 0})
        self.assertEqual(index.read_text(encoding="utf-8"), html)

        with patch.object(finder, "render_current_class_finder", return_value=(html, {"9876"})):
            with self.assertRaisesRegex(ValueError, "mismatches"):
                routes.refresh(root=self.root)

        index.write_text(html + '<article class="class-finder-card">phantom</article>', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unexpected class cards"):
            routes.refresh(root=self.root)


if __name__ == "__main__":
    unittest.main()
