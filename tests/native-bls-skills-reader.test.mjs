import test from 'node:test';
import assert from 'node:assert/strict';
import {skillsOffers,BLS_PACKAGES} from '../supabase/functions/skills-session-reservation/policy.mjs';
import {genericCheckout} from '../supabase/functions/public-registration/generic.mjs';
const now=Date.parse('2030-01-01T00:00:00Z'),stamp=n=>new Date(n).toISOString();
function feed(course='509474'){
 const nativeOfferId='native-skills:'+'a'.repeat(64),checkoutPackage=BLS_PACKAGES[course],selectionId='skills:'+nativeOfferId+':bls-skills:'+checkoutPackage;
 const registrationUrl='/register/skills-session/?'+new URLSearchParams({course,skillsContext:'bls-skills',selectionId});
 return {pageKey:'bls',schemaVersion:'selector-resolved-availability.v1',generatedAt:stamp(now),validUntil:stamp(now+600000),dates:[{date:'2030-01-03',startTimes:[{startTime:'01:00',courses:[{
  courseId:course,publicCourseId:course,physicalCourseId:'509474',checkoutPackage,selectionId,registrationUrl,appointmentUrl:registrationUrl,
  profileKey:'native_skills_shared',profileVersion:2,offerType:'dynamic_appointment',authority:'native-skills-publication.v1',proofObservedAt:stamp(now-60000),calendarProofObservedAt:stamp(now-60000),policyProofObservedAt:stamp(now),
  nativeScopeId:'brian-shipyard-b.v1',nativeOfferId,qualificationPolicy:'skills-session-policy.v1',skillsContexts:['bls-skills'],capacity:2,publicSelectable:true,
  instructor:'Brian Ennis',resource:':: Wilmington; Shipyard Blvd - B',location:':: Wilmington; Shipyard Blvd',availabilityBlockId:'native-window',sourceSessionIds:[],
  durationMinutes:45,schedulerConsumptionMinutes:60,cleanupBufferMinutes:15,setupBufferMinutes:0,occupiedUntil:'2030-01-03T07:00:00Z',validUntil:stamp(now+600000)}]}]}]};
}
const row=p=>p.dates[0].startTimes[0].courses[0],gates={blsSkillsEnabled:true,blsBundleEnabled:true,profileVersion:2};
test('BLS package reader has separate gates, exact alias identity and original native proof',()=>{
 for(const course of ['509474','210549']){
  const p=feed(course);assert.equal(skillsOffers(p,'bls-skills',now,course,gates).length,1);
  assert.deepEqual(skillsOffers(p,'bls-skills',now,course,{nativePublicationEnabled:true}),[]);
  assert.deepEqual(skillsOffers(p,'bls-skills',now+600001,course,gates),[]);
  for(const patch of [{publicCourseId:null},{physicalCourseId:null},{checkoutPackage:null},{profileVersion:1},{profileKey:'other'},
   {skillsContexts:['bls-skills','cpr-aed']},{policyProofObservedAt:stamp(now+1)},{calendarProofObservedAt:null},
   {selectionId:'skills:legacy'},{authority:null},{validUntil:stamp(now+900001)},{publicCourseId:course==='509474'?'210549':'509474'}]){
   const changed=feed(course);Object.assign(row(changed),patch);assert.deepEqual(skillsOffers(changed,'bls-skills',now,course,gates),[],JSON.stringify(patch));
  }
 }
 assert.equal(skillsOffers(feed(),'bls-skills',now,'509474',{...gates,blsBundleEnabled:false}).length,1);
 assert.equal(skillsOffers(feed('210549'),'bls-skills',now,'210549',{...gates,blsBundleEnabled:false}).length,0);
});
const profile={profile_key:'native_skills_shared',version:2,course_id:'skills-session-only',display_name:'Skills Session',active:true,requirements:[],form_schema:{
 schemaVersion:'native-checkout.form.v1',inventory_kind:'leased_skills_v1',allowed_contexts:['bls-skills'],max_students:2,
 fields:[{key:'first_name',wire:'firstName',type:'text',required:true},{key:'last_name',wire:'lastName',type:'text',required:true},{key:'email',wire:'email',type:'email',required:true},
 {key:'online_completed',wire:'onlineCompleted',type:'checkbox',required:true,unless_choice:'online_and_skills'},{key:'online_ack',wire:'onlineCompletionAcknowledged',type:'checkbox',required:true,when_choice:'online_and_skills'}],
 option_groups:[{key:'learning_path',type:'radio',required:true,choices:[{key:'skills_only',catalog_keys:[],bindings:{learningPath:'skills-only'}},{key:'online_and_skills',contexts:['bls-skills'],catalog_keys:['aha_heartcode_bls_online'],bindings:{learningPath:'online-and-skills'}}]}],
 default_choices:['skills_only'],driver_rules:[{driver:'native_order'}],public_aliases:[{public_course_id:'210549',context:'bls-skills',default_choices:['online_and_skills'],title:'HeartCode BLS online access + skills session'}]}};
const catalog={course_id:'509474',unit_amount:5500,currency:'usd',addons:[{key:'aha_heartcode_bls_online',unit_amount:4000,active:true}]};
test('generic checkout freezes55/95 explicit packages; old210549 links and cross-package changes cannot upgrade',async()=>{
 let enabled=true,bundleEnabled=true,course='509474',saved=null;const calls=[];
 const deps={now:()=>now,skillsPolicy:async()=>({nativePublicationEnabled:false}),blsSkillsPolicy:async()=>({skillsEnabled:enabled,bundleEnabled,profileVersion:2}),
 publication:async()=>feed(course),catalog:async()=>catalog,rpc:async(name,args)=>{
  calls.push({name,args});if(name==='native_checkout_profile')return {profile,physicalCourseId:'509474'};
  if(name==='native_checkout_receipt'){if(saved)return saved;throw Error('reservation_not_found');}
  if(name==='native_checkout_release_abandoned')return 0;if(name==='skills_session_native_option')return {capacity:2};
  if(name==='reserve_native_checkout_order')return {status:'held',orderId:'synthetic',amountCents:args.p_expected_total};
  throw Error('unexpected_rpc:'+name);
 }};
 const api=genericCheckout(deps),selection=c=>({course:c,skillsContext:'bls-skills',selectionId:row(feed(c)).selectionId});
 await assert.rejects(api.model({course:'210549',skillsContext:'bls-skills'}),/session_not_available/);
 assert.equal(calls.length,0,'reject ambiguous historic link before new product lookup');
 for(course of ['509474','210549']){
  const m=await api.model(selection(course)),choice=course==='509474'?'skills_only':'online_and_skills';
  assert.deepEqual(m.profile.defaultChoices,[choice]);assert.equal(m.profile.optionGroups[0].choices.length,1);
  assert.equal(m.profile.baseCents+m.profile.optionGroups[0].choices[0].amountCents,course==='509474'?5500:9500);
  const fields={first_name:'Synthetic',last_name:'Person',email:'synthetic@example.invalid',online_completed:true,online_ack:true};
  const body={profileKey:m.profile.profileKey,profileVersion:2,selection:selection(course),students:[{fields,selectedChoices:[choice]}]};
  assert.equal((await api.reserve('11111111-1111-4111-8111-111111111111',body)).receipt.amountCents,course==='509474'?5500:9500);
  await assert.rejects(api.reserve('22222222-1111-4111-8111-111111111111',{...body,students:[{fields,selectedChoices:[choice==='skills_only'?'online_and_skills':'skills_only']}]}),/option_unavailable/);
 }
 course='210549';bundleEnabled=false;await assert.rejects(api.model(selection(course)),/session_not_available/);
 course='509474';assert.equal((await api.model(selection(course))).profile.baseCents,5500);
 enabled=false;await assert.rejects(api.model(selection(course)),/session_not_available/);
 // Recovery uses saved immutable55-dollar snapshot, even when current bundle gates differ.
 saved={status:'held',kind:'public_order',orderId:'old-skills',amountCents:5500,physicalCourseId:'509474',context:'bls-skills',students:[{}],
  profileSnapshot:{profile,physicalCourseId:'509474',catalog,context:'bls-skills',selection:{offerId:'skills:legacy55'},inputs:[{selectedChoices:['skills_only']}]} };
 assert.equal((await api.resume('33333333-1111-4111-8111-111111111111')).receipt.amountCents,5500);
 assert.deepEqual((await api.resume('33333333-1111-4111-8111-111111111111')).receipt.students[0].selectedChoices,['skills_only']);
});


test('dated legacy210549 links resolve only to one current native55-dollar skills package',async()=>{
 let publication=feed(),remaining=1,canonical=true,skillsEnabled=true,receipt=null;
 const calls=[],legacy={course:'210549',skillsContext:'bls-skills',date:'2030-01-03',startTime:'01:00',
  instructor:'Brian Ennis',location:':: Wilmington; Shipyard Blvd'};
 const offlineCatalog={...catalog,addons:[{...catalog.addons[0],active:false}]};
 const api=genericCheckout({now:()=>now,publication:async()=>publication,catalog:async()=>offlineCatalog,
  skillsPolicy:async()=>({nativePublicationEnabled:false}),
  blsSkillsPolicy:async()=>({skillsEnabled,bundleEnabled:false,profileVersion:2}),rpc:async(name,args)=>{
   calls.push({name,args});
   if(name==='native_checkout_profile'){assert.equal(args.p_public_course_id,'509474');return {profile,physicalCourseId:'509474'};}
   if(name==='native_checkout_receipt'){if(receipt)return receipt;throw Error('reservation_not_found');}
   if(name==='native_checkout_release_abandoned')return 0;
   if(name==='skills_session_native_option')return canonical?{capacity:2,targetSessionId:'synthetic-session'}:null;
   if(name==='landerware_public_seat_state')return {remaining};
   if(name==='reserve_native_checkout_order')return {status:'held',orderId:'synthetic55',amountCents:args.p_expected_total};
   throw Error('unexpected_rpc:'+name); // In particular, no stock or bundle RPC is required.
  }});
 const m=await api.model(legacy);
 assert.equal(m.selection.course,'509474');assert.equal(m.selection.selectionId,row(feed()).selectionId);
 assert.equal(m.profile.title,'BLS Skills Session Only');assert.deepEqual(m.profile.defaultChoices,['skills_only']);
 assert.equal(m.profile.optionGroups[0].choices.length,1);assert.equal(m.profile.maxStudents,1);
 assert.equal(m.profile.baseCents+m.profile.optionGroups[0].choices[0].amountCents,5500);
 const fields={first_name:'Synthetic',last_name:'Legacy',email:'legacy@example.invalid',online_completed:true};
 const body={profileKey:'native_skills_shared',profileVersion:2,selection:legacy,students:[{fields,selectedChoices:['skills_only']}]};
 const key='44444444-1111-4111-8111-111111111111';
 assert.equal((await api.reserve(key,body)).receipt.amountCents,5500);
 const claim=calls.findLast(c=>c.name==='reserve_native_checkout_order').args;
 assert.equal(claim.p_expected_total,5500);assert.equal(claim.p_offer.checkoutPackage,'bls-skills-only.v1');
 assert.equal(claim.p_offer.publicCourseId,'509474');assert.deepEqual(claim.p_students[0].addons,[]);
 await assert.rejects(api.reserve(key,{...body,students:[{fields,selectedChoices:['online_and_skills']}]}),/option_unavailable/);
 for(const patch of [{date:undefined},{startTime:undefined},{date:'2030-02-30'},{date:'2030-1-03'},{startTime:'24:00'},
  {startTime:'01:0'},{date:'2030-01-04'},{instructor:'Unknown'},{location:'Elsewhere'},{location:[]},
  {selectionId:'skills:legacy55'},{selectionId:''},{selectionId:row(feed()).selectionId},{session:'old-session'}]){
  await assert.rejects(api.model({...legacy,...patch}),/session_not_available/,JSON.stringify(patch));
 }
 for(const patch of [{publicCourseId:'210549'},{checkoutPackage:'heartcode-bls-online-and-skills.v1'},
  {profileVersion:999},{authority:null},{validUntil:stamp(now-1)}]){
  publication=feed();Object.assign(row(publication),patch);await assert.rejects(api.model(legacy),/session_not_available/);
 }
 publication=feed('210549');await assert.rejects(api.model(legacy),/session_not_available/);
 publication=feed();publication.dates[0].startTimes[0].courses.push({...row(publication)});
 await assert.rejects(api.model(legacy),/session_not_available/);
 publication=feed();remaining=0;await assert.rejects(api.model(legacy),/insufficient_seats/);
 remaining=1;canonical=false;await assert.rejects(api.model(legacy),/session_not_available/);
 canonical=true;skillsEnabled=false;await assert.rejects(api.model(legacy),/session_not_available/);
 // A held55-dollar receipt replays without current publication, gates, stock, or repricing.
 receipt={status:'held',kind:'public_order',orderId:'legacy55',amountCents:5500,students:[{}],profileSnapshot:{
  profile,catalog:offlineCatalog,physicalCourseId:'509474',context:'bls-skills',selection:{offerId:'skills:legacy55'},inputs:claim.p_inputs}};
 const before=calls.length;
 assert.equal((await api.reserve(key,body)).receipt.amountCents,5500);
 assert.deepEqual(calls.slice(before).map(c=>c.name),['native_checkout_receipt']);
});
