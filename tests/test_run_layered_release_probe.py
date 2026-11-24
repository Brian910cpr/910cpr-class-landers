"""Read-only V2 replay must fingerprint all real selector source inputs."""
import tempfile
import json
import unittest
from pathlib import Path

from scripts import run_layered_release_probe as probe


class FrozenSourceReplayTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for index, relative in enumerate(probe.SOURCE_PATHS):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('{"fixture": ' + str(index) + '}', encoding="utf-8")

    def test_same_snapshot_has_stable_digest(self):
        first = probe.source_fingerprint(self.root)
        self.assertEqual(first, probe.source_fingerprint(self.root))
        self.assertEqual(len(first), 64)

    def test_any_selected_source_change_invalidates_replay(self):
        baseline = probe.source_fingerprint(self.root)
        for relative in probe.SOURCE_PATHS:
            path = self.root / relative
            original = path.read_bytes()
            path.write_bytes(original + b" changed")
            self.assertNotEqual(baseline, probe.source_fingerprint(self.root), relative)
            path.write_bytes(original)
            self.assertEqual(baseline, probe.source_fingerprint(self.root))

    def test_missing_source_fails_closed(self):
        (self.root / probe.SOURCE_PATHS[0]).unlink()
        with self.assertRaises(FileNotFoundError):
            probe.source_fingerprint(self.root)


    def test_public_summary_is_90_days_and_does_not_expose_slot_or_identity(self):
        proof = {
            "source_snapshot_unchanged": True,
            "source_snapshot_sha256": "a" * 64,
            "replay_clock_utc": "2026-11-22T07:14:08+00:00",
            "canonical_session_count": 26,
            "calendar_coverage_count": 2,
            "calculation_completed": True,
            "diagnostic_passed": True, "release_passed": True,
            "pages": {
                "bls": {
                    "day_patterns": {
                        "2026-11-22": {
                            "private-course-id": {"anchor": ["14:00"], "barnacle": ["11:30"], "open": []}
                        },
                        "2026-11-23": {"private-course-id": {"anchor": [], "barnacle": [], "open": ["08:00", "08:30"]}},
                        "2027-03-01": {"private-course-id": {"anchor": ["09:00"], "barnacle": [], "open": []}
                        },
                    },
                    "counts": {"input_windows": 146, "failed_windows": 11},
                    "offer_roles": {"barnacle": 1, "open_day": 2},
                    "rejection_reasons": {
                        "outside_explicit_availability:person@example.com": 2,
                        "customer@example.com": 1,
                    },
                    "failed_window_issue_categories": {"travel_assumption_unverified": 11},
                    "calculation_issue_counts": {
                        "HARD_BLOCK_COLLISION": 3,
                        "human name:personal detail": 8,
                    },
                    "synthesis_blocked_dates": [],
                },
            },
        }
        safe = probe.public_safe_summary(proof)
        self.assertFalse(safe["published"])
        self.assertTrue(safe["diagnostic_passed"])
        self.assertFalse(safe["release_passed"])
        self.assertEqual(safe["horizon_days"], 90)
        self.assertEqual(safe["horizon_start"], "2026-11-22")
        self.assertEqual(safe["horizon_end"], "2027-02-19")
        self.assertEqual(len(safe["pages"]["bls"]["ninety_day_offer_counts"]), 90)
        self.assertEqual(
            safe["pages"]["bls"]["next_three_days"][0],
            {"date": "2026-11-22", "anchor": 1, "barnacle": 1, "open": 0},
        )
        self.assertEqual(safe["pages"]["bls"]["next_three_days"][1]["open"], 2)
        self.assertEqual(safe["pages"]["bls"]["reconciliation_issue_code_categories"],
                         {"hard_block_collision": 3, "unclassified": 8})
        self.assertEqual(safe["pages"]["bls"]["failed_window_issue_categories"],
                         {"travel_assumption_unverified": 11})
        summary = json.dumps(safe)
        self.assertNotIn("private-course-id", summary)
        self.assertNotIn("14:00", summary)
        self.assertNotIn("@example.com", summary)


    def test_failed_window_categories_are_fixed_and_do_not_expose_raw_error(self):
        issue = {"reason": "missing directional travel assumption: person@example.com"}
        self.assertEqual(probe._window_issue_category(issue), "travel_assumption_unverified")
        self.assertEqual(probe._window_issue_category({"reason": "unresolved_occupied_bounds: private"}),
                         "unresolved_occupied_bounds")
        self.assertEqual(probe._window_issue_category({"reason": "some person's private details"}),
                         "other_window_error")

    def test_fixed_failure_categories_do_not_depend_on_private_identity_suffix(self):
        cases = {
            "duplicate source id: private travel instructor@example.com": "duplicate_source_identity",
            "duplicate durable source id": "duplicate_source_identity",
            "duplicate availability source identity": "duplicate_source_identity",
            "invalid course duration: private location": "course_duration_policy_invalid",
            "invalid evidenced course duration override: private": "course_duration_policy_invalid",
            "invalid slot grid": "slot_grid_policy_invalid",
            "unresolved zero-duration occupancy": "unresolved_occupied_bounds",
        }
        for reason, expected in cases.items():
            with self.subTest(reason=reason):
                self.assertEqual(probe._window_issue_category({"reason": reason}), expected)

    def test_public_summary_fails_closed_on_mutable_or_naive_source(self):
        sample = {"source_snapshot_unchanged": False, "source_snapshot_sha256": "a" * 64,
                  "replay_clock_utc": "2026-11-22T07:14:08+00:00", "pages": {}}
        with self.assertRaises(ValueError):
            probe.public_safe_summary(sample)
        sample["source_snapshot_unchanged"] = True
        sample["replay_clock_utc"] = "2026-11-22T07:14:08"
        with self.assertRaises(ValueError):
            probe.public_safe_summary(sample)


    def _comparable_replay(self):
        first = probe.datetime.fromisoformat("2026-11-22T00:00:00+00:00")
        days = [(first + probe.timedelta(days=i)).date().isoformat() for i in range(90)]
        return {
            "published": False, "source_snapshot_unchanged": True,
            "calculation_completed": True, "diagnostic_passed": True, "release_passed": True,
            "source_snapshot_sha256": "a" * 64,
            "replay_clock_utc": "2026-11-22T08:18:24+00:00",
            "horizon_start": days[0], "horizon_end": days[-1], "horizon_days": 90,
            "pages": {family: {"ninety_day_offer_counts": [
                {"date": day, "anchor": 0, "barnacle": 0, "open": 1} for day in days
            ]} for family in probe.EXPECTED_FAMILIES}
        }

    def test_same_snapshot_main_draft_comparison_returns_only_daily_aggregate_deltas(self):
        main = self._comparable_replay()
        draft = json.loads(json.dumps(main))
        draft["pages"]["bls"]["ninety_day_offer_counts"][0]["open"] = 3
        draft["pages"]["bls"]["ninety_day_offer_counts"][0]["barnacle"] = 1
        delta = probe.compare_safe_summaries(main, draft)
        self.assertTrue(delta["same_source_verified"])
        self.assertFalse(delta["published"])
        self.assertFalse(delta["registration_or_checkout_proven"])
        self.assertEqual(delta["families"]["bls"]["days_with_different_counts"], 1)
        self.assertEqual(delta["families"]["bls"]["offer_roles"]["open"],
                         {"main": 90, "draft": 92, "delta": 2})
        self.assertEqual(delta["families"]["bls"]["offer_roles"]["barnacle"]["delta"], 1)
        self.assertNotIn("ninety_day_offer_counts", delta["families"]["bls"])

    def test_partial_or_missing_window_coverage_is_not_release_success(self):
        main = self._comparable_replay()
        for row in main["pages"].values():
            row["counts"] = {"input_windows": 147, "evaluated_windows": 147, "failed_windows": 0}
        self.assertTrue(probe.coverage_complete(main["pages"]))
        draft = json.loads(json.dumps(main))
        draft["pages"]["acls"]["counts"].update(evaluated_windows=136, failed_windows=11)
        self.assertFalse(probe.coverage_complete(draft["pages"]))
        delta = probe.compare_safe_summaries(main, draft)
        self.assertTrue(delta["same_source_verified"])
        self.assertTrue(delta["main_release_passed"])
        self.assertFalse(delta["draft_release_passed"])
        self.assertEqual(delta["families"]["acls"]["window_coverage"]["draft"]["failed_windows"], 11)
        for bad_counts in ({}, {"input_windows": 0, "evaluated_windows": 0, "failed_windows": 0},
                           {"input_windows": 1, "evaluated_windows": 1, "failed_windows": False},
                           {"input_windows": 2, "evaluated_windows": 1, "failed_windows": 0}):
            draft["pages"]["acls"]["counts"] = bad_counts
            self.assertFalse(probe.coverage_complete(draft["pages"]))

    def test_main_draft_requires_all_eight_real_family_keys(self):
        main = self._comparable_replay()
        self.assertEqual(len(main["pages"]), 8)
        self.assertIn("uscg_first_aid_cpr_aed", main["pages"])
        self.assertEqual(len(probe.compare_safe_summaries(main, main)["families"]), 8)

        missing = json.loads(json.dumps(main))
        missing["pages"].pop("uscg_first_aid_cpr_aed")
        with self.assertRaises(ValueError):
            probe.compare_safe_summaries(main, missing)

        extra = json.loads(json.dumps(main))
        extra["pages"]["unverified_family"] = extra["pages"]["bls"]
        with self.assertRaises(ValueError):
            probe.compare_safe_summaries(main, extra)

    def test_comparison_family_keys_match_actual_selector_runtime(self):
        self.assertEqual(set(probe.load_block_schedule_page_configs()), probe.EXPECTED_FAMILIES)
        # Config uses a hyphenated page key; normalizing to underscores is
        # required to compare the actual eight-family replay.
        self.assertIn("uscg_first_aid_cpr_aed", probe.EXPECTED_FAMILIES)
        self.assertNotIn("uscg-first-aid-cpr-aed", probe.EXPECTED_FAMILIES)

    def test_direct_selector_inputs_are_all_fingerprinted(self):
        for path in ("data/config/travel_time_rules.json",
                     "data/config/anchor_schedule_policy.json",
                     "data/config/native_skills_activation.json",
                     "data/config/calendar_sources.json"):
            self.assertIn(path, probe.SOURCE_PATHS)

    def test_main_draft_horizon_must_start_on_replay_clock_et_day(self):
        main = self._comparable_replay()
        draft = json.loads(json.dumps(main))
        # Both replays can match each other yet still falsely claim a stale
        # 90-day baseline. This used to pass the comparison gate.
        main["replay_clock_utc"] = "2026-11-23T08:18:24+00:00"
        draft["replay_clock_utc"] = main["replay_clock_utc"]
        with self.assertRaisesRegex(ValueError, "horizon does not start"):
            probe.compare_safe_summaries(main, draft)

        # The public horizon follows America/New_York, not the UTC date.
        main["replay_clock_utc"] = "2026-11-23T02:30:00+00:00"
        draft["replay_clock_utc"] = main["replay_clock_utc"]
        self.assertTrue(probe.compare_safe_summaries(main, draft)["same_source_verified"])

    def test_main_draft_mismatched_source_clock_or_family_fails_closed(self):
        main = self._comparable_replay()
        for field, wrong in (
            ("source_snapshot_sha256", "b" * 64),
            ("replay_clock_utc", "2026-11-22T08:18:25+00:00"),
            ("horizon_days", 89),
        ):
            draft = json.loads(json.dumps(main))
            draft[field] = wrong
            with self.assertRaises(ValueError, msg=field):
                probe.compare_safe_summaries(main, draft)
        draft = json.loads(json.dumps(main))
        draft["pages"]["heartsaver"] = draft["pages"].pop("bls")
        with self.assertRaises(ValueError):
            probe.compare_safe_summaries(main, draft)

    def test_main_draft_rejects_incomplete_private_or_mutable_evidence(self):
        main = self._comparable_replay()
        for field, wrong in (
            ("published", True), ("source_snapshot_unchanged", False),
            ("calculation_completed", False),
            ("diagnostic_passed", False),
        ):
            bad = json.loads(json.dumps(main))
            bad[field] = wrong
            with self.assertRaises(ValueError, msg=field):
                probe.compare_safe_summaries(bad, main)
        bad = json.loads(json.dumps(main))
        bad["pages"]["bls"]["ninety_day_offer_counts"][0]["open"] = -1
        with self.assertRaises(ValueError):
            probe.compare_safe_summaries(main, bad)
        bad = json.loads(json.dumps(main))
        bad["pages"]["bls"]["ninety_day_offer_counts"][1]["date"] = "2026-11-23-private-student"
        with self.assertRaises(ValueError):
            probe.compare_safe_summaries(main, bad)
        bad = json.loads(json.dumps(main))
        bad["pages"]["private-person@example.com"] = bad["pages"].pop("bls")
        with self.assertRaises(ValueError):
            probe.compare_safe_summaries(bad, bad)



if __name__ == "__main__":
    unittest.main()
