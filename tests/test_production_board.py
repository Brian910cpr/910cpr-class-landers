import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "admin" / "production.html"
SCRIPT = ROOT / "docs" / "admin" / "production.js"
SUMMARY = ROOT / "docs" / "admin" / "production-summary.js"
API = ROOT / "supabase" / "functions" / "production-board" / "index.ts"
MIGRATION = ROOT / "supabase" / "migrations" / "20260812161043_production_board.sql"
CONTEXT_MIGRATION = ROOT / "supabase" / "migrations" / "20260813103000_production_board_context_manifest.sql"
PLANNING_MIGRATION = ROOT / "supabase" / "migrations" / "20260813115137_production_board_epics_dependencies.sql"


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
        self.assertIn("/thoughts", js)
        self.assertIn("draggable=\"true\"", js)
        self.assertIn("Copy standalone handoff", html)
        self.assertIn("Copy raw card JSON", html)
        self.assertIn("landerware-card-context-v1", js)

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

    def test_context_catalog_migration_is_forward_only_and_seeds_tabbed_lanes(self):
        sql = CONTEXT_MIGRATION.read_text(encoding="utf-8")
        self.assertIn("add column if not exists context_manifest jsonb", sql)
        self.assertIn("Tabbed instructor schedule lanes with overlapping cards", sql)
        self.assertIn("Tabbed Lanes Scheduling", sql)
        self.assertIn("Build LanderWare production board", sql)
        self.assertIn('"status": "pending"', sql)
        self.assertIn('"status": "enriched"', sql)

    def test_api_preserves_a_bounded_context_manifest(self):
        api = API.read_text(encoding="utf-8")
        self.assertIn("cleanContext", api)
        self.assertIn("cleanThread", api)
        self.assertIn("review_status", api)
        self.assertIn("confidence", api)
        self.assertIn("context_manifest:cleanContext", api)
        self.assertIn("related_threads", api)
        self.assertNotIn("transcript", api)

    def test_epics_dependencies_and_bundle_scoring_are_supported(self):
        sql = PLANNING_MIGRATION.read_text(encoding="utf-8")
        api = API.read_text(encoding="utf-8")
        js = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("production_board_dependencies", sql)
        self.assertIn("parent_card_id", sql)
        self.assertIn("original_work_score", sql)
        self.assertIn("bundled_work_score", sql)
        self.assertIn("bundle_advantage", sql)
        self.assertIn("Finish Durable Maxim", sql)
        self.assertIn("Private LanderWare Platform", sql)
        self.assertIn("3,000 BLS providers/year", sql)
        self.assertIn('c.card_type==="epic"', api)
        self.assertIn("EPIC · ", js)
        self.assertIn("BLOCKED BY", js)

    def test_operations_has_protected_summary_hook(self):
        dashboard = (ROOT / "docs" / "admin" / "dashboard.html").read_text(encoding="utf-8")
        summary = SUMMARY.read_text(encoding="utf-8")
        self.assertIn('id="productionSummary"', dashboard)
        self.assertIn("maximPortalSession", summary)
        self.assertIn(".slice(0,6)", summary)


if __name__ == "__main__":
    unittest.main()
