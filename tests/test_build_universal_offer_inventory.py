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
                        "source_availability_window": "test-block",
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
                    },
                    {
                        "course_id": "329495",
                        "course_key": "aha_heartsaver_first_aid_cpr_aed_blended",
                        "official_title": "AHA Heartsaver First Aid CPR AED - Blended",
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
                    },
                    "329495": {
                        "course_id": "329495",
                        "course_key": "aha_heartsaver_first_aid_cpr_aed_blended",
                        "course_code": "AHA_HS_FA_CPR_AED_BL",
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
                            },
                            {
                                "id": "hs-fa-cpr-aed-bl",
                                "label": "First Aid CPR AED - Blended",
                                "course_codes": ["AHA_HS_FA_CPR_AED_BL"],
                            }
                        ],
                    }
                ]
            },
            "course_visibility_policy": {"default_state": "active_public", "courses": {}},
            "universal_offer_policy": {
                "minimum_visible_offers_per_course": 2,
                "minimum_visible_offer_lookahead_days": 60,
                "minimum_lead_hours": 24,
                "enable_planned_visibility": True,
                "planned_visibility_audit_only": True,
                "default_first_public_lead_hours": 24,
                "course_family_first_public_lead_hours": {},
                "max_request_block_offers_per_course": 3,
                "max_block_offers_per_course": 3,
                "max_request_block_offers_per_course_per_week": 2,
                "max_total_request_block_offers_per_hub": 12,
                "max_start_times_per_block_per_page": 3,
                "preferred_start_minutes": ["00", "30", "15", "45"],
                "request_only_families": ["Heartsaver"],
                "stacking_compatibility_groups": {
                    "heartsaver_workplace_stack": ["aha_heartsaver_cpr_aed_online"]
                },
                "course_key_tab_overrides": {
                    "aha_heartsaver_cpr_aed_online": ["hs-cpr-aed-bl"],
                    "aha_heartsaver_first_aid_cpr_aed_blended": ["hs-fa-cpr-aed-bl"],
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
        self.assertEqual("stack-test_block", request_offers[0]["stack_group_id"])
        self.assertEqual("heartsaver_workplace_stack", request_offers[0]["stacking_compatibility_group"])
        self.assertFalse(request_offers[0]["public_schedule_row_created"])
        self.assertFalse(request_offers[0]["standalone_class_lander_created"])
        self.assertEqual(1, payload["summary"]["stack_groups_created"])

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
        min_rejection = next(
            rejection for rejection in payload["stack_trace"]["minimum_visible_offer_rejections"]
            if rejection["course_id"] == "209808"
        )
        self.assertEqual("aha_heartsaver_cpr_aed_online|heartsaver|hs-cpr-aed-bl", min_rejection["visible_inventory_key"])
        self.assertEqual(["hs-cpr-aed-bl"], min_rejection["counted_visible_offer_delivery_buckets"])

    def test_other_heartsaver_delivery_bucket_does_not_block_request_offer(self) -> None:
        loaded = self.base_loaded()
        loaded["schedule_future"] = {
            "sessions": [
                {"session_id": "real-1", "course_id": "329495", "start_at": (datetime.now() + timedelta(days=7)).isoformat()},
                {"session_id": "real-2", "course_id": "329495", "start_at": (datetime.now() + timedelta(days=14)).isoformat()},
            ]
        }

        payload = engine.build_inventory(loaded)

        request_offers = [offer for offer in payload["offers"] if offer["offer_type"] == "request_only_block"]
        self.assertEqual(1, len(request_offers))
        self.assertEqual("209808", request_offers[0]["course_id"])
        self.assertNotIn("minimum_visible_offers_already_met", payload["summary"]["rejections_by_reason"])

    def test_block_start_cap_limits_repeated_candidates(self) -> None:
        loaded = self.base_loaded()
        base = datetime.now() + timedelta(days=7)
        offers = []
        for index, (hour, minute) in enumerate([(18, 0), (20, 0), (22, 0), (23, 30)], start=1):
            start = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
            offers.append({
                **loaded["dynamic_offers_preview"]["offers"][0],
                "offer_id": f"offer-{index}",
                "start_time": start.strftime("%H:%M"),
                "appointment_display_start": start.isoformat(),
                "appointment_display_end": (start + timedelta(minutes=45)).isoformat(),
                "scheduler_consumption_start": start.isoformat(),
                "scheduler_consumption_end": (start + timedelta(minutes=90)).isoformat(),
            })
        loaded["dynamic_offers_preview"]["offers"] = offers
        loaded["universal_offer_policy"]["minimum_visible_offers_per_course"] = 10
        loaded["universal_offer_policy"]["max_request_block_offers_per_course_per_week"] = 10
        loaded["universal_offer_policy"]["max_request_block_offers_per_course"] = 10
        loaded["universal_offer_policy"]["max_block_offers_per_course"] = 10
        loaded["universal_offer_policy"]["max_start_times_per_block_per_page"] = 2

        payload = engine.build_inventory(loaded)

        self.assertEqual(2, payload["summary"]["request_only_block_offers_generated"])
        self.assertIn("max_start_times_per_block_per_page", payload["summary"]["rejections_by_reason"])
        self.assertEqual(1, payload["summary"]["stack_groups_created"])

    def test_inside_lead_time_becomes_planned_visibility_candidate(self) -> None:
        loaded = self.base_loaded()
        start = datetime.now() + timedelta(hours=2)
        loaded["dynamic_offers_preview"]["offers"][0].update({
            "date": start.date().isoformat(),
            "start_time": start.strftime("%H:%M"),
            "appointment_display_start": start.isoformat(),
            "appointment_display_end": (start + timedelta(minutes=45)).isoformat(),
            "scheduler_consumption_start": start.isoformat(),
            "scheduler_consumption_end": (start + timedelta(minutes=90)).isoformat(),
        })

        payload = engine.build_inventory(loaded)

        self.assertEqual(0, payload["summary"]["request_only_block_offers_generated"])
        self.assertEqual(1, payload["summary"]["planned_future_visibility_count"])
        self.assertNotIn("inside_minimum_lead_time", payload["summary"]["rejections_by_reason"])
        planned = payload["planned_future_visibility"][0]
        self.assertEqual("planned_future_visibility", planned["candidate_state"])
        self.assertEqual("inside_minimum_lead_time", planned["not_public_reason"])
        self.assertTrue(planned["would_otherwise_fit"])
        self.assertTrue(planned["request_only_fallback_available"])
        self.assertFalse(planned["deterministic_appointment_url_available"])


if __name__ == "__main__":
    unittest.main()
