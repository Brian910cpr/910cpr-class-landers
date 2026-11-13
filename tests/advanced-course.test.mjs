import test from 'node:test';import assert from 'node:assert/strict';
import {fullCourseOffers,fullCoursePage,fullCourseOptionRpc} from '../supabase/functions/public-registration/full-course.mjs';
const now=Date.parse('2030-12-20T12:00:00Z');
const uuid='11111111-1111-4111-8111-111111111111';
function fixture(course='241108'){
 const page=['241108','209818'].includes(course)?'acls':'pals';
 const policy={materializationEnabled:true,nativePublicationEnabled:true,pageKey:page,nativeScopeId:'qualified-advanced-shipyard-b.v1',coursePolicyKey:`advanced-full:${course}.v1`,canonicalCourseId:uuid,instructionMinutes:240,setupMinutes:0,cleanupMinutes:0,maxStudents:6,resource:'TEST ROOM',location:'TEST VENUE',instructors:[{id:uuid,name:'Fixture qualified instructor',availabilityPersonId:'fixture-person',calendarSourceKeys:['fixture-calendar'],qualificationValidThrough:'2031-01-01T00:00:00Z'}]};
 const offer={courseId:course,authority:'native-full-course.v3',publicSelectable:true,offerType:'dynamic_appointment',nativeScopeId:policy.nativeScopeId,coursePolicyKey:policy.coursePolicyKey,canonicalCourseId:uuid,selectionId:'native-full:'+'a'.repeat(64),resource:policy.resource,location:policy.location,availabilityBlockId:'fixture-block',sourceSessionIds:[],durationMinutes:240,setupBufferMinutes:0,cleanupBufferMinutes:0,schedulerConsumptionMinutes:240,instructorId:uuid,instructor:policy.instructors[0].name,availabilityPersonId:'fixture-person',calendarSourceKey:'fixture-calendar',availabilityStartsAt:'2030-12-26T18:00:00Z',availabilityEndsAt:'2030-12-26T23:00:00Z',occupiedFrom:'2030-12-26T19:00:00Z',occupiedUntil:'2030-12-26T23:00:00Z',proofObservedAt:new Date(now).toISOString(),validUntil:new Date(now+600000).toISOString()};
 const payload={pageKey:page,schemaVersion:'selector-resolved-availability.v1',generatedAt:new Date(now).toISOString(),validUntil:offer.validUntil,dates:[{date:'2030-12-26',startTimes:[{startTime:'14:00',courses:[offer]}]}]};
 return {policy,payload,offer};
}
const match=f=>fullCourseOffers(f.payload,f.offer.courseId,now,{coursePolicy:f.policy});
test('four exact advanced full variants use independent native four-hour proof without an external appointment container',()=>{
 for(const course of ['241108','209818','209805','251496']){const f=fixture(course),rows=match(f);assert.equal(rows.length,1);assert.equal(rows[0].startsAt,'2030-12-26T19:00:00.000Z');assert.equal(rows[0].endsAt,'2030-12-26T23:00:00.000Z');assert.equal(rows[0].calendarSourceKey,'fixture-calendar');assert.equal(rows[0].availabilityStartsAt,f.offer.availabilityStartsAt);assert.equal(fullCoursePage(course),f.policy.pageKey);assert.equal(fullCourseOptionRpc(course),'native_advanced_full_course_option');}
 assert.equal(fullCoursePage('209811'),null);assert.equal(fullCoursePage('209812'),null);assert.equal(fullCourseOptionRpc('209806'),'native_full_course_option');
});
test('unverified buffers, capacity, canonical identity, teacher and publication gate fail closed',()=>{
 for(const patch of [{setupMinutes:null},{cleanupMinutes:null},{maxStudents:null},{canonicalCourseId:null},{instructors:[]},{materializationEnabled:false},{nativePublicationEnabled:false},{instructionMinutes:120}]){const f=fixture();Object.assign(f.policy,patch);assert.equal(match(f).length,0);}
});
test('qualified calendar coverage, fit, exact source and fresh leases are mandatory',()=>{
 for(const patch of [{calendarSourceKey:'other'},{calendarSourceKey:null},{availabilityStartsAt:null},{availabilityEndsAt:null},{availabilityStartsAt:'2030-12-26T20:00:00Z'},{availabilityEndsAt:'2030-12-26T22:00:00Z'},{instructorId:'22222222-2222-4222-8222-222222222222'},{durationMinutes:120},{appointmentDayId:123},{matchedContainerId:123},{proofObservedAt:new Date(now-900001).toISOString()},{validUntil:new Date(now+900001).toISOString()},{occupiedUntil:'2030-12-26T23:30:00Z'}]){const f=fixture();Object.assign(f.offer,patch);assert.equal(match(f).length,0,JSON.stringify(patch));}
 const f=fixture();f.policy.instructors[0].qualificationValidThrough='2030-12-26T22:59:00Z';assert.equal(match(f).length,0);
});
test('explicit cleanup must fit inside availability; no inferred zero buffer',()=>{
 const f=fixture();f.policy.cleanupMinutes=15;f.offer.cleanupBufferMinutes=15;f.offer.schedulerConsumptionMinutes=255;f.offer.occupiedUntil='2030-12-26T23:15:00Z';assert.equal(match(f).length,0);f.offer.availabilityEndsAt='2030-12-26T23:15:00Z';assert.equal(match(f).length,1);
});
import {genericCheckout} from '../supabase/functions/public-registration/generic.mjs';
test('shared generic API routes all advanced claims through reviewed native policy, preserving price and current profile identity',async()=>{
 for(const course of ['241108','209818','209805','251496']){
  const f=fixture(course),calls=[];
  const price=course==='209805'?27500:22500;
  const profile={profile_key:'fixture-advanced-'+course,version:3,active:true,course_id:'fixture-'+course,display_name:'Fixture advanced',requirements:[],form_schema:{schemaVersion:'native-checkout.form.v1',inventory_kind:'scheduled_session_v1',max_students:6,fields:[{key:'first_name',wire:'firstName',type:'text',required:true}],option_groups:[],default_choices:[],driver_rules:[{driver:'native_order'}]}};
  const api=genericCheckout({now:()=>now,appointmentSession:async()=>null,publication:async page=>{assert.equal(page,f.policy.pageKey);return f.payload;},fullPolicy:async c=>{assert.equal(c,course);return f.policy;},catalog:async()=>({unit_amount:price,currency:'usd',addons:[]}),rpc:async(name,args)=>{calls.push({name,args});if(name==='native_checkout_receipt')throw Error('reservation_not_found');if(name==='native_checkout_profile')return {profile,physicalCourseId:course};if(name==='native_checkout_release_abandoned')return 0;if(name==='native_advanced_full_course_option')return {capacity:6};if(name==='reserve_native_advanced_checkout_order')return {orderId:'fixture-order',status:'held',amountCents:args.p_expected_total,currency:'usd'};throw Error('unexpected_rpc:'+name);}});
  const selection={course,date:'2030-12-26',startTime:'14:00'};
  const model=await api.model(selection);assert.equal(model.session.durationMinutes,240);assert.equal(model.profile.baseCents,price);
  const body={selection:model.selection,profileKey:profile.profile_key,profileVersion:3,students:[{fields:{first_name:'Synthetic'},selectedChoices:[]}]};
  await assert.rejects(api.reserve('11111111-1111-4111-8111-111111111111',{...body,profileVersion:2}),/profile_changed/);
  const result=await api.reserve('11111111-1111-4111-8111-111111111111',body);assert.equal(result.receipt.amountCents,price);
  const call=calls.find(x=>x.name==='reserve_native_advanced_checkout_order');assert.equal(call.args.p_expected_total,price);assert.equal(call.args.p_offer.calendarSourceKey,'fixture-calendar');assert.equal(call.args.p_external_id,null);
  assert.equal(calls.some(x=>x.name==='reserve_native_checkout_order'),false);
 }
});
