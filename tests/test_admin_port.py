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
        self.assertIn("functions/v1/canonical-session-workspace", js)
        self.assertIn("'X-Hot-Sync-Admin-Key':adminKey()", js)
        self.assertNotIn("method:'POST'", js)
        self.assertEqual([], list((ROOT / "docs" / "data" / "session-bundles").glob("*.json")))

    def test_screen_uses_server_resolved_canonical_roster_fields(self) -> None:
        js = JS.read_text(encoding="utf-8")
        self.assertIn("CanonicalSessionModel.participantCount(row)", js)
        self.assertIn("CanonicalSessionModel.participantRows(row)", js)
        self.assertIn("row.count_source", js)
        self.assertNotIn("registrations_not_present", js)

    def test_navigation_exposes_admin_port(self) -> None:
        nav = (ROOT / "docs" / "admin" / "admin-nav.js").read_text(encoding="utf-8")
        self.assertIn("['/admin/admin-port.html','Admin Port']", nav)


if __name__ == "__main__":
    unittest.main()
