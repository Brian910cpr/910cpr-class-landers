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
            "release_passed": True,
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
            "calculation_completed": True, "release_passed": True,
            "source_snapshot_sha256": "a" * 64,
            "replay_clock_utc": "2026-11-22T08:18:24+00:00",
            "horizon_start": days[0], "horizon_end": days[-1], "horizon_days": 90,
            "pages": {"bls": {"ninety_day_offer_counts": [
                {"date": day, "anchor": 0, "barnacle": 0, "open": 1} for day in days
            ]}}
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
            ("release_passed", False),
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
