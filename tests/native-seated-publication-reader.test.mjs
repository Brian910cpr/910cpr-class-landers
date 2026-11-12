import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {genericCheckout} from '../supabase/functions/public-registration/generic.mjs';
const require=createRequire(import.meta.url),reader=require('../docs/assets/resolved-selector-availability.js');
test('native existing seats expire at original proof; compatibility seated rows remain unchanged',()=>{
 const now=Date.parse('2030-01-01T12:00:00Z');
 const row={offerType:'seated_class',authority:'native-session-booking.v1',remainingSeats:5,
  proofObservedAt:new Date(now).toISOString(),validUntil:new Date(now+900000).toISOString()};
 const dates=r=>[{date:'2030-01-02',startTimes:[{startTime:'10:00',courses:[r]}]}];
 assert.equal(reader.datesForPublication(dates(row),'2030-01-01T11:00:00Z',now).length,1);
 assert.deepEqual(reader.datesForPublication(dates(row),'2099-01-01T00:00:00Z',now+900000),[]);
 for(const change of [{proofObservedAt:undefined},{proofObservedAt:new Date(now+1).toISOString()},{validUntil:undefined},{validUntil:new Date(now+900001).toISOString()},{remainingSeats:0}])assert.deepEqual(reader.datesForPublication(dates({...row,...change}),'2099-01-01T00:00:00Z',now),[]);
 assert.equal(reader.datesForPublication(dates({offerType:'seated_class'}),'2000-01-01T00:00:00Z',now).length,1);
});
test('owned existing native-session route rechecks seats and reserves same class without dynamic materialization',async()=>{
 const sid='lw-11111111-1111-4111-8111-111111111111',calls=[];
 const profile={profile_key:'fixture',version:1,active:true,course_id:'bls',display_name:'BLS',form_schema:{schemaVersion:'native-checkout.form.v1',inventory_kind:'scheduled_session_v1',max_students:6,fields:[],option_groups:[],default_choices:[],driver_rules:[{driver:'native_order'}]}};
 const api=genericCheckout({now:()=>0,
  scheduleSession:async id=>{assert.equal(id,sid);return {nativeReady:true,course_id:'359474',start_at:'2030-01-02T12:00:00Z',end_at:'2030-01-02T14:00:00Z',seats:{capacity:6,remaining:5}};},
  catalog:async()=>({unit_amount:7500,currency:'usd',addons:[]}),
  publication:()=>{throw Error('must not reload dynamic publication');},
  rpc:async(name,args)=>{calls.push({name,args});if(name==='native_checkout_profile')return {profile,physicalCourseId:'359474'};
   if(name==='native_checkout_receipt')throw Error('reservation_not_found');
   if(name==='reserve_native_checkout_order')return {orderId:'fixture',status:'held',students:[{}]};throw Error('unexpected RPC '+name);}
 });
 const selection={session:sid};const model=await api.model(selection);assert.equal(model.session.remainingSeats,5);assert.equal(model.view,undefined);
 await api.reserve('11111111-1111-4111-8111-111111111111',{selection,profileKey:'fixture',profileVersion:1,students:[{fields:{},selectedChoices:[]}]});
 const claim=calls.find(c=>c.name==='reserve_native_checkout_order').args;assert.equal(claim.p_external_id,sid);assert.deepEqual(claim.p_offer,{});
 assert.equal(calls.some(c=>/materialize|native_full_course_option/.test(c.name)),false);
});
