import copy
import json
import subprocess
import unittest
from contextlib import ExitStack
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from scripts import block_start_time_selector as selector
from scripts import native_publication_scope as scope
from scripts.layered_publication_adapter import publish
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload, render_html
from tests import test_skills_session_509474 as skills_fixtures
from tests import test_layered_publication_adapter as layered_fixtures

ROOT = Path(__file__).resolve().parents[1]

class NativeSkillsPublicationTests(unittest.TestCase):
    def fixture(self, page='heartsaver'):
        course_case=skills_fixtures.SkillsOnlyTests();course_case.setUp()
        case=layered_fixtures.LayeredPublicationTests();case.setUp()
        course=course_case.course(page)
        case.page=course_case.pages[page]
        case.courses=[course]
        case.native_policy={'schemaVersion':'native-publication-scope.v1','enabled':True,'skillsEnabled':True,'scopeId':scope.SCOPE}
        case.policy['native_publication_scope']=case.native_policy
        for proof in case.coverage:
            proof['valid_until']=(case.now+timedelta(minutes=15)).isoformat();proof['freshness_minutes']=15
        for window in case.windows:
            window.update(native_publication_scope_id=scope.SCOPE,native_proof_observed_at=case.now.isoformat(),
                native_valid_until=(case.now+timedelta(minutes=15)).isoformat(),native_calendar_source_ids=['brian_do_not_schedule','personal'])
        case.add(11,'12:00','14:00',cid='209809',count=None)
        return case

    def publish(self, case):
        return publish(case.calculation(),case.page,case.courses,case.windows,case.now,
            lambda *args:(_ for _ in ()).throw(AssertionError('legacy URL lookup forbidden')),
            lambda *args:[],native_policy=case.native_policy)

    def test_actual_first_party_snapshot_preserves_original_proof_on_selected_windows(self):
        from scripts import build_live_availability_snapshot as snapshot
        from tests import test_native_publication_scope as fixtures
        case=fixtures.NativeScopeTests();case.setUp()
        case.source.update(default_location_key='shipyard',inverse_expansion_min_gap_minutes=90)
        full=skills_fixtures.SkillsOnlyTests();full.setUp()
        people={'people':[{'person_id':'instructor_24057895173','display_name':'Brian Ennis','certifications':[{'certification_code':'AHA_BLS_INSTRUCTOR'}]}]}
        with patch.object(snapshot,'appointment_container_date_ranges',side_effect=AssertionError('legacy bounds forbidden')):
            blocks,_,_=snapshot.build_snapshot(case.calendars,people,{'courses':list(full.catalog.values())},case.snapshot,None,native_policy=case.policy,now=case.now)
        resources=json.loads((ROOT/'data/config/location_resource_map.json').read_text())
        windows,_=selector.selected_public_page_live_windows({'availability_blocks':blocks},resources)
        self.assertTrue(windows)
        for window in windows:
            self.assertEqual(window['native_publication_scope_id'],scope.SCOPE)
            self.assertEqual(scope.instant(window['native_proof_observed_at']),case.now)
            self.assertEqual(scope.instant(window['native_valid_until']),case.now+timedelta(minutes=15))
            self.assertEqual(window['native_calendar_source_ids'],['brian_do_not_schedule','personal'])

    def test_default_off_and_explicit_skills_gate(self):
        policy=json.loads((ROOT/'data/config/native_publication_scope.json').read_text())
        self.assertFalse(scope.skills_active(policy,'heartsaver'))
        self.assertFalse(scope.skills_active(dict(policy,enabled=True),'heartsaver'))
        self.assertFalse(scope.skills_active(dict(policy,enabled=True,skillsEnabled=True),'bls'))
        case=self.fixture();calc=case.calculation();url=lambda *args:(123,'legacy','/unchanged',None)
        a=publish(calc,case.page,case.courses,case.windows,case.now,url,lambda *args:[])
        b=publish(calc,case.page,case.courses,case.windows,case.now,url,lambda *args:[],native_policy=dict(case.native_policy,skillsEnabled=False))
        self.assertEqual(a,b)

    def test_three_provider_pages_roundtrip_actual_reader_no_external_identity(self):
        identities=[]
        for page in scope.SKILLS_CONTEXTS:
            with self.subTest(page=page):
                case=self.fixture(page);before=copy.deepcopy(case.sources)
                result=self.publish(case);self.assertTrue(result['offers'])
                self.assertEqual({o['startTime'] for o in result['offers']},{'11:00','14:00'})
                for offer in result['offers']:
                    self.assertEqual(offer['authority'],scope.SKILLS_AUTHORITY)
                    self.assertEqual((offer['durationMinutes'],offer['schedulerConsumptionMinutes'],offer['cleanupBufferMinutes'],offer['capacity']),(45,60,15,2))
                    self.assertNotIn('appointmentDayId',offer);self.assertNotIn('matchedContainerId',offer)
                    self.assertNotIn('enrollware',offer['registrationUrl'])
                    self.assertEqual(offer['courseName'],'Skills Session Only')
                identities.append(result['offers'][0]['nativeOfferId'])
                self.assertEqual(case.sources,before)
                feed=public_selector_availability_payload(result)
                for context in scope.SKILLS_CONTEXTS[page]:
                    code="import {skillsOffers} from './supabase/functions/skills-session-reservation/policy.mjs';let s='';for await(const x of process.stdin)s+=x;const p=JSON.parse(s);const ctx=process.argv[1];console.log(JSON.stringify({off:skillsOffers(p,ctx,Date.parse(p.generatedAt)),on:skillsOffers(p,ctx,Date.parse(p.generatedAt),'509474',{nativePublicationEnabled:true})}));"
                    read=subprocess.run(['node','--input-type=module','-e',code,context],input=json.dumps(feed),text=True,capture_output=True,check=True,cwd=ROOT)
                    parsed=json.loads(read.stdout);self.assertEqual(parsed['off'],[]);self.assertEqual(len(parsed['on']),len(result['offers']))
                    self.assertTrue(all(o['context']==context and o['capacity']==2 and o['proofObservedAt']==result['offers'][0]['proofObservedAt'] for o in parsed['on']))
                html=render_html(result)
                self.assertIn('Skills Session Only',html);self.assertIn('selectedSkillsContext',html)
        self.assertEqual(len(set(identities)),1,'physical identity is the same across contexts/pages')

    def test_wrong_timing_context_identity_scope_or_coverage_never_publishes(self):
        patches=[('window',{'native_publication_scope_id':'other'}),('window',{'native_calendar_source_ids':[]}),
            ('window',{'native_proof_observed_at':'2000-01-01T00:00:00Z'}),('window',{'native_valid_until':'2000-01-01T00:00:00Z'}),
            ('window',{'person_id':'other'}),('course',{'default_capacity':4}),('course',{'duration_minutes':120}),
            ('course',{'schedule_page_option':{'skills_contexts':[]}})]
        for target,changes in patches:
            with self.subTest(changes=changes):
                case=self.fixture();(case.windows[0] if target=='window' else case.courses[0]).update(changes)
                self.assertFalse(self.publish(case)['offers'])
        case=self.fixture();case.coverage[0]['valid_until']=case.now.isoformat()
        self.assertFalse(self.publish(case)['offers'])

    def test_unknown_bounds_and_cleanup_block_offers_and_closure_is_retained(self):
        case=self.fixture();case.add(11,'14:45','15:00',cid='210549')
        self.assertNotIn('14:00',{o['startTime'] for o in self.publish(case)['offers']})
        case=self.fixture();case.add(11,'15:00','15:00',cid='unknown')
        self.assertFalse(self.publish(case)['offers'])
        case=self.fixture()
        closure=[{'startsAt':case.at(11,'11:45').isoformat(),'endsAt':case.at(11,'12:00').isoformat()}]
        with patch('scripts.public_registration_closures.load_closures',return_value=closure):result=self.publish(case)
        self.assertNotIn('11:00',{o['startTime'] for o in result['offers']})
        self.assertEqual(result['registrationClosures'],closure)
        self.assertEqual(len(result['layeredDiagnostics']['projected_sources']),1)

    def test_mixed_page_other_dynamic_courses_fail_closed_not_external_fallback(self):
        case=self.fixture();case.courses.append(dict(course_id='210549',course_family='BLS',kind='skills',blended_classroom_skills='blended'))
        result=self.publish(case)
        self.assertTrue(result['offers']);self.assertEqual({o['courseId'] for o in result['offers']},{'509474'})
        self.assertTrue(any('unsupported_native_skills_course' in o.get('reasons',[]) for o in result['rejectedCourseStartTimes']))

    def test_actual_selector_skills_admission_never_reads_containers(self):
        for page in scope.SKILLS_CONTEXTS:
            case=self.fixture(page)
            full=skills_fixtures.SkillsOnlyTests();full.setUp()
            catalog={cid:selector.contextual_course(cid,{},full.catalog,full.rules) for cid in full.catalog if cid in full.rules}
            catalog['509474']=dict(case.courses[0],appointment_eligible=True,appointment_allowed=True)
            page_config=dict(case.page,allowed_course_ids=['509474'],include_seated_classes=False)
            inputs={selector.LOCATION_RESOURCE_MAP_PATH:case.resources,selector.COURSE_CATALOG_PATH:{},selector.PEOPLE_CATALOG_PATH:{},selector.SESSIONS_CURRENT_PATH:{'sessions':[]},selector.SCHEDULE_FUTURE_PATH:{'sessions':[]},selector.COURSE_RULES_PATH:{},selector.PUBLIC_LOCATION_POLICY_PATH:{},selector.PUBLIC_OFFER_POLICY_PATH:{'minimum_lead_hours':24,'maximum_days_out':90},selector.ROOT/'data/config/layered_scheduling_policy.json':case.policy}
            patches={'require_current_live_availability_snapshot':lambda:{'layered_commitment_coverage':case.coverage},'load_block_schedule_page_configs':lambda:{page:page_config},'read_required_json':lambda path:copy.deepcopy(inputs[path]),'load_publication_demand':lambda root:{'sessions':[]},'sessions_with_canonical_demand':lambda rows:(rows,{}),'course_rules_by_id':lambda value:catalog,'courses_by_id':lambda value:catalog,'people_lookup':lambda value:{case.policy['brian_person_id']:{'person_id':case.policy['brian_person_id']}},'selected_public_page_live_windows':lambda *args:(case.windows,{}),'build_occupancy':lambda *args,**kwargs:case.sources,'window_datetimes':lambda w:(case.at(11,'00:00').replace(tzinfo=None),case.at(12,'00:00').replace(tzinfo=None)),'selector_reference_datetime':lambda:case.now.replace(tzinfo=None),'public_location_allowed':lambda *args:True,'public_policy_reasons':lambda *args,**kwargs:[],'native_reservation_reasons':lambda *args:[],'find_url':lambda *args:(_ for _ in ()).throw(AssertionError('legacy URL forbidden'))}
            with ExitStack() as stack:
                for name,value in patches.items():stack.enter_context(patch.object(selector,name,value))
                stack.enter_context(patch.object(scope,'load_policy',return_value=case.native_policy))
                result=selector.build_block_schedule_page(page_config)
            self.assertTrue(result['offers']);self.assertTrue(all(o['authority']==scope.SKILLS_AUTHORITY for o in result['offers']))

if __name__=='__main__':unittest.main()
