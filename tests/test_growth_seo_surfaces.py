import json
from pathlib import Path
import unittest

from scripts import build_index_and_sitemap
from scripts import build_slug_hubs


ROOT = Path(__file__).resolve().parents[1]


class GrowthSeoSurfaceTests(unittest.TestCase):
    def test_homepage_keeps_direct_course_finder_and_adds_local_search_context(self):
        html = build_index_and_sitemap.render_homepage()
        self.assertIn("CPR, BLS, ACLS &amp; First Aid Classes in Wilmington, NC | 910CPR", html)
        self.assertIn("Find the right CPR class—without guessing", html)
        self.assertIn('id="class-finder"', html)
        self.assertIn('"@type": "LocalBusiness"', html)
        self.assertIn('"@type": "FAQPage"', html)

    def test_group_training_keeps_existing_hub_design_and_adds_service_schema(self):
        payload = json.loads(build_slug_hubs.MANIFEST_PATH.read_text(encoding="utf-8"))
        pages = payload.get("pages", payload)
        banners = payload.get("guidance_banners", {}) if isinstance(payload, dict) else {}
        page = next(item for item in pages if item.get("slug") == "group-training")
        html = build_slug_hubs.render_page(
            page,
            [],
            banners,
            requestable_offers=[],
            appointment_seed_offers=[],
            universal_offers=[],
        )
        self.assertIn('class="card slug-hub-shell"', html)
        self.assertIn('class="section-box slug-tabs-block"', html)
        self.assertIn('"@type": "Service"', html)
        self.assertIn("Healthcare and dental teams", html)
        self.assertIn("Schools and childcare", html)
        self.assertIn("Workplaces and hospitality", html)
        self.assertIn("Wilmington and Coastal North Carolina", html)

    def test_llms_file_points_to_canonical_course_pages(self):
        text = (ROOT / "docs" / "llms.txt").read_text(encoding="utf-8")
        for path in ("bls.html", "acls.html", "pals.html", "heartsaver.html", "group-training.html"):
            self.assertIn(f"https://www.910cpr.com/{path}", text)


if __name__ == "__main__":
    unittest.main()
