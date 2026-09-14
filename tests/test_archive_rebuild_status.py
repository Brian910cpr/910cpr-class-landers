import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('archive_rebuild_status', ROOT / 'scripts/archive_rebuild_status.py')
status_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status_module)

AT = '2026-09-14T13:00:00+00:00'
SHA = 'a' * 40


def fixture():
    recovery = json.loads((ROOT / status_module.RECOVERY).read_text())
    identity = json.loads((ROOT / status_module.IDENTITY).read_text())
    provenance = {'repository': 'Brian910cpr/910cpr-class-landers', 'branch': 'codex/monitor-test',
                  'commit': SHA, 'pr': None,
                  'sources': [{'commit': SHA, 'path': path} for path in (status_module.RECOVERY, status_module.IDENTITY)]}
    return recovery, identity, provenance


def baseline():
    return status_module.initial(*fixture(), AT, 'test-run')


def update(status):
    return {key: status_module.deepcopy(status[key]) for key in ('phase', 'state', 'blockers', 'metrics', 'evidence', 'gsc')} | {'expected_revision': status['revision']}


def generation(status):
    change = update(status)
    change.update(phase='GENERATION', state='RUNNING', blockers=[])
    change['metrics']['eligible_pages'] = 100
    change['metrics']['pages_generated'] = 10
    change['evidence']['eligibility'] = {'commit': SHA, 'path': 'data/audit/approved_test.json'}
    return change


class ArchiveRebuildStatusTests(unittest.TestCase):
    def test_real_audit_baseline_distinguishes_candidates_from_approval(self):
        result = baseline()
        self.assertEqual(result['baseline']['source_rows_recovered'], 26165)
        self.assertEqual(result['baseline']['html_urls_recovered'], 26171)
        self.assertEqual(result['baseline']['preliminary_candidates'], 23488)
        self.assertEqual(result['baseline']['non_candidate_rows'], 2677)
        self.assertEqual(result['baseline']['excluded_private_ambiguous_rows'], 2037)
        self.assertEqual(result['baseline']['not_elapsed_rows'], 640)
        self.assertIsNone(result['metrics']['eligible_pages'])
        self.assertTrue(all(value is None for value in result['gsc'].values()))

    def test_mismatched_source_totals_and_approval_fail_closed(self):
        for mutate in ('historical_rows', 'dispositions', 'approval'):
            r, i, p = fixture()
            if mutate == 'historical_rows':
                i['historical_rows'] -= 1
            elif mutate == 'dispositions':
                i['exclusive_historical_dispositions']['shared_identity_invalid_timing'] += 1
            else:
                r['publication_authorized_count'] = 23488
            with self.assertRaises(ValueError):
                status_module.initial(r, i, p, AT, 'test')

    def test_source_private_fields_are_not_copied(self):
        r, i, p = fixture()
        r['private'] = {'email': 'private@example.test', 'token': 'private-token'}
        i['source_rows'] = [{'name': 'Private Person'}]
        encoded = json.dumps(status_module.initial(r, i, p, AT, 'test'))
        for sentinel in ('private@example.test', 'private-token', 'Private Person', 'orphans_by_path_sha256'):
            self.assertNotIn(sentinel, encoded)

    def test_update_rejects_unstructured_private_payload(self):
        result = baseline()
        change = update(result)
        change['message'] = 'student data must not be accepted'
        with self.assertRaises(ValueError):
            status_module.advance(result, change, AT)
        change = update(result)
        change['metrics']['customer_email'] = 'private@example.test'
        with self.assertRaises(ValueError):
            status_module.advance(result, change, AT)

    def test_generation_requires_eligibility_and_immutable_evidence(self):
        result = baseline()
        for mutation in ('unknown', 'unproved', 'too_many'):
            change = generation(result)
            if mutation == 'unknown':
                change['metrics']['eligible_pages'] = None
            elif mutation == 'unproved':
                change['evidence']['eligibility'] = None
            else:
                change['metrics']['pages_generated'] = 101
            with self.assertRaises(ValueError):
                status_module.advance(result, change, AT)

    def test_numeric_validation_rejects_bool_float_negative_and_string(self):
        for invalid in (True, -1, 1.5, '10'):
            result = baseline()
            change = generation(result)
            change['metrics']['pages_generated'] = invalid
            with self.assertRaises(ValueError):
                status_module.advance(result, change, AT)

    def test_progress_denominator_is_full_eligible_corpus(self):
        result = baseline()
        advanced = status_module.advance(result, generation(result), AT)
        self.assertEqual(advanced['metrics']['eligible_pages'], 100)
        self.assertEqual(advanced['metrics']['pages_generated'], 10)
        self.assertEqual(advanced['revision'], 1)
        self.assertEqual(advanced['events'][0]['metrics']['pages_generated'], 10)
        self.assertIsNone(result['metrics']['eligible_pages'])

    def test_validation_and_deployment_need_evidence_and_consistent_counts(self):
        result = baseline()
        for mutation in ('unproved_validation', 'partition', 'sitemap', 'publication', 'unproved_deploy'):
            change = generation(result)
            change['metrics']['pages_validated'] = 8
            change['evidence']['validation'] = {'commit': SHA, 'path': 'data/audit/validation_test.json'}
            if mutation == 'unproved_validation':
                change['evidence']['validation'] = None
            elif mutation == 'partition':
                change['metrics']['pages_failed_validation'] = 3
            elif mutation == 'sitemap':
                change['metrics']['sitemap_urls_generated'] = 9
            elif mutation == 'publication':
                change['metrics']['pages_published'] = 9
                change['evidence']['deployment'] = {'commit': SHA, 'path': 'data/audit/deploy_test.json'}
            else:
                change['metrics']['pages_published'] = 8
            with self.assertRaises(ValueError):
                status_module.advance(result, change, AT)

    def test_stale_heartbeat_cannot_be_hidden_by_polling(self):
        result = baseline()
        running = status_module.advance(result, generation(result), AT)
        self.assertEqual(status_module.health(running, '2026-09-14T13:05:00Z'), 'RUNNING')
        self.assertEqual(status_module.health(running, '2026-09-14T13:05:01Z'), 'STALLED')
        self.assertEqual(status_module.health(running, '2026-09-14T13:06:00Z'), 'STALLED')
        self.assertEqual(running['last_checkpoint_at'], AT)
        self.assertEqual(status_module.health(result, '2026-09-15T13:00:00Z'), 'BLOCKED')
        self.assertEqual(status_module.health(running, '2026-09-14T12:59:59Z'), 'CLOCK_MISMATCH')

    def test_conflicts_time_and_count_regressions_preserve_original(self):
        base = baseline()
        running = status_module.advance(base, generation(base), AT)
        for mutation in ('revision', 'time', 'count', 'phase', 'eligibility'):
            change = update(running)
            at = AT
            if mutation == 'revision':
                change['expected_revision'] = 0
            elif mutation == 'time':
                at = '2026-09-14T12:00:00Z'
            elif mutation == 'count':
                change['metrics']['pages_generated'] = 9
            elif mutation == 'phase':
                change['phase'] = 'SOURCE_RECOVERY'
            else:
                change['metrics']['eligible_pages'] = 101
            with self.assertRaises(ValueError):
                status_module.advance(running, change, at)
        self.assertEqual(running['revision'], 1)

    def test_gsc_is_unknown_until_observed_with_window_and_evidence(self):
        result = baseline()
        change = generation(result)
        change['gsc'].update(discovered=20, indexed=10, class_impressions=30, class_clicks=2,
                             observed_at=AT, window_start='2026-09-01T00:00:00Z', window_end='2026-09-14T00:00:00Z')
        with self.assertRaises(ValueError):
            status_module.advance(result, change, AT)
        change['evidence']['gsc'] = {'commit': SHA, 'path': 'data/audit/gsc_test.json'}
        self.assertEqual(status_module.advance(result, change, AT)['gsc']['indexed'], 10)
        change['gsc']['window_end'] = '2026-09-15T00:00:00Z'
        with self.assertRaises(ValueError):
            status_module.advance(result, change, AT)

    def test_event_rail_is_bounded_newest_first_and_checked(self):
        result = baseline()
        for _ in range(105):
            result = status_module.advance(result, update(result), AT)
        self.assertEqual(len(result['events']), 100)
        self.assertEqual(result['events'][0]['revision'], 105)
        result['events'][0]['metrics']['pages_generated'] = 1
        with self.assertRaises(ValueError):
            status_module.validate(result)

    def test_lock_prevents_competing_writer_and_cleans_up(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'status.json'
            with status_module.writer_lock(output):
                with self.assertRaises(FileExistsError):
                    with status_module.writer_lock(output):
                        self.fail('Second writer entered')
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_atomic_failure_preserves_last_good_feed_and_removes_temporary(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'status.json'
            output.write_text('last-good')
            with patch.object(status_module.os, 'replace', side_effect=OSError('synthetic failure')):
                with self.assertRaises(OSError):
                    status_module.write_atomic(output, baseline())
            self.assertEqual(output.read_text(), 'last-good')
            self.assertEqual(list(Path(directory).iterdir()), [output])
            status_module.write_atomic(output, baseline())
            self.assertEqual(json.loads(output.read_text())['issue'], 229)

    def test_cli_rejects_public_output_before_creating_files(self):
        with patch.object(sys, 'argv', ['archive_rebuild_status.py', 'init', '--output', str(ROOT / 'docs/status.json')]), \
             patch.object(status_module, 'git', return_value=str(ROOT).encode()):
            with self.assertRaisesRegex(ValueError, 'never docs'):
                status_module.main()


if __name__ == '__main__':
    unittest.main()
