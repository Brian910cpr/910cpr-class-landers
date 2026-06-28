from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import public_offer_integrity_audit


class PublicOfferIntegrityAuditTest(unittest.TestCase):
    def test_run_writes_report_contract_and_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audit_dir = root / "data" / "audit"
            data_dir = root / "data"
            docs_data_dir = root / "docs" / "data"
            inventory_dir = root / "data" / "inventory"
            audit_dir.mkdir(parents=True)
            data_dir.mkdir(exist_ok=True)
            docs_data_dir.mkdir(parents=True)
            inventory_dir.mkdir(parents=True)

            (docs_data_dir / "schedule_future.json").write_text(json.dumps({
                "sessions": [{
                    "session_id": "class-1",
                    "course_id": "209806",
                    "course_key": "bls",
                    "official_course_name": "AHA BLS Provider",
                    "start_at": "2026-07-10T08:00:00-04:00",
                    "end_at": "2026-07-10T10:00:00-04:00",
                    "location_name": "Shipyard",
                    "lead_instructor_name": "Brian Ennis",
                }]
            }), encoding="utf-8")
            (data_dir / "sessions_current.json").write_text(json.dumps({"sessions": []}), encoding="utf-8")
            (audit_dir / "live_availability_snapshot_preview.json").write_text(json.dumps({
                "availability_blocks": [{
                    "source_event_id": "open-gap",
                    "instructor_name": "Brian Ennis",
                    "date": "2026-07-10",
                    "start_time": "12:00",
                    "end_time": "14:00",
                    "availability_status": "available",
                    "location_name": "Shipyard",
                }]
            }), encoding="utf-8")
            (inventory_dir / "instructor_availability.json").write_text(json.dumps({"availability_blocks": []}), encoding="utf-8")
            dynamic_offer = {
                "offer_id": "dyn-1",
                "course_id": "209806",
                "course_title": "AHA BLS Provider",
                "course_family": "BLS",
                "instructor_display_name": "Brian Ennis",
                "location": "Shipyard",
                "date": "2026-07-10",
                "start_time": "12:00",
                "end_time": "13:00",
                "appointment_display_start": "2026-07-10T12:00:00",
                "appointment_display_end": "2026-07-10T13:00:00",
                "scheduler_consumption_start": "2026-07-10T12:00:00",
                "scheduler_consumption_end": "2026-07-10T14:00:00",
                "source_availability_window": "open-gap",
                "appointmentDayId": 123,
            }
            (audit_dir / "dynamic_offers_preview.json").write_text(json.dumps({
                "stats": {
                    "offers_generated": 1,
                    "offers_rejected_by_reason": {
                        "conflicts_with_existing_occupancy": 2,
                        "course_does_not_fit_window": 3,
                    },
                },
                "offers": [dynamic_offer],
            }), encoding="utf-8")
            (audit_dir / "public_sellable_offers_preview.json").write_text(json.dumps({
                "offers": [dynamic_offer],
                "hidden_offers": [{
                    "offer": {"offer_id": "hidden"},
                    "reason_codes": ["inside_minimum_lead_time", "missing_container_for_instructor"],
                }],
            }), encoding="utf-8")

            originals = (
                public_offer_integrity_audit.AUDIT_DIR,
                public_offer_integrity_audit.DYNAMIC_OFFERS_PATH,
                public_offer_integrity_audit.PUBLIC_SELLABLE_OFFERS_PATH,
                public_offer_integrity_audit.SCHEDULE_FUTURE_PATH,
                public_offer_integrity_audit.SESSIONS_CURRENT_PATH,
                public_offer_integrity_audit.LIVE_AVAILABILITY_PATH,
                public_offer_integrity_audit.LEGACY_AVAILABILITY_PATH,
                public_offer_integrity_audit.REPORT_MD_PATH,
                public_offer_integrity_audit.REPORT_JSON_PATH,
            )
            try:
                public_offer_integrity_audit.AUDIT_DIR = audit_dir
                public_offer_integrity_audit.DYNAMIC_OFFERS_PATH = audit_dir / "dynamic_offers_preview.json"
                public_offer_integrity_audit.PUBLIC_SELLABLE_OFFERS_PATH = audit_dir / "public_sellable_offers_preview.json"
                public_offer_integrity_audit.SCHEDULE_FUTURE_PATH = docs_data_dir / "schedule_future.json"
                public_offer_integrity_audit.SESSIONS_CURRENT_PATH = data_dir / "sessions_current.json"
                public_offer_integrity_audit.LIVE_AVAILABILITY_PATH = audit_dir / "live_availability_snapshot_preview.json"
                public_offer_integrity_audit.LEGACY_AVAILABILITY_PATH = inventory_dir / "instructor_availability.json"
                public_offer_integrity_audit.REPORT_MD_PATH = audit_dir / "public_offer_integrity_report.md"
                public_offer_integrity_audit.REPORT_JSON_PATH = audit_dir / "public_offer_integrity_report.json"

                report = public_offer_integrity_audit.run()

                self.assertFalse(report["stats"]["audit_failed"])
                self.assertEqual(1, report["stats"]["existing_enrollware_classes_shown"])
                self.assertEqual(1, report["stats"]["dynamic_appointment_seed_offers_generated"])
                self.assertEqual(2, report["stats"]["dynamic_offers_blocked_by_occupancy_overlap"])
                self.assertEqual(1, report["stats"]["dynamic_offers_blocked_by_lead_time"])
                self.assertEqual(3, report["stats"]["dynamic_offers_blocked_by_insufficient_gap"])
                self.assertEqual(1, report["stats"]["dynamic_offers_blocked_by_missing_ids"])
                self.assertEqual(2, report["stats"]["public_sellable_total"])
                self.assertTrue((audit_dir / "public_offer_integrity_report.md").exists())
                self.assertTrue((audit_dir / "public_offer_integrity_report.json").exists())
            finally:
                (
                    public_offer_integrity_audit.AUDIT_DIR,
                    public_offer_integrity_audit.DYNAMIC_OFFERS_PATH,
                    public_offer_integrity_audit.PUBLIC_SELLABLE_OFFERS_PATH,
                    public_offer_integrity_audit.SCHEDULE_FUTURE_PATH,
                    public_offer_integrity_audit.SESSIONS_CURRENT_PATH,
                    public_offer_integrity_audit.LIVE_AVAILABILITY_PATH,
                    public_offer_integrity_audit.LEGACY_AVAILABILITY_PATH,
                    public_offer_integrity_audit.REPORT_MD_PATH,
                    public_offer_integrity_audit.REPORT_JSON_PATH,
                ) = originals


if __name__ == "__main__":
    unittest.main()
