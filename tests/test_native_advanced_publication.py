import unittest,json,subprocess
from copy import deepcopy
from datetime import datetime,timedelta,timezone
from pathlib import Path
from scripts import native_advanced_publication as advanced
from scripts.layered_publication_adapter import calculate,publish
from scripts.layered_selector_adapter import aware
from scripts.build_bls_block_schedule_pilot import public_selector_availability_payload
ROOT=Path(__file__).resolve().parents[1]
class AdvancedPublicationTests(unittest.TestCase):
 def setUp(self):
  self.now=datetime(2030,1,1,tzinfo=timezone.utc)
  self.scheduler=json.loads((ROOT/'data/config/layered_scheduling_policy.json').read_text());self.scheduler.update(mode='active_local_v2',lead_minutes=1440)
  self.resources=json.loads((ROOT/'data/config/location_resource_map.json').read_text());room=self.scheduler['primary_resource']
  self.window={'source_availability_window':'PRIVATE-window','instructor_name':'Fixture qualified instructor','person_id':'fixture-person','calendar_source_key':'fixture-calendar','location_name':':: Wilmington; Shipyard Blvd','start':'2030-01-03T13:00:00-05:00','end':'2030-01-03T18:00:00-05:00','source_live_availability_block':{'email':'PRIVATE-contact@example.invalid'}}
  self.coverage=[dict(status='known_complete',instructor=self.window['instructor_name'],location=room,start=self.window['start'],end=self.window['end'],observed_at=self.now.isoformat(),valid_until=(self.now+timedelta(minutes=10)).isoformat(),freshness_minutes=15,source_ids=['fixture-calendar'])]
  teacher=dict(id='11111111-1111-4111-8111-111111111111',name=self.window['instructor_name'],availabilityPersonId='fixture-person',calendarSourceKeys=['fixture-calendar'],qualificationValidThrough='2031-01-01T00:00:00Z')
  self.proof=dict(schemaVersion=advanced.SCHEMA,observedAt=self.now.isoformat(),validUntil=(self.now+timedelta(minutes=15)).isoformat(),courses={cid:dict(materializationEnabled=True,nativePublicationEnabled=True,pageKey=page,nativeScopeId=advanced.SCOPE,coursePolicyKey='advanced-full:'+cid+'.v1',canonicalCourseId=f'22222222-2222-4222-8222-{index:012d}',instructionMinutes=240,setupMinutes=0,cleanupMinutes=0,maxStudents=2,resource=room,location=self.window['location_name'],instructors=[deepcopy(teacher)]) for index,(cid,page) in enumerate(advanced.COURSES.items(),1)})
  self.policy=dict(schemaVersion='native-publication-scope.v1',scopeId='brian-shipyard-b.v1',enabled=True,advancedFullEnabled=True,_advancedProof=self.proof)
 def build(self,page='acls'):
  courses=[dict(course_id=cid,course_family=family.upper(),kind='full') for cid,family in advanced.COURSES.items() if family==page]
  policy=advanced.duration_policy(self.policy,self.scheduler,self.now);policy['native_publication_scope']=self.policy
  calc=calculate([self.window],[],courses,policy,self.resources,self.now,lambda w:(aware(w['start']),aware(w['end'])),lambda w,c:advanced.qualified(self.policy,w,c,self.now),self.coverage,{})
  payload=publish(calc,dict(page_key=page,output_path='docs/'+page+'.html'),courses,[self.window],self.now,lambda *args: (_ for _ in ()).throw(AssertionError('external container must not be used')),lambda *args:[],native_policy=self.policy)
  return payload
 def test_four_hour_qualified_positive_calendar_offers_use_native_checkout_and_private_source_never_leaks(self):
  for page in ['acls','pals']:
   payload=self.build(page);self.assertTrue(payload['offers']);compact=public_selector_availability_payload(payload)
   self.assertNotIn('PRIVATE',json.dumps(compact));self.assertNotIn('enrollware',json.dumps(compact))
   for row in payload['offers']:
    dto=advanced.validate_public(row,payload['generatedAt'],self.proof,self.now)
    self.assertEqual(row['durationMinutes'],240);self.assertTrue(dto['selectionId'].startswith('native-full:'));self.assertNotIn('appointmentDayId',row)
   self.assertEqual({str(x['courseId']) for x in payload['offers']},{cid for cid,p in advanced.COURSES.items() if p==page})
 def test_public_feed_and_server_claim_dto_round_trip_match_exactly(self):
  payload=self.build();compact=public_selector_availability_payload(payload)
  code="""import {advancedFullCourseOffers} from './supabase/functions/public-registration/advanced-course.mjs';let t='';for await(const c of process.stdin)t+=c;const x=JSON.parse(t);console.log(JSON.stringify(advancedFullCourseOffers(x.feed,'241108',Date.parse(x.now),x.policy)));"""
  node='node'
  import shutil
  node=shutil.which(node) or r'C:\Program Files\nodejs\node.exe'
  result=subprocess.run([node,'--input-type=module','-e',code],input=json.dumps({'feed':compact,'now':self.now.isoformat(),'policy':self.proof['courses']['241108']}),text=True,capture_output=True,cwd=ROOT,check=True)
  actual=json.loads(result.stdout)
  expected=[advanced.claim_dto(o,payload['generatedAt']) for o in payload['offers'] if o['courseId']=='241108']
  self.assertTrue(actual);self.assertEqual(actual,expected)
 def test_browser_feed_filter_accepts_new_authority_and_rejects_expiry_or_tampering(self):
  payload=self.build();compact=public_selector_availability_payload(payload)
  code="""const api=require('./docs/assets/resolved-selector-availability.js');const fs=require('node:fs');const x=JSON.parse(fs.readFileSync(0,'utf8'));const n=Date.parse(x.now);const filtered=api.datesForPublication(x.feed.dates,x.feed.validUntil,n);const bad=structuredClone(x.feed);bad.dates[0].startTimes[0].courses[0].cleanupBufferMinutes=99;console.log(JSON.stringify({good:filtered.length,expired:api.datesForPublication(x.feed.dates,'2099-01-01',n+900001).length,bad:api.datesForPublication(bad.dates,bad.validUntil,n)[0]?.startTimes[0]?.courses.length,original:x.feed.dates[0].startTimes[0].courses.length}));"""
  import shutil
  node=shutil.which('node') or r'C:\Program Files\nodejs\node.exe'
  result=subprocess.run([node,'-e',code],input=json.dumps({'feed':compact,'now':self.now.isoformat()}),text=True,capture_output=True,cwd=ROOT,check=True)
  actual=json.loads(result.stdout);self.assertGreater(actual['good'],0);self.assertEqual(actual['expired'],0);self.assertLess(actual['bad'],actual['original'])
 def test_unknown_buffers_qualification_calendar_and_expired_policy_remain_closed(self):
  for patch in [{'cleanupMinutes':None},{'setupMinutes':15},{'maxStudents':None}]:
   bad=deepcopy(self.proof);bad['courses']['241108'].update(patch)
   with self.assertRaises(ValueError):advanced.validate_proof(bad,self.now)
  self.proof['courses']['241108']['instructors'][0]['qualificationValidThrough']='2030-01-02T00:00:00Z'
  self.assertFalse(advanced.qualified(self.policy,self.window,{'course_id':'241108'},self.now))
  self.proof['observedAt']=(self.now-timedelta(minutes=16)).isoformat();self.proof['validUntil']=self.now.isoformat()
  with self.assertRaises(ValueError):advanced.validate_proof(self.proof,self.now)
 def test_leases_identity_and_directional_coverage_cannot_be_extended_or_tampered(self):
  payload=self.build();offer=payload['offers'][0]
  for patch in [{'selectionId':'native-full:'+'f'*64},{'instructorId':'different'},{'occupiedUntil':'2030-01-03T23:59:00Z'},{'validUntil':(self.now+timedelta(minutes=16)).isoformat()},{'calendarSourceKey':'PRIVATE@example.invalid'}]:
   with self.assertRaises(ValueError):advanced.validate_public(dict(offer,**patch),payload['generatedAt'],self.proof,self.now)
  self.coverage=[];self.assertFalse(self.build()['offers'])
 def seated_fixture(self):
  from scripts import run_native_publication as runner
  from scripts.block_start_time_selector import seated_class_selector_offers
  p=self.proof['courses']['241108'];teacher=p['instructors'][0];sid='lw-11111111-1111-4111-8111-111111111111'
  b=dict(schemaVersion='native-advanced-session-booking.v1',publicCourseId='241108',canonicalCourseId=p['canonicalCourseId'],coursePolicyKey=p['coursePolicyKey'],profileKey='fixture_advanced',profileVersion=1,sourceSessionId=sid,identityWitness='a'*32,capacity=2,remaining=1,instructionMinutes=240,setupMinutes=0,cleanupMinutes=0)
  source=dict(canonical_session_id='fixture-canonical',external_class_id=sid,external_course_id='241108',course_id=p['canonicalCourseId'],source='landerware_event',registration_backend='landerware',registration_authority='landerware-generated-session.v1',session_status='scheduled',registration_status='open',visibility='public',workspace_projection_status='current',count_available=True,active_registration_count=1,canonical_registered_count=1,held_seat_count=0,unreconciled_reserved_count=0,start_at=self.window['start'],end_at='2030-01-03T17:00:00-05:00',consumption_start_at=self.window['start'],consumption_end_at='2030-01-03T17:00:00-05:00',location_name=p['location'],lead_instructor_id=teacher['id'],lead_instructor_name=teacher['name'],course_name='Synthetic ACLS',native_advanced_booking_admission=b)
  demand=dict(generated_at=self.now.isoformat(),sessions=[source],native_advanced_policy_proof=self.proof)
  schedule=runner.retained_projection({'sessions':[]},demand,advanced_enabled=True,now=self.now)
  courses=[dict(course_id='241108',course_family='ACLS',kind='full')]
  offers=seated_class_selector_offers(schedule_future_payload=schedule,selected_courses=courses,selected_course_ids={'241108'},course_rules={'241108':{'scheduler_consumption_minutes':240}})
  from scripts.apply_anchor_policy import _rebuild_dates
  payload=_rebuild_dates(dict(pageKey='acls',generatedAt=self.now.isoformat(),validUntil=self.now.isoformat()),offers)
  payload['offers']=offers
  runner.annotate_seated_offers(payload,schedule)
  payload=_rebuild_dates(payload,payload['offers'])
  return source,demand,schedule,payload
 def test_seated_native_publication_preserves_identity_capacity_and_revalidates_original_source(self):
  source,demand,schedule,payload=self.seated_fixture()
  self.assertTrue(schedule['sessions'][0]['public_direct_booking']);self.assertEqual(len(payload['offers']),1)
  compact=public_selector_availability_payload(payload)
  for row in payload['offers']:advanced.validate_seated(row,schedule,demand,self.now)
  row=compact['dates'][0]['startTimes'][0]['courses'][0]
  self.assertEqual(row['remainingSeats'],1);self.assertEqual(row['capacity'],2)
  advanced.validate_seated(dict(row,date=payload['offers'][0]['date'],startTime=payload['offers'][0]['startTime']),schedule,demand,self.now)
  self.assertEqual(row['registrationUrl'],'/register/checkout/?course=241108&session='+source['external_class_id'])
  for patch in [{'count_available':False},{'active_registration_count':None},{'workspace_projection_status':'stale'},{'native_advanced_booking_admission':None}]:
   bad=deepcopy(source);bad.update(patch)
   self.assertIsNone(advanced.seated_admission(schedule['sessions'][0],bad,demand['generated_at'],self.proof,self.now))
  with self.assertRaises(ValueError):advanced.validate_seated(dict(payload['offers'][0],remainingSeats=2),schedule,demand,self.now)
  with self.assertRaises(ValueError):advanced.validate_seated(payload['offers'][0],schedule,demand,self.now+timedelta(minutes=16))
  self.assertNotIn('native_advanced_booking_admission',__import__('scripts.run_native_publication',fromlist=['retained_projection']).retained_projection(schedule,demand,now=self.now)['sessions'][0])
 def test_dst_gap_and_fold_are_rejected(self):
  for day,clock in [('2030-03-10','02:30'),('2030-11-03','01:30')]:
   with self.assertRaises(ValueError):advanced._offset(day,clock)
 def test_disabled_gate_leaves_existing_page_allowlist_unchanged(self):
  from scripts.run_native_publication import publication_pages,native_page_config
  self.assertEqual(publication_pages(),('bls',));self.assertEqual(publication_pages(advanced_enabled=True),('bls','acls','pals'))
  config=json.loads((ROOT/'data/config/block_schedule_pages.json').read_text())['pages']['acls']
  native=native_page_config(config,'acls',advanced_enabled=True)
  self.assertEqual(set(native['allowed_course_ids']),{'241108','209818'});self.assertTrue(native['include_seated_classes'])
if __name__=='__main__':unittest.main()
