from __future__ import annotations

import unittest

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

    def test_auto_public_appointment_seed_requires_full_booking_tuple(self) -> None:
        offer = {
            "public_display_item_type": "appointment_seed_offer",
            "display_item_type": "appointment_seed_offer",
            "seed_publication_mode": "appointment_seed_offer",
            "approval_status": "auto_approved_by_rules",
            "public_ready": True,
            "appointment_registration_url": "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260713",
            "standalone_class_lander_allowed": False,
            "class_lander_created": False,
            "public_schedule_row_created": False,
            "render_source": "auto_public_appointment_seed",
        }

        self.assertFalse(build_slug_hubs.is_renderable_appointment_seed_offer(offer))

        offer["appointment_registration_url"] = (
            "https://coastalcprtraining.enrollware.com/enroll?"
            "appointmentDayId=260713&startTime=9%3A15%20AM&courseId=359474"
        )
        self.assertTrue(build_slug_hubs.is_renderable_appointment_seed_offer(offer))

    def test_render_appointment_seed_offer_card_suppresses_incomplete_tuple(self) -> None:
        offer = {
            "course_title": "AHA BLS Provider Renewal",
            "start_datetime": "2026-08-03T09:00:00-04:00",
            "end_datetime": "2026-08-03T12:00:00-04:00",
            "location_name": "shipyard",
            "instructor_display_name": "Brian",
            "appointment_registration_url": "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260713",
            "render_source": "auto_public_appointment_seed",
        }

        self.assertEqual("", build_slug_hubs.render_appointment_seed_offer_card(offer))


if __name__ == "__main__":
    unittest.main()
