from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import build_internal_dynamic_seed_preview as preview


class InternalDynamicSeedPreviewTest(unittest.TestCase):
    def test_builds_internal_preview_from_seeds_and_url_previews(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            audit_dir = root / "data" / "audit"
            config_dir = root / "data" / "config"
            audit_dir.mkdir(parents=True)
            config_dir.mkdir(parents=True)

            seeds_path = audit_dir / "schedule_seeds_preview.json"
            urls_path = audit_dir / "seed_appointment_url_preview.json"
            public_policy_path = config_dir / "public_offer_policy.json"
            seed_policy_path = config_dir / "seed_strategy_policy.json"
            html_path = audit_dir / "internal_dynamic_seed_preview.html"
            json_path = audit_dir / "internal_dynamic_seed_preview.json"
            report_path = audit_dir / "internal_dynamic_seed_preview_report.md"

            seeds_path.write_text(json.dumps({
                "seeds": [{
                    "seed_id": "seed-1",
                    "source_offer_id": "offer-1",
                    "date": "2026-07-04",
                    "start_time": "12:00",
                    "end_time": "14:00",
                    "appointment_display_start": "2026-07-04T12:00:00",
                    "appointment_display_end": "2026-07-04T14:00:00",
                    "scheduler_consumption_start": "2026-07-04T12:00:00",
                    "scheduler_consumption_end": "2026-07-04T14:45:00",
                    "scheduler_consumption_minutes": 165,
                    "instructor_lock_start": "2026-07-04T12:00:00",
                    "instructor_lock_end": "2026-07-04T14:45:00",
                    "resource_lock_start": "2026-07-04T12:00:00",
                    "resource_lock_end": "2026-07-04T14:45:00",
                    "course_id": "209806",
                    "course_title": "AHA BLS Provider",
                    "course_family": "BLS",
                    "instructor_display_name": "Brian Ennis",
                    "location": "NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office",
                    "source_location": "4018 Shipyard Blvd, Wilmington, NC",
                    "confidence": "high",
                }]
            }), encoding="utf-8")
            urls_path.write_text(json.dumps({
                "previews": [{
                    "seed_id": "seed-1",
                    "source_offer_id": "offer-1",
                    "matched_container_id": "shipyard_brian",
                    "appointmentDayId": 260683,
                    "appointment_url_preview": "https://example.test/enroll?appointmentDayId=260683",
                    "confidence": "high",
                    "blocking_reason": None,
                }]
            }), encoding="utf-8")
            public_policy_path.write_text(json.dumps({"require_confirmed_appointment_container": True}), encoding="utf-8")
            seed_policy_path.write_text(json.dumps({"max_seeds_per_date": 8}), encoding="utf-8")

            originals = {
                "AUDIT_DIR": preview.AUDIT_DIR,
                "SEEDS_PATH": preview.SEEDS_PATH,
                "URL_PREVIEW_PATH": preview.URL_PREVIEW_PATH,
                "PUBLIC_OFFER_POLICY_PATH": preview.PUBLIC_OFFER_POLICY_PATH,
                "SEED_STRATEGY_POLICY_PATH": preview.SEED_STRATEGY_POLICY_PATH,
                "HTML_PATH": preview.HTML_PATH,
                "JSON_PATH": preview.JSON_PATH,
                "REPORT_PATH": preview.REPORT_PATH,
            }
            try:
                preview.AUDIT_DIR = audit_dir
                preview.SEEDS_PATH = seeds_path
                preview.URL_PREVIEW_PATH = urls_path
                preview.PUBLIC_OFFER_POLICY_PATH = public_policy_path
                preview.SEED_STRATEGY_POLICY_PATH = seed_policy_path
                preview.HTML_PATH = html_path
                preview.JSON_PATH = json_path
                preview.REPORT_PATH = report_path

                result = preview.run()

                self.assertEqual(1, result["stats"]["seeds_read"])
                self.assertEqual(1, result["stats"]["urls_matched"])
                self.assertEqual(1, result["stats"]["preview_rows_rendered"])
                self.assertEqual(0, result["stats"]["missing_urls"])
                payload = json.loads(json_path.read_text(encoding="utf-8"))
                self.assertEqual("shipyard_brian", payload["rows"][0]["matched_container_id"])
                html = html_path.read_text(encoding="utf-8")
                self.assertIn("This is not public", html)
                self.assertIn("REVIEW ONLY — would redirect to Enrollware", html)
                self.assertIn("Customer appointment time", html)
                self.assertIn("Lander scheduler lock window", html)
                self.assertIn("2026-07-04T14:45:00", html)
                self.assertTrue(report_path.exists())
                written = sorted(path.name for path in audit_dir.glob("internal_dynamic_seed_preview*"))
                self.assertEqual([
                    "internal_dynamic_seed_preview.html",
                    "internal_dynamic_seed_preview.json",
                    "internal_dynamic_seed_preview_report.md",
                ], written)
            finally:
                for name, value in originals.items():
                    setattr(preview, name, value)


if __name__ == "__main__":
    unittest.main()
