from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts import build_slug_hubs


class BuildSlugHubsPublicSellableSeedsTest(unittest.TestCase):
    def test_public_sellable_offer_becomes_renderable_appointment_seed(self) -> None:
        offer = {
            "course_id": "329495",
            "course_title": "AHA Heartsaver First Aid CPR AED - Blended",
            "course_family": "Heartsaver",
            "date": "2026-07-04",
            "start_time": "14:30",
            "appointment_display_start": "2026-07-04T14:30:00",
            "appointment_display_end": "2026-07-04T15:15:00",
            "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
            "instructor_display_name": "Brian Ennis",
            "appointmentDayId": 260683,
        }
        catalog = {
            "329495": {
                "course_id": "329495",
                "course_key": "aha_heartsaver_first_aid_cpr_aed_blended",
                "family": "Heartsaver",
                "appointment_allowed": True,
            }
        }

        course_master = {
            "329495": {
                "enrollware_course_id": "329495",
                "course_key": "aha_heartsaver_first_aid_cpr_aed_blended",
                "appointment_seed_allowed": True,
                "dynamic_offer_allowed": False,
                "review_needed_for_scheduling": False,
            }
        }

        with patch.object(build_slug_hubs, "load_course_master_by_id", return_value=course_master):
            row = build_slug_hubs.build_hub_seed_offer_from_public_sellable(
                "offer-329495-instructor_24057895173-20260704-1430",
                offer,
                catalog,
                [],
                {},
            )

        self.assertIsNotNone(row)
        assert row is not None
        self.assertEqual("heartsaver", row["hub_slug"])
        self.assertEqual("appointment_seed_offer", row["display_item_type"])
        self.assertEqual("public_sellable_offers_preview", row["render_source"])
        self.assertIn("appointmentDayId=260683", row["appointment_registration_url"])
        self.assertIn("courseId=329495", row["appointment_registration_url"])
        self.assertIn("hs-fa-cpr-aed-bl", row["tab_ids"])

    def test_existing_enrollware_class_row_can_render_when_dynamic_flags_are_false(self) -> None:
        decision = build_slug_hubs.course_master_public_row_gate(
            row_source="existing_enrollware_class",
            course_id="209806",
            course_key="aha_bls_provider",
            hub_slug="bls",
            tab_ids=["bls-provider"],
            registration_url="https://coastalcprtraining.enrollware.com/enroll?id=13652934",
            course_master_by_id={
                "209806": {
                    "dynamic_offer_allowed": False,
                    "appointment_seed_allowed": False,
                    "review_needed_for_scheduling": True,
                }
            },
        )

        self.assertTrue(decision["allowed"], decision)
        self.assertIn("existing_enrollware_class_allowed", decision["reasons"])

    def test_appointment_seed_row_cannot_render_when_seed_not_allowed(self) -> None:
        offer = {
            "course_id": "329495",
            "course_title": "AHA Heartsaver First Aid CPR AED - Blended",
            "course_family": "Heartsaver",
            "date": "2026-07-04",
            "start_time": "14:30",
            "appointment_display_start": "2026-07-04T14:30:00",
            "appointment_display_end": "2026-07-04T15:15:00",
            "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
            "instructor_display_name": "Brian Ennis",
            "appointmentDayId": 260683,
        }
        catalog = {
            "329495": {
                "course_id": "329495",
                "course_key": "aha_heartsaver_first_aid_cpr_aed_blended",
                "family": "Heartsaver",
                "appointment_allowed": True,
            }
        }
        course_master = {
            "329495": {
                "appointment_seed_allowed": False,
                "dynamic_offer_allowed": False,
                "review_needed_for_scheduling": False,
            }
        }

        with patch.object(build_slug_hubs, "load_course_master_by_id", return_value=course_master):
            row = build_slug_hubs.build_hub_seed_offer_from_public_sellable(
                "offer-329495-instructor_24057895173-20260704-1430",
                offer,
                catalog,
                [],
                {},
            )

        self.assertIsNone(row)

    def test_appointment_seed_row_can_render_with_explicit_exception(self) -> None:
        decision = build_slug_hubs.course_master_public_row_gate(
            row_source="appointment_seed",
            course_id="329495",
            course_key="aha_heartsaver_first_aid_cpr_aed_blended",
            hub_slug="heartsaver",
            tab_ids=["hs-fa-cpr-aed-bl"],
            appointment_day_id="260683",
            start_time="2:30 PM",
            registration_url="https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A30%20PM&courseId=329495",
            explicit_exception=True,
            course_master_by_id={
                "329495": {
                    "appointment_seed_allowed": False,
                    "dynamic_offer_allowed": False,
                    "review_needed_for_scheduling": False,
                }
            },
        )

        self.assertTrue(decision["allowed"], decision)

    def test_dynamic_offer_row_cannot_render_when_dynamic_not_allowed(self) -> None:
        decision = build_slug_hubs.course_master_public_row_gate(
            row_source="dynamic_offer",
            course_id="329495",
            course_key="aha_heartsaver_first_aid_cpr_aed_blended",
            hub_slug="heartsaver",
            tab_ids=["hs-fa-cpr-aed-bl"],
            course_master_by_id={
                "329495": {
                    "dynamic_offer_allowed": False,
                    "appointment_seed_allowed": True,
                    "review_needed_for_scheduling": False,
                }
            },
        )

        self.assertFalse(decision["allowed"], decision)
        self.assertIn("dynamic_offer_not_allowed", decision["reasons"])

    def test_review_needed_blocks_generated_rows(self) -> None:
        for row_source in ("appointment_seed", "dynamic_offer"):
            with self.subTest(row_source=row_source):
                decision = build_slug_hubs.course_master_public_row_gate(
                    row_source=row_source,
                    course_id="329495",
                    course_key="aha_heartsaver_first_aid_cpr_aed_blended",
                    hub_slug="heartsaver",
                    tab_ids=["hs-fa-cpr-aed-bl"],
                    appointment_day_id="260683",
                    start_time="2:30 PM",
                    registration_url="https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A30%20PM&courseId=329495",
                    course_master_by_id={
                        "329495": {
                            "dynamic_offer_allowed": True,
                            "appointment_seed_allowed": True,
                            "review_needed_for_scheduling": True,
                        }
                    },
                )

                self.assertFalse(decision["allowed"], decision)
                self.assertIn("review_needed_for_scheduling", decision["reasons"])

    def test_unknown_course_key_generated_row_cannot_render(self) -> None:
        decision = build_slug_hubs.course_master_public_row_gate(
            row_source="appointment_seed",
            course_id="999999",
            course_key="UNKNOWN",
            hub_slug="heartsaver",
            tab_ids=["hs-fa-cpr-aed-bl"],
            appointment_day_id="260683",
            start_time="2:30 PM",
            registration_url="https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A30%20PM&courseId=999999",
            course_master_by_id={
                "999999": {
                    "dynamic_offer_allowed": True,
                    "appointment_seed_allowed": True,
                    "review_needed_for_scheduling": False,
                }
            },
        )

        self.assertFalse(decision["allowed"], decision)
        self.assertIn("unknown_course_key", decision["reasons"])

    def test_legacy_auto_public_seed_requires_course_id_in_url(self) -> None:
        offer = {
            "public_display_item_type": "appointment_seed_offer",
            "display_item_type": "appointment_seed_offer",
            "seed_publication_mode": "appointment_seed_offer",
            "approval_status": "auto_approved_by_rules",
            "public_ready": True,
            "standalone_class_lander_allowed": False,
            "class_lander_created": False,
            "public_schedule_row_created": False,
            "render_source": "auto_public_appointment_seed",
            "hub_slug": "bls",
            "course_key": "aha_bls_provider_renewal",
            "tab_ids": ["bls-renewal"],
            "appointment_registration_url": "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260713",
            "start_datetime": "2026-08-03T09:00:00-04:00",
        }

        self.assertFalse(build_slug_hubs.is_renderable_appointment_seed_offer(offer))

    def test_pediatric_online_course_maps_to_pediatric_blended_tab(self) -> None:
        self.assertEqual(
            {"hs-pediatric-bl"},
            build_slug_hubs.APPOINTMENT_COURSE_TAB_IDS["aha_heartsaver_pediatric_first_aid_cpr_aed_online"],
        )

    def test_merge_appointment_seed_offers_dedupes_by_href(self) -> None:
        offer = {
            "hub_slug": "heartsaver",
            "appointment_registration_url": "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=1&startTime=2%3A30%20PM&courseId=329495",
            "start_datetime": "2026-07-04T14:30:00",
        }

        merged = build_slug_hubs.merge_appointment_seed_offers(
            {"heartsaver": [offer]},
            {"heartsaver": [dict(offer, render_source="second")]},
        )

        self.assertEqual(1, len(merged["heartsaver"]))


if __name__ == "__main__":
    unittest.main()
