from __future__ import annotations

import unittest

from scripts.hybrid_inventory import (
    availability_window_policy_for,
    can_consume_availability_window,
    course_consumption_rule_for,
    load_availability_window_policies,
    load_course_consumption_rules,
)


class InventoryRulesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.course_rules = load_course_consumption_rules()
        self.window_policies = load_availability_window_policies()

    def test_acls_consumes_full_advanced_block_independent_of_instructor(self) -> None:
        rule = course_consumption_rule_for(
            {"course_id": "241108", "course_family": "ACLS"},
            self.course_rules,
        )
        policy = availability_window_policy_for(
            {"capacity_mode": "single_advanced_provider_block"},
            self.window_policies,
        )

        allowed, reason = can_consume_availability_window(rule, policy)

        self.assertTrue(allowed, reason)
        self.assertEqual(240, rule["minimum_reservation_block_minutes"])
        self.assertFalse(policy["split_allowed"])

    def test_advanced_block_does_not_auto_split_for_bls(self) -> None:
        rule = course_consumption_rule_for(
            {"course_id": "209806", "course_family": "BLS"},
            self.course_rules,
        )
        policy = availability_window_policy_for(
            {"capacity_mode": "single_advanced_provider_block"},
            self.window_policies,
        )

        allowed, reason = can_consume_availability_window(rule, policy)

        self.assertFalse(allowed)
        self.assertEqual("fallback_course_family_requires_manual_approval", reason)

    def test_slot_interval_does_not_define_course_consumption(self) -> None:
        rule = course_consumption_rule_for(
            {"course_id": "209806", "course_family": "BLS", "appointment_slot_interval_minutes": 15},
            self.course_rules,
        )

        self.assertEqual(120, rule["minimum_reservation_block_minutes"])

    def test_overlapping_reservations_are_distinct_from_window_subdivision(self) -> None:
        rule = course_consumption_rule_for(
            {"course_id": "209806", "course_family": "BLS"},
            self.course_rules,
        )
        policy = availability_window_policy_for(
            {"capacity_mode": "open_bls_block"},
            self.window_policies,
        )

        allowed, reason = can_consume_availability_window(
            rule,
            policy,
            existing_reservation_count=1,
            existing_overlapping_reservation_count=0,
        )
        self.assertTrue(allowed, reason)

        allowed, reason = can_consume_availability_window(
            rule,
            policy,
            existing_reservation_count=1,
            existing_overlapping_reservation_count=1,
        )
        self.assertFalse(allowed)
        self.assertEqual("course_prohibits_overlapping_reservations", reason)


if __name__ == "__main__":
    unittest.main()
