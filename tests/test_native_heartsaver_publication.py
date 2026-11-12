"""Synthetic local proof of the actual layered publisher and canonical readers."""
import copy
from contextlib import ExitStack
from datetime import timedelta
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from scripts import native_publication_scope as scope
from scripts import run_native_publication as runner
from scripts import build_bls_block_schedule_pilot as generator
from scripts import block_start_time_selector as selector
from scripts import build_live_availability_snapshot as snapshot
from scripts import validate_public_refresh_output as validator
from scripts import fetch_canonical_scheduling_demand as fetcher
from scripts.layered_publication_adapter import publish
from tests import test_layered_publication_adapter as layered_fixtures
from tests import test_native_skills_publication as skills_fixtures
from tests import test_native_full_publication_validator as bls_fixtures
ROOT=Path(__file__).resolve().parents[1]


def fixture(skills=False):
    case=layered_fixtures.LayeredPublicationTests();case.setUp()
    case.courses=[dict(course_id=cid,course_family='Heartsaver',kind='full',blended_classroom_skills='classroom',clean_course_name='Synthetic '+cid) for cid in scope.HEARTSAVER]
    case.page=runner.native_page_config(selector.load_block_schedule_page_configs()['heartsaver'],'heartsaver',skills_enabled=skills,heartsaver_enabled=True)
    proof={'schemaVersion':scope.HEARTSAVER_PROOF,'observedAt':case.now.isoformat(),'validUntil':(case.now+timedelta(minutes=15)).isoformat(),
           'courses':{cid:{**values,'coursePolicyKey':'heartsaver-full:'+cid+'.v1','nativeScopeId':scope.SCOPE,'pageKey':'heartsaver',
               'materializationEnabled':True,'nativePublicationEnabled':True,'maxStudents':3,
               'qualificationValidThrough':(case.now+timedelta(days=365)).isoformat()} for cid,values in scope.HEARTSAVER.items()}}
    case.native_policy={'schemaVersion':'native-publication-scope.v1','enabled':True,'skillsEnabled':skills,'heartsaverFullEnabled':True,'scopeId':scope.SCOPE,'_heartsaverProof':proof}
    case.policy['native_publication_scope']=case.native_policy
    if skills:case.courses+=skills_fixtures.NativeSkillsPublicationTests().fixture().courses
    for row in case.coverage:row.update(valid_until=(case.now+timedelta(minutes=15)).isoformat(),freshness_minutes=15)
    for window in case.windows:window.update(native_publication_scope_id=scope.SCOPE,native_proof_observed_at=case.now.isoformat(),
        native_valid_until=(case.now+timedelta(minutes=15)).isoformat(),native_calendar_source_ids=['brian_do_not_schedule','personal'])
    return case


def emit(case,seated=()):
    return publish(case.calculation(),case.page,case.courses,case.windows,case.now,
        lambda *a:(_ for _ in ()).throw(AssertionError('external fallback forbidden')),lambda *a:[],seated,native_policy=case.native_policy)


def offers(feed):return [o for d in feed['dates'] for s in d['startTimes'] for o in s['courses']]


def seat_fixture():
    case=fixture();first=emit(case);choice=next(o for o in first['offers'] if o['courseId']=='344085')
    start=scope.instant(choice['date']+'T'+choice['startTime']+':00-04:00');sid='lw-11111111-1111-4111-8111-111111111111'
    booking=dict(schemaVersion='native-heartsaver-session-booking.v1',publicCourseId='344085',canonicalCourseId=scope.HEARTSAVER['344085']['canonicalCourseId'],
        coursePolicyKey='heartsaver-full:344085.v1',profileKey='native_heartsaver_344085_draft',profileVersion=1,sourceSessionId=sid,identityWitness='a'*32,
        capacity=3,remaining=2,instructionMinutes=90,cleanupMinutes=15)
    source=dict(canonical_session_id='canonical-fixture',external_class_id=sid,external_course_id='344085',source='landerware_event',registration_backend='landerware',
        registration_authority='landerware-generated-session.v1',session_status='scheduled',registration_status='open',visibility='public',workspace_projection_status='current',
        count_available=True,active_registration_count=1,canonical_registered_count=0,held_seat_count=1,unreconciled_reserved_count=0,
        start_at=start.isoformat(),end_at=(start+timedelta(minutes=90)).isoformat(),consumption_start_at=start.isoformat(),consumption_end_at=(start+timedelta(minutes=105)).isoformat(),
        location_name=':: Wilmington; Shipyard Blvd',lead_instructor_name='Brian Ennis',course_name='Heartsaver CPR AED',native_heartsaver_booking_admission=booking)
    demand={'generated_at':case.now.isoformat(),'sessions':[source],'native_heartsaver_policy_proof':case.native_policy['_heartsaverProof']}
    return case,choice,source,demand


class HeartsaverPublicationTests(unittest.TestCase):
    def test_default_off_exact_target_counts_and_strict_gate(self):
        policy=json.loads((ROOT/runner.POLICY).read_text());self.assertIs(policy['heartsaverFullEnabled'],False)
        self.assertFalse(scope.heartsaver_active(policy));self.assertFalse(scope.heartsaver_active(dict(policy,enabled=True)))
        for skills,hs,count in [(False,False,6),(False,True,10),(True,False,15),(True,True,15)]:
            paths=runner.publication_paths(skills,hs);self.assertEqual(len(paths),count);self.assertEqual(len(set(paths)),count)
        for value in [None,1,'true']:
            with self.assertRaises(ValueError):runner.policy_enabled(dict(policy,heartsaverFullEnabled=value))
            with self.assertRaises(ValueError):runner.publication_paths(False,value)
        self.assertNotIn('native_heartsaver',fetcher.request_url(fetcher.DEFAULT_URL))
        self.assertIn('native_heartsaver=1',fetcher.request_url(fetcher.DEFAULT_URL,heartsaver_enabled=True))

    def test_actual_layered_two_full_courses_roundtrip_reader_and_precise_geometry(self):
        case=fixture();payload=emit(case);feed=generator.public_selector_availability_payload(payload)
        self.assertEqual({o['courseId'] for o in offers(feed)},set(scope.HEARTSAVER))
        with patch.object(validator,'load_json',return_value=feed):validator.validate_selector('heartsaver',set(),now=case.now)
        for cid,expected in scope.HEARTSAVER.items():
            rows=[o for o in offers(feed) if o['courseId']==cid];self.assertTrue(rows)
            self.assertTrue(all(o['durationMinutes']==expected['instructionMinutes'] and o['cleanupBufferMinutes']==expected['cleanupMinutes'] for o in rows))
            self.assertTrue(all('capacity' not in o for o in rows),'dynamic alternatives must not invent extra seat inventory')
            script="import {fullCourseOffers} from './supabase/functions/public-registration/full-course.mjs';let s='';for await(const x of process.stdin)s+=x;const p=JSON.parse(s);console.log(JSON.stringify(fullCourseOffers(p.feed,p.cid,p.now,{nativePublicationEnabled:true,coursePolicy:p.policy})));"
            result=subprocess.run(['node','--input-type=module','-e',script],input=json.dumps(dict(feed=feed,cid=cid,now=case.now.timestamp()*1000,policy=case.native_policy['_heartsaverProof']['courses'][cid])),text=True,capture_output=True,check=True,cwd=ROOT)
            self.assertEqual(len(json.loads(result.stdout)),len(rows))

    def test_missing_disabled_wrong_policy_cap_or_expiring_qualification_cannot_publish(self):
        for changes in [dict(nativePublicationEnabled=False),dict(materializationEnabled=False),dict(maxStudents=None),dict(maxStudents=True),dict(canonicalCourseId='other'),dict(coursePolicyKey='bls'),dict(instructionMinutes=45),dict(qualificationValidThrough='2000-01-01T00:00:00Z')]:
            case=fixture();case.native_policy['_heartsaverProof']['courses']['344085'].update(changes)
            self.assertNotIn('344085',{o['courseId'] for o in emit(case)['offers']},str(changes))
        case=fixture();case.native_policy.pop('_heartsaverProof');self.assertEqual(emit(case)['offers'],[])
        case=fixture();case.native_policy['_heartsaverProof']['courses']['344085']['qualificationValidThrough']=(case.now+timedelta(days=1)).isoformat()
        self.assertNotIn('344085',{o['courseId'] for o in emit(case)['offers']})

    def test_original_policy_time_never_renewed_and_validator_rejects_tampering(self):
        case=fixture();proof=case.native_policy['_heartsaverProof'];proof['observedAt']=(case.now-timedelta(minutes=2)).isoformat();proof['validUntil']=(case.now+timedelta(minutes=13)).isoformat()
        feed=generator.public_selector_availability_payload(emit(case));self.assertTrue(offers(feed))
        self.assertEqual(scope.instant(offers(feed)[0]['proofObservedAt']),case.now-timedelta(minutes=2))
        for change in [dict(coursePolicyKey='bls'),dict(policyProofObservedAt=case.now.isoformat()),dict(durationMinutes=45),dict(capacity=4,authority='native-skills-publication.v1'),dict(registrationUrl='https://retired.invalid')]:
            bad=copy.deepcopy(feed);offers(bad)[0].update(change)
            with patch.object(validator,'load_json',return_value=bad),self.assertRaises(ValueError):validator.validate_selector('heartsaver',set(),now=case.now)
        case.native_policy['_heartsaverProof']['observedAt']=(case.now-timedelta(minutes=16)).isoformat();self.assertEqual(emit(case)['offers'],[])

    def test_mixed_skills_full_routing_and_unknown_course_never_external(self):
        case=fixture(True);result=emit(case);self.assertEqual({o['courseId'] for o in result['offers']},set(scope.HEARTSAVER)|{'509474'})
        self.assertTrue(all(o['authority']==scope.SKILLS_AUTHORITY for o in result['offers'] if o['courseId']=='509474'))
        case.courses.append(dict(course_id='351632',course_family='Heartsaver',kind='full',blended_classroom_skills='classroom'))
        self.assertNotIn('351632',{o['courseId'] for o in emit(case)['offers']})

    def test_one_seat_snapshot_reuses_canonical_class_and_does_not_duplicate_capacity(self):
        case,choice,source,demand=seat_fixture();schedule=runner.retained_projection({'sessions':[]},demand,heartsaver_enabled=True,now=case.now)
        self.assertTrue(schedule['sessions'][0]['public_direct_booking'])
        case.sources.append(dict(source_event_id=source['canonical_session_id'],external_class_id=source['external_class_id'],start=source['start_at'],end=source['consumption_end_at'],
            instructor='Brian Ennis',course_id='344085',resource=case.room,location_resolution='location_resource_map',source_file='canonical_class_sessions',active_registration_count=1,count_available=True))
        seated=selector.seated_class_selector_offers(schedule_future_payload=schedule,selected_courses=case.courses,selected_course_ids=set(scope.HEARTSAVER),course_rules={'344085':{'scheduler_consumption_minutes':150}})
        self.assertEqual(len(seated),1)
        result=runner.annotate_seated_offers(emit(case,seated),schedule);feed=generator.public_selector_availability_payload(result);rows=offers(feed)
        same=[o for o in rows if o['courseId']=='344085'];self.assertEqual(len(same),1)
        self.assertEqual(same[0]['capacity'],3);self.assertEqual(same[0]['remainingSeats'],2);self.assertEqual(same[0]['schedulerConsumptionMinutes'],105)
        runner.validate_heartsaver_seated_offer(same[0],schedule,case.now,300)
        with patch.object(validator,'load_json',return_value=feed):validator.validate_selector('heartsaver',{source['external_class_id']},now=case.now)
        self.browser_contract(feed,case.now)
        for change in [dict(capacity=6),dict(remainingSeats=3),dict(coursePolicyKey='heartsaver-full:209809.v1'),dict(identityWitness='b'*32),dict(registrationUrl='/register/?session=123')]:
            with self.assertRaises(ValueError):runner.validate_heartsaver_seated_offer(dict(same[0],**change),schedule,case.now,300)
        for change in [dict(native_heartsaver_booking_admission=None),dict(active_registration_count=3),dict(visibility='private'),dict(workspace_projection_status='stale')]:
            bad=copy.deepcopy(demand);bad['sessions'][0].update(change)
            revised=runner.retained_projection(schedule,bad,heartsaver_enabled=True,now=case.now)
            self.assertEqual(len(revised['sessions']),1);self.assertFalse(revised['sessions'][0]['public_direct_booking']);self.assertNotIn('registration_url',revised['sessions'][0])
        off=runner.retained_projection(schedule,demand);self.assertFalse(off['sessions'][0]['public_direct_booking'])

    def test_enabled_runner_checks_policy_proof_and_revalidates_every_offer(self):
        case=fixture();_,bls=bls_fixtures.NativeFullValidatorTests().fixture();hs=generator.public_selector_availability_payload(emit(case));feeds={'bls':bls,'heartsaver':hs}
        demand={'generated_at':(case.now-timedelta(seconds=5)).isoformat(),'sessions':[],'native_heartsaver_policy_proof':case.native_policy['_heartsaverProof']}
        policy={k:v for k,v in case.native_policy.items() if not k.startswith('_')}
        def read(path):return policy if path==runner.POLICY else {'sessions':[]} if path.endswith('schedule_future.json') else feeds[Path(path).stem]
        with patch.object(runner,'read',side_effect=read),patch.object(validator,'load_json',side_effect=lambda p:feeds[Path(p).stem]),patch.object(runner,'load_publication_demand',return_value=demand),patch.object(runner,'calendar_bounds',return_value={'validUntil':case.now+timedelta(minutes=15),'observedAt':case.now}):
            result=runner.validate(now=case.now);self.assertEqual(set(result['pageCounts']),{'bls','heartsaver'})
            self.assertEqual(scope.instant(result['validUntil']),case.now+timedelta(minutes=15,seconds=-5))
            demand['native_heartsaver_policy_proof']['courses']['344085']['nativePublicationEnabled']=False
            with self.assertRaisesRegex(ValueError,'native_heartsaver_course_not_ready'):runner.validate(now=case.now)

    def test_exact_manifest_path_and_gate_drift_before_any_git_write(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(runner,'ROOT',Path(directory)):
            paths=runner.publication_paths(False,True)
            for path in paths:
                target=Path(directory)/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b'local')
            report=dict(schemaVersion='native-publication-run.v1',preview=False,skillsEnabled=False,heartsaverFullEnabled=True,files={p:sha256(b'local').hexdigest() for p in paths})
            runner.assert_manifest(report)
            with self.assertRaises(ValueError):runner.assert_manifest(dict(report,heartsaverFullEnabled=False))
            policy={k:v for k,v in fixture().native_policy.items() if not k.startswith('_')};policy['heartsaverFullEnabled']=False
            with patch.dict('os.environ',{'GITHUB_REF':'refs/heads/main'}),patch.object(runner,'read',side_effect=[policy,report]),patch.object(runner,'git') as git:
                with self.assertRaisesRegex(ValueError,'heartsaver_publication_gate_changed'):runner.publish()
                git.assert_not_called()



    def browser_contract(self,feed,now):
        code="""const ui=require('./docs/assets/resolved-selector-availability.js');let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>{
        const {feed,now}=JSON.parse(s),fresh=ui.datesForPublication(feed.dates,feed.validUntil,now);
        if(!fresh.length)throw Error('fresh scoped feed hidden');
        if(ui.datesForPublication(feed.dates,'2099-01-01T00:00:00Z',now+900000).length)throw Error('expired source renewed');
        const changes=[{authority:'other'},{coursePolicyKey:'bls'},{nativeScopeId:'other'},{proofObservedAt:null},{durationMinutes:45},{cleanupBufferMinutes:0},{registrationUrl:'https://retired.invalid'},{publicSelectable:false},{appointmentDayId:123}];
        for(const change of changes){const bad=structuredClone(feed);for(const d of bad.dates)for(const t of d.startTimes)for(const row of t.courses)Object.assign(row,change);
          if(ui.datesForPublication(bad.dates,bad.validUntil,now).length)throw Error('malformed scoped feed accepted:'+JSON.stringify(change));}
        console.log(JSON.stringify({fresh:true,mutations:changes.length,expired:true}));});"""
        result=subprocess.run(['node','-e',code],input=json.dumps(dict(feed=feed,now=now.timestamp()*1000)),text=True,capture_output=True,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stderr);self.assertTrue(json.loads(result.stdout)['fresh'])

    def test_actual_browser_module_drops_expired_or_malformed_full_proof(self):
        case=fixture();self.browser_contract(generator.public_selector_availability_payload(emit(case)),case.now)

    def test_actual_selector_reads_scoped_proof_and_never_legacy_containers(self):
        case=fixture();catalog={c['course_id']:dict(c,appointment_eligible=True,appointment_allowed=True) for c in case.courses}
        inputs={selector.LOCATION_RESOURCE_MAP_PATH:case.resources,selector.COURSE_CATALOG_PATH:{},selector.PEOPLE_CATALOG_PATH:{},
            selector.SESSIONS_CURRENT_PATH:{'sessions':[]},selector.SCHEDULE_FUTURE_PATH:{'sessions':[]},selector.COURSE_RULES_PATH:{},
            selector.PUBLIC_LOCATION_POLICY_PATH:{},selector.PUBLIC_OFFER_POLICY_PATH:{'minimum_lead_hours':24,'maximum_days_out':90},
            selector.ROOT/'data/config/layered_scheduling_policy.json':case.policy}
        demand={'sessions':[],'native_heartsaver_policy_proof':case.native_policy['_heartsaverProof']}
        patches={'require_current_live_availability_snapshot':lambda:{'layered_commitment_coverage':case.coverage},
            'load_block_schedule_page_configs':lambda:{'heartsaver':case.page},'read_required_json':lambda path:copy.deepcopy(inputs[path]),
            'load_publication_demand':lambda root:demand,'sessions_with_canonical_demand':lambda rows:(rows,{}),
            'course_rules_by_id':lambda value:catalog,'courses_by_id':lambda value:catalog,'people_lookup':lambda value:{case.policy['brian_person_id']:{}},
            'has_required_cert':lambda *args:True,'selected_public_page_live_windows':lambda *args:(case.windows,{}),
            'build_occupancy':lambda *args,**kw:case.sources,'window_datetimes':lambda w:(case.at(11,'00:00').replace(tzinfo=None),case.at(12,'00:00').replace(tzinfo=None)),
            'selector_reference_datetime':lambda:case.now.replace(tzinfo=None),'public_location_allowed':lambda *a:True,'public_policy_reasons':lambda *a,**kw:[],
            'find_url':lambda *a:(_ for _ in ()).throw(AssertionError('external fallback forbidden'))}
        with ExitStack() as stack:
            for name,value in patches.items():stack.enter_context(patch.object(selector,name,value))
            stack.enter_context(patch.object(scope,'load_policy',return_value={k:v for k,v in case.native_policy.items() if not k.startswith('_')}))
            result=selector.build_block_schedule_page(case.page)
            self.assertEqual({o['courseId'] for o in result['offers']},set(scope.HEARTSAVER))
            demand.pop('native_heartsaver_policy_proof')
            with self.assertRaisesRegex(ValueError,'native_heartsaver_policy_proof_required'):selector.build_block_schedule_page(case.page)

    def test_real_generator_exact_ten_or_fifteen_outputs_and_preview_restores_gates(self):
        # Each run writes only 10 or 15 declared docs paths + bounded private reports
        # inside TemporaryDirectory. No generated production artifact is modified.
        configs=selector.load_block_schedule_page_configs()
        for skills in [False,True]:
            case=fixture(skills);now=case.now
            demand={'generated_at':now.isoformat(),'sessions':[],'native_heartsaver_policy_proof':case.native_policy['_heartsaverProof']}
            def payload(config):
                key=config['page_key']
                if key=='heartsaver':
                    current=fixture(skills);current.page=config;return emit(current)
                if key=='bls':
                    from tests import test_native_publication_wiring as wiring
                    current=wiring.NativeWiringTests().fixture()
                    return publish(current.calculation(),config,current.courses,current.windows,current.now,
                        lambda *a:(_ for _ in ()).throw(AssertionError('external fallback forbidden')),lambda *a:[],native_policy=current.policy['native_publication_scope'])
                current=skills_fixtures.NativeSkillsPublicationTests().fixture(key);current.page=config
                return skills_fixtures.NativeSkillsPublicationTests().publish(current)
            real_validate=runner.validate
            with self.subTest(skills=skills),tempfile.TemporaryDirectory() as directory,ExitStack() as stack:
                root=Path(directory)
                for module in [runner,generator,validator]:stack.enter_context(patch.object(module,'ROOT',root))
                stack.enter_context(patch.object(generator,'SELECTOR_AVAILABILITY_DIR',root/'docs/data/block-selector-availability'))
                stack.enter_context(patch.object(validator,'SELECTOR_DIR',root/'docs/data/block-selector-availability'))
                stack.enter_context(patch.object(generator,'apply_final_live_availability_guard',side_effect=lambda p:p))
                stack.enter_context(patch.object(selector,'load_block_schedule_page_configs',return_value=configs))
                stack.enter_context(patch.object(selector,'build_block_schedule_page',side_effect=payload))
                stack.enter_context(patch.object(snapshot,'run',return_value={'missing':False,'stats':{'blocks':1}}))
                stack.enter_context(patch.object(runner,'git',return_value='local-fixture-only'))
                schedule={'sessions':[],'build':{'counts':{'sessions_output':0}}}
                stack.enter_context(patch.object(runner,'prepare',return_value=schedule))
                stack.enter_context(patch.object(runner,'load_publication_demand',return_value=demand))
                stack.enter_context(patch.object(runner,'calendar_bounds',return_value={'validUntil':now+timedelta(minutes=15),'observedAt':now}))
                stack.enter_context(patch.object(runner,'validate',side_effect=lambda:real_validate(now=now)))
                runner.write(runner.POLICY,{k:v for k,v in dict(case.native_policy,enabled=False).items() if not k.startswith('_')})
                runner.write('docs/data/schedule_future.json',schedule)
                asset=root/'docs/assets/resolved-selector-availability.js';asset.parent.mkdir(parents=True)
                shutil.copyfile(ROOT/'docs/assets/resolved-selector-availability.js',asset)
                original=(root/runner.POLICY).read_bytes();evidence=runner.build(preview=True)
                self.assertEqual((root/runner.POLICY).read_bytes(),original)
                self.assertEqual(set(evidence['files']),set(runner.publication_paths(skills,True)))
                from tests.test_native_publication_runner import workflow_report_paths
                self.assertEqual(workflow_report_paths(evidence),
                    'paths<<NATIVE_PUBLICATION_PATHS\n' + '\n'.join(runner.publication_paths(skills,True)) + '\nNATIVE_PUBLICATION_PATHS\n')
                self.assertEqual({str(path.relative_to(root)) for path in (root/'docs').rglob('*') if path.is_file()},set(evidence['files']))
                html=(root/'docs/heartsaver.html').read_text();self.assertIn('20261111-native-heartsaver1',html)
                self.assertIn('First Aid CPR AED',html);self.assertIn('CPR AED',html)
                self.assertNotIn('"courseId": "209808"',html);self.assertNotIn('"courseId": "351632"',html)
                self.assertEqual('"courseId": "509474"' in html,skills)

if __name__=='__main__':unittest.main()
