from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import build_bls_block_schedule_pilot
from scripts.block_start_time_selector import load_block_schedule_page_configs


ROOT = Path(__file__).resolve().parents[1]


class CoreSelectorSeoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base_payload = json.loads((ROOT / "data" / "audit" / "bls_block_schedule_pilot.json").read_text(encoding="utf-8"))
        cls.configs = load_block_schedule_page_configs()

    def test_core_pages_explain_local_course_funnel_to_people_and_search_engines(self) -> None:
        expected = {
            "bls": "Choose the BLS path that matches your requirement",
            "acls": "Choose the ACLS path that matches your requirement",
            "pals": "Choose the PALS path that matches your requirement",
            "heartsaver": "Choose the Heartsaver course your requirement actually names",
        }
        for page_key, guide_title in expected.items():
            payload = dict(self.base_payload)
            payload["pageKey"] = page_key
            payload["pageConfig"] = self.configs[page_key]
            rendered = build_bls_block_schedule_pilot.render_html(payload)
            with self.subTest(page_key=page_key):
                self.assertIn("Wilmington, NC", rendered)
                self.assertIn("4018 Shipyard Boulevard", rendered)
                self.assertIn('<meta name="description" content="', rendered)
                self.assertIn(guide_title, rendered)


if __name__ == "__main__":
    unittest.main()
