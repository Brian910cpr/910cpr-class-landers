from __future__ import annotations

import unittest
from datetime import date

from scripts.inventory_controller import (
    APPOINTMENT_CONTAINERS_PATH,
    build_registration_url,
    compute_appointment_day_id,
    generate_inventory,
    load_json,
    parse_time,
    validate_appointment_day_id,
)


class InventoryControllerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.container = load_json(APPOINTMENT_CONTAINERS_PATH)["containers"][0]

    def test_appointment_day_id_computed_correctly_inside_range(self) -> None:
        self.assertEqual(260671, compute_appointment_day_id(self.container, date(2026, 6, 22)))
        self.assertEqual(260870, compute_appointment_day_id(self.container, date(2027, 1, 7)))

    def test_last_valid_and_first_invalid_boundaries(self) -> None:
        valid, appointment_day_id, reason = validate_appointment_day_id(self.container, date(2027, 4, 30))
        self.assertTrue(valid, reason)
        self.assertEqual(260983, appointment_day_id)

        valid, appointment_day_id, reason = validate_appointment_day_id(self.container, date(2027, 5, 1))
        self.assertFalse(valid)
        self.assertEqual(260984, appointment_day_id)
        self.assertEqual("date_after_owned_appointment_range", reason)

    def test_out_of_range_dates_are_rejected(self) -> None:
        valid, _, reason = validate_appointment_day_id(self.container, date(2026, 6, 20))
        self.assertFalse(valid)
        self.assertEqual("date_before_owned_appointment_range", reason)

        valid, _, reason = validate_appointment_day_id(self.container, date(2027, 5, 2))
        self.assertFalse(valid)
        self.assertEqual("date_after_owned_appointment_range", reason)

    def test_registration_urls_are_generated_for_core_course_ids(self) -> None:
        for course_id in ("359474", "241108", "209805"):
            url = build_registration_url(260671, parse_time("08:30"), course_id)
            self.assertIn("appointmentDayId=260671", url)
            self.assertIn("startTime=8%3A30%20AM", url)
            self.assertIn(f"courseId={course_id}", url)

    def test_anchor_required_block_exposes_only_acls_pals_before_anchor(self) -> None:
        result = generate_inventory("no_anchor_case")
        amy_public = [
            candidate for candidate in result["public_offerings"]
            if candidate["instructor"] == "Amy"
        ]
        self.assertTrue(amy_public)
        self.assertEqual({"ACLS", "PALS"}, {candidate["course_family"] for candidate in amy_public})

        suppressed_small = [
            candidate for candidate in result["suppressed"]
            if candidate["instructor"] == "Amy"
            and candidate["course_family"] in {"BLS", "Heartsaver"}
            and "anchor_required_unmet_non_anchor_suppressed" in candidate["reasons"]
        ]
        self.assertTrue(suppressed_small)

    def test_after_mock_acls_anchor_smaller_post_anchor_offerings_can_appear(self) -> None:
        result = generate_inventory("acls_booked_case")
        amy_public = [
            candidate for candidate in result["public_offerings"]
            if candidate["instructor"] == "Amy"
        ]
        self.assertTrue(any(candidate["course_id"] == "210549" for candidate in amy_public))
        self.assertTrue(all("overlaps_existing_anchor_booking" not in candidate["reasons"] for candidate in amy_public))

    def test_no_public_offering_crosses_block_end_time(self) -> None:
        result = generate_inventory("acls_booked_case")
        for candidate in result["public_offerings"]:
            start = parse_time_12h(candidate["start_time"])
            end = parse_time_12h(candidate["end_time"])
            self.assertLessEqual((end.hour * 60 + end.minute) - (start.hour * 60 + start.minute), candidate["duration_minutes"])
            self.assertNotIn("course_does_not_fit_contiguous_block", candidate["reasons"])

    def test_suppressed_candidates_include_explainable_reasons(self) -> None:
        result = generate_inventory("no_anchor_case")
        self.assertTrue(result["suppressed"])
        self.assertTrue(all(candidate["reasons"] for candidate in result["suppressed"]))


def parse_time_12h(value: str):
    from datetime import datetime

    return datetime.strptime(value, "%I:%M %p").time()


if __name__ == "__main__":
    unittest.main()
