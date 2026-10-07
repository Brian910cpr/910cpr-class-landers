from __future__ import annotations

import json
import io
import urllib.error
import urllib.parse
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
    def test_http_key_accepts_latin1_unchanged_and_rejects_only_transport_problems(self):
        for key in ("test-key", "caf\u00e9-test"):
            self.assertEqual(subject.validate_admin_key(key), key)
        for key in ("test\r\nvalue", "test\x00value", "test\u2014value", " test", "test "):
            with self.assertRaises(ValueError) as error:
                subject.validate_admin_key(key)
            self.assertNotIn(key, str(error.exception))

    def test_request_owns_iso_bounds_and_does_not_append_second_question_mark(self):
        url = subject.request_url(subject.DEFAULT_URL + "?from=bad&to=bad&secret=private")
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        self.assertEqual(set(query), {"from", "to"})
        start = datetime.fromisoformat(query["from"][0])
        stop = datetime.fromisoformat(query["to"][0])
        self.assertEqual((stop - start).days, 366)

    def test_request_rejects_credential_leaking_targets(self):
        for url in ("https://evil.test/read", subject.DEFAULT_URL.replace("https://", "https://key@"), subject.DEFAULT_URL + "#private"):
            with self.assertRaises(ValueError):
                subject.request_url(url)

    def test_safe_http_error_exposes_only_known_public_error(self):
        for body, expected in [(b'{"error":"Invalid time value","private":"roster"}', "Invalid time value"),
                               (b'{"error":"credential or private roster"}', "withheld"),
                               (b'private HTML', "withheld")]:
            error = urllib.error.HTTPError("https://key@private", 400, "private", {}, io.BytesIO(body))
            result = subject.safe_http_error(error)
            self.assertIn(expected, result)
            self.assertNotIn("roster", result)
            self.assertNotIn("key@", result)

    def test_gateway_formats_do_not_expose_private_body(self):
        for body in (b'{"message":"Invalid API key","private":"student"}',
                     b'{"msg":"Invalid API key"}',
                     b'<html><title>400 Bad Request</title>private student</html>'):
            error = urllib.error.HTTPError("https://private", 400, "private", {}, io.BytesIO(body))
            result = subject.safe_http_error(error)
            self.assertNotIn("student", result)
            self.assertNotIn("withheld", result)

    def test_http_failure_preserves_snapshot_and_redacts_status(self):
        with tempfile.TemporaryDirectory() as directory:
            output, status = Path(directory) / "demand.json", Path(directory) / "status.json"
            output.write_text('{"last":"good"}\n', encoding="utf-8")
            error = urllib.error.HTTPError("https://private", 400, "private", {}, io.BytesIO(b'{"error":"Invalid date range","key":"private"}'))
            with patch.object(subject, "OUTPUT", output), patch.object(subject, "STATUS_OUTPUT", status), patch.object(subject, "fetch", side_effect=error), patch.dict(subject.os.environ, {"HOT_SYNC_ADMIN_KEY":"private"}, clear=True):
                self.assertEqual(subject.run(now=NOW), 1)
            self.assertEqual(output.read_text(), '{"last":"good"}\n')
            result = json.loads(status.read_text())
            self.assertEqual(result["error"], "HTTP 400: Invalid date range")
            self.assertTrue(result["snapshot_preserved"])

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

    def test_fresh_response_does_not_extend_external_roster_watermark(self):
        original = payload(freshness_minutes=60, source_observed_at="2026-09-11T21:59:00Z")
        row = subject.validate_payload(original, now=NOW)["sessions"][0]
        self.assertIsNone(row["active_registration_count"])
        self.assertFalse(row["count_available"])
        self.assertEqual(row["demand_status"], "stale_reconciliation")
        self.assertEqual(original["sessions"][0]["active_registration_count"], 2)

    def test_current_external_roster_and_native_counts_remain_known(self):
        for fields in ({"freshness_minutes":60,"source_observed_at":"2026-09-11T22:01:00Z"},
                       {"freshness_minutes":None,"source_observed_at":None}):
            self.assertEqual(subject.validate_payload(payload(**fields), now=NOW)["sessions"][0]["active_registration_count"],2)

    def test_missing_external_source_watermark_stays_unknown(self):
        row=subject.validate_payload(payload(freshness_minutes=60),now=NOW)["sessions"][0]
        self.assertIsNone(row["active_registration_count"])
        self.assertEqual(row["demand_basis"],"unknown")

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
