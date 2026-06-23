from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from scripts import build_universal_offer_inventory as engine


class UniversalOfferInventoryTests(unittest.TestCase):
    def base_loaded(self) -> dict:
        future = datetime.now() + timedelta(days=7)
        return {
            "schedule_future": {"sessions": []},
            "dynamic_offers_preview": {
                "offers": [
                    {
                        "offer_id": "offer-1",
                        "course_id": "209808",
                        "course_title": "AHA Heartsaver CPR AED Online",
                        "course_family": "Heartsaver",
                        "date": future.date().isoformat(),
                        "start_time": "18:00",
                        "appointment_display_start": future.replace(hour=18, minute=0, second=0, microsecond=0).isoformat(),
                        "appointment_display_end": future.replace(hour=18, minute=45, second=0, microsecond=0).isoformat(),
                        "scheduler_consumption_start": future.replace(hour=18, minute=0, second=0, microsecond=0).isoformat(),
                        "scheduler_consumption_end": future.replace(hour=19, minute=30, second=0, microsecond=0).isoformat(),
                        "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                        "instructor_display_name": "Brian Ennis",
                    }
                ]
            },
            "public_sellable_offers_preview": {"offers": []},
            "seed_appointment_url_preview": {"previews": []},
            "course_catalog": {
                "courses": [
                    {
                        "course_id": "209808",
                        "course_key": "aha_heartsaver_cpr_aed_online",
                        "official_title": "AHA Heartsaver CPR AED Online",
                        "family": "Heartsaver",
                    }
                ]
            },
            "course_map": {
                "courses_by_id": {
                    "209808": {
                        "course_id": "209808",
                        "course_key": "aha_heartsaver_cpr_aed_online",
                        "course_code": "AHA_HS_CPR_AED_BL",
                    }
                }
            },
            "slug_hubs": {
                "pages": [
                    {
                        "slug": "heartsaver",
                        "tabs": [
                            {
                                "id": "hs-cpr-aed-bl",
                                "label": "CPR + AED Only",
                                "course_codes": ["AHA_HS_CPR_AED_BL"],
                            }
                        ],
                    }
                ]
            },
            "course_visibility_policy": {"default_state": "active_public", "courses": {}},
            "universal_offer_policy": {
                "minimum_visible_offers_per_course": 2,
                "minimum_lead_hours": 24,
                "max_request_block_offers_per_course": 3,
                "max_request_block_offers_per_course_per_week": 2,
                "max_total_request_block_offers_per_hub": 12,
                "preferred_start_minutes": ["00", "30", "15", "45"],
                "request_only_families": ["Heartsaver"],
                "course_key_tab_overrides": {
                    "aha_heartsaver_cpr_aed_online": ["hs-cpr-aed-bl"]
                },
            },
        }

    def test_low_inventory_course_gets_request_only_offer(self) -> None:
        payload = engine.build_inventory(self.base_loaded())
        request_offers = [offer for offer in payload["offers"] if offer["offer_type"] == "request_only_block"]
        self.assertEqual(1, len(request_offers))
        self.assertEqual("heartsaver", request_offers[0]["hub_slug"])
        self.assertEqual(["hs-cpr-aed-bl"], request_offers[0]["tab_ids"])
        self.assertTrue(request_offers[0]["request_url"].startswith("/request_group_session.html?"))
        self.assertFalse(request_offers[0]["public_schedule_row_created"])
        self.assertFalse(request_offers[0]["standalone_class_lander_created"])

    def test_real_inventory_meeting_minimum_blocks_request_offer(self) -> None:
        loaded = self.base_loaded()
        loaded["schedule_future"] = {
            "sessions": [
                {"course_id": "209808"},
                {"course_id": "209808"},
            ]
        }
        payload = engine.build_inventory(loaded)
        self.assertEqual(0, payload["summary"]["request_only_block_offers_generated"])
        self.assertIn("minimum_visible_offers_already_met", payload["summary"]["rejections_by_reason"])


if __name__ == "__main__":
    unittest.main()
