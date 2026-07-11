from __future__ import annotations

import unittest
import importlib.util
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime

from scripts import build_index_and_sitemap
from scripts import block_start_time_selector
from scripts import build_course_at_city
from scripts import build_course_landers
from scripts import build_index
from scripts import build_schedule_future
from scripts import hub_utils
from scripts import build_seed_appointment_url_preview
from scripts import filter_public_sellable_offers
from scripts import suppress_tbd_public_inventory
from scripts.public_class_eligibility import is_public_class_location, public_location_rejection_reason


def load_legacy_class_index_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "build-classes-index.py"
    spec = importlib.util.spec_from_file_location("build_classes_index_legacy", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PublicClassEligibilityTests(unittest.TestCase):
    AMY_ACLS_PALS_SESSION_IDS = {
        "13673159", "13673169", "13673179", "13673189",
        "13673160", "13673170", "13673180", "13673190",
        "13673161", "13673171", "13673181", "13673191",
        "13673162", "13673172", "13673182", "13673192",
        "13673163", "13673173", "13673185", "13673193",
        "13673164", "13673174", "13673183", "13673194",
        "13673165", "13673175", "13673184", "13673195",
    }

    def test_double_colon_public_locations_are_public(self) -> None:
        self.assertTrue(is_public_class_location(":: Wilmington"))
        self.assertTrue(is_public_class_location(":: Holly Ridge"))

    def test_private_and_blank_locations_are_not_public(self) -> None:
        self.assertFalse(is_public_class_location("Brunswick Oral & Maxillofacial Surgery"))
        self.assertFalse(is_public_class_location(""))
        self.assertFalse(is_public_class_location(None))

    def test_leading_whitespace_is_trimmed_before_exact_prefix_check(self) -> None:
        self.assertTrue(is_public_class_location("  :: Wilmington"))
        self.assertFalse(is_public_class_location(" : : Wilmington"))

    def test_selector_pages_exclude_private_locations(self) -> None:
        self.assertFalse(block_start_time_selector.public_location_allowed("Brunswick Oral & Maxillofacial Surgery", {}))
        self.assertTrue(block_start_time_selector.public_location_allowed(":: Wilmington; Shipyard Blvd - B", {}))

    def test_schedule_future_direct_double_colon_location_is_public(self) -> None:
        session = {"location": {"location_name": ":: Wilmington; Shipyard Blvd"}}
        self.assertEqual(
            ":: Wilmington; Shipyard Blvd",
            build_schedule_future.public_location_for_session(session, {}),
        )

    def test_schedule_future_room_a_b_c_locations_map_to_public_resources(self) -> None:
        aliases = build_schedule_future.load_public_location_aliases(
            Path(__file__).resolve().parents[1] / build_schedule_future.LOCATION_RESOURCE_MAP_PATH
        )
        cases = {
            "NC - Wilmington: 4018 Shipyard Blvd; Room A @ 910CPR's Office": ":: Wilmington; Shipyard Blvd - A",
            "NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office": ":: Wilmington; Shipyard Blvd - B",
            "NC - Wilmington: 4018 Shipyard Blvd; Room C @ 910CPR's Office": ":: Wilmington; Shipyard Blvd - C (Other)",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                session = {"location": {"location_name": raw}}
                self.assertEqual(expected, build_schedule_future.public_location_for_session(session, aliases))

    def test_schedule_future_unmapped_non_double_colon_location_is_suppressed(self) -> None:
        session = {"location": {"location_name": "Brunswick Oral & Maxillofacial Surgery"}}
        self.assertIsNone(build_schedule_future.public_location_for_session(session, {}))

    def test_schedule_future_mapped_private_location_is_suppressed(self) -> None:
        session = {"location": {"location_name": "Private Alias"}}
        aliases = {build_schedule_future.normalize_location_key("Private Alias"): "Private Canonical"}
        self.assertIsNone(build_schedule_future.public_location_for_session(session, aliases))

    def test_schedule_future_has_no_blanket_ical_bypass_for_unmapped_private_location(self) -> None:
        session = {
            "session_id": "private-ical",
            "location": {"location_name": "Brunswick Oral & Maxillofacial Surgery"},
        }
        self.assertIsNone(build_schedule_future.public_location_for_session(session, {}))

    def test_private_location_cannot_receive_direct_booking_url_preview(self) -> None:
        seeds = {
            "seeds": [{
                "seed_id": "private-seed",
                "date": "2026-08-10",
                "start_time": "11:30",
                "course_id": "209818",
                "course_title": "AHA ACLS Provider (Renewal)",
                "instructor_display_name": "Brian Ennis",
                "location": "Brunswick Oral & Maxillofacial Surgery",
            }]
        }
        courses = {"courses": [{"course_id": "209818", "appointment_allowed": True}]}
        containers = {"containers": [{
            "status": "active",
            "container_id": "private-test",
            "instructor_name": "Brian Ennis",
            "location_name": "Brunswick Oral & Maxillofacial Surgery",
            "first_valid_date": "2026-08-01",
            "last_valid_date": "2026-08-31",
            "first_valid_appointmentDayId": 1,
            "last_valid_appointmentDayId": 31,
        }]}
        records, _stats = build_seed_appointment_url_preview.build_preview_records(seeds, courses, containers, {})
        self.assertEqual(records[0]["blocking_reason"], "location_not_public_double_colon_prefix_required")
        self.assertIsNone(records[0]["appointment_url_preview"])

    def test_counters_and_quick_date_public_sessions_exclude_private_location(self) -> None:
        session = {
            "session_id": "12946261",
            "course_name": "AHA ACLS Provider (Renewal)",
            "start_at": "2026-08-10T11:30:00-04:00",
            "location_name": "Brunswick Oral & Maxillofacial Surgery",
            "registration_url": "https://coastalcprtraining.enrollware.com/enroll?id=12946261",
            "session_status": "active",
        }
        self.assertIsNone(build_index_and_sitemap.schedule_future_to_public_session(session))

    def test_future_external_publishing_filter_excludes_private_location(self) -> None:
        reasons = filter_public_sellable_offers.base_rejection_reasons(
            {
                "offer_id": "private-external",
                "course_id": "209818",
                "course_family": "ACLS",
                "date": "2026-08-10",
                "start_time": "11:30",
                "location": "Brunswick Oral & Maxillofacial Surgery",
            },
            {"course_id": "209818"},
            {},
            datetime(2026, 7, 10),
        )
        self.assertIn("location_not_public_double_colon_prefix_required", reasons)

    def test_public_schedule_json_writer_excludes_private_locations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "schedule_future.json"
            out = root / "public_schedule.json"
            source.write_text(json_dump({
                "build": {"generated_at": "2026-07-10T12:00:00-04:00"},
                "sessions": [
                    {
                        "session_id": "20000001",
                        "course_id": "209806",
                        "course_name": "AHA BLS Provider",
                        "start_at": "2026-08-10T09:00:00-04:00",
                        "location_name": ":: Wilmington",
                        "registration_url": "https://example.test/enroll?id=20000001",
                    },
                    {
                        "session_id": "12946261",
                        "course_id": "209818",
                        "course_name": "AHA ACLS Provider (Renewal)",
                        "start_at": "2026-08-10T11:30:00-04:00",
                        "location_name": "Brunswick Oral & Maxillofacial Surgery",
                        "registration_url": "https://example.test/enroll?id=12946261",
                    },
                ],
            }), encoding="utf-8")
            count = suppress_tbd_public_inventory.write_public_schedule_from_future(source, [out], set())
            payload = json_load(out)
            self.assertEqual(count, 1)
            self.assertEqual(payload["count"], 1)
            self.assertEqual(payload["sessions"][0]["class_id"], "20000001")
            self.assertNotIn("12946261", out.read_text(encoding="utf-8"))

    def test_public_schedule_json_writer_excludes_closed_and_full_direct_booking_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "schedule_future.json"
            out = root / "public_schedule.json"
            base = {
                "course_id": "209806",
                "course_name": "AHA BLS Provider",
                "start_at": "2026-08-10T09:00:00-04:00",
                "location_name": ":: Wilmington",
                "registration_url": "https://example.test/enroll",
            }
            source.write_text(json_dump({
                "build": {"generated_at": "2026-07-10T12:00:00-04:00"},
                "sessions": [
                    {**base, "session_id": "open", "registration_status": "open", "public_direct_booking": True},
                    {**base, "session_id": "closed", "registration_status": "closed", "public_direct_booking": False},
                    {**base, "session_id": "full", "registration_status": "full", "public_direct_booking": False},
                ],
            }), encoding="utf-8")

            count = suppress_tbd_public_inventory.write_public_schedule_from_future(source, [out], set())
            text = out.read_text(encoding="utf-8")
            self.assertEqual(count, 1)
            self.assertIn('"class_id": "open"', text)
            self.assertNotIn('"class_id": "closed"', text)
            self.assertNotIn('"class_id": "full"', text)

    def test_suppress_tbd_cli_uses_normalized_schedule_future_not_raw_current_locations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            schedule_future = root / "docs" / "data" / "schedule_future.json"
            public_schedule = root / "docs" / "public_schedule.json"
            current = root / "data" / "sessions_current.json"
            schedule_future.parent.mkdir(parents=True)
            current.parent.mkdir(parents=True)

            schedule_future.write_text(json_dump({
                "build": {"generated_at": "2026-07-11T12:00:00-04:00"},
                "sessions": [
                    {
                        "session_id": "13673159",
                        "course_id": "209818",
                        "course_name": "AHA ACLS Provider (Initial)",
                        "start_at": "2026-08-10T09:00:00-04:00",
                        "location_name": ":: Wilmington; Shipyard Blvd - B",
                        "location_display": ":: Wilmington; Shipyard Blvd - B",
                        "registration_url": "https://example.test/enroll?id=13673159",
                    }
                ],
            }), encoding="utf-8")
            current.write_text(json_dump({
                "sessions": [
                    {
                        "session_id": "13673159",
                        "location_name": "NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office",
                    }
                ],
            }), encoding="utf-8")

            old_root = suppress_tbd_public_inventory.ROOT
            try:
                suppress_tbd_public_inventory.ROOT = root
                suppress_tbd_public_inventory.main()
            finally:
                suppress_tbd_public_inventory.ROOT = old_root

            payload = json_load(public_schedule)
            self.assertEqual(1, payload["count"])
            self.assertEqual("13673159", payload["sessions"][0]["class_id"])
            self.assertEqual(":: Wilmington; Shipyard Blvd - B", payload["sessions"][0]["location_name"])

    def test_schedule_future_contains_known_good_amy_acls_pals_sessions_after_regeneration(self) -> None:
        path = Path(__file__).resolve().parents[1] / "docs" / "data" / "schedule_future.json"
        payload = json_load(path)
        sessions = payload.get("sessions", [])
        amy_sessions = [
            session for session in sessions
            if str(session.get("session_id")) in self.AMY_ACLS_PALS_SESSION_IDS
        ]
        self.assertEqual(28, len(amy_sessions))
        self.assertEqual(self.AMY_ACLS_PALS_SESSION_IDS, {str(session.get("session_id")) for session in amy_sessions})
        self.assertTrue(all(str(session.get("location_name") or "").startswith("::") for session in amy_sessions))

    def test_schedule_future_public_rows_all_have_public_locations(self) -> None:
        path = Path(__file__).resolve().parents[1] / "docs" / "data" / "schedule_future.json"
        payload = json_load(path)
        bad = [
            (session.get("session_id"), session.get("location_name"))
            for session in payload.get("sessions", [])
            if not str(session.get("location_name") or "").strip().startswith("::")
        ]
        self.assertEqual([], bad)

    def test_topic_source_loader_excludes_private_locations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "schedule.json"
            source.write_text(json_dump({
                "sessions": [
                    {"session_id": "20000001", "course_name": "AHA BLS Provider", "location_name": ":: Wilmington"},
                    {"session_id": "12946261", "course_name": "AHA ACLS Provider (Renewal)", "location_name": "Brunswick Oral & Maxillofacial Surgery"},
                ]
            }), encoding="utf-8")
            old_schedule = build_index.SCHEDULE_FILE
            old_fallback = build_index.SCHEDULE_FALLBACK_FILE
            try:
                build_index.SCHEDULE_FILE = source
                build_index.SCHEDULE_FALLBACK_FILE = source
                sessions = build_index.load_sessions()
            finally:
                build_index.SCHEDULE_FILE = old_schedule
                build_index.SCHEDULE_FALLBACK_FILE = old_fallback
            self.assertEqual([s["session_id"] for s in sessions], ["20000001"])

    def test_course_at_city_generator_excludes_private_locations(self) -> None:
        sessions = [
            SimpleNamespace(location_raw=":: Wilmington", city="Wilmington", course_family="BLS"),
            SimpleNamespace(location_raw="Brunswick Oral & Maxillofacial Surgery", city="Supply", course_family="ACLS"),
        ]
        eligible = build_course_at_city.eligible_course_at_city_sessions(sessions)
        self.assertEqual(len(eligible), 1)
        self.assertEqual(eligible[0].city, "Wilmington")

    def test_class_report_hub_source_can_exclude_nonpublic_current_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sessions_current.json"
            source.write_text(json_dump({
                "sessions": [
                    {"session_id": "12774095", "location_name": "___TBD___"},
                    {"session_id": "20000001", "location_name": ":: Wilmington"},
                ]
            }), encoding="utf-8")
            ids = hub_utils.nonpublic_session_ids_from_current(source)
            self.assertIn("12774095", ids)
            self.assertNotIn("20000001", ids)

    def test_course_landers_session_source_excludes_private_locations(self) -> None:
        sessions = build_course_landers.public_course_lander_sessions({
            "sessions": [
                {"session_id": "20000001", "course_name": "AHA BLS Provider", "location_name": ":: Wilmington"},
                {"session_id": "12946261", "course_name": "AHA ACLS Provider (Renewal)", "location_name": "Brunswick Oral & Maxillofacial Surgery"},
            ]
        })
        self.assertEqual([s["session_id"] for s in sessions], ["20000001"])

    def test_proposed_sessions_are_excluded_from_sitemap_deploy_listing(self) -> None:
        generate_sitemap = Path(__file__).resolve().parents[1] / "scripts" / "generate_sitemap.py"
        text = generate_sitemap.read_text(encoding="utf-8")
        self.assertIn('"proposed-sessions"', text)
        self.assertIn("excluded_relative_parts", text)

    def test_legacy_class_aggregate_generator_deletes_private_and_stale_outputs(self) -> None:
        legacy = load_legacy_class_index_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            classes_dir = root / "docs" / "classes"
            schedule_path = root / "docs" / "data" / "schedule_future.json"
            manifest_path = root / "docs" / "data" / "generated_class_aggregate_manifest.json"
            schedule_path.parent.mkdir(parents=True)
            classes_dir.mkdir(parents=True)

            legacy.BASE_DIR = str(classes_dir)
            legacy.SCHEDULE_PATH = str(schedule_path)
            legacy.LEGACY_SCHEDULE_PATH = str(schedule_path)
            legacy.MANIFEST_PATH = str(manifest_path)
            legacy.CONTROLLED_GENERATED_DIRS = (
                str(classes_dir),
                str(classes_dir / "months"),
                str(classes_dir / "cities"),
                str(classes_dir / "courses"),
                str(classes_dir / "course-at-city"),
            )

            # Existing generated files from a prior build.
            stale_private_direct = classes_dir / "12946261.html"
            stale_public_direct = classes_dir / "20000001.html"
            stale_private_direct.write_text("Brunswick Oral & Maxillofacial Surgery 12946261", encoding="utf-8")
            stale_public_direct.write_text(":: Wilmington 20000001", encoding="utf-8")
            (classes_dir / "months").mkdir(parents=True)
            stale_month = classes_dir / "months" / "2026-09.html"
            stale_month.write_text("Brunswick Oral & Maxillofacial Surgery 12946261", encoding="utf-8")
            outside = root / "docs" / "private-do-not-touch.html"
            outside.parent.mkdir(parents=True, exist_ok=True)
            outside.write_text("Brunswick Oral & Maxillofacial Surgery", encoding="utf-8")

            schedule_path.write_text(
                json_dump([
                    {
                        "session_id": "20000001",
                        "course_name": "AHA BLS Provider",
                        "start_at": "2026-08-10T09:00:00-04:00",
                        "location_name": ":: Wilmington",
                        "city": "Wilmington",
                    },
                    {
                        "session_id": "12946261",
                        "course_name": "AHA ACLS Provider (Renewal)",
                        "start_at": "2026-08-10T11:30:00-04:00",
                        "location_name": "Brunswick Oral & Maxillofacial Surgery",
                        "city": "Supply",
                    },
                ]),
                encoding="utf-8",
            )

            legacy.main()

            self.assertFalse(stale_private_direct.exists())
            self.assertFalse(stale_month.exists())
            self.assertTrue(stale_public_direct.exists())
            self.assertTrue(outside.exists())

            aggregate_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in classes_dir.rglob("*.html")
            )
            self.assertIn("AHA BLS Provider", aggregate_text)
            self.assertIn("Wilmington", aggregate_text)
            self.assertNotIn("12946261", aggregate_text)
            self.assertNotIn("Brunswick Oral & Maxillofacial Surgery", aggregate_text)

            manifest = json_load(manifest_path)
            self.assertIn(str(stale_private_direct).replace(os.sep, "/"), "\n".join(manifest["deleted_stale_files"]))


def json_dump(value):
    import json

    return json.dumps(value, indent=2)


def json_load(path: Path):
    import json

    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
