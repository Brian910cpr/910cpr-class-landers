from __future__ import annotations

from datetime import datetime
import tempfile
import unittest
from pathlib import Path

from scripts import filter_public_sellable_offers


class PublicSellableOffersTest(unittest.TestCase):
    def test_filters_disabled_family_and_start_minutes(self) -> None:
        dynamic = {
            "offers": [
                {
                    "offer_id": "ok",
                    "date": "2026-06-22",
                    "start_time": "08:30",
                    "course_id": "209806",
                    "course_family": "BLS",
                },
                {
                    "offer_id": "bad-minute",
                    "date": "2026-06-22",
                    "start_time": "08:45",
                    "course_id": "209806",
                    "course_family": "BLS",
                },
                {
                    "offer_id": "bad-family",
                    "date": "2026-06-22",
                    "start_time": "08:30",
                    "course_id": "999",
                    "course_family": "HSI",
                },
            ]
        }
        courses = {
            "courses": [
                {"course_id": "209806", "family": "BLS", "online_only": False, "manual_only": False},
                {"course_id": "999", "family": "HSI", "online_only": False, "manual_only": False},
            ]
        }
        policy = {
            "enabled_course_families": ["BLS"],
            "disabled_course_families": ["HSI"],
            "allowed_start_minutes": ["00", "30"],
            "minimum_lead_hours": 24,
            "maximum_days_out": 60,
            "max_offers_per_course_per_day": 4,
            "max_total_offers_per_day": 24,
        }

        kept, hidden, stats = filter_public_sellable_offers.filter_offers(
            dynamic,
            courses,
            policy,
            now=datetime(2026, 6, 19, 12, 0),
        )

        self.assertEqual(["ok"], [offer["offer_id"] for offer in kept])
        reasons = {reason for item in hidden for reason in item["reason_codes"]}
        self.assertIn("start_minute_not_allowed", reasons)
        self.assertIn("course_family_disabled", reasons)
        self.assertEqual(1, stats["public_sellable_offers_kept"])

    def test_applies_per_course_and_total_day_caps(self) -> None:
        offers = []
        for index, minute in enumerate(["00", "30", "00", "30", "00"]):
            hour = 8 + index
            offers.append({
                "offer_id": f"offer-{index}",
                "date": "2026-06-22",
                "start_time": f"{hour:02d}:{minute}",
                "course_id": "209806",
                "course_family": "BLS",
            })
        dynamic = {"offers": offers}
        courses = {"courses": [{"course_id": "209806", "family": "BLS"}]}
        policy = {
            "enabled_course_families": ["BLS"],
            "allowed_start_minutes": ["00", "30"],
            "minimum_lead_hours": 24,
            "maximum_days_out": 60,
            "max_offers_per_course_per_day": 2,
            "max_total_offers_per_day": 3,
        }

        kept, hidden, _ = filter_public_sellable_offers.filter_offers(
            dynamic,
            courses,
            policy,
            now=datetime(2026, 6, 19, 12, 0),
        )

        self.assertEqual(2, len(kept))
        self.assertTrue(any("max_offers_per_course_per_day_exceeded" in item["reason_codes"] for item in hidden))

    def test_confirmed_container_policy_keeps_only_container_backed_offers(self) -> None:
        dynamic = {
            "offers": [
                {
                    "offer_id": "shipyard",
                    "date": "2026-06-22",
                    "start_time": "08:30",
                    "course_id": "209806",
                    "course_family": "BLS",
                    "instructor_display_name": "Brian Ennis",
                    "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                    "resource": "Shipyard Office",
                },
                {
                    "offer_id": "offsite",
                    "date": "2026-06-22",
                    "start_time": "09:00",
                    "course_id": "209806",
                    "course_family": "BLS",
                    "instructor_display_name": "Brian Ennis",
                    "location": "Somewhere Else",
                    "resource": "Somewhere Else",
                },
            ]
        }
        courses = {"courses": [{"course_id": "209806", "family": "BLS"}]}
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
        policy = {
            "enabled_course_families": ["BLS"],
            "allowed_start_minutes": ["00", "30"],
            "minimum_lead_hours": 24,
            "maximum_days_out": 60,
            "require_confirmed_appointment_container": True,
        }

        kept, hidden, stats = filter_public_sellable_offers.filter_offers(
            dynamic,
            courses,
            policy,
            now=datetime(2026, 6, 19, 12, 0),
            appointment_containers=containers,
        )

        self.assertEqual(["shipyard"], [offer["offer_id"] for offer in kept])
        self.assertEqual({"location_mismatch": 1}, stats["offers_hidden_by_container_reason"])
        self.assertTrue(any("location_mismatch" in item["reason_codes"] for item in hidden))

    def test_run_outputs_are_scoped_to_audit_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit_dir = root / "data" / "audit"
            missing = root / "missing"

            original_audit_dir = filter_public_sellable_offers.AUDIT_DIR
            original_dynamic = filter_public_sellable_offers.DYNAMIC_OFFERS_PATH
            original_course = filter_public_sellable_offers.COURSE_CATALOG_PATH
            original_containers = filter_public_sellable_offers.APPOINTMENT_CONTAINERS_PATH
            original_policy = filter_public_sellable_offers.PUBLIC_OFFER_POLICY_PATH
            original_output = filter_public_sellable_offers.SELLABLE_OFFERS_PATH
            original_report = filter_public_sellable_offers.REPORT_PATH
            try:
                filter_public_sellable_offers.AUDIT_DIR = audit_dir
                filter_public_sellable_offers.DYNAMIC_OFFERS_PATH = missing / "dynamic.json"
                filter_public_sellable_offers.COURSE_CATALOG_PATH = missing / "courses.json"
                filter_public_sellable_offers.APPOINTMENT_CONTAINERS_PATH = missing / "containers.json"
                filter_public_sellable_offers.PUBLIC_OFFER_POLICY_PATH = missing / "policy.json"
                filter_public_sellable_offers.SELLABLE_OFFERS_PATH = audit_dir / "public_sellable_offers_preview.json"
                filter_public_sellable_offers.REPORT_PATH = audit_dir / "public_sellable_offers_report.md"

                result = filter_public_sellable_offers.run()

                self.assertEqual(0, result["stats"]["public_sellable_offers_kept"])
                written = sorted(path.relative_to(root).as_posix() for path in audit_dir.glob("public_sellable_offers_*"))
                self.assertEqual(
                    [
                        "data/audit/public_sellable_offers_preview.json",
                        "data/audit/public_sellable_offers_report.md",
                    ],
                    written,
                )
            finally:
                filter_public_sellable_offers.AUDIT_DIR = original_audit_dir
                filter_public_sellable_offers.DYNAMIC_OFFERS_PATH = original_dynamic
                filter_public_sellable_offers.COURSE_CATALOG_PATH = original_course
                filter_public_sellable_offers.APPOINTMENT_CONTAINERS_PATH = original_containers
                filter_public_sellable_offers.PUBLIC_OFFER_POLICY_PATH = original_policy
                filter_public_sellable_offers.SELLABLE_OFFERS_PATH = original_output
                filter_public_sellable_offers.REPORT_PATH = original_report


if __name__ == "__main__":
    unittest.main()
