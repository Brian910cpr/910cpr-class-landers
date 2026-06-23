import re
import unittest

from scripts.build_slug_hubs import render_heartsaver_course_flow


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
