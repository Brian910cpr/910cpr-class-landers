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
    select_appointment_container,
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

    def test_advanced_blocks_explain_certification_and_profitability_boosts(self) -> None:
        result = generate_inventory("no_anchor_case")
        advanced_anchor = next(
            candidate for candidate in result["public_offerings"]
            if candidate["instructor"] == "Amy"
            and candidate["course_family"] in {"ACLS", "PALS"}
        )
        self.assertIn("certification_ceiling_boost_advanced_provider_anchor", advanced_anchor["reasons"])
        self.assertIn("profitability_boost_high_value_course", advanced_anchor["reasons"])

    def test_bls_only_blocks_use_fair_rotation_and_brand_mix(self) -> None:
        result = generate_inventory("no_anchor_case")
        bls_public = [
            candidate for candidate in result["public_offerings"]
            if candidate["instructor"] == "BLS Sample Instructor"
        ]
        self.assertTrue(bls_public)
        self.assertFalse(any(candidate["course_family"] in {"ACLS", "PALS"} for candidate in bls_public))
        self.assertTrue(any("fair_rotation_boost_bls_level_block" in candidate["reasons"] for candidate in bls_public))
        self.assertTrue(any("brand_mix_boost_primary_aha_inventory" in candidate["reasons"] for candidate in bls_public))

        waiting_for_momentum = [
            candidate for candidate in result["suppressed"]
            if candidate["instructor"] == "BLS Sample Instructor"
            and candidate["occupancy_pool"] == "BLS_SKILLS_POOL"
            and "escalation_tier_2_suppressed_until_momentum" in candidate["reasons"]
        ]
        self.assertTrue(waiting_for_momentum)

    def test_compatible_occupancy_pool_can_ride_existing_momentum(self) -> None:
        result = generate_inventory("bls_skills_momentum_case")
        bls_public = [
            candidate for candidate in result["public_offerings"]
            if candidate["instructor"] == "BLS Sample Instructor"
            and candidate["occupancy_pool"] == "BLS_SKILLS_POOL"
        ]
        self.assertTrue(bls_public)
        self.assertTrue(all(candidate["escalation_tier"] == 2 for candidate in bls_public))
        self.assertTrue(any(candidate["momentum_triggered"] for candidate in bls_public))
        self.assertGreaterEqual(len({candidate["course_id"] for candidate in bls_public}), 2)

        secondary_brand = [
            candidate for candidate in result["candidates"]
            if candidate["instructor"] == "BLS Sample Instructor"
            and candidate["course_name"].startswith(("ARC", "HSI"))
            and "brand_mix_penalty_hsi_arc_secondary_inventory" in candidate["reasons"]
        ]
        self.assertTrue(secondary_brand)

    def test_anchor_momentum_enables_secondary_escalation(self) -> None:
        result = generate_inventory("acls_booked_case")
        secondary_public = [
            candidate for candidate in result["public_offerings"]
            if candidate["instructor"] == "Amy"
            and candidate["escalation_tier"] == 2
        ]
        self.assertTrue(secondary_public)
        self.assertTrue(any(candidate["momentum_triggered"] for candidate in secondary_public))
        self.assertTrue(any("momentum_triggered_by_anchor_strength_3" in candidate["reasons"] for candidate in secondary_public))

    def test_candidates_include_occupancy_and_escalation_debug_fields(self) -> None:
        result = generate_inventory("no_anchor_case")
        candidate = result["candidates"][0]
        self.assertIn("occupancy_pool", candidate)
        self.assertIn("escalation_tier", candidate)
        self.assertIn("momentum_triggered", candidate)
        self.assertTrue(any("occupancy_pool_" in reason for reason in candidate["reasons"]))
        self.assertTrue(any("escalation_tier_" in reason for reason in candidate["reasons"]))

    def test_duplicate_courses_are_suppressed_for_consolidation(self) -> None:
        result = generate_inventory("no_anchor_case")
        suppressed_duplicates = [
            candidate for candidate in result["suppressed"]
            if "duplicate_same_course_suppressed_for_consolidation" in candidate["reasons"]
        ]
        self.assertTrue(suppressed_duplicates)

    def test_multiple_appointment_containers_can_exist(self) -> None:
        containers = load_json(APPOINTMENT_CONTAINERS_PATH)["containers"]
        extra = dict(containers[0], container_id="shipyard_future_extension", priority=10)
        self.assertEqual(2, len(containers + [extra]))

    def test_resolver_selects_container_by_instructor_location_and_date(self) -> None:
        containers = [
            dict(self.container, container_id="brian_shipyard", instructor_name="Brian", priority=50),
            dict(self.container, container_id="amy_shipyard", instructor_name="Amy", priority=50),
        ]
        block = {
            "instructor_name": "Amy",
            "location_name": self.container["location_name"],
            "date": "2026-06-22",
        }
        selected, appointment_day_id, reason = select_appointment_container(containers, block, date(2026, 6, 22))
        self.assertEqual("owned_appointment_container", reason)
        self.assertEqual("amy_shipyard", selected["container_id"])
        self.assertEqual(260671, appointment_day_id)

    def test_higher_priority_container_wins_when_valid_ranges_overlap(self) -> None:
        containers = [
            dict(self.container, container_id="lower_priority", priority=10),
            dict(self.container, container_id="higher_priority", priority=90),
        ]
        block = {
            "instructor_name": "Brian",
            "location_name": self.container["location_name"],
            "date": "2026-06-22",
        }
        selected, _, reason = select_appointment_container(containers, block, date(2026, 6, 22))
        self.assertEqual("owned_appointment_container", reason)
        self.assertEqual("higher_priority", selected["container_id"])

    def test_no_matching_container_suppresses_candidate(self) -> None:
        block = {
            "instructor_name": "Brian",
            "location_name": "NC - Wilmington: Missing Location",
            "date": "2026-06-22",
        }
        selected, appointment_day_id, reason = select_appointment_container([self.container], block, date(2026, 6, 22))
        self.assertIsNone(selected)
        self.assertIsNone(appointment_day_id)
        self.assertEqual("no_matching_appointment_container", reason)

    def test_out_of_range_container_suppresses_candidate(self) -> None:
        block = {
            "instructor_name": "Brian",
            "location_name": self.container["location_name"],
            "date": "2027-05-01",
        }
        selected, appointment_day_id, reason = select_appointment_container([self.container], block, date(2027, 5, 1))
        self.assertIsNone(selected)
        self.assertEqual(260984, appointment_day_id)
        self.assertEqual("appointment_container_out_of_range", reason)

    def test_generated_urls_never_cross_first_invalid_boundary(self) -> None:
        result = generate_inventory("no_anchor_case")
        first_invalid = int(self.container["first_invalid_appointmentDayId"])
        public_with_urls = [candidate for candidate in result["public_offerings"] if candidate["registration_url"]]
        self.assertTrue(public_with_urls)
        self.assertTrue(all(int(candidate["appointmentDayId"]) < first_invalid for candidate in public_with_urls))

        out_of_range = [
            candidate for candidate in result["suppressed"]
            if "appointment_container_out_of_range" in candidate["reasons"]
        ]
        self.assertTrue(out_of_range)
        self.assertTrue(all(not candidate["registration_url"] for candidate in out_of_range))


def parse_time_12h(value: str):
    from datetime import datetime

    return datetime.strptime(value, "%I:%M %p").time()


if __name__ == "__main__":
    unittest.main()
