from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "docs" / "admin" / "admin-port.html"
JS = ROOT / "docs" / "admin" / "admin-port.js"
BUNDLE = ROOT / "data" / "fixtures" / "session_bundle_2026-09-19.json"


class AdminPortTests(unittest.TestCase):
    def test_screen_is_read_only_and_loads_session_bundle(self) -> None:
        html = HTML.read_text(encoding="utf-8")
        js = JS.read_text(encoding="utf-8")
        self.assertIn("Canonical Day Inspector", html)
        self.assertIn("https://schedule.910cpr.com/admin/session-bundles", js)
        self.assertIn("'X-Hot-Sync-Admin-Key':adminKey()", js)
        self.assertNotIn("method:'POST'", js)
        self.assertEqual([], list((ROOT / "docs" / "data" / "session-bundles").glob("*.json")))

    def test_september_19_screen_data_preserves_operational_truth(self) -> None:
        payload = json.loads(BUNDLE.read_text(encoding="utf-8"))
        by_start = {row["start_at"]: row for row in payload["sessions"]}
        self.assertTrue(by_start["2026-09-19T09:00:00-04:00"]["occupancy"]["reserves_customer_availability"])
        self.assertTrue(by_start["2026-09-19T11:00:00-04:00"]["occupancy"]["reserves_customer_availability"])
        self.assertFalse(by_start["2026-09-19T14:00:00-04:00"]["occupancy"]["reserves_customer_availability"])
        self.assertIn("registrations_not_present", {row["code"] for row in payload["missing_dependencies"]})

    def test_navigation_exposes_admin_port(self) -> None:
        nav = (ROOT / "docs" / "admin" / "admin-nav.js").read_text(encoding="utf-8")
        self.assertIn("['/admin/admin-port.html','Admin Port']", nav)


if __name__ == "__main__":
    unittest.main()
