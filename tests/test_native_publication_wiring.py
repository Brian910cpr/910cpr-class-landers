import copy
import unittest
from contextlib import ExitStack
from datetime import timedelta
from unittest.mock import patch
from scripts import build_live_availability_snapshot as snapshot
from scripts import block_start_time_selector as selector
from scripts import native_publication_scope as scope
from scripts.layered_publication_adapter import publish
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload, render_html
import json
import subprocess
from pathlib import Path
from tests import test_native_publication_scope as scope_fixtures
from tests import test_layered_publication_adapter as layered_fixtures

class NativeWiringTests(unittest.TestCase):
    def test_actual_inverse_snapshot_without_containers_and_with_private_block(self):
        case=scope_fixtures.NativeScopeTests();case.setUp()
        case.source.update(default_location_key='shipyard',inverse_expansion_min_gap_minutes=90)
        case.snapshot['events_by_source']['brian_do_not_schedule']=[{'id':'private','summary':'Busy','start':'2030-01-03T01:00:00-05:00','end':'2030-01-03T04:00:00-05:00'}]
        people={'people':[{'person_id':'brian','display_name':'Brian Ennis','certifications':[{'certification_code':'AHA_BLS_INSTRUCTOR'}]}]}
        courses={'courses':[{'course_id':'209806','family':'BLS','required_instructor_certifications':['AHA_BLS_INSTRUCTOR']}]}
        with patch.object(snapshot,'appointment_container_date_ranges',side_effect=AssertionError('legacy container path forbidden')):
            blocks,blocked,_=snapshot.build_snapshot(case.calendars,people,courses,case.snapshot,None,native_policy=case.policy,now=case.now)
        available=[b for b in blocks if b.get('availability_status')=='available']
        self.assertTrue(available)
        self.assertTrue(any(b.get('availability_status')=='blocked' for b in blocks))
        for b in available:
            start,end=selector.parse_dt(b['start_datetime']),selector.parse_dt(b['end_datetime'])
            self.assertFalse(start<selector.parse_dt('2030-01-03T04:00') and end>selector.parse_dt('2030-01-03T01:00'))
        case.snapshot['source_evidence']['personal']['warnings']=['partial']
        blocks,blocked,_=snapshot.build_snapshot(case.calendars,people,courses,case.snapshot,None,native_policy=case.policy,now=case.now)
        self.assertFalse(any(b.get('availability_status')=='available' for b in blocks))
        self.assertTrue(any(b['reason_code']=='native_calendar_coverage_required' for b in blocked))
    def fixture(self):
        case=layered_fixtures.LayeredPublicationTests();case.setUp()
        case.policy['native_publication_scope']={'schemaVersion':'native-publication-scope.v1','enabled':True,'scopeId':scope.SCOPE}
        case.courses=[c for c in case.courses if c['course_id']=='359474']
        case.page={'page_key':'bls','allowed_course_ids':['359474'],'include_seated_classes':False,'course_options':[{'course_id':'359474'}]}
        for proof in case.coverage:proof['valid_until']=(case.now+timedelta(minutes=15)).isoformat();proof['freshness_minutes']=15
        case.add(11,'12:00','14:00',cid='209809',count=None,organization_id='private-fixture')
        return case
    def test_actual_layered_publisher_has_no_legacy_id_or_lookup_and_preserves_unknown_occupancy(self):
        case=self.fixture();before=copy.deepcopy(case.sources)
        calc=case.calculation()
        def forbidden(*args):raise AssertionError('legacy URL path forbidden')
        policy={'schemaVersion':'native-publication-scope.v1','enabled':True,'scopeId':scope.SCOPE}
        result=publish(calc,case.page,case.courses,case.windows,case.now,forbidden,lambda *args:[],native_policy=policy)
        self.assertTrue(result['offers'])
        for offer in result['offers']:
            self.assertNotIn('appointmentDayId',offer);self.assertNotIn('matchedContainerId',offer)
            self.assertEqual(offer['authority'],'native-full-course.v2')
            self.assertIn('selectionId=native-full',offer['registrationUrl'])
            self.assertEqual(offer['appointmentUrl'],offer['registrationUrl'])
            start=case.at(11,offer['startTime'])
            end=scope.instant(offer['occupiedUntil'])
            self.assertFalse(start<case.at(11,'14:00') and end>case.at(11,'12:00'))
        self.assertEqual(case.sources,before)
        self.assertIsNone(calc['projected_sources'][0]['active_registration_count'])
        # Unknown occupied interval remains represented; no invented zero.
        self.assertTrue(calc['reports'][0]['blocks'])
        feed=public_selector_availability_payload(result)
        rows=[c for d in feed['dates'] for t in d['startTimes'] for c in t['courses']]
        self.assertTrue(rows)
        self.assertTrue(all(c['authority']=='native-full-course.v2' and c['publicSelectable'] is True and 'appointmentDayId' not in c for c in rows))
        # Execute the actual edge reader on the emitted JSON, without networking.
        code="import {fullCourseOffers} from './supabase/functions/public-registration/full-course.mjs';let s='';for await(const x of process.stdin)s+=x;const p=JSON.parse(s);console.log(JSON.stringify(fullCourseOffers(p,'359474',Date.parse(p.generatedAt),{nativePublicationEnabled:true})));"
        read=subprocess.run(['node','--input-type=module','-e',code],input=json.dumps(feed),text=True,capture_output=True,check=True,cwd=Path(__file__).resolve().parents[1])
        self.assertEqual(len(json.loads(read.stdout)),len(rows))
        html=render_html(result)
        self.assertIn('selector-resolved-availability.v1',html)

    def test_disabled_publisher_output_is_identical(self):
        case=self.fixture();calc=case.calculation()
        url=lambda *args:(123,'old','/unchanged',None)
        a=publish(calc,case.page,case.courses,case.windows,case.now,url,lambda *args:[])
        b=publish(calc,case.page,case.courses,case.windows,case.now,url,lambda *args:[],native_policy={'enabled':False})
        self.assertEqual(a,b)
    def test_actual_selector_bls_admission_never_reads_containers_or_matches_legacy_url(self):
        case=self.fixture()
        catalog={c['course_id']:dict(c,appointment_eligible=True,appointment_allowed=True,duration_minutes=120,scheduler_consumption_minutes=150,setup_buffer_minutes=0,cleanup_buffer_minutes=30) for c in case.courses}
        inputs={selector.LOCATION_RESOURCE_MAP_PATH:case.resources,selector.COURSE_CATALOG_PATH:{},selector.PEOPLE_CATALOG_PATH:{},selector.SESSIONS_CURRENT_PATH:{'sessions':[]},selector.SCHEDULE_FUTURE_PATH:{'sessions':[]},selector.COURSE_RULES_PATH:{},selector.PUBLIC_LOCATION_POLICY_PATH:{},selector.PUBLIC_OFFER_POLICY_PATH:{'minimum_lead_hours':24,'maximum_days_out':90},selector.ROOT/'data/config/layered_scheduling_policy.json':case.policy}
        policy={'schemaVersion':'native-publication-scope.v1','enabled':True,'scopeId':scope.SCOPE}
        patches={'require_current_live_availability_snapshot':lambda:{'layered_commitment_coverage':case.coverage},'load_block_schedule_page_configs':lambda:{'bls':case.page},'read_required_json':lambda path:copy.deepcopy(inputs[path]),'load_publication_demand':lambda root:{'sessions':[]},'sessions_with_canonical_demand':lambda rows:(rows,{}),'course_rules_by_id':lambda value:catalog,'courses_by_id':lambda value:catalog,'people_lookup':lambda value:{case.policy['brian_person_id']:{}},'has_required_cert':lambda *args:True,'selected_public_page_live_windows':lambda *args:(case.windows,{}),'build_occupancy':lambda *args,**kwargs:case.sources,'window_datetimes':lambda w:(case.at(11,'00:00').replace(tzinfo=None),case.at(12,'00:00').replace(tzinfo=None)),'selector_reference_datetime':lambda:case.now.replace(tzinfo=None),'public_location_allowed':lambda *args:True,'public_policy_reasons':lambda *args,**kwargs:[],'find_url':lambda *args:(_ for _ in ()).throw(AssertionError('legacy URL path forbidden'))}
        # Real selector admission, layered calculation, native publication. Only source
        # readers/qualification evidence are bounded deterministic fixture injections.
        with ExitStack() as stack:
            for name,value in patches.items():stack.enter_context(patch.object(selector,name,value))
            stack.enter_context(patch.object(scope,'load_policy',return_value=policy))
            result=selector.build_block_schedule_page(case.page)
        self.assertTrue(result['offers'])
        self.assertTrue(all(o.get('authority')=='native-full-course.v2' for o in result['offers']))

if __name__=='__main__':unittest.main()
