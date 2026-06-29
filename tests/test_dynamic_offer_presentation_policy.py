from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from scripts import build_slug_hubs
from scripts import dynamic_offer_presentation_policy as presentation
from scripts.dynamic_offer_presentation_policy import apply_presentation_policy


def offer(course_id: str, start: datetime, minutes: int = 45, consumption: int = 60) -> dict:
    return {
        "offer_id": f"offer-{course_id}-instructor_test-{start:%Y%m%d-%H%M}",
        "course_id": course_id,
        "course_key": f"course_{course_id}",
        "course_title": f"Course {course_id}",
        "course_family": "BLS",
        "date": start.date().isoformat(),
        "start_time": start.strftime("%H:%M"),
        "end_time": (start + timedelta(minutes=minutes)).strftime("%H:%M"),
        "appointment_display_start": start.isoformat(),
        "appointment_display_end": (start + timedelta(minutes=minutes)).isoformat(),
        "scheduler_consumption_start": start.isoformat(),
        "scheduler_consumption_end": (start + timedelta(minutes=consumption)).isoformat(),
        "scheduler_consumption_minutes": consumption,
        "instructor_person_id": "instructor_test",
        "instructor_display_name": "Brian Ennis",
        "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
        "offer_location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
        "source_availability_window": "window-1",
        "appointmentDayId": 260683,
    }


class DynamicOfferPresentationPolicyTest(unittest.TestCase):
    def test_anchor_prefers_after_anchor_stack_start_not_all_adjacent(self) -> None:
        base = datetime(2026, 7, 4, 8, 45)
        offers = [offer("209806", base + timedelta(minutes=15 * index)) for index in range(4)]
        anchors = [{
            "session_id": "anchor-1",
            "course_id": "anchor",
            "course_title": "Anchor",
            "start": datetime(2026, 7, 4, 8, 0),
            "end": datetime(2026, 7, 4, 8, 45),
            "instructor": "Brian Ennis",
            "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
            "source": "test",
        }]

        with patch.object(presentation, "public_sellable_appointment_gate", return_value={"allowed": True, "reasons": ["test_allowed"]}):
            render_offers, audit_rows, stats = apply_presentation_policy(offers, anchors)

        self.assertEqual(1, len(render_offers))
        self.assertEqual("09:00", render_offers[0]["start_time"])
        self.assertEqual("anchor_stack_after", render_offers[0]["presentation_mode"])
        self.assertEqual(3, stats["suppressed_adjacent_duplicates"])
        self.assertTrue(any(row["presentation_mode"] == "suppressed_adjacent_candidate" for row in audit_rows))

    def test_before_anchor_requires_consumption_end_before_anchor_start(self) -> None:
        offers = [
            offer("209806", datetime(2026, 7, 4, 7, 0), minutes=45, consumption=60),
            offer("209806", datetime(2026, 7, 4, 7, 30), minutes=45, consumption=60),
        ]
        anchors = [{
            "session_id": "anchor-1",
            "course_id": "anchor",
            "course_title": "Anchor",
            "start": datetime(2026, 7, 4, 8, 0),
            "end": datetime(2026, 7, 4, 8, 45),
            "instructor": "Brian Ennis",
            "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
            "source": "test",
        }]

        with patch.object(presentation, "public_sellable_appointment_gate", return_value={"allowed": True, "reasons": ["test_allowed"]}):
            render_offers, audit_rows, _stats = apply_presentation_policy(offers, anchors)

        self.assertEqual("07:00", render_offers[0]["start_time"])
        self.assertEqual("anchor_stack_before", render_offers[0]["presentation_mode"])
        suppressed_ids = {row["offer_id"] for row in audit_rows if row["presentation_mode"] == "suppressed_adjacent_candidate"}
        self.assertIn("offer-209806-instructor_test-20260704-0730", suppressed_ids)

    def test_open_window_renders_one_flexible_start_offer_with_15_minute_choices(self) -> None:
        offers = [
            offer("329495", datetime(2026, 7, 4, 14, 30) + timedelta(minutes=15 * index), consumption=90)
            for index in range(3)
        ]

        with patch.object(presentation, "public_sellable_appointment_gate", return_value={"allowed": True, "reasons": ["test_allowed"]}):
            render_offers, audit_rows, stats = apply_presentation_policy(offers, [])

        self.assertEqual(3, stats["course_master_gate_eligible_candidates"])
        self.assertEqual(0, stats["suppressed_course_master_gate"])

        self.assertEqual(1, len(render_offers))
        self.assertEqual("flexible_start_window", render_offers[0]["presentation_mode"])
        self.assertEqual("When would YOU like to start?", render_offers[0]["flexible_start_button_text"])
        self.assertEqual(["14:30", "14:45", "15:00"], [choice["start_time"] for choice in render_offers[0]["flexible_start_choices"]])
        self.assertEqual("2026-07-04T15:00:00", render_offers[0]["latest_flexible_start"])
        self.assertEqual(1, stats["rendered_flexible_start_windows"])
        self.assertEqual(2, stats["suppressed_adjacent_duplicates"])
        self.assertTrue(any(row["public_render_decision"] == "suppress_as_duplicate_adjacent_start" for row in audit_rows))

    def test_course_master_gate_suppresses_unreviewed_candidate_before_presentation(self) -> None:
        offers = [offer("329495", datetime(2026, 7, 4, 14, 30), consumption=90)]

        with patch.object(presentation, "public_sellable_appointment_gate", return_value={"allowed": False, "reasons": ["appointment_seed_not_allowed"]}):
            render_offers, audit_rows, stats = apply_presentation_policy(offers, [])

        self.assertEqual([], render_offers)
        self.assertEqual(1, stats["suppressed_course_master_gate"])
        self.assertEqual("suppressed_course_master_gate", audit_rows[0]["presentation_mode"])
        self.assertEqual("suppress_course_master_gate", audit_rows[0]["public_render_decision"])

    def test_flexible_start_card_renders_choice_links_without_repeated_cards(self) -> None:
        row = {
            "course_title": "AHA Heartsaver First Aid CPR AED - Blended",
            "start_datetime": "2026-07-04T14:30:00",
            "end_datetime": "2026-07-04T15:15:00",
            "location_name": "Shipyard",
            "instructor_display_name": "Brian Ennis",
            "appointment_registration_url": "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=1&startTime=2%3A30%20PM&courseId=329495",
            "presentation_mode": "flexible_start_window",
            "flexible_start_button_text": "When would YOU like to start?",
            "source_offer_id": "offer-329495-instructor_test-20260704-1430",
            "render_source": "dynamic_offer_presentation_policy",
            "flexible_start_choices": [
                {
                    "offer_id": "offer-329495-instructor_test-20260704-1430",
                    "appointment_display_start": "2026-07-04T14:30:00",
                    "appointment_display_end": "2026-07-04T15:15:00",
                    "appointment_registration_url": "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=1&startTime=2%3A30%20PM&courseId=329495",
                },
                {
                    "offer_id": "offer-329495-instructor_test-20260704-1445",
                    "appointment_display_start": "2026-07-04T14:45:00",
                    "appointment_display_end": "2026-07-04T15:30:00",
                    "appointment_registration_url": "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=1&startTime=2%3A45%20PM&courseId=329495",
                },
            ],
        }

        html = build_slug_hubs.render_appointment_seed_offer_card(row)

        self.assertEqual(1, html.count("slug-appointment-option"))
        self.assertIn("When would YOU like to start?", html)
        self.assertIn("2%3A30%20PM", html)
        self.assertIn("2%3A45%20PM", html)
        self.assertIn('data-presentation-mode="flexible_start_window"', html)


if __name__ == "__main__":
    unittest.main()
