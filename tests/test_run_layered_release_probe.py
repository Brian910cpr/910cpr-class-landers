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


if __name__ == "__main__":
    unittest.main()
