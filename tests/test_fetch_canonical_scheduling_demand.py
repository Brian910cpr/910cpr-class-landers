from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from scripts import fetch_canonical_scheduling_demand as subject
from scripts import apply_anchor_policy


NOW = datetime(2026, 9, 11, 23, 0, tzinfo=timezone.utc)


def payload(**session_overrides):
    session = {
        "canonical_session_id": "session-1",
        "external_class_id": "12345",
        "active_registration_count": 2,
    }
    session.update(session_overrides)
    return {
        "schema_version": subject.SCHEMA_VERSION,
        "generated_at": "2026-09-11T22:59:00Z",
        "active_registration_statuses": ["registered", "confirmed", "completed"],
        "sessions": [session],
    }


class FetchCanonicalSchedulingDemandTests(unittest.TestCase):
    def test_validate_accepts_fresh_pii_free_contract(self):
        self.assertEqual(subject.validate_payload(payload(), now=NOW)["sessions"][0]["active_registration_count"], 2)

    def test_validate_rejects_stale_payload(self):
        stale = payload()
        stale["generated_at"] = "2026-09-11T22:00:00Z"
        with self.assertRaisesRegex(ValueError, "freshness window"):
            subject.validate_payload(stale, now=NOW)

    def test_validate_rejects_pii_like_fields(self):
        with self.assertRaisesRegex(ValueError, "PII-like field"):
            subject.validate_payload(payload(email="student@example.com"), now=NOW)

    def test_stable_hash_ignores_generated_at(self):
        first = payload()
        second = payload()
        second["generated_at"] = "2026-09-11T23:00:00Z"
        self.assertEqual(subject.stable_hash(first), subject.stable_hash(second))

    def test_run_atomically_publishes_valid_snapshot_and_status(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "runtime" / "demand.json"
            status = Path(directory) / "debug" / "status.json"
            with (
                patch.object(subject, "OUTPUT", output),
                patch.object(subject, "STATUS_OUTPUT", status),
                patch.object(subject, "fetch", return_value=payload()),
                patch.dict(subject.os.environ, {"HOT_SYNC_ADMIN_KEY": "test-key"}, clear=True),
            ):
                self.assertEqual(subject.run(now=NOW), 0)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["sessions"][0]["canonical_session_id"], "session-1")
            self.assertTrue(json.loads(status.read_text(encoding="utf-8"))["success"])

    def test_run_preserves_last_good_snapshot_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "runtime" / "demand.json"
            status = Path(directory) / "debug" / "status.json"
            output.parent.mkdir(parents=True)
            output.write_text('{"last":"good"}\n', encoding="utf-8")
            with (
                patch.object(subject, "OUTPUT", output),
                patch.object(subject, "STATUS_OUTPUT", status),
                patch.dict(subject.os.environ, {}, clear=True),
            ):
                self.assertEqual(subject.run(now=NOW), 1)
            self.assertEqual(output.read_text(encoding="utf-8"), '{"last":"good"}\n')
            result = json.loads(status.read_text(encoding="utf-8"))
            self.assertFalse(result["success"])
            self.assertTrue(result["snapshot_preserved"])

    def test_anchor_consumer_rejects_stale_runtime_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            demand_path = Path(directory) / "demand.json"
            stale = payload()
            stale["generated_at"] = "2020-01-01T00:00:00Z"
            demand_path.write_text(json.dumps(stale), encoding="utf-8")
            with patch.object(apply_anchor_policy, "CANONICAL_DEMAND_PATH", demand_path):
                with self.assertRaisesRegex(ValueError, "freshness window"):
                    apply_anchor_policy.sessions_with_canonical_demand([])


if __name__ == "__main__":
    unittest.main()
