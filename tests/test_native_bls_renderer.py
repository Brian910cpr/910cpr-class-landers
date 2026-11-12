"""Local synthetic BLS envelope and browser-reader proof; no external I/O."""
import copy
import json
import subprocess
import unittest
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlencode
from tests.test_native_skills_publication_validator import NativeSkillsValidatorTests
from scripts import native_publication_scope as scope
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload, render_html

ROOT = Path(__file__).resolve().parents[1]

class BlsRendererTests(unittest.TestCase):
    def fixture(self):
        helper = NativeSkillsValidatorTests()
        case, feed = helper.fixture()
        feed['pageKey'] = 'bls'
        for day in feed['dates']:
            for slot in day['startTimes']:
                for row in slot['courses']:
                    row.update(scope.bls_offer_identity(row, '509474'), profileVersion=1,
                               calendarProofObservedAt=row['proofObservedAt'], policyProofObservedAt=row['proofObservedAt'])
                    row['appointmentUrl'] = row['registrationUrl']
        return helper, case, feed

    def validate(self, feed, now):
        return NativeSkillsValidatorTests().validate(feed, now)

    def browser(self, feed, now):
        code = "const r=require('./docs/assets/resolved-selector-availability.js');let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>{const p=JSON.parse(s);console.log(JSON.stringify(r.datesForPublication(p.dates,p.validUntil,Date.parse(p.generatedAt),'bls-skills')))});"
        return json.loads(subprocess.run(['node','-e',code], cwd=ROOT, input=json.dumps(feed),text=True,capture_output=True,check=True).stdout)

    def test_both_exact_packages_keep_physical_identity_and_validate(self):
        _, case, feed = self.fixture()
        physical = copy.deepcopy(feed)
        self.assertTrue(self.validate(feed,case.now))
        self.assertTrue(self.browser(feed,case.now))
        for day in feed['dates']:
            for slot in day['startTimes']:
                for row in slot['courses']:
                    row.update(scope.bls_offer_identity(row,'210549'))
                    row['appointmentUrl'] = row['registrationUrl']
        self.assertTrue(self.validate(feed,case.now))
        self.assertTrue(self.browser(feed,case.now))
        self.assertEqual(feed['dates'][0]['startTimes'][0]['courses'][0]['nativeOfferId'], physical['dates'][0]['startTimes'][0]['courses'][0]['nativeOfferId'])

    def test_real_layered_candidate_uses_bls_qualification_and_shared_timing(self):
        from tests.test_native_skills_publication import NativeSkillsPublicationTests
        from scripts.block_start_time_selector import contextual_course
        from tests.test_skills_session_509474 import SkillsOnlyTests
        helper=NativeSkillsPublicationTests(); case=helper.fixture()
        source=SkillsOnlyTests(); source.setUp()
        option=dict(course_id='509474', display_label='Skills Session Only',
                    scheduling_template_course_id='209806', native_registration_path='/register/skills-session/',
                    skills_contexts=[{'key':'bls-skills','template_course_id':'209806'}])
        case.page=dict(case.page,page_key='bls',course_options=[option])
        case.courses=[contextual_course('509474',option,source.catalog,source.rules)]
        self.assertEqual(case.courses[0]['required_instructor_certifications'],source.rules['209806'].get('required_instructor_certifications',source.catalog['209806'].get('required_instructor_certifications')))
        case.native_policy.update(blsSkillsEnabled=True, skillsEnabled=False, _blsSkillsProof={
            'schemaVersion':'native-bls-skills-publication-policy.v1','nativeScopeId':scope.SCOPE,
            'observedAt':case.now.isoformat(),'validUntil':(case.now+timedelta(minutes=15)).isoformat(),
            'physicalCourseId':'509474','context':'bls-skills','profileKey':'native_skills_shared','profileVersion':1,
            'qualificationValidThrough':(case.now+timedelta(days=91)).isoformat(),'skillsEnabled':True,'bundleEnabled':True,
            'instructionMinutes':45,'cleanupMinutes':15,'capacity':2,'skillsCents':5500,'bundleCents':9500})
        result=helper.publish(case)
        self.assertTrue(result['offers'])
        for offer in result['offers']:
            self.assertEqual(offer['skillsContexts'],['bls-skills'])
            self.assertEqual(offer['schedulerConsumptionMinutes'],60)
        case.native_policy['_blsSkillsProof']['validUntil']=case.now.isoformat()
        self.assertFalse(helper.publish(case)['offers'])

    def test_mismatched_package_context_profile_and_lease_fail_closed(self):
        _, case, feed = self.fixture()
        for change in [dict(publicCourseId='210549'),dict(physicalCourseId='210549'),dict(checkoutPackage='other'),
                       dict(profileKey='other'),dict(profileVersion=True),dict(skillsContexts=['cpr-aed']),
                       dict(selectionId='legacy'),dict(policyProofObservedAt=(case.now+timedelta(seconds=1)).isoformat()),
                       dict(validUntil=(case.now+timedelta(minutes=16)).isoformat())]:
            bad=copy.deepcopy(feed)
            for day in bad['dates']:
                for slot in day['startTimes']:
                    for row in slot['courses']: row.update(change)
            with self.subTest(change=change):
                with self.assertRaises(ValueError): self.validate(bad,case.now)
                self.assertEqual(self.browser(bad,case.now),[])

if __name__ == '__main__': unittest.main()
