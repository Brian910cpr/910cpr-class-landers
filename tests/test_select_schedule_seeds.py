from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts import select_schedule_seeds


class ScheduleSeedsTest(unittest.TestCase):
    def test_removes_amy_advanced_before_1300(self) -> None:
        public_preview = {
            "offers": [
                {
                    "offer_id": "amy-acls",
                    "date": "2026-06-23",
                    "start_time": "09:00",
                    "end_time": "13:00",
                    "course_id": "209818",
                    "course_title": "AHA ACLS Provider (Renewal)",
                    "course_family": "ACLS",
                    "instructor_display_name": "Amy Arnold",
                    "instructor_person_id": "amy",
                    "source_availability_window": "window-1",
                }
            ]
        }
        policy = {
            "advanced_families": ["ACLS", "PALS"],
            "amy_advanced_not_before": "13:00",
            "max_seeds_per_instructor_window": 1,
        }

        seeds, hidden, stats = select_schedule_seeds.select_seeds(public_preview, policy)

        self.assertEqual([], seeds)
        self.assertEqual("amy_advanced_before_1300", hidden[0]["reason_code"])
        self.assertEqual(1, stats["amy_advanced_course_violations_removed"])

    def test_selects_daily_family_mix_without_duplicate_start_times(self) -> None:
        public_preview = {
            "offers": [
                {
                    "offer_id": "bls",
                    "date": "2026-06-22",
                    "start_time": "08:30",
                    "end_time": "10:30",
                    "course_id": "209806",
                    "course_title": "AHA BLS Provider",
                    "course_family": "BLS",
                    "instructor_display_name": "Brian Ennis",
                    "instructor_person_id": "brian",
                    "source_availability_window": "window-1",
                },
                {
                    "offer_id": "heart",
                    "date": "2026-06-22",
                    "start_time": "09:00",
                    "end_time": "12:00",
                    "course_id": "209809",
                    "course_title": "AHA Heartsaver First Aid CPR AED",
                    "course_family": "Heartsaver",
                    "instructor_display_name": "Brian Ennis",
                    "instructor_person_id": "brian",
                    "source_availability_window": "window-1",
                },
            ]
        }
        policy = {
            "required_seed_mix_by_date": {
                "BLS": {"count": 1, "required": True},
                "Heartsaver": {"count": 1, "required": True},
            },
            "max_seeds_per_instructor_window": 2,
            "max_seeds_per_family_per_date": {"BLS": 1, "Heartsaver": 1},
            "family_priority_by_time_band": {"morning": ["BLS", "Heartsaver"]},
            "preferred_start_times_by_family": {"BLS": ["08:30"], "Heartsaver": ["09:00"]},
            "course_title_priority_terms": ["BLS Provider"],
            "avoid_same_start_time_per_date": True,
        }

        seeds, hidden, _ = select_schedule_seeds.select_seeds(public_preview, policy)

        self.assertEqual(["bls", "heart"], [seed["source_offer_id"] for seed in seeds])
        self.assertEqual([], hidden)

    def test_container_backed_filter_keeps_only_matching_container_offers(self) -> None:
        public_preview = {
            "offers": [
                {
                    "offer_id": "shipyard",
                    "date": "2026-06-22",
                    "start_time": "08:30",
                    "end_time": "10:30",
                    "course_id": "209806",
                    "course_title": "AHA BLS Provider",
                    "course_family": "BLS",
                    "instructor_display_name": "Brian Ennis",
                    "instructor_person_id": "brian",
                    "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                    "resource": "Shipyard Office",
                    "source_availability_window": "window-1",
                },
                {
                    "offer_id": "offsite",
                    "date": "2026-06-22",
                    "start_time": "09:00",
                    "end_time": "11:00",
                    "course_id": "209806",
                    "course_title": "AHA BLS Provider",
                    "course_family": "BLS",
                    "instructor_display_name": "Brian Ennis",
                    "instructor_person_id": "brian",
                    "location": "Somewhere Else",
                    "resource": "Somewhere Else",
                    "source_availability_window": "window-2",
                },
            ]
        }
        policy = {
            "required_seed_mix_by_date": {"BLS": {"count": 1, "required": True}},
            "max_seeds_per_instructor_window": 1,
            "max_seeds_per_family_per_date": {"BLS": 1},
        }
        course_catalog = {
            "courses": [{
                "course_id": "209806",
                "appointment_allowed": True,
            }]
        }
        containers = {
            "containers": [{
                "container_id": "shipyard_brian",
                "status": "active",
                "instructor_name": "Brian",
                "location_name": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                "room_or_resource_name": "Shipyard Office",
                "first_valid_date": "2026-06-21",
                "last_valid_date": "2026-06-30",
                "first_valid_appointmentDayId": 260670,
                "last_valid_appointmentDayId": 260679,
                "first_invalid_appointmentDayId": 260680,
            }]
        }

        seeds, hidden, stats = select_schedule_seeds.select_seeds(public_preview, policy, course_catalog, containers)

        self.assertEqual(["shipyard"], [seed["source_offer_id"] for seed in seeds])
        self.assertEqual({"location_mismatch": 1}, stats["offers_hidden_by_container_reason"])
        self.assertEqual("location_mismatch", hidden[0]["reason_code"])

    def test_seed_selection_blocks_same_lane_consumption_overlap(self) -> None:
        public_preview = {
            "offers": [
                {
                    "offer_id": "bls-1700",
                    "date": "2026-06-22",
                    "start_time": "17:00",
                    "end_time": "19:00",
                    "appointment_display_start": "2026-06-22T17:00:00",
                    "appointment_display_end": "2026-06-22T19:00:00",
                    "scheduler_consumption_start": "2026-06-22T17:00:00",
                    "scheduler_consumption_end": "2026-06-22T19:45:00",
                    "course_id": "209806",
                    "course_title": "AHA BLS Provider",
                    "course_family": "BLS",
                    "instructor_display_name": "Brian Ennis",
                    "instructor_person_id": "brian",
                    "location": "Shipyard",
                    "resource": "Shipyard Office",
                    "source_availability_window": "window-1",
                },
                {
                    "offer_id": "bls-1900",
                    "date": "2026-06-22",
                    "start_time": "19:00",
                    "end_time": "21:00",
                    "appointment_display_start": "2026-06-22T19:00:00",
                    "appointment_display_end": "2026-06-22T21:00:00",
                    "scheduler_consumption_start": "2026-06-22T19:00:00",
                    "scheduler_consumption_end": "2026-06-22T21:45:00",
                    "course_id": "209806",
                    "course_title": "AHA BLS Provider",
                    "course_family": "BLS",
                    "instructor_display_name": "Brian Ennis",
                    "instructor_person_id": "brian",
                    "location": "Shipyard",
                    "resource": "Shipyard Office",
                    "source_availability_window": "window-1",
                },
            ]
        }
        policy = {
            "required_seed_mix_by_date": {"BLS": {"count": 2, "required": True}},
            "max_seeds_per_instructor_window": 2,
            "max_seeds_per_family_per_date": {"BLS": 2},
            "preferred_start_times_by_family": {"BLS": ["17:00", "19:00"]},
        }

        seeds, hidden, _stats = select_schedule_seeds.select_seeds(public_preview, policy)

        self.assertEqual(["bls-1700"], [seed["source_offer_id"] for seed in seeds])
        self.assertIn("scheduler_consumption_window_overlap", [item["reason_code"] for item in hidden])

    def test_bls_variant_balance_alternates_initial_and_renewal_by_seed_date(self) -> None:
        offers = []
        for date in ["2026-08-03", "2026-08-04", "2026-08-05", "2026-08-06"]:
            offers.extend([
                {
                    "offer_id": f"initial-{date}",
                    "date": date,
                    "start_time": "09:15",
                    "end_time": "11:15",
                    "course_id": "209806",
                    "course_title": "AHA BLS Provider",
                    "course_family": "BLS",
                    "instructor_display_name": "Brian Ennis",
                    "instructor_person_id": "brian",
                    "location": "Shipyard",
                    "resource": "Shipyard Office",
                    "source_availability_window": f"window-{date}",
                },
                {
                    "offer_id": f"renewal-{date}",
                    "date": date,
                    "start_time": "09:15",
                    "end_time": "11:15",
                    "course_id": "359474",
                    "course_title": "AHA BLS Provider Renewal",
                    "course_family": "BLS",
                    "instructor_display_name": "Brian Ennis",
                    "instructor_person_id": "brian",
                    "location": "Shipyard",
                    "resource": "Shipyard Office",
                    "source_availability_window": f"window-{date}",
                },
            ])
        policy = {
            "required_seed_mix_by_date": {"BLS": {"count": 1, "required": True}},
            "max_seeds_per_instructor_window": 1,
            "max_seeds_per_family_per_date": {"BLS": 1},
            "preferred_start_times_by_family": {"BLS": ["09:15"]},
            "course_title_priority_terms": ["BLS Provider"],
            "bls_seed_variant_balance": {
                "enabled": True,
                "mode": "alternate_initial_renewal_by_bls_date",
                "course_id_order": ["209806", "359474"],
            },
        }

        seeds, hidden, _stats = select_schedule_seeds.select_seeds({"offers": offers}, policy)

        self.assertEqual(
            ["209806", "359474", "209806", "359474"],
            [seed["course_id"] for seed in seeds],
        )
        self.assertEqual(4, len({(seed["date"], seed["start_time"]) for seed in seeds}))
        self.assertTrue(all(item["reason_code"] == "family_mix_target_already_met" for item in hidden))

    def test_run_outputs_are_scoped_to_audit_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit_dir = root / "data" / "audit"
            missing = root / "missing"

            original_audit_dir = select_schedule_seeds.AUDIT_DIR
            original_public = select_schedule_seeds.PUBLIC_SELLABLE_OFFERS_PATH
            original_policy = select_schedule_seeds.SEED_POLICY_PATH
            original_seeds = select_schedule_seeds.SEEDS_PATH
            original_report = select_schedule_seeds.REPORT_PATH
            original_amy_stack_fill = select_schedule_seeds.AMY_STACK_FILL_PATH
            original_amy_strategy_report = select_schedule_seeds.AMY_STRATEGY_REPORT_PATH
            try:
                select_schedule_seeds.AUDIT_DIR = audit_dir
                select_schedule_seeds.PUBLIC_SELLABLE_OFFERS_PATH = missing / "public.json"
                select_schedule_seeds.SEED_POLICY_PATH = missing / "policy.json"
                select_schedule_seeds.SEEDS_PATH = audit_dir / "schedule_seeds_preview.json"
                select_schedule_seeds.REPORT_PATH = audit_dir / "schedule_seeds_report.md"
                select_schedule_seeds.AMY_STACK_FILL_PATH = audit_dir / "amy_stack_fill_candidates.json"
                select_schedule_seeds.AMY_STRATEGY_REPORT_PATH = audit_dir / "amy_protected_pilot_strategy_report.md"
                result = select_schedule_seeds.run()

                self.assertEqual(0, result["stats"]["seeds_selected"])
                written = sorted(path.relative_to(root).as_posix() for path in audit_dir.glob("schedule_seeds_*"))
                self.assertEqual(
                    [
                        "data/audit/schedule_seeds_preview.json",
                        "data/audit/schedule_seeds_report.md",
                    ],
                    written,
                )
            finally:
                select_schedule_seeds.AUDIT_DIR = original_audit_dir
                select_schedule_seeds.PUBLIC_SELLABLE_OFFERS_PATH = original_public
                select_schedule_seeds.SEED_POLICY_PATH = original_policy
                select_schedule_seeds.SEEDS_PATH = original_seeds
                select_schedule_seeds.REPORT_PATH = original_report
                select_schedule_seeds.AMY_STACK_FILL_PATH = original_amy_stack_fill
                select_schedule_seeds.AMY_STRATEGY_REPORT_PATH = original_amy_strategy_report


if __name__ == "__main__":
    unittest.main()
