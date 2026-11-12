import test from 'node:test';
import assert from 'node:assert/strict';
import {fullCourseOffers} from '../supabase/functions/public-registration/full-course.mjs';
const now=Date.parse('2030-01-01T00:00Z');
function feed(){return {pageKey:'bls',schemaVersion:'selector-resolved-availability.v1',generatedAt:new Date(now).toISOString(),validUntil:new Date(now+600000).toISOString(),dates:[{date:'2030-01-03',startTimes:[{startTime:'01:00',courses:[{courseId:'209806',offerType:'dynamic_appointment',authority:'native-full-course.v2',proofObservedAt:new Date(now-60000).toISOString(),nativeScopeId:'brian-shipyard-b.v1',selectionId:'native-full:'+'a'.repeat(64),publicSelectable:true,instructor:'Brian Ennis',resource:':: Wilmington; Shipyard Blvd - B',location:':: Wilmington; Shipyard Blvd',availabilityBlockId:'native-window',sourceSessionIds:[],durationMinutes:120,schedulerConsumptionMinutes:150,cleanupBufferMinutes:30,setupBufferMinutes:0,occupiedUntil:'2030-01-03T08:30:00Z',validUntil:new Date(now+600000).toISOString()}]}]}]};}
test('native publication reader defaults off; explicit gate admits native identity without external appointment ID',()=>{const p=feed();assert.deepEqual(fullCourseOffers(p,'209806',now),[]);const o=fullCourseOffers(p,'209806',now,{nativePublicationEnabled:true});assert.equal(o.length,1);assert.equal(o[0].authority,'native-full-course.v2');assert.equal(o[0].nativeScopeId,'brian-shipyard-b.v1');assert.ok(!Object.hasOwn(o[0],'appointmentDayId'));});
test('native reader rejects wrong scope, extended proof lease, stale generation, invalid identity, duration and unsupported course',()=>{for(const patch of [{nativeScopeId:'other'},{selectionId:'dynamic:old'},{validUntil:new Date(now+900001).toISOString()},{durationMinutes:90}]){const p=feed();Object.assign(p.dates[0].startTimes[0].courses[0],patch);assert.deepEqual(fullCourseOffers(p,'209806',now,{nativePublicationEnabled:true}),[]);}const p=feed();p.generatedAt=new Date(now-900001).toISOString();assert.deepEqual(fullCourseOffers(p,'209806',now,{nativePublicationEnabled:true}),[]);assert.throws(()=>fullCourseOffers(feed(),'209809',now,{nativePublicationEnabled:true}),/invalid_session/);});

test('native reader rejects ninety-one-day offers while preserving the v1 horizon contract',()=>{
 const p=feed();p.dates[0].date='2030-04-02';
 const c=p.dates[0].startTimes[0].courses[0];c.occupiedUntil='2030-04-02T07:30:00Z';
 assert.deepEqual(fullCourseOffers(p,'209806',now,{nativePublicationEnabled:true}),[]);
 delete c.authority;delete c.nativeScopeId;delete c.selectionId;c.appointmentDayId=123;
 assert.equal(fullCourseOffers(p,'209806',now).length,1);
});

test('native original calendar observation is preserved and cannot be renewed by publication generation',()=>{
 const p=feed(),c=p.dates[0].startTimes[0].courses[0];
 const accepted=fullCourseOffers(p,'209806',now,{nativePublicationEnabled:true});
 assert.equal(accepted[0].proofObservedAt,c.proofObservedAt);
 for(const patch of [{proofObservedAt:undefined},{proofObservedAt:'2030-01-01T00:00:00'},{proofObservedAt:new Date(now+1).toISOString()},{proofObservedAt:new Date(now-16*60000).toISOString()},{proofObservedAt:new Date(now-6*60000).toISOString()},{validUntil:new Date(now+11*60000).toISOString()}]){
  const bad=structuredClone(p);Object.assign(bad.dates[0].startTimes[0].courses[0],patch);
  assert.deepEqual(fullCourseOffers(bad,'209806',now,{nativePublicationEnabled:true}),[],JSON.stringify(patch));
 }
 const olderGeneration=structuredClone(p);olderGeneration.generatedAt=new Date(now-2*60000).toISOString();
 assert.deepEqual(fullCourseOffers(olderGeneration,'209806',now,{nativePublicationEnabled:true}),[],'calendar proof cannot postdate publication');
});
