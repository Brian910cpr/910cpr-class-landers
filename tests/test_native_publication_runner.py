import copy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import run_native_publication as runner
from tests.test_native_full_publication_validator import NativeFullValidatorTests

NOW = datetime(2030, 1, 1, tzinfo=timezone.utc)
POLICY = dict(schemaVersion='native-publication-scope.v1', enabled=False, scopeId='brian-shipyard-b.v1')


class NativePublicationRunnerTests(unittest.TestCase):
    def test_strict_default_off_gate_and_invalid_policy_fail_closed(self):
        self.assertFalse(runner.policy_enabled(POLICY))
        self.assertTrue(runner.policy_enabled(dict(POLICY, enabled=True)))
        for value in [{}, dict(POLICY, enabled='false'), dict(POLICY, scopeId='other')]:
            with self.assertRaises(ValueError):
                runner.policy_enabled(value)

    def test_preserves_retained_occurrences_and_unknown_is_not_zero(self):
        rows = [{'session_id': '123', 'course_id': '359474', 'start_at': '2030-01-02T12:00:00Z',
                 'end_at': '2030-01-02T14:30:00Z', 'active_registration_count': 7,
                 'count_available': True, 'registration_url': 'https://retired.invalid/enroll?id=123', 'client': 'PRIVATE CUSTOMER', 'email': 'private@example.test'},
                {'session_id': '124', 'start_at': '2030-01-03T01:00:00Z', 'end_at': '2030-01-03T03:00:00Z'}]
        original = copy.deepcopy(rows)
        result = runner.retained_projection({'sessions': rows}, {'generated_at': NOW.isoformat(), 'sessions': []})
        self.assertEqual([r['session_id'] for r in result['sessions']], ['123', '124'])
        self.assertEqual(rows, original)
        for row in result['sessions']:
            self.assertFalse(row['count_available'])
            self.assertIsNone(row['active_registration_count'])
        self.assertEqual(result['sessions'][0]['start_at'], rows[0]['start_at'])
        self.assertNotIn('retired.invalid', json.dumps(result))
        self.assertNotIn('PRIVATE CUSTOMER', json.dumps(result))
        self.assertNotIn('private@example.test', json.dumps(result))
        self.assertTrue(all(row['public_direct_booking'] is False for row in result['sessions']))
        from scripts.block_start_time_selector import seated_class_selector_offers
        from scripts.generate_dynamic_offers import normalize_occupancy
        self.assertEqual(seated_class_selector_offers(schedule_future_payload=result, selected_courses=[{'course_id': '359474'}], selected_course_ids={'359474'}, course_rules={}), [])
        blockers = normalize_occupancy(result, 'retained')
        self.assertEqual(len(blockers), 2)
        self.assertEqual(blockers[0]['start'].isoformat(), '2030-01-02T07:00:00')

    def test_native_new_occurrence_and_canonical_reserves_preserved(self):
        sid = 'lw-12345678-1234-1234-1234-123456789012'
        row = dict(external_class_id=sid, canonical_session_id='canonical', external_course_id='359474',
                   source='landerware_event', registration_backend='landerware', session_status='scheduled',
                   visibility='public', registration_status='open', workspace_projection_status='current',
                   count_available=True, active_registration_count=6,
                   start_at='2030-01-02T12:00:00Z', end_at='2030-01-02T14:30:00Z')
        result = runner.retained_projection({'sessions': []}, {'generated_at': NOW.isoformat(), 'sessions': [row]})
        self.assertEqual(result['sessions'][0]['session_id'], sid)
        self.assertEqual(result['sessions'][0]['active_registration_count'], 6)
        self.assertEqual(result['sessions'][0]['registration_backend'], 'landerware')
        self.assertFalse(result['sessions'][0]['public_direct_booking'])
        self.assertNotIn('registration_url', result['sessions'][0])

    def test_duplicate_or_missing_retained_identity_rejected(self):
        for rows in [[{}], [{'session_id': '1'}, {'session_id': '1'}]]:
            with self.assertRaises(ValueError):
                runner.retained_projection({'sessions': rows}, {'generated_at': NOW.isoformat(), 'sessions': []})

    def test_private_nested_field_rejected(self):
        with self.assertRaises(ValueError):
            runner.privacy_check({'rows': [{'student_name': 'Private fixture'}]})

    def test_original_fifteen_minute_lease_has_five_minute_deployment_margin(self):
        expiry = NOW + timedelta(minutes=15)
        runner.check_budget(expiry, NOW + timedelta(minutes=10))
        for current in [NOW + timedelta(minutes=10, seconds=1), expiry, expiry + timedelta(seconds=1)]:
            with self.assertRaisesRegex(ValueError, 'insufficient_publication_budget'):
                runner.check_budget(expiry, current)
        self.assertEqual(expiry, NOW + timedelta(minutes=15))

    def test_real_native_selector_validation_and_private_payload_guard(self):
        case, feed = NativeFullValidatorTests().fixture()
        bounds = dict(validUntil=case.now+timedelta(minutes=15), observedAt=case.now)
        demand = {'generated_at': case.now.isoformat(), 'sessions': []}
        def read(path):
            return {'sessions': []} if path == 'docs/data/schedule_future.json' else feed
        from scripts import validate_public_refresh_output as validator
        with patch.object(runner, 'calendar_bounds', return_value=bounds), patch.object(runner, 'load_publication_demand', return_value=demand), patch.object(runner, 'read', side_effect=read), patch.object(validator, 'load_json', return_value=feed):
            result = runner.validate(now=case.now)
            self.assertGreater(result['nativeFullOffers'], 0)
            with self.assertRaises(ValueError):
                runner.validate(now=case.now+timedelta(minutes=11))
            feed['private'] = {'email': 'private@example.test'}
            with self.assertRaisesRegex(ValueError, 'private_field'):
                runner.validate(now=case.now)

    def test_actual_page_configuration_admits_only_native_full_courses(self):
        from scripts.block_start_time_selector import load_block_schedule_page_configs
        original = load_block_schedule_page_configs()['bls']
        config = runner.native_page_config(original)
        self.assertFalse(config['include_seated_classes'])
        self.assertEqual(set(config['allowed_course_ids']), {'209806', '359474'})
        self.assertEqual({str(c['course_id']) for c in config['course_options']}, {'209806', '359474'})
        self.assertTrue(original['include_seated_classes'])
        self.assertNotIn('HeartCode', config['intro'])

    def test_unadmitted_seated_skills_and_bundle_ctas_rejected(self):
        case, original = NativeFullValidatorTests().fixture()
        for course_id, offer_type in [('209806', 'seated_class'), ('509474', 'dynamic_appointment'), ('210549', 'dynamic_appointment')]:
            feed = copy.deepcopy(original)
            row = feed['dates'][0]['startTimes'][0]['courses'][0]
            row.update(courseId=course_id, offerType=offer_type)
            row.pop('authority', None)
            with patch.object(runner, 'calendar_bounds', return_value=dict(validUntil=case.now+timedelta(minutes=15), observedAt=case.now)), patch.object(runner, 'load_publication_demand', return_value={'generated_at': case.now.isoformat()}), patch.object(runner, 'read', side_effect=[{'sessions': []}, feed]), patch.object(runner, 'validate_selector', return_value={}):
                with self.assertRaisesRegex(ValueError, 'unadmitted_public_offer'):
                    runner.validate(now=case.now)

    def test_manifest_is_exact_allowlist_and_rejects_preview_or_mutation(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'ROOT', Path(directory)):
            for path in runner.PATHS:
                target = Path(directory) / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b'fixture')
            report = dict(schemaVersion='native-publication-run.v1', preview=False,
                          files={p: sha256(b'fixture').hexdigest() for p in runner.PATHS})
            runner.assert_manifest(report)
            with self.assertRaises(ValueError): runner.assert_manifest(dict(report, preview=True))
            with self.assertRaises(ValueError): runner.assert_manifest(dict(report, files={**report['files'], 'docs/private.json': 'x'}))
            (Path(directory) / runner.PATHS[0]).write_bytes(b'changed')
            with self.assertRaises(ValueError): runner.assert_manifest(report)

    def test_source_head_changed_stops_before_fetch_or_push(self):
        with patch.dict(os.environ, {'GITHUB_REF': 'refs/heads/main'}), patch.object(runner, 'read', side_effect=[dict(POLICY, enabled=True), {'sourceHead': 'original'}]), patch.object(runner, 'assert_manifest'), patch.object(runner, 'git', return_value='changed') as git:
            with self.assertRaisesRegex(ValueError, 'source_head_changed'): runner.publish()
            self.assertEqual(git.call_args_list[0].args, ('rev-parse', 'HEAD'))
            self.assertEqual(git.call_count, 1)

    def test_remote_head_advanced_stops_before_stage_or_push(self):
        with patch.dict(os.environ, {'GITHUB_REF': 'refs/heads/main'}), patch.object(runner, 'read', side_effect=[dict(POLICY, enabled=True), {'sourceHead': 'original'}]), patch.object(runner, 'assert_manifest'), patch.object(runner, 'git', side_effect=['original', '', '', '', 'changed']) as git:
            with self.assertRaisesRegex(ValueError, 'remote_main_advanced'): runner.publish()
            self.assertFalse(any(c.args[0] in {'add', 'commit', 'push'} for c in git.call_args_list))

    def test_preview_restores_disabled_config_even_on_failure(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'ROOT', Path(directory)):
            runner.write(runner.POLICY, POLICY)
            before = (Path(directory) / runner.POLICY).read_bytes()
            with patch.object(runner, 'git', return_value='head'), patch.object(runner, 'prepare', side_effect=RuntimeError('fixture')):
                with self.assertRaises(RuntimeError): runner.build(preview=True)
            self.assertEqual((Path(directory) / runner.POLICY).read_bytes(), before)

    def test_workflow_has_no_retired_fetch_or_broad_public_staging(self):
        root = Path(__file__).resolve().parents[1]
        native = (root / '.github/workflows/publish-native-availability.yml').read_text()
        preview = (root / '.github/workflows/verify-skills-native-claim.yml').read_text().split('  selector-preview:', 1)[1]
        for text in [native, preview, (root / 'scripts/run_native_publication.py').read_text()]:
            self.assertNotIn('scripts.build_sessions_current', text)
            self.assertNotIn('scripts.build_schedule_future', text)
            self.assertNotIn('scripts.run_validated_public_build', text)
            self.assertNotIn('scripts.fetch_hot_sync_snapshot', text)
        self.assertIn('python -m scripts.run_native_publication build --preview', preview)
        self.assertIn('default: false', native)
        self.assertIn('group: schedule-publish-main', native)
        self.assertIn('cancel-in-progress: false', native)
        self.assertNotIn('\n  schedule:', native)
        self.assertIn('pages/builds', native)
        self.assertIn('run_native_publication observe', native)

    def test_both_retired_publishers_and_admin_probe_skip_before_fetch(self):
        root = Path(__file__).resolve().parents[1]
        for name, expected_jobs in [('refresh-public-site.yml', 1), ('refresh-admin-availability.yml', 2)]:
            text = (root / '.github/workflows' / name).read_text()
            self.assertIn('Stop retired publisher before any source fetch', text)
            self.assertEqual(text.count('needs: source-mode'), expected_jobs)
            self.assertEqual(text.count("needs.source-mode.outputs.legacy == 'true'"), expected_jobs)


if __name__ == '__main__':
    unittest.main()
