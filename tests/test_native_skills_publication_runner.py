"""Bounded publication tests. Synthetic local inputs; no hosted reads or writes."""
import copy
from contextlib import ExitStack
from datetime import timedelta
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts import run_native_publication as runner
from scripts import build_bls_block_schedule_pilot as generator
from scripts import block_start_time_selector as selector
from scripts import build_live_availability_snapshot as snapshot
from scripts import validate_public_refresh_output as validator
from scripts.layered_publication_adapter import publish
from tests import test_native_skills_publication as skills_fixtures
from tests import test_native_full_publication_validator as bls_fixtures
from tests import test_native_publication_wiring as wiring_fixtures

ROOT = Path(__file__).resolve().parents[1]
POLICY = dict(schemaVersion='native-publication-scope.v1', enabled=True,
              skillsEnabled=True, scopeId='brian-shipyard-b.v1')


class NativeSkillsRunnerTests(unittest.TestCase):
    def feeds(self):
        case, bls = bls_fixtures.NativeFullValidatorTests().fixture()
        feeds = {'bls': bls}
        helper = skills_fixtures.NativeSkillsPublicationTests()
        for page in runner.scope.SKILLS_CONTEXTS:
            fixture = helper.fixture(page)
            feeds[page] = generator.public_selector_availability_payload(helper.publish(fixture))
        return case, feeds

    def validate(self, feeds, now, policy=None):
        policy = policy or POLICY
        def read(path):
            if path == runner.POLICY: return policy
            if path == 'docs/data/schedule_future.json': return {'sessions': []}
            return feeds[Path(path).stem]
        def load(path): return feeds[Path(path).stem]
        with patch.object(runner, 'read', side_effect=read), patch.object(validator, 'load_json', side_effect=load), \
             patch.object(runner, 'load_publication_demand', return_value={'generated_at': now.isoformat(), 'sessions': []}), \
             patch.object(runner, 'calendar_bounds', return_value={'validUntil': now+timedelta(minutes=15), 'observedAt': now}):
            return runner.validate(now=now)

    def test_independent_default_off_exact_targets_and_boolean_gate(self):
        saved = json.loads((ROOT / runner.POLICY).read_text())
        self.assertIs(saved['skillsEnabled'], False)
        self.assertEqual(runner.publication_pages(), ('bls',))
        self.assertEqual(runner.publication_paths(), runner.PATHS)
        paths = runner.publication_paths(True)
        self.assertEqual(len(paths), 15)
        self.assertEqual(len(paths), len(set(paths)))
        self.assertEqual(set(paths)-set(runner.PATHS), {
            'docs/heartsaver.html', 'docs/HEARTSAVER.html', 'docs/heartsaver-schedule.html',
            'docs/data/block-selector-availability/heartsaver.json', 'docs/arc.html',
            'docs/data/block-selector-availability/arc.json', 'docs/hsi.html',
            'docs/hsi-schedule.html', 'docs/data/block-selector-availability/hsi.json'})
        for value in ['true', 1, None]:
            with self.assertRaises(ValueError): runner.policy_enabled(dict(POLICY, skillsEnabled=value))
            with self.assertRaises(ValueError): runner.publication_paths(value)

    def test_only_known_skills_option_contexts_and_outputs_are_allowed_before_writes(self):
        pages = selector.load_block_schedule_page_configs()
        for key in runner.publication_pages(True):
            original = copy.deepcopy(pages[key])
            config = runner.native_page_config(pages[key], key)
            runner.check_page_outputs(config, key)
            self.assertEqual(original, pages[key])
            self.assertIs(config['include_seated_classes'], True)
            if key != 'bls':
                self.assertEqual(config['allowed_course_ids'], ['509474'])
                self.assertEqual([o['course_id'] for o in config['course_options']], ['509474'])
                self.assertEqual(config['default_course_id'], '509474')
            for mutation in [{'output_path': 'docs/unapproved.html'}, {'alias_output_paths': ['docs/extra.html']},
                             {'report_json_path': 'docs/private.json'}, {'render_html': False}]:
                with self.subTest(page=key, mutation=mutation), self.assertRaises(ValueError):
                    runner.check_page_outputs(dict(config, **mutation), key)
        bad = copy.deepcopy(pages['arc']); bad['course_options'][-1]['skills_contexts'] = []
        with self.assertRaises(ValueError): runner.native_page_config(bad, 'arc')
        with self.assertRaises(ValueError): runner.native_page_config(pages['hsi'], 'bls')

    def test_every_enabled_feed_validated_and_original_expiry_bounds_manifest(self):
        case, feeds = self.feeds()
        evidence = self.validate(feeds, case.now)
        self.assertEqual(set(evidence['pageCounts']), set(runner.publication_pages(True)))
        self.assertGreater(evidence['nativeFullOffers'], 0)
        self.assertGreater(evidence['nativeSkillsOffers'], 0)
        early = (case.now+timedelta(minutes=8)).isoformat()
        feeds['hsi']['validUntil'] = early
        for day in feeds['hsi']['dates']:
            for slot in day['startTimes']:
                for offer in slot['courses']: offer['validUntil'] = early
        self.assertEqual(self.validate(feeds, case.now)['validUntil'], runner.scope.instant(early).isoformat())
        # Later global generation cannot extend original source proof.
        for page in ['heartsaver', 'arc', 'hsi']:
            _, bad = self.feeds()
            bad[page]['generatedAt'] = (case.now+timedelta(minutes=14)).isoformat()
            bad[page]['validUntil'] = (case.now+timedelta(minutes=24)).isoformat()
            with self.subTest(page=page), self.assertRaises(ValueError): self.validate(bad, case.now)
            _, bad = self.feeds()
            row = bad[page]['dates'][0]['startTimes'][0]['courses'][0]
            row['validUntil'] = (case.now+timedelta(minutes=4)).isoformat()
            with self.assertRaisesRegex(ValueError, 'insufficient_publication_budget'): self.validate(bad, case.now)
            _, bad = self.feeds()
            bad[page]['dates'][0]['startTimes'][0]['courses'][0]['courseId'] = '210549'
            with self.assertRaises(ValueError): self.validate(bad, case.now)
        # Disabled skills must not even read the three providers' existing files.
        off = self.validate({'bls': feeds['bls']}, case.now, dict(POLICY, skillsEnabled=False))
        self.assertEqual(set(off['pageCounts']), {'bls'})
        self.assertEqual(off['nativeSkillsOffers'], 0)

    def test_manifest_explicit_paths_and_gate_drift_fail_before_git(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(runner, 'ROOT', Path(directory)):
            paths = runner.publication_paths(True)
            for p in paths:
                target=Path(directory)/p; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(b'fixture')
            report = dict(schemaVersion='native-publication-run.v1', preview=False, skillsEnabled=True,
                          files={p:sha256(b'fixture').hexdigest() for p in paths})
            runner.assert_manifest(report)
            for mutation in [dict(skillsEnabled=False), dict(files={p:h for p,h in report['files'].items() if p!='docs/hsi.html'}),
                             dict(files={**report['files'], 'docs/unapproved.html': 'x'})]:
                with self.assertRaises(ValueError): runner.assert_manifest(dict(report, **mutation))
            with patch.dict('os.environ', {'GITHUB_REF':'refs/heads/main'}), \
                 patch.object(runner,'read',side_effect=[dict(POLICY,skillsEnabled=False),report]), \
                 patch.object(runner,'git') as git:
                with self.assertRaisesRegex(ValueError, 'skills_publication_gate_changed'): runner.publish()
                git.assert_not_called()

    def test_real_generator_emits_only_gate_selected_paths_and_preview_restores_gates(self):
        configs = selector.load_block_schedule_page_configs()
        helper = skills_fixtures.NativeSkillsPublicationTests()
        now = helper.fixture().now
        def payload(config):
            key = config['page_key']
            if key == 'bls':
                fixture = wiring_fixtures.NativeWiringTests().fixture()
                result = publish(fixture.calculation(), config, fixture.courses, fixture.windows, fixture.now,
                    lambda *a: self.fail('external URL lookup'), lambda *a: [],
                    native_policy=fixture.policy['native_publication_scope'])
            else:
                fixture = helper.fixture(key); fixture.page = config; result = helper.publish(fixture)
            return result
        real_validate = runner.validate
        for enabled in [False, True]:
            with self.subTest(skills=enabled), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                root = Path(directory)
                stack.enter_context(patch.object(runner, 'ROOT', root))
                stack.enter_context(patch.object(generator, 'ROOT', root))
                stack.enter_context(patch.object(generator, 'SELECTOR_AVAILABILITY_DIR', root/'docs/data/block-selector-availability'))
                stack.enter_context(patch.object(validator, 'ROOT', root))
                stack.enter_context(patch.object(validator, 'SELECTOR_DIR', root/'docs/data/block-selector-availability'))
                stack.enter_context(patch.object(generator, 'apply_final_live_availability_guard', side_effect=lambda p:p))
                stack.enter_context(patch.object(selector, 'load_block_schedule_page_configs', return_value=configs))
                stack.enter_context(patch.object(selector, 'build_block_schedule_page', side_effect=payload))
                stack.enter_context(patch.object(snapshot, 'run', return_value={'missing':False,'stats':{'blocks':1}}))
                stack.enter_context(patch.object(runner, 'git', return_value='fixture-local-head'))
                schedule={'sessions':[], 'build':{'counts':{'sessions_output':0}}}
                stack.enter_context(patch.object(runner, 'prepare', return_value=schedule))
                stack.enter_context(patch.object(runner, 'load_publication_demand', return_value={'generated_at':now.isoformat(),'sessions':[]}))
                stack.enter_context(patch.object(runner, 'calendar_bounds', return_value={'validUntil':now+timedelta(minutes=15),'observedAt':now}))
                stack.enter_context(patch.object(runner, 'validate', side_effect=lambda:real_validate(now=now)))
                runner.write(runner.POLICY, dict(POLICY, enabled=False, skillsEnabled=enabled))
                runner.write('docs/data/schedule_future.json',schedule)
                asset=root/'docs/assets/resolved-selector-availability.js';asset.parent.mkdir(parents=True)
                shutil.copyfile(ROOT/'docs/assets/resolved-selector-availability.js',asset)
                original=(root/runner.POLICY).read_bytes()
                evidence=runner.build(preview=True)
                self.assertEqual((root/runner.POLICY).read_bytes(), original)
                self.assertEqual(set(evidence['files']),set(runner.publication_paths(enabled)))
                self.assertEqual({str(p.relative_to(root)) for p in (root/'docs').rglob('*') if p.is_file()},set(evidence['files']))
                for page in runner.publication_pages(enabled):
                    html=(root/runner.PAGE_PATHS[page][0]).read_text()
                    self.assertIn('/assets/resolved-selector-availability.js?v=',html)
                    self.assertIn('data/block-selector-availability/'+page+'.json',html)
                    if page!='bls':
                        self.assertIn('Skills Session Only',html)
                        self.assertIn('selectedSkillsContext',html)
                        self.assertNotIn('"course_id": "210549"',html)
                with self.assertRaisesRegex(ValueError,'production_manifest_required'):runner.assert_manifest(evidence)

if __name__ == '__main__': unittest.main()
