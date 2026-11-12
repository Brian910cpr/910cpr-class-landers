"""Synthetic endpoint -> publisher -> compact feed -> actual browser reader proof."""
import copy,json,subprocess,unittest,re
from pathlib import Path
from datetime import datetime,timedelta,timezone
from scripts import native_pediatric_publication as p
from scripts import build_bls_block_schedule_pilot as generator
from scripts import run_native_publication as runner
from scripts import block_start_time_selector as selector
from scripts import fetch_canonical_scheduling_demand as fetcher
from scripts import validate_public_refresh_output as validator
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]

def fixture():
    now=datetime(2030,1,1,tzinfo=timezone.utc); start=now+timedelta(days=2,hours=15)
    policy=dict(schemaVersion='native-pediatric-existing-session-policy.v1',publicCourseId=p.COURSE,canonicalCourseId=p.CANONICAL,
        coursePolicyKey=p.KEY,profileKey='native_heartsaver_351632_draft',packageCode='full-course',courseKey='aha-heartsaver-pediatric-fa-cpr-aed',pageKey='heartsaver',
        materializationEnabled=False,existingSessionEnabled=True,nativePublicationEnabled=True,observedAt=now.isoformat(),validUntil=(now+timedelta(minutes=15)).isoformat(),
        instructionMinutes=137,setupMinutes=7,cleanupMinutes=13,maxStudents=4,profileVersion=2,unitAmount=9500,currency='usd',qualificationValidThrough=(now+timedelta(days=30)).isoformat())
    sid='lw-11111111-1111-4111-8111-111111111111'
    row=dict(id='11111111-1111-4111-8111-111111111111',course_id=p.CANONICAL,external_course_id=p.COURSE,external_class_id=sid,record_scope='operational',
        start_at=start.isoformat(),end_at=(start+timedelta(minutes=137)).isoformat(),consumption_start_at=(start-timedelta(minutes=7)).isoformat(),consumption_end_at=(start+timedelta(minutes=150)).isoformat(),
        lead_instructor_id='synthetic-instructor',location_id='synthetic-location',resource_id=None,organization_id=None,registration_backend='landerware',source='landerware_event',status='scheduled',registration_status='open',visibility='public',
        external_session_evidence={'materializedBy':'native_full_course'},native_checkout_generated_sessions={'identity_hash':'a'*32,'state':'holding'},
        courses={'course_key':policy['courseKey'],'name':'Synthetic'},people={'display_name':'Synthetic instructor'},locations={'name':'Synthetic location'})
    row['landerware_sessions']=[dict(id='workspace',starts_at=row['start_at'],ends_at=row['end_at'])]
    b={k:policy[k] for k in ('publicCourseId','canonicalCourseId','coursePolicyKey','profileKey','profileVersion','instructionMinutes','setupMinutes','cleanupMinutes','packageCode','unitAmount','currency')}
    b.update(schemaVersion=p.AUTHORITY,sourceSessionId=sid,identityWitness='a'*32,capacity=4,remaining=1)
    seats=dict(registrationAuthority='landerware-generated-session.v1',authorityRevision=None,generatedIdentity='a'*32,
        sessionIdentity=[row[k] for k in ('course_id','start_at','end_at','consumption_start_at','consumption_end_at','lead_instructor_id','location_id','resource_id','organization_id','external_class_id','record_scope')],
        sessionStatus='scheduled',registrationStatus='open',visibility='public',capacity=4,registered=1,holds=2,unreconciledReserved=0,pediatricBooking=b)
    row['landerware_session_authority_events']=[dict(enabled=True,revision=1,session_identity=seats['sessionIdentity'])]
    seats.update(registrationAuthority='landerware-session-authority.v1',authorityRevision=1,generatedIdentity=None)
    return now,policy,row,seats

def endpoint(row,seats):
    script="const {loadEndpoint}=require('./tests/helpers/canonical_demand_endpoint.cjs');let s='';process.stdin.on('data',x=>s+=x).on('end',()=>{let p=JSON.parse(s);console.log(JSON.stringify(loadEndpoint(()=>{throw Error('network')}).projectDemand(p.row,p.seats)));});"
    return json.loads(subprocess.run(['node','-e',script],input=json.dumps(dict(row=row,seats=seats)),text=True,capture_output=True,check=True,cwd=ROOT).stdout)

def reader(feed,now):
    script="const r=require('./docs/assets/resolved-selector-availability.js');let s='';process.stdin.on('data',x=>s+=x).on('end',()=>{let p=JSON.parse(s);console.log(JSON.stringify(r.datesForPublication(p.feed.dates,p.feed.validUntil,p.now)));});"
    return json.loads(subprocess.run(['node','-e',script],input=json.dumps(dict(feed=feed,now=now.timestamp()*1000)),text=True,capture_output=True,check=True,cwd=ROOT).stdout)

class PediatricPublicationTests(unittest.TestCase):
    def setUp(self):
        self.now,self.policy,self.row,self.seats=fixture()
        self.source=endpoint(self.row,self.seats)
        self.demand=dict(generated_at=self.now.isoformat(),sessions=[self.source],**{p.PROOF_KEY:self.policy})
        self.gate=dict(schemaVersion='native-publication-scope.v1',enabled=True,pediatricExistingSessionEnabled=True)
        self.payload=dict(pageKey='heartsaver',offers=[],dates=[],counts={},anchor_policy={'finalized':True},validUntil=self.policy['validUntil'])
    def emit(self):return p.project(self.payload,self.demand,self.gate,self.now)
    def test_real_contract_occupied_seats_and_nondefault_geometry(self):
        self.assertEqual(self.source['active_registration_count'],3)
        payload=self.emit();self.assertEqual(len(payload['offers']),1)
        feed=generator.public_selector_availability_payload(payload);dates=reader(feed,self.now)
        offer=dates[0]['startTimes'][0]['courses'][0]
        self.assertEqual(offer['remainingSeats'],1);self.assertEqual(offer['durationMinutes'],137)
        self.assertEqual(offer['registrationUrl'],'/register/?session='+self.row['external_class_id']+'&course=351632')
        self.assertNotIn('selectionId',offer)
    def test_actual_generated_picker_and_static_validator(self):
        payload=self.emit()
        for adult in (False,True):
            config=runner.native_page_config(selector.load_block_schedule_page_configs()['heartsaver'],'heartsaver',skills_enabled=False,heartsaver_enabled=adult,pediatric_enabled=True)
            self.assertIn('351632',[str(o['course_id']) for o in config['course_options']])
            self.assertNotIn('251545',[str(o['course_id']) for o in config['course_options']])
            self.assertNotIn('351632',config['allowed_course_ids'], 'pediatric is never a dynamic scheduler candidate')
            rendered=generator.render_html({**payload,'pageConfig':config})
            self.assertIn('"courseId": "351632"',rendered)
        feed=generator.public_selector_availability_payload(payload)
        with patch.object(validator,'load_json',return_value=feed):
            validator.validate_selector('heartsaver',{self.row['external_class_id']},now=self.now)

    def test_default_off_byte_identical_and_independent(self):
        for gate in ({},dict(self.gate,pediatricExistingSessionEnabled=False)):
            self.assertIs(p.project(self.payload,self.demand,gate,self.now),self.payload)
            cached=self.emit();self.assertEqual(p.project(cached,self.demand,gate,self.now)['offers'],[])
        self.assertFalse(json.loads((ROOT/runner.POLICY).read_text())['pediatricExistingSessionEnabled'])
        self.assertEqual(runner.publication_paths(),runner.publication_paths(False,False,False))
        self.assertEqual(runner.publication_pages(False,False,True),('bls','heartsaver'))
    def test_missing_disabled_stale_forged_policy_and_qualification(self):
        for change in ({'existingSessionEnabled':False},{'nativePublicationEnabled':False},{'materializationEnabled':True},{'profileVersion':3},{'packageCode':'skills-only'},
            {'instructionMinutes':180},{'setupMinutes':0},{'maxStudents':3},{'qualificationValidThrough':self.now.isoformat()},
            {'observedAt':(self.now-timedelta(minutes=16)).isoformat()},{'validUntil':(self.now+timedelta(minutes=16)).isoformat()},{'canonicalCourseId':'other'}):
            self.demand[p.PROOF_KEY]={**self.policy,**change};self.assertEqual(self.emit()['offers'],[],change)
        self.demand.pop(p.PROOF_KEY);self.assertEqual(self.emit()['offers'],[])
    def test_unavailable_pediatric_price_is_not_displayed_as_zero(self):
        config=runner.native_page_config(selector.load_block_schedule_page_configs()['heartsaver'],'heartsaver',skills_enabled=False,pediatric_enabled=True)
        html=generator.render_html({**self.payload,'pageConfig':config})
        expressions=re.findall(r'price.textContent = (.*);',html)
        self.assertEqual(len(expressions),2)
        for expression in expressions:
            script="const course={price:null};console.log(JSON.stringify("+expression+"));"
            self.assertEqual(json.loads(subprocess.run(['node','-e',script],text=True,capture_output=True,check=True).stdout),'')

    def test_price_proof_snapshot_and_picker_stay_consistent(self):
        config=runner.native_page_config(selector.load_block_schedule_page_configs()['heartsaver'],'heartsaver',skills_enabled=False,pediatric_enabled=True)
        self.payload['pageConfig']=config
        self.assertNotIn('price',config['course_options'][0])
        self.assertEqual(self.emit()['pageConfig']['course_options'][0]['price'],95)
        self.policy['unitAmount']=10500
        self.assertEqual(self.emit()['offers'],[])
        self.source['native_pediatric_booking_admission']['unitAmount']=10500
        self.assertEqual(self.emit()['pageConfig']['course_options'][0]['price'],105)

    def test_pediatric_only_and_combined_exact_workflow_paths(self):
        from tests.test_native_publication_runner import workflow_report_paths
        for skills,adult,count in ((False,False,10),(False,True,10),(True,False,15),(True,True,15)):
            paths=runner.publication_paths(skills,adult,True)
            self.assertEqual(len(paths),count);self.assertEqual(len(paths),len(set(paths)))
            self.assertEqual(workflow_report_paths(dict(skillsEnabled=skills,heartsaverFullEnabled=adult,pediatricExistingSessionEnabled=True,files=dict.fromkeys(paths))), 'paths<<NATIVE_PUBLICATION_PATHS\n'+'\n'.join(paths)+'\nNATIVE_PUBLICATION_PATHS\n')
        self.assertNotIn('native_pediatric',fetcher.request_url(fetcher.DEFAULT_URL))
        self.assertIn('native_pediatric=1',fetcher.request_url(fetcher.DEFAULT_URL,pediatric_enabled=True))
        self.demand['generated_at']=(self.now+timedelta(minutes=1)).isoformat();self.assertEqual(self.emit()['offers'],[])

    def test_forged_snapshot_alias_and_missing_authority(self):
        for change in ({'registration_backend':'external'},{'external_course_id':'251545'},{'count_available':False},{'active_registration_count':4},
                       {'workspace_projection_status':'stale'},{'native_pediatric_booking_admission':None},{'course_key':'blended'}):
            self.demand['sessions']=[{**self.source,**change}];self.assertEqual(self.emit()['offers'],[],change)
        bad=copy.deepcopy(self.seats);bad['pediatricBooking']['remaining']=2
        with self.assertRaises(subprocess.CalledProcessError):endpoint(self.row,bad)
    def test_reader_rejects_stale_dynamic_tampered_identity_and_geometry(self):
        feed=generator.public_selector_availability_payload(self.emit())
        for change in ({'courseId':'251545'},{'offerType':'dynamic_appointment'},{'checkoutPackage':'skills-only'},{'setupBufferMinutes':0},
                       {'canonicalCourseId':'other'},{'remainingSeats':0},{'registrationUrl':'https://external.invalid/'},{'selectionId':'invented'},
                       {'proofObservedAt':(self.now-timedelta(minutes=16)).isoformat()}):
            altered=copy.deepcopy(feed);altered['dates'][0]['startTimes'][0]['courses'][0].update(change)
            self.assertEqual(reader(altered,self.now),[],change)
        self.assertEqual(reader(feed,self.now+timedelta(minutes=16)),[])

if __name__=='__main__':unittest.main()
