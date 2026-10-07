"""Real September 29 iCal occurrences, with no participant data or network calls."""
import json
import unittest
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import build_sessions_current as ingest
from scripts import generate_dynamic_offers as offers
from scripts.anchor_state import promote_seated_sessions
from scripts.block_start_time_selector import build_occupancy, course_rules_by_id
from scripts.build_schedule_future import build_public_future_session
from scripts.publish_admin_schedule import normalize_session
from scripts.publish_landerware_ical import build_ical

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = json.loads((ROOT / "tests/fixtures/enrollware_zero_duration_20260929.json").read_text())


class ZeroDurationPipelineTests(unittest.TestCase):
    def setUp(self):
        self.course_map = ingest.load_course_map(ROOT, "data/config/course_map.json")
        self.rules = course_rules_by_id(json.loads((ROOT / "data/inventory/course_consumption_rules.json").read_text()))

    def session(self, event):
        return ingest.build_session_from_ical_event(
            {**event, "description": "Instructors:\nBrian Ennis (lead)"},
            "2026-09-29T08:00:00-04:00", self.course_map,
        )

    def test_six_source_events_reserve_full_window_through_every_projection(self):
        self.assertEqual(6, len(FIXTURES))
        for event in FIXTURES:
            with self.subTest(session_id=event["uid"]):
                session = self.session(event)
                expected_end = datetime.fromisoformat(event["dtstart"]) + timedelta(minutes=event["expected_minutes"])
                self.assertEqual(expected_end.isoformat(), session["end"])
                self.assertEqual(event["expected_minutes"], session["timing"]["inferred_scheduler_consumption_minutes"])
                public = build_public_future_session(session)
                admin = normalize_session(session)
                for row in (public, admin):
                    self.assertEqual(expected_end.isoformat(), row["end_at"])
                    self.assertEqual(event["expected_minutes"], row["inferred_scheduler_consumption_minutes"])
                # Demand is synthetic here: duration repair must not manufacture
                # registrations or change the real anchor promotion policy.
                anchors = promote_seated_sessions([{**public, "active_registration_count": 1, "demand_basis": "canonical_active_registrations"}])
                self.assertEqual(expected_end.isoformat(), anchors[0]["end_at"])
                calendar = ingest.parse_ical_events(build_ical({"sessions": [admin]}))
                self.assertEqual(expected_end.isoformat(), calendar[0]["dtend"])
                sources = {"sessions_current": {"sessions": [session]}, "schedule_future": {"sessions": [public]}}
                selector_blocks = build_occupancy(sources, self.rules)
                dynamic_blocks = offers.normalize_occupancy(sources["sessions_current"], "sessions_current")
                for blocks in (selector_blocks, dynamic_blocks):
                    end = expected_end.replace(tzinfo=None)
                    start = datetime.fromisoformat(event["dtstart"]).replace(tzinfo=None)
                    index = offers.occupancy_by_date(blocks)
                    # Every quarter-hour inside the occupied window must block,
                    # including its final minute. Exact adjacency stays valid.
                    for minute in [*range(0, event["expected_minutes"], 15), event["expected_minutes"] - 1]:
                        candidate = start + timedelta(minutes=minute)
                        candidates = offers.occupancy_candidates(index, candidate, candidate + timedelta(minutes=1))
                        self.assertTrue(offers.has_conflict(candidate, candidate + timedelta(minutes=1), candidates, event["location"], {"display_name": "Brian Ennis"})[0])
                    self.assertFalse(offers.has_conflict(end, end + timedelta(minutes=15), blocks, event["location"], {"display_name": "Brian Ennis"})[0])

    def test_nonzero_source_end_is_preserved_but_cannot_shorten_occupied_duration(self):
        for event in FIXTURES:
            for minutes in (30, 90, 180):
                with self.subTest(session_id=event["uid"], minutes=minutes):
                    end = (datetime.fromisoformat(event["dtstart"]) + timedelta(minutes=minutes)).isoformat()
                    session = self.session({**event, "dtend": end})
                    self.assertEqual(end, session["end"])
                    self.assertIsNone(session["timing"]["end_inference_reason"])
                    public = build_public_future_session(session)
                    self.assertEqual(end, public["end_at"])
                    blocks = build_occupancy({"schedule_future": {"sessions": [public]}}, self.rules)
                    minimum_end = datetime.fromisoformat(event["dtstart"]) + timedelta(minutes=event["expected_minutes"])
                    self.assertEqual(max(datetime.fromisoformat(end), minimum_end).replace(tzinfo=None), blocks[0]["end"])

    def test_offer_generation_filters_occupied_windows_before_returning_candidates(self):
        catalog = json.loads((ROOT / "data/config/course_catalog.json").read_text())
        heartcode = next(c for c in catalog["courses"] if c["course_id"] == "210549")
        for event in FIXTURES:
            with self.subTest(session_id=event["uid"]):
                session = self.session(event)
                start = datetime.fromisoformat(session["start"]).replace(tzinfo=None)
                end = datetime.fromisoformat(session["end"]).replace(tzinfo=None)
                loaded = {
                    "course_catalog": {"courses": [heartcode]},
                    "people_catalog": {"people": [{"person_id": "fixture_brian", "display_name": "Brian Ennis", "assignment_mode": "PRIMARY", "dynamic_offer_eligible": True, "certifications": [{"certification_code": "AHA_BLS_INSTRUCTOR"}]}]},
                    "live_availability_snapshot": {"availability_blocks": [{"instructor_name": "Brian Ennis", "start_datetime": (start - timedelta(hours=2)).isoformat(), "end_datetime": (end + timedelta(hours=2)).isoformat(), "availability_status": "available", "source_type": "google_calendar", "source_calendar_id": "fixture_google", "location_name": event["location"], "allowed_course_families": ["BLS"]}]},
                    "sessions_current": {"sessions": [session]},
                }
                generated, rejected, _ = offers.generate_offers(loaded)
                self.assertTrue(generated, "Nonconflicting time on either side remains offerable")
                self.assertTrue(rejected)
                self.assertEqual({"conflicts_with_existing_occupancy"}, {r["reason_code"] for r in rejected})
                for offer in generated:
                    self.assertFalse(offers.intervals_overlap(datetime.fromisoformat(offer["scheduler_consumption_start"]), datetime.fromisoformat(offer["scheduler_consumption_end"]), start, end))
                loaded["sessions_current"] = {"sessions": []}
                without_occupancy, _, _ = offers.generate_offers(loaded)
                self.assertEqual(len(without_occupancy), len(generated) + len(rejected))

    def test_unknown_future_duration_stops_import_without_overwriting_last_snapshot(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "sessions.json"
            original = '{"sessions": []}'
            output.write_text(original)
            event = {**FIXTURES[0], "summary": "Unmapped course", "dtstart": "2099-01-01T10:00:00-05:00", "dtend": "2099-01-01T10:00:00-05:00"}
            with patch.object(ingest, "fetch_ical_text", return_value=""), patch.object(ingest, "parse_ical_events", return_value=[event]):
                with self.assertRaisesRegex(ValueError, "Unresolved occupied duration.*publication blocked"):
                    ingest.build_sessions_from_enrollware_ical(repo_root=root, ical_url="unused", output_path=output, audit_dir=root / "audit", course_map=self.course_map)
            self.assertEqual(original, output.read_text())

    def test_rule_cache_does_not_leak_between_metadata_snapshots(self):
        self.assertEqual(120, ingest.course_consumption_minutes(self.course_map, "252737"))
        self.assertIsNone(ingest.course_consumption_minutes({}, "252737"))

    def test_ambiguous_catalog_identity_is_not_guessed(self):
        course_map = deepcopy(self.course_map)
        family = next(c for c in course_map["_catalog_courses"] if c["course_id"] == "252737")
        course_map["_catalog_courses"].append({**family, "course_id": "ambiguous"})
        mapped, status, _ = ingest.resolve_course_mapping(course_map, course_id=None, course_number=None, raw_course_title="AHA - Family & Friends® CPR")
        self.assertIsNone(mapped)
        self.assertEqual("unmapped", status)


if __name__ == "__main__":
    unittest.main()
