import test from 'node:test';
import assert from 'node:assert/strict';
import {createHandler} from '../supabase/functions/skills-session-reservation/handler.mjs';
import {skillsOffers} from '../supabase/functions/skills-session-reservation/policy.mjs';
import client from '../docs/assets/skills-reservation-client.js';
const now=Date.parse('2026-11-06T12:00:00Z');
function feed(){return {schemaVersion:'selector-resolved-availability.v1',pageKey:'heartsaver',generatedAt:new Date(now).toISOString(),validUntil:new Date(now+60000).toISOString(),dates:[{date:'2026-11-10',startTimes:[{startTime:'10:00',courses:[{courseId:'509474',offerType:'dynamic_appointment',publicSelectable:true,durationMinutes:45,schedulerConsumptionMinutes:60,cleanupBufferMinutes:15,occupiedUntil:'2026-11-10T16:00:00Z',instructor:'Fixture Instructor',resource:':: Wilmington; Shipyard Blvd - B',location:':: Wilmington; Shipyard Blvd',availabilityBlockId:'fixture',sourceSessionIds:[],validUntil:new Date(now+60000).toISOString()}]}]}]};}
const student={firstName:'Fixture',lastName:'Student',email:'fixture@example.invalid',onlineCompleted:true};
const key='11111111-1111-4111-8111-111111111111';
const request=(body,route='reserve',origin='https://www.910cpr.com')=>new Request('https://test/'+route,{method:'POST',headers:{origin,'content-type':'application/json','idempotency-key':key},body:JSON.stringify(body)});
test('default-off endpoint makes no publication or RPC calls',async()=>{
  const fail=()=>{throw Error('unexpected dependency')};const handler=createHandler({publication:fail,rpc:fail});
  assert.equal((await handler(request({}))).status,503);
});
test('server selects exact offer, ignores forged price/dates, optional certificate absent',async()=>{
  const calls=[];const actual=skillsOffers(feed(),'cpr-aed',now)[0];
  const handler=createHandler({enabled:()=>true,now:()=>now,publication:async()=>feed(),rpc:async(name,args)=>{
    calls.push(args);return args.p_offer.startsAt?{ok:true,status:'reserved',registrationId:'fixture-reg',sessionId:'fixture-session',amountCents:5500,paymentStatus:'pending'}:{ok:false,status:'offer_required'};
  }});
  const response=await handler(request({context:'cpr-aed',selectionId:actual.selectionId,student,startsAt:'attacker',amountCents:0,offer:{startsAt:'attacker'}}));
  assert.equal(response.status,200);assert.equal(calls.length,2);assert.equal(calls[1].p_offer.startsAt,actual.startsAt);assert.equal(calls[1].p_offer.context,'cpr-aed');
  assert.equal(client.reservationState(await response.json(),true).state,'reserved');
});
test('tampered context, selection, stale feed and unavailable choices never claim',async()=>{
  const id=skillsOffers(feed(),'cpr-aed',now)[0].selectionId;
  for(const [context,selectionId,payload] of [['pediatric',id,feed()],['first-aid-cpr-aed',id,feed()],['cpr-aed','skills:forged',feed()],['cpr-aed',id,{...feed(),validUntil:new Date(now-1).toISOString()}],['cpr-aed',id,{...feed(),dates:[]}]]){
    let writes=0;const handler=createHandler({enabled:()=>true,now:()=>now,publication:async()=>payload,rpc:async(_,args)=>{if(args.p_offer.startsAt)writes++;return {status:'offer_required'};}});
    const response=await handler(request({context,selectionId,student}));assert.notEqual(response.status,200);assert.equal(writes,0);
  }
});
test('lost response can replay after publication expiry; DB rejection never confirms',async()=>{
  const handler=createHandler({enabled:()=>true,publication:()=>{throw Error('must not fetch expired publication on saved replay')},rpc:async()=>({ok:true,status:'reserved',registrationId:'saved',sessionId:'saved',idempotentReplay:true})});
  assert.equal((await handler(request({context:'cpr-aed',selectionId:'skills:saved',student}))).status,200);
  const rejected=createHandler({enabled:()=>true,publication:async()=>feed(),rpc:async()=>{throw Error('session_not_available')}});
  const response=await rejected(request({context:'cpr-aed',selectionId:'skills:saved',student}));
  assert.equal(client.reservationState(await response.json(),response.ok).state,'unconfirmed');
  assert.equal(client.reservationState({ok:true,status:'reserved'},true).state,'unconfirmed');
});
test('untrusted origin is rejected before reading data',async()=>{
  const handler=createHandler({enabled:()=>true,publication:()=>{throw Error('read')},rpc:()=>{throw Error('write')}});
  assert.equal((await handler(request({},'reserve','https://evil.invalid'))).status,403);
});
test('online completion acknowledgement and valid student identity are required before any RPC',async()=>{
  let calls=0;const handler=createHandler({enabled:()=>true,publication:async()=>feed(),rpc:async()=>{calls++;throw Error('unexpected write')}});
  for(const changes of [{onlineCompleted:false},{email:'not-an-email'},{firstName:''}]){
    const response=await handler(request({context:'cpr-aed',selectionId:'skills:test',student:{...student,...changes}}));
    assert.equal(response.status,409);assert.equal((await response.json()).error,'invalid_student');
  }
  assert.equal(calls,0);
});
test('fresh existing native seats survive synthetic lease expiry but retain exact source identity',()=>{
  const payload=feed(),course=payload.dates[0].startTimes[0].courses[0];
  payload.validUntil=new Date(now-1000).toISOString();
  Object.assign(course,{offerType:'seated_class',session_id:'lw-fixture',availabilityBlockId:'seated:lw-fixture'});
  delete course.validUntil;
  const offers=skillsOffers(payload,'cpr-aed',now);assert.equal(offers.length,1);assert.equal(offers[0].sourceSessionId,'lw-fixture');
  course.availabilityBlockId='seated:other';assert.equal(skillsOffers(payload,'cpr-aed',now).length,0);
});
test('selected date is canonically checked read-only before exposing a reservation form',async()=>{
  const selected=skillsOffers(feed(),'cpr-aed',now)[0],calls=[];
  let available=false;
  const handler=createHandler({enabled:()=>true,now:()=>now,publication:async()=>feed(),rpc:async(name,args)=>{calls.push(name);assert.equal(name,'skills_session_native_option');assert.equal(args.p_offer.selectionId,selected.selectionId);return available?{capacity:2}:null;}});
  const body={context:'cpr-aed',selection:{localStart:selected.localStart,instructor:selected.instructor,location:selected.location}};
  let response=await handler(request(body,'choices'));assert.equal((await response.json()).offers.length,0);
  available=true;response=await handler(request(body,'choices'));assert.equal((await response.json()).offers[0].selectionId,selected.selectionId);
  response=await handler(request({...body,selection:{...body.selection,localStart:'2030-01-01T10:00'}},'choices'));assert.equal((await response.json()).offers.length,0);
  assert.equal(calls.length,2);
});
