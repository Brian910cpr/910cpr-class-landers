import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "admin" / "production.html"
SCRIPT = ROOT / "docs" / "admin" / "production.js"
SUMMARY = ROOT / "docs" / "admin" / "production-summary.js"
API = ROOT / "supabase" / "functions" / "production-board" / "index.ts"
MIGRATION = ROOT / "supabase" / "migrations" / "20260812161043_production_board.sql"


class ProductionBoardTests(unittest.TestCase):
    def test_page_is_internal_and_uses_maxim_session(self):
        html = PAGE.read_text(encoding="utf-8")
        js = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('content="noindex,nofollow,noarchive"', html)
        self.assertIn("maxim-portal/login", js)
        self.assertIn("maximPortalSession", js)
        self.assertNotIn("localStorage", js)

    def test_board_has_required_lanes_scoring_and_context_hook(self):
        html = PAGE.read_text(encoding="utf-8")
        js = SCRIPT.read_text(encoding="utf-8")
        for lane in ("doing", "next", "decision", "parked"):
            self.assertIn(f"['{lane}'", js)
        self.assertIn("Number(c.value_score)/", js)
        self.assertIn("Work with ChatGPT", html)
        self.assertIn("/thoughts", js)
        self.assertIn("draggable=\"true\"", js)

    def test_storage_is_server_side_and_seed_is_complete(self):
        sql = MIGRATION.read_text(encoding="utf-8")
        api = API.read_text(encoding="utf-8")
        self.assertIn("enable row level security", sql)
        self.assertIn("revoke all", sql)
        self.assertIn("to service_role", sql)
        self.assertIn("maxim_portal_sessions", api)
        self.assertGreaterEqual(len(re.findall(r"^\('.*','.*','(?:doing|next|decision|parked)'", sql, re.M)), 24)
        self.assertIn("BLS selector 3-column comparison matrix", sql)
        self.assertIn("Preserve existing course IDs", sql)
        self.assertIn("production_board_thoughts", sql)
        self.assertIn("production_board_activity", sql)

    def test_operations_has_protected_summary_hook(self):
        dashboard = (ROOT / "docs" / "admin" / "dashboard.html").read_text(encoding="utf-8")
        summary = SUMMARY.read_text(encoding="utf-8")
        self.assertIn('id="productionSummary"', dashboard)
        self.assertIn("maximPortalSession", summary)
        self.assertIn(".slice(0,6)", summary)


if __name__ == "__main__":
    unittest.main()
