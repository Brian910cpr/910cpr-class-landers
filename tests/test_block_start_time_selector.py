from __future__ import annotations

import json
import unittest
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from scripts import build_bls_block_schedule_pilot
from scripts import block_start_time_selector

ROOT = Path(__file__).resolve().parents[1]
PILOT_REPORT_PATH = ROOT / "data" / "audit" / "bls_block_schedule_pilot.json"


class BlockStartTimeSelectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(PILOT_REPORT_PATH.read_text(encoding="utf-8"))

    def test_uses_live_availability_when_present(self):
        self.assertEqual(self.payload["availability_source_used"], "live_availability_snapshot")
        self.assertFalse(self.payload["availability_fallback_used"])

    def test_bls_offers_are_current_live_traced_when_present(self):
        course_ids = {offer["courseId"] for offer in self.payload["offers"]}
        self.assertLessEqual(course_ids, set(block_start_time_selector.BLS_PILOT_COURSE_IDS))
        self.assertEqual(
            self.payload["counts"]["publicSelectableOfferCount"],
            len(self.payload["offers"]),
        )
        for offer in self.payload["offers"]:
            self.assertTrue(offer.get("availabilityBlockId"))
            self.assertTrue(offer.get("sourceAvailabilityBlock"))

    def test_public_starts_are_inside_business_hours(self):
        for offer in self.payload["offers"]:
            hour, minute = [int(part) for part in offer["startTime"].split(":")]
            self.assertGreaterEqual((hour, minute), (8, 0))
            self.assertLessEqual((hour, minute), (19, 0))
            self.assertNotEqual(offer["startTime"], "00:00")

    def test_appointment_urls_include_required_query_params(self):
        for offer in self.payload["offers"][:25]:
            parsed = urlparse(offer["appointmentUrl"])
            query = parse_qs(parsed.query)
            self.assertEqual(parsed.scheme, "https")
            self.assertEqual(parsed.netloc, "coastalcprtraining.enrollware.com")
            self.assertIn("appointmentDayId", query)
            self.assertIn("startTime", query)
            self.assertEqual(query.get("courseId"), [offer["courseId"]])

    def test_whole_block_is_not_presented_as_class(self):
        self.assertFalse(self.payload["whole_block_presented_as_class"])
        self.assertFalse(self.payload["counts"]["wholeBlockPresentedAsClass"])
        visible_labels = set(self.payload["proof"]["visibleStartLabels"])
        for window in self.payload["proof"]["availabilityWindowsThatGeneratedOffers"]:
            self.assertNotIn(window, visible_labels)

    def test_rendered_html_has_register_links_but_not_block_class_label(self):
        html = build_bls_block_schedule_pilot.render_html(self.payload)
        self.assertIn("BLS Schedule Pilot", html)
        self.assertIn("Register", html)
        if self.payload["offers"]:
            self.assertIn("appointmentDayId", html)
        self.assertIn("Need BLS ASAP? Show all AHA BLS options", html)
        self.assertIn("const courseOptions =", html)
        self.assertIn("const optionGroups =", html)
        self.assertIn("let compareMode = false", html)
        self.assertIn("function activeCourseIds()", html)
        self.assertNotIn("12:00 AM-6:00 PM", html)
        self.assertNotIn("12:00 AM\u20136:00 PM", html)
        self.assertNotIn("Calendy", html)
        self.assertNotIn("shotgun", html.lower())

    def test_compare_mode_data_model_groups_bls_family_generically(self):
        html = build_bls_block_schedule_pilot.render_html(self.payload)
        self.assertIn('"family": "BLS"', html)
        self.assertIn('"209806"', html)
        self.assertIn('"359474"', html)
        self.assertIn('"210549"', html)
        self.assertIn("Object.values(optionGroups).find", html)
        self.assertIn("optionGroups[selected.family]?.courseIds", html)

    def test_rendered_register_cards_hide_debug_details(self):
        html = build_bls_block_schedule_pilot.render_html(self.payload)
        self.assertIn("Times shown are start times.", html)
        self.assertIn("course.location", html)
        self.assertNotIn("appointmentDayId $", html)
        self.assertNotIn("courseId $", html)
        self.assertNotIn("durationMinutes} min", html)
        self.assertIn("className = 'course-card'", html)
        self.assertIn('id="date-list" class="month-stack"', html)

    def test_config_driven_heartsaver_page_generates_valid_schedule(self):
        configs = block_start_time_selector.load_block_schedule_page_configs()
        payload = block_start_time_selector.build_block_schedule_page(configs["heartsaver"])
        self.assertEqual(payload["publicPage"], "docs/heartsaver-schedule.html")
        course_ids = {offer["courseId"] for offer in payload["offers"]}
        self.assertLessEqual(course_ids, {"344085", "209809", "251545"})
        html = build_bls_block_schedule_pilot.render_html(payload)
        self.assertIn("Heartsaver Schedule", html)
        self.assertIn("Need First Aid or CPR ASAP? Show all AHA Heartsaver options", html)
        if payload["offers"]:
            self.assertIn("appointmentDayId", html)
        self.assertNotIn("appointmentDayId $", html)
        self.assertNotIn("courseId $", html)

    def test_final_live_guard_suppresses_july_4_stale_offer_without_live_block(self):
        stale_payload = {
            "pageConfig": {"allowed_course_ids": ["209806"]},
            "counts": {
                "publicSelectableOfferCount": 1,
                "publicSelectableDateCount": 1,
                "publicSelectableStartTimeCount": 1,
                "rejectedOfferCount": 0,
                "wholeBlockPresentedAsClass": False,
            },
            "proof": {"visibleStartLabels": ["8:00 AM"], "availabilityWindowsThatGeneratedOffers": ["08:00-12:00"]},
            "offers": [{
                "date": "2026-07-04",
                "displayDate": "Saturday, July 4, 2026",
                "startTime": "08:00",
                "displayStartTime": "8:00 AM",
                "courseId": "209806",
                "courseName": "AHA BLS Provider",
                "availabilityBlockId": "stale-july-4-block",
                "availabilityWindow": "08:00-12:00",
                "schedulerConsumptionEnd": "10:30",
            }],
            "dates": [{
                "date": "2026-07-04",
                "displayDate": "Saturday, July 4, 2026",
                "startTimes": [{
                    "startTime": "08:00",
                    "displayStartTime": "8:00 AM",
                    "courses": [],
                }],
            }],
        }
        original = block_start_time_selector.current_public_live_block_index
        block_start_time_selector.current_public_live_block_index = lambda: {
            "current-july-5-block": {
                "start": datetime(2026, 7, 5, 8, 0),
                "end": datetime(2026, 7, 5, 12, 0),
                "block": {},
            }
        }
        try:
            guarded = block_start_time_selector.apply_final_live_availability_guard(stale_payload)
        finally:
            block_start_time_selector.current_public_live_block_index = original
        self.assertEqual(guarded["offers"], [])
        self.assertEqual(guarded["dates"], [])
        self.assertEqual(guarded["counts"]["publicSelectableOfferCount"], 0)
        self.assertEqual(guarded["liveAvailabilityGuard"]["suppressedDates"], ["2026-07-04"])
        self.assertEqual(
            guarded["liveAvailabilityGuard"]["suppressedStaleOrOrphanedOffers"][0]["reason"],
            "source_availability_block_missing_from_current_live_snapshot",
        )

    def test_public_live_windows_allow_approved_inverse_sources_only(self):
        live_payload = {
            "generated_at": "2026-07-02T12:00:00-04:00",
            "availability_blocks": [
                {
                    "availability_status": "available",
                    "inverse_generated": True,
                    "source_calendar_id": "brian_do_not_schedule",
                    "source_event_id": "approved-gap",
                    "instructor_name": "Brian Ennis",
                    "person_id": "instructor_24057895173",
                    "date": "2026-07-04",
                    "end_date": "2026-07-04",
                    "start_datetime": "2026-07-04T08:00:00",
                    "end_datetime": "2026-07-04T12:00:00",
                    "start_time": "08:00",
                    "end_time": "12:00",
                    "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                    "allowed_course_families": ["BLS"],
                    "source_type": "inverse_google_calendar",
                },
                {
                    "availability_status": "available",
                    "inverse_generated": True,
                    "source_calendar_id": "unapproved_calendar",
                    "source_event_id": "unapproved-gap",
                    "instructor_name": "Brian Ennis",
                    "person_id": "instructor_24057895173",
                    "date": "2026-07-05",
                    "end_date": "2026-07-05",
                    "start_datetime": "2026-07-05T08:00:00",
                    "end_datetime": "2026-07-05T12:00:00",
                    "start_time": "08:00",
                    "end_time": "12:00",
                    "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                    "allowed_course_families": ["BLS"],
                    "source_type": "inverse_google_calendar",
                },
            ],
        }
        windows, stats = block_start_time_selector.selected_public_page_live_windows(live_payload, {})
        self.assertEqual([window["source_availability_window"] for window in windows], ["approved-gap"])
        self.assertEqual(stats["approved_inverse_blocks_used_count"], 1)
        self.assertEqual(stats["unapproved_inverse_blocks_suppressed_count"], 1)
        self.assertEqual(
            stats["suppressed_available_blocks"][0]["reason"],
            "inverse_generated_availability_source_not_approved_for_public_page",
        )


if __name__ == "__main__":
    unittest.main()
