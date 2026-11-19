"""Read-only public lead-time contract; no booking or offer decision changes."""
from __future__ import annotations

import json
import unittest

from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload


class PublishedSelectorLeadPolicyTests(unittest.TestCase):
    def test_all_family_feeds_publish_authoritative_lead_hours(self):
        for page in ("bls", "acls", "pals", "heartsaver", "arc", "hsi", "uscg", "family-cpr"):
            with self.subTest(page=page):
                feed = public_selector_availability_payload({
                    "pageKey": page, "minimumLeadHours": 24,
                    "dates": [], "counts": {"publicSelectableOfferCount": 0},
                    "privatePolicy": {"internalToken": "never-expose"},
                })
                self.assertEqual(feed["minimumLeadHours"], 24)
                self.assertEqual(feed["pageKey"], page)
                self.assertEqual(feed["dates"], [])
                self.assertNotIn("never-expose", json.dumps(feed))

    def test_zero_is_explicit_policy_not_missing_policy(self):
        feed = public_selector_availability_payload({"minimumLeadHours": 0, "dates": []})
        self.assertEqual(feed["minimumLeadHours"], 0)

    def test_missing_or_invalid_source_policy_does_not_claim_zero_hours(self):
        for missing in (None, -1, "24", True, 99999):
            with self.subTest(missing=missing):
                feed = public_selector_availability_payload({
                    "minimumLeadHours": missing, "dates": [],
                })
                self.assertIsNone(feed["minimumLeadHours"])
        feed = public_selector_availability_payload({"dates": []})
        self.assertIsNone(feed["minimumLeadHours"])


if __name__ == "__main__":
    unittest.main()
