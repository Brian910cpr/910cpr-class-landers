from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
HTML = DOCS / "group-training.html"
JS = DOCS / "assets" / "group-training-builder.js"
CSS = DOCS / "css" / "lander.css"


class GroupTrainingBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = HTML.read_text(encoding="utf-8")
        cls.js = JS.read_text(encoding="utf-8")
        cls.css = CSS.read_text(encoding="utf-8")

    def test_training_types_are_peer_rows_with_independent_counts(self) -> None:
        expected = {
            "bls",
            "first_aid_cpr_aed",
            "acls",
            "pals",
            "bloodborne_pathogens",
            "fire_extinguisher",
            "other",
        }
        rows = set(re.findall(r'data-training-row="([^"]+)"', self.html))
        counts = set(re.findall(r'data-count-for="([^"]+)"', self.html))
        self.assertEqual(expected, rows)
        self.assertEqual(expected, counts)
        self.assertNotIn("slug-tabs-group-training", self.html)
        self.assertNotIn("Request on-site BLS", self.html)

    def test_structured_request_supports_mixed_training(self) -> None:
        for contract_key in (
            'schema_version: "training_day_request_v1"',
            "training_items: selectedTraining()",
            "participant_count:",
            "delivery_preference:",
            "location:",
            "timing:",
            "contact:",
            "instructor_availability: \"pending\"",
            "tentative_reservation: \"not_offered\"",
        ):
            self.assertIn(contract_key, self.js)
        self.assertIn("request.training_items.forEach", self.js)

    def test_query_parameter_compatibility(self) -> None:
        self.assertIn("new URLSearchParams(window.location.search)", self.js)
        for key in ("program", "location", "preferred_date", "preferred_time", "preferred_month"):
            self.assertIn(f'params.get("{key}")', self.js)
        adapter = (DOCS / "request_group_session.html").read_text(encoding="utf-8")
        self.assertIn('window.location.search + window.location.hash', adapter)

    def test_summary_email_and_analytics_contracts(self) -> None:
        self.assertIn("window.landerwareTrainingDayRequest", self.js)
        self.assertIn("humanSummary(request)", self.js)
        self.assertIn("JSON.stringify(request, null, 2)", self.js)
        self.assertIn("mailto:info@910cpr.com", self.js)
        self.assertIn('event: "group_training_day_request"', self.js)
        self.assertIn("training_count:", self.js)

    def test_mobile_compaction_contract(self) -> None:
        mobile = re.search(r"@media \(max-width: 640px\) \{(?P<body>.*?)\n\}", self.css, re.S)
        self.assertIsNotNone(mobile)
        body = mobile.group("body")
        self.assertIn(".training-day-row", body)
        self.assertIn("grid-template-columns: minmax(0, 1fr) 78px", body)
        self.assertIn(".training-day-choice small", body)
        self.assertIn("display: none", body)
        self.assertIn(".training-day-mobile-summary", body)

    def test_canonical_and_json_ld_are_valid(self) -> None:
        self.assertIn('<link rel="canonical" href="https://www.910cpr.com/group-training.html">', self.html)
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', self.html, re.S)
        self.assertTrue(blocks)
        payload = json.loads(blocks[0])
        types = {item.get("@type") for item in payload["@graph"]}
        self.assertIn("Service", types)


if __name__ == "__main__":
    unittest.main()
