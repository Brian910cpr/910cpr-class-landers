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
 def test_dst_gap_and_fold_are_rejected(self):
  for day,clock in [('2030-03-10','02:30'),('2030-11-03','01:30')]:
   with self.assertRaises(ValueError):advanced._offset(day,clock)
 def test_disabled_gate_leaves_existing_page_allowlist_unchanged(self):
  from scripts.run_native_publication import publication_pages,native_page_config
  self.assertEqual(publication_pages(),('bls',));self.assertEqual(publication_pages(advanced_enabled=True),('bls','acls','pals'))
  config=json.loads((ROOT/'data/config/block_schedule_pages.json').read_text())['pages']['acls']
  native=native_page_config(config,'acls',advanced_enabled=True)
  self.assertEqual(set(native['allowed_course_ids']),{'241108','209818'});self.assertFalse(native['include_seated_classes'])
if __name__=='__main__':unittest.main()
