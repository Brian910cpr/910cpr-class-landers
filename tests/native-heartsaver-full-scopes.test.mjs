import test from 'node:test';
import assert from 'node:assert/strict';
import {proveHeartsaverScopes} from './native-heartsaver-full-proof.mjs';
import {fullCourseOffers,fullCoursePage} from '../supabase/functions/public-registration/full-course.mjs';
import {genericCheckout} from '../supabase/functions/public-registration/generic.mjs';
const ids={'209809':'23dfcfa7-4224-46ed-8d45-64d43d5425db','344085':'306bc81a-0e09-49e1-8910-e05501222eb4'};
const config=course=>({materializationEnabled:true,nativePublicationEnabled:true,nativeScopeId:'brian-shipyard-b.v1',pageKey:'heartsaver',coursePolicyKey:`heartsaver-full:${course}.v1`,canonicalCourseId:ids[course],instructionMinutes:course==='344085'?90:120,cleanupMinutes:course==='344085'?15:30,maxStudents:3});
const now=Date.parse('2030-01-01T00:00:00Z');
function publication(course='344085'){
 const p=config(course),start=Date.parse('2030-01-02T15:00:00Z');
 return {pageKey:'heartsaver',schemaVersion:'selector-resolved-availability.v1',generatedAt:new Date(now).toISOString(),validUntil:new Date(now+600000).toISOString(),dates:[{date:'2030-01-02',startTimes:[{startTime:'10:00',courses:[{courseId:course,authority:'native-full-course.v2',nativeScopeId:p.nativeScopeId,coursePolicyKey:p.coursePolicyKey,proofObservedAt:new Date(now).toISOString(),selectionId:'native-full:'+'a'.repeat(64),offerType:'dynamic_appointment',publicSelectable:true,instructor:'Brian Ennis',resource:':: Wilmington; Shipyard Blvd - B',location:':: Wilmington; Shipyard Blvd',availabilityBlockId:'synthetic',sourceSessionIds:[],durationMinutes:p.instructionMinutes,cleanupBufferMinutes:p.cleanupMinutes,schedulerConsumptionMinutes:p.instructionMinutes+p.cleanupMinutes,setupBufferMinutes:0,occupiedUntil:new Date(start+(p.instructionMinutes+p.cleanupMinutes)*60000).toISOString(),validUntil:new Date(now+600000).toISOString()}]}]}]};
}
test('Heartsaver full-course reader requires exact independently enabled course policy and native proof',()=>{
 for(const course of ['209809','344085']){
  const feed=publication(course),policy=config(course),options={nativePublicationEnabled:true,coursePolicy:policy};
  assert.equal(fullCoursePage(course),'heartsaver');
  assert.deepEqual(fullCourseOffers(feed,course,now),[]);
  const [offer]=fullCourseOffers(feed,course,now,options);
  assert.equal(offer.coursePolicyKey,policy.coursePolicyKey);
  assert.equal((Date.parse(offer.endsAt)-Date.parse(offer.startsAt))/60000,policy.instructionMinutes);
  assert.equal((Date.parse(offer.consumptionEndsAt)-Date.parse(offer.endsAt))/60000,policy.cleanupMinutes);
  for(const patch of [{materializationEnabled:false},{nativePublicationEnabled:false},{maxStudents:null},{canonicalCourseId:'wrong'},{coursePolicyKey:'bls'},{instructionMinutes:240},{cleanupMinutes:0},{pageKey:'bls'}])assert.deepEqual(fullCourseOffers(feed,course,now,{...options,coursePolicy:{...policy,...patch}}),[]);
  for(const patch of [{coursePolicyKey:undefined},{coursePolicyKey:'heartsaver-full:209808.v1'},{authority:'native-full-course.v1'},{appointmentDayId:'123'},{durationMinutes:45},{cleanupBufferMinutes:0},{proofObservedAt:new Date(now-16*60000).toISOString()},{sourceSessionIds:null}]){
   const changed=structuredClone(feed);Object.assign(changed.dates[0].startTimes[0].courses[0],patch);assert.deepEqual(fullCourseOffers(changed,course,now,options),[],JSON.stringify(patch));
  }
 }
 for(const course of ['209808','329495','351632','509474']){assert.equal(fullCoursePage(course),null);assert.throws(()=>fullCourseOffers(publication(),course,now),/invalid_session/);}
});

test('generic checkout routes full Heartsaver through course-specific policy and Heartsaver publication',async()=>{
 const profile={profile_key:'native_heartsaver_344085_draft',version:1,active:true,course_id:'hist-course:a3d354b88fbc55fd',display_name:'Synthetic CPR AED',requirements:[],form_schema:{schemaVersion:'native-checkout.form.v1',inventory_kind:'scheduled_session_v1',max_students:10,fields:[{key:'first_name',wire:'firstName',type:'text',required:true}],option_groups:[],default_choices:[],driver_rules:[{driver:'native_order'}]}};
 const catalog={unit_amount:3333,currency:'usd',addons:[]},packet={profile,physicalCourseId:'344085',catalog};
 const f={profile,packet,deps:{catalog:async()=>catalog,rpc:async name=>name==='native_checkout_profile'?packet:0}},seen=[],p=config('344085');
 f.packet.physicalCourseId='344085';f.profile.course_id='hist-course:a3d354b88fbc55fd';
 f.deps.fullPolicy=async course=>{seen.push(['policy',course]);return p;};f.deps.publication=async page=>{seen.push(['publication',page]);return publication();};f.deps.now=()=>now;
 const base=f.deps.rpc;f.deps.rpc=async(name,args)=>name==='native_full_course_option'?{capacity:3}:base(name,args);
 const api=genericCheckout(f.deps),selection={course:'344085',selectionId:'native-full:'+'a'.repeat(64)};
 const model=await api.model(selection);assert.equal(model.session.durationMinutes,90);assert.equal(model.session.capacity,3);
 assert.deepEqual(seen,[['policy','344085'],['publication','heartsaver']]);
 p.materializationEnabled=false;await assert.rejects(api.model(selection),/native_registration_unavailable/);
 assert.equal(seen.filter(([x])=>x==='publication').length,1,'disabled policy cannot even read/publish an offer');
});

test('actual additive SQL preserves canonical data/BLS/guards and keeps incomplete Heartsaver scopes unsellable',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{await proveHeartsaverScopes(db);}finally{await db.close();}
});
