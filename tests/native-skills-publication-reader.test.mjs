import test from 'node:test';
import assert from 'node:assert/strict';
import {skillsOffers} from '../supabase/functions/skills-session-reservation/policy.mjs';
import {genericCheckout} from '../supabase/functions/public-registration/generic.mjs';
import {createRequire} from 'node:module';
const browser=createRequire(import.meta.url)('../docs/assets/resolved-selector-availability.js');
const now=Date.parse('2030-01-01T00:00:00Z');
const stamp=n=>new Date(n).toISOString();
function feed(){return {pageKey:'heartsaver',schemaVersion:'selector-resolved-availability.v1',generatedAt:stamp(now),validUntil:stamp(now+600000),dates:[{date:'2030-01-03',startTimes:[{startTime:'01:00',courses:[{courseId:'509474',offerType:'dynamic_appointment',authority:'native-skills-publication.v1',proofObservedAt:stamp(now-60000),nativeScopeId:'brian-shipyard-b.v1',nativeOfferId:'native-skills:'+'a'.repeat(64),qualificationPolicy:'skills-session-policy.v1',skillsContexts:['cpr-aed','first-aid-cpr-aed'],capacity:2,publicSelectable:true,instructor:'Brian Ennis',resource:':: Wilmington; Shipyard Blvd - B',location:':: Wilmington; Shipyard Blvd',availabilityBlockId:'native-window',sourceSessionIds:[],durationMinutes:45,schedulerConsumptionMinutes:60,cleanupBufferMinutes:15,setupBufferMinutes:0,occupiedUntil:'2030-01-03T07:00:00Z',validUntil:stamp(now+600000)}]}]}]};}
const rows=(p=feed(),context='cpr-aed',publicCourse='509474')=>skillsOffers(p,context,now,publicCourse,{nativePublicationEnabled:true});
test('browser hides expired skills despite global restamp and rejects extension beyond original proof',()=>{
 const p=feed();assert.equal(browser.datesForPublication(p.dates,p.validUntil,now).length,1);
 assert.deepEqual(browser.datesForPublication(p.dates,'2099-01-01T00:00:00Z',now+600000),[]);
 for(const change of [{authority:undefined},{courseId:'210549'},{offerType:'seated_class'},
   {proofObservedAt:undefined},{proofObservedAt:stamp(now+1)},{validUntil:stamp(now+900000)},{capacity:6}]){
  const bad=feed();Object.assign(bad.dates[0].startTimes[0].courses[0],change);
  assert.deepEqual(browser.datesForPublication(bad.dates,'2099-01-01T00:00:00Z',now),[],JSON.stringify(change));
 }
});
test('native skills reader is independently default-off, contexts stay separate and physical identity refreshes safely',()=>{
 const p=feed();assert.deepEqual(skillsOffers(p,'cpr-aed',now),[]);
 const first=rows(p)[0];assert.equal(first.capacity,2);assert.equal(first.authority,'native-skills-publication.v1');assert.ok(!Object.hasOwn(first,'appointmentDayId'));
 assert.notEqual(rows(p,'first-aid-cpr-aed')[0].selectionId,first.selectionId);
 p.dates[0].startTimes[0].courses[0].availabilityBlockId='refreshed-window';assert.equal(rows(p)[0].selectionId,first.selectionId);
 for(const [page,context] of [['arc','arc-blended'],['hsi','hsi-blended']]){const other=feed();other.pageKey=page;other.dates[0].startTimes[0].courses[0].skillsContexts=[context];assert.equal(rows(other,context).length,1);}
});
test('native version cannot fall back to legacy; stale proof, extensions, wrong scope, identity and bundle are rejected',()=>{
 for(const patch of [{authority:undefined},{authority:'unknown'},{nativeScopeId:'other'},{nativeOfferId:'bad'},{qualificationPolicy:'guess'},{capacity:4},{skillsContexts:['hsi-blended']},{setupBufferMinutes:15},{appointmentDayId:123},{matchedContainerId:'legacy'},{offerType:'seated_class'},{instructor:'Other'},{proofObservedAt:undefined},{proofObservedAt:'2030-01-01T00:00:00'},{proofObservedAt:stamp(now+1)},{proofObservedAt:stamp(now-16*60000)},{proofObservedAt:stamp(now-6*60000)},{validUntil:stamp(now+11*60000)},{durationMinutes:120},{cleanupBufferMinutes:30}]){
  const p=feed();Object.assign(p.dates[0].startTimes[0].courses[0],patch);assert.deepEqual(rows(p),[],JSON.stringify(patch));
 }
 const stale=feed();stale.generatedAt=stamp(now-16*60000);assert.deepEqual(rows(stale),[]);
 const tooEarly=feed();tooEarly.generatedAt=stamp(now-2*60000);assert.deepEqual(rows(tooEarly),[]);
 const future=feed();future.dates[0].date='2030-04-02';future.dates[0].startTimes[0].courses[0].occupiedUntil='2030-04-02T06:00:00Z';assert.deepEqual(rows(future),[]);
 const bundle=feed();bundle.pageKey='bls';Object.assign(bundle.dates[0].startTimes[0].courses[0],{courseId:'210549',skillsContexts:['bls-skills']});assert.deepEqual(rows(bundle,'bls-skills','210549'),[]);
});
test('shared checkout requires canonical runtime gate then exact selection and canonical option before showing date',async()=>{
 const profile={profile_key:'fixture-skills',version:1,active:true,course_id:'fixture-skills',display_name:'Skills Session Only',requirements:[],form_schema:{schemaVersion:'native-checkout.form.v1',inventory_kind:'leased_skills_v1',allowed_contexts:['cpr-aed','first-aid-cpr-aed'],max_students:2,fields:[],option_groups:[],driver_rules:[{driver:'native_order'}],default_choices:[]}};
 let enabled=false,qualified=true;const calls=[];
 const deps={now:()=>now,skillsPolicy:async()=>({nativePublicationEnabled:enabled}),publication:async()=>feed(),catalog:async()=>({course_id:'509474',unit_amount:5500,currency:'usd',addons:[]}),rpc:async(name,args)=>{
  calls.push({name,args});if(name==='native_checkout_profile')return {profile,physicalCourseId:'509474'};
  if(name==='native_checkout_release_abandoned')return 0;
  if(name==='skills_session_native_option')return qualified?{capacity:2}:null;
  throw Error('unexpected_rpc:'+name);
 }};
 const api=genericCheckout(deps),selection={course:'509474',skillsContext:'cpr-aed',date:'2030-01-03',startTime:'01:00'};
 await assert.rejects(api.model(selection),/session_not_available/);assert.equal(calls.filter(c=>c.name==='skills_session_native_option').length,0);
 enabled=true;let model=await api.model(selection);assert.equal(model.session.durationMinutes,45);assert.equal(model.session.capacity,2);assert.equal(model.profile.title,'Skills Session Only');
 const option=calls.find(c=>c.name==='skills_session_native_option').args.p_offer;assert.equal(option.proofObservedAt,stamp(now-60000));assert.equal(option.capacity,2);
 await assert.rejects(api.model({...selection,selectionId:'skills:forged'}),/session_not_available/);
 await assert.rejects(api.model({...selection,skillsContext:'first-aid-cpr-aed',selectionId:model.selection.selectionId}),/session_not_available/);
 qualified=false;await assert.rejects(api.model(selection),/session_not_available/);
});
