from __future__ import annotations

import json
import io
import urllib.error
import urllib.parse
import tempfile
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

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



def native_id(number):
    return f"lw-{number:08x}-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def release(number, now):
    return {"authority": "native-generated-release.v1", "release_reason": "expired_unpaid_hold",
            "canonical_session_id": native_id(number)[3:], "external_class_id": native_id(number),
            "released_at": (now-timedelta(minutes=4)).isoformat(),
            "start_at": (now+timedelta(days=1)).isoformat(), "end_at": (now+timedelta(days=1,hours=1)).isoformat(),
            "consumption_start_at": (now+timedelta(days=1,minutes=-10)).isoformat(),
            "consumption_end_at": (now+timedelta(days=1,hours=1,minutes=10)).isoformat()}


class FetchNativeReleaseProofTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.retained = Path(self.directory.name)/'schedule.json'
        self.now = datetime.now(timezone.utc)
        self.calls = []
        self.history = {native_id(n): release(n,self.now) for n in range(900)}
        self.base = dict(schema_version=subject.SCHEMA_VERSION,generated_at=self.now.isoformat(),sessions=[],released_native_sessions=[])
        self.mutate = lambda proof, index: proof
        self.patch = patch.object(subject,'RETAINED_SCHEDULE',self.retained)
        self.patch.start();self.addCleanup(self.patch.stop)

    def retain(self, numbers):
        self.retained.write_text(json.dumps({'sessions':[{'session_id':native_id(n)} for n in numbers]}))

    def read(self, *, url, **kwargs):
        query = parse_qs(urlsplit(url).query)
        self.calls.append(query)
        if 'release_ids' not in query:
            return deepcopy(self.base)
        self.assertEqual(set(query),{'projection','release_ids'})
        ids = query['release_ids'][0].split(',')
        self.assertLessEqual(len(ids),64)
        proof = dict(schema_version=subject.RELEASE_PROOF_SCHEMA,generated_at=self.now.isoformat(),complete=True,
                     requested_external_class_ids=ids,released_native_sessions=[self.history[sid] for sid in ids if sid in self.history])
        return self.mutate(deepcopy(proof),len(self.calls)-1)

    def fetch(self):
        with patch.object(subject,'_fetch_json',side_effect=self.read):
            return subject.fetch(url=subject.DEFAULT_URL,key='fixture-only')

    def test_900_historical_releases_request_only_one_still_retained_id(self):
        self.retain([800]);payload=self.fetch()
        self.assertEqual(len(self.calls),2)
        self.assertEqual([r['external_class_id'] for r in payload['released_native_sessions']],[native_id(800)])

    def test_501_truly_retained_ids_complete_all_eight_bounded_batches(self):
        self.retain(range(501));payload=self.fetch()
        self.assertEqual(len(self.calls),9)
        ids=[sid for call in self.calls[1:] for sid in call['release_ids'][0].split(',')]
        self.assertEqual(ids,[native_id(n) for n in range(501)])
        self.assertEqual(len(payload['released_native_sessions']),501)
        self.assertEqual(subject._parse_instant(payload['generated_at']),self.now)

    def test_earliest_source_time_is_preserved_not_restamped(self):
        self.retain(range(65))
        oldest=self.now-timedelta(minutes=3)
        self.mutate=lambda p,i:dict(p,generated_at=(oldest if i==1 else self.now).isoformat())
        self.assertEqual(subject._parse_instant(self.fetch()['generated_at']),oldest)

    def test_no_retained_native_ids_need_no_release_rpc(self):
        self.retained.write_text(json.dumps({'sessions':[{'session_id':'123'}]}))
        self.assertEqual(self.fetch()['released_native_sessions'],[]);self.assertEqual(len(self.calls),1)

    def test_unknown_requested_id_is_not_release_authority(self):
        self.retain([999]);self.assertEqual(self.fetch()['released_native_sessions'],[])

    def test_failed_or_incomplete_later_chunk_never_replaces_existing_snapshot(self):
        self.retain(range(65))
        output=Path(self.directory.name)/'demand.json';status=Path(self.directory.name)/'status.json'
        def fail(proof,index):
            if index==2:raise OSError('fixture transport failure')
            return proof
        cases=[fail,lambda p,i:dict(p,complete=False) if i==2 else p,
               lambda p,i:dict(p,requested_external_class_ids=[]) if i==2 else p,
               lambda p,i:dict(p,released_native_sessions=[release(899,self.now)]) if i==2 else p]
        for mutate in cases:
            self.calls=[];self.mutate=mutate;output.write_text('{"last":"good"}\n')
            with patch.object(subject,'_fetch_json',side_effect=self.read),patch.object(subject,'OUTPUT',output),patch.object(subject,'STATUS_OUTPUT',status),patch.dict(subject.os.environ,{'HOT_SYNC_ADMIN_KEY':'fixture-only'},clear=True):
                self.assertEqual(subject.run(now=self.now),1)
            self.assertEqual(output.read_text(),'{"last":"good"}\n')
            self.assertFalse(json.loads(status.read_text())['success'])

    def test_batch_budget_exhaustion_and_bad_retained_input_reject_before_fetch(self):
        for payload in [{'sessions':[{'session_id':native_id(i)} for i in range(4097)]},
                        {'sessions':[{'session_id':native_id(1)}]*2},{'sessions':[{'session_id':'lw-bad'}]},{}]:
            self.retained.write_text(json.dumps(payload))
            with self.assertRaises(ValueError):self.fetch()
            self.assertEqual(self.calls,[])
        self.retained.unlink()
        with self.assertRaises(FileNotFoundError):self.fetch()

    def test_active_released_conflict_rejects_external_or_canonical_identity(self):
        self.retain([1]);row=release(1,self.now)
        for active in [dict(row),dict(row,external_class_id=native_id(999))]:
            active.update(active_registration_count=0,count_available=True)
            self.base['sessions']=[active]
            with self.assertRaisesRegex(ValueError,'Conflicting native release'):self.fetch()

    def test_exact_release_identity_and_all_intervals_required(self):
        self.retain([1])
        for field in ['canonical_session_id','external_class_id','start_at','end_at','consumption_start_at','consumption_end_at']:
            def omit(proof,index):
                proof['released_native_sessions'][0].pop(field)
                return proof
            self.mutate=omit
            with self.assertRaises(ValueError):self.fetch()

    def test_new_release_after_earlier_active_snapshot_rejects_instead_of_restamping(self):
        self.retain([1]);self.base['generated_at']=(self.now-timedelta(minutes=5)).isoformat()
        with self.assertRaisesRegex(ValueError,'Invalid native release timing'):self.fetch()

    def test_duplicate_release_across_chunks_and_stale_proof_reject(self):
        self.retain(range(65))
        def duplicate_canonical(proof,index):
            if index==2:proof['released_native_sessions'][0]['canonical_session_id']=native_id(0)[3:]
            return proof
        self.mutate=duplicate_canonical
        with self.assertRaisesRegex(ValueError,'Conflicting native release'):self.fetch()
        self.mutate=lambda p,i:dict(p,generated_at=(self.now-timedelta(hours=1)).isoformat())
        with self.assertRaisesRegex(ValueError,'freshness window'):self.fetch()

    def test_all_requests_refuse_redirect_without_forwarding_owner_key(self):
        self.retain([1])
        requested=[]
        class RedirectingFixture:
            def open(self, request, timeout):
                requested.append(request)
                return subject.NoRedirect().redirect_request(
                    request,None,302,'Found',{},'https://unapproved.example/private')
        with patch.object(subject.urllib.request,'build_opener',return_value=RedirectingFixture()) as build:
            for url in [subject.request_url(subject.DEFAULT_URL),subject.request_url(subject.DEFAULT_URL,release_ids=[native_id(1)])]:
                with self.assertRaisesRegex(ValueError,'Canonical demand redirect refused'):
                    subject._fetch_json(url=url,key='fixture-only',timeout=30)
                self.assertEqual(build.call_args.args,(subject.NoRedirect,))
        self.assertEqual(len(requested),2)
        self.assertTrue(all(urlsplit(request.full_url).hostname=='wktwgcnwdvbebcobgyey.supabase.co' for request in requested))
        with patch.object(subject.urllib.request,'build_opener') as build:
            with self.assertRaises(ValueError):subject._fetch_json(url='https://unapproved.example/',key='fixture-only',timeout=30)
            build.assert_not_called()

    def test_retained_input_size_bound_is_checked_before_any_network(self):
        self.retain([1])
        with patch.object(subject,'MAX_RETAINED_BYTES',8):
            with self.assertRaisesRegex(ValueError,'input budget'):self.fetch()
        self.assertEqual(self.calls,[])


if __name__=='__main__':unittest.main()
