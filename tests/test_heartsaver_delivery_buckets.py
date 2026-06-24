import os
import re
import unittest
from unittest.mock import patch

from scripts.build_slug_hubs import (
    debug_display_dt,
    parse_dt,
    public_inventory_decision,
    render_appointment_seed_offer_card,
    render_heartsaver_course_flow,
    render_session_card,
    render_universal_request_offer_card,
)


def _section_start_tag(html, section_id):
    match = re.search(rf'<section\b[^>]*id="{re.escape(section_id)}"[^>]*>', html)
    return match.group(0) if match else ""


def _section_chunk(html, section_id, next_section_id=None):
    start = html.index(f'id="{section_id}"')
    if next_section_id:
        end = html.index(f'id="{next_section_id}"', start)
    else:
        end = html.index("</section>", start)
    return html[start:end]


class HeartsaverDeliveryBucketTests(unittest.TestCase):
    def test_source_time_debug_offsets_display_only_for_seed_offer(self):
        offer = {
            "course_id": "329495",
            "course_title": "AHA Heartsaver First Aid CPR AED - Blended",
            "start_datetime": "2026-07-04T14:30:00-04:00",
            "end_datetime": "2026-07-04T15:30:00-04:00",
            "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
            "appointment_registration_url": "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A30%20PM&courseId=329495",
        }

        with patch.dict(os.environ, {"LANDER_DEBUG_SOURCE_TIMES": "1"}):
            html = render_appointment_seed_offer_card(offer)

        self.assertIn("2:31 PM - 3:31 PM", html)
        self.assertIn("DEBUG SEED", html)
        self.assertIn('data-source-type="seed"', html)
        self.assertIn('data-course-id="329495"', html)
        self.assertIn('data-appointment-day-id="260683"', html)
        self.assertIn("startTime=2%3A30%20PM", html)
        self.assertNotIn("startTime=2%3A31%20PM", html)

    def test_source_time_debug_is_absent_in_production_render(self):
        session = {
            "source": "enrollware_ical",
            "session_id": "13657403",
            "course_id": "209809",
            "course_name": "AHA Heartsaver First Aid CPR AED",
            "start_at": "2026-07-04T09:15:00-04:00",
            "end_at": "2026-07-04T11:45:00-04:00",
            "location_name": "NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office",
            "registration_url": "https://coastalcprtraining.enrollware.com/schedule",
        }

        with patch.dict(os.environ, {}, clear=True):
            html = render_session_card(session, group_mode=False, page_slug="heartsaver")

        self.assertIn("9:15 AM", html)
        self.assertNotIn("DEBUG", html)
        self.assertNotIn("data-source-type", html)
        self.assertNotIn("data-source-file", html)
        self.assertNotIn("data-appointment-day-id", html)

    def test_source_time_debug_marks_ical_without_offset(self):
        session = {
            "source": "enrollware_ical",
            "session_id": "13657403",
            "course_id": "209809",
            "course_name": "AHA Heartsaver First Aid CPR AED",
            "start_at": "2026-07-04T09:15:00-04:00",
            "end_at": "2026-07-04T11:45:00-04:00",
            "location_name": "NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office",
            "registration_url": "https://coastalcprtraining.enrollware.com/schedule",
        }

        with patch.dict(os.environ, {"LANDER_DEBUG_SOURCE_TIMES": "1"}):
            html = render_session_card(session, group_mode=False, page_slug="heartsaver")

        self.assertIn("9:15 AM", html)
        self.assertNotIn("9:16 AM", html)
        self.assertIn("DEBUG ICAL", html)
        self.assertIn('data-source-type="ical"', html)
        self.assertIn('data-source-file="docs/data/schedule_future.json"', html)
        self.assertIn('data-class-id="13657403"', html)

    def test_source_time_debug_marks_unknown_with_two_minute_offset(self):
        dt = parse_dt("2026-07-04T09:15:00-04:00")
        with patch.dict(os.environ, {"LANDER_DEBUG_SOURCE_TIMES": "1"}):
            shifted = debug_display_dt(dt, {"course_id": "x"}, kind_hint="real_session")
        self.assertEqual("09:17", shifted.strftime("%H:%M"))

    def test_source_time_debug_offsets_universal_request_display_only(self):
        offer = {
            "_universal_request_offer": True,
            "course_id": "209809",
            "course_title": "AHA Heartsaver First Aid CPR AED",
            "start_datetime": "2026-07-04T18:00:00-04:00",
            "end_datetime": "2026-07-04T18:45:00-04:00",
            "scheduler_consumption_end": "2026-07-04T20:45:00-04:00",
            "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
            "request_url": "/request_group_session.html?program=AHA%20Heartsaver",
        }

        with patch.dict(os.environ, {"LANDER_DEBUG_SOURCE_TIMES": "1"}):
            html = render_universal_request_offer_card(offer)

        self.assertIn("6:01 PM - 6:46 PM", html)
        self.assertIn("Time held through 8:46 PM", html)
        self.assertIn("DEBUG DYNAMIC", html)
        self.assertIn('data-source-type="dynamic"', html)
        self.assertIn('data-course-id="209809"', html)

    def test_enrollware_ical_shipyard_room_location_is_public_inventory(self):
        page = {
            "slug": "heartsaver",
            "approved_public_locations": ["Wilmington; Shipyard Blvd"],
        }
        session = {
            "course_id": "329495",
            "course_name": "AHA Heartsaver First Aid CPR AED - Blended",
            "course_subtitle": "",
            "location_name": "NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office",
            "location_display": "NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office",
        }

        self.assertEqual((True, "included:public_inventory"), public_inventory_decision(session, page))

    def test_blended_offer_stays_out_of_in_person_delivery_panel(self):
        page = {"slug": "heartsaver", "hero_title": "Heartsaver"}
        in_person_tab = {
            "id": "hs-fa-cpr-aed-ip",
            "label": "First Aid + CPR + AED",
            "program": "AHA Heartsaver First Aid CPR AED",
            "description_short": "In-person classroom option.",
            "full_schedule_url": "/heartsaver.html",
            "full_schedule_label": "See full Heartsaver schedule",
        }
        blended_tab = {
            "id": "hs-fa-cpr-aed-bl",
            "label": "First Aid + CPR + AED",
            "program": "AHA Heartsaver First Aid CPR AED - Blended",
            "description_short": "Online coursework plus skills.",
            "tab_badge": "Online + Skills",
            "full_schedule_url": "/heartsaver.html",
            "full_schedule_label": "See full Heartsaver schedule",
        }
        blended_offer = {
            "course_title": "AHA Heartsaver First Aid CPR AED - Blended",
            "course_key": "aha_heartsaver_first_aid_cpr_aed_blended",
            "tab_ids": ["hs-fa-cpr-aed-bl"],
            "start_datetime": "2026-07-04T14:30:00-04:00",
            "end_datetime": "2026-07-04T15:30:00-04:00",
            "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
            "appointment_registration_url": "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A30%20PM&courseId=329495",
        }

        html = render_heartsaver_course_flow(
            page,
            [(in_person_tab, []), (blended_tab, [])],
            group_mode=False,
            appointment_seed_offers=[blended_offer],
            only_group_ids={"heartsaver-first-aid-cpr-aed"},
        )

        self.assertIn('data-tabs', html)
        self.assertIn('class="tab-btn heartsaver-delivery-tab active"', html)
        self.assertIn('class="tab-btn heartsaver-delivery-tab"', html)
        self.assertIn('<span class="hub-tab-label">First Aid + CPR + AED</span>', html)
        self.assertIn('<span class="hub-tab-tag">Online + Skills</span>', html)
        self.assertIn('class="hub-tab-tag hub-tab-count" data-count-target', html)
        self.assertNotIn("course-jump-card heartsaver-delivery-card", html)
        self.assertIn('data-tab-target="#hs-fa-cpr-aed-ip"', html)
        self.assertIn('data-tab-target="#hs-fa-cpr-aed-bl"', html)
        self.assertIn("active", _section_start_tag(html, "hs-fa-cpr-aed-ip"))
        self.assertNotIn("active", _section_start_tag(html, "hs-fa-cpr-aed-bl"))

        in_person_chunk = _section_chunk(html, "hs-fa-cpr-aed-ip", "hs-fa-cpr-aed-bl")
        blended_chunk = _section_chunk(html, "hs-fa-cpr-aed-bl")
        self.assertNotIn("AHA Heartsaver First Aid CPR AED - Blended", in_person_chunk)
        self.assertIn("AHA Heartsaver First Aid CPR AED - Blended", blended_chunk)
        self.assertNotIn("appointmentDayId", in_person_chunk)
        self.assertIn("appointmentDayId", blended_chunk)


if __name__ == "__main__":
    unittest.main()
