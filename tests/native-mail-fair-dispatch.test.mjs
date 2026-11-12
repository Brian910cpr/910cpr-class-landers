import test from 'node:test';
import assert from 'node:assert/strict';
import {nativeConfirmationService} from '../supabase/functions/_shared/native-confirmation-service.mjs';
const uuid=n=>`${String(n).padStart(8,'0')}-1111-4111-8111-111111111111`;
function fixture({empty=false,blocked=false}={}){
 let turn=0,sends=0,claims=0;const lanes=[],calls=[];
 const service=nativeConfirmationService({env:k=>k==='RESEND_API_KEY'?'synthetic':undefined,
 request:async(_url,options)=>{sends++;return Response.json({id:'receipt_'+sends});},
 rpc:async(name,args)=>{calls.push({name,args});
  if(name==='native_mail_next_lane'){const lane=turn++%2?'learner_code':'confirmation';lanes.push(lane);return {lane};}
  if(name==='native_learner_code_runtime_tick')return {recorded:true};
  if(name==='native_checkout_claim_confirmation'){claims++;return empty?{empty:true}:{messageId:uuid(claims),lease:uuid(99),recipient:'brian@910cpr.com',subject:'Synthetic',body:'Fixture',customerTemplate:false};}
  if(name==='native_claim_learner_code'){claims++;return empty?{empty:true}:{deliveryId:uuid(claims),lease:uuid(99)};}
  if(name==='native_prepare_learner_code')return blocked?{blocked:true}:{recipient:'synthetic@example.invalid',product:'Synthetic',code:'SYNTHETIC-PRIVATE-CODE'};
  if(name.includes('settle'))return {settled:true};
  throw Error('unexpected '+name);
 }});
 return {service,lanes,calls,get sends(){return sends},get claims(){return claims}};
}
test('scheduled limit one alternates durable lanes and cannot send twice in one tick',async()=>{
 const f=fixture();for(let i=0;i<4;i++){const before=f.sends;const r=await f.service.deliver(null,{limit:1});assert.equal(f.sends-before,1);assert.equal(r.claimed,1);assert.equal(r.accepted,1);}
 assert.deepEqual(f.lanes,['confirmation','learner_code','confirmation','learner_code']);
});
test('default owner/postcommit batch shares ten total slots between lanes',async()=>{
 const f=fixture();const r=await f.service.deliver();assert.equal(f.claims,10);assert.equal(f.sends,10);assert.equal(r.claimed,10);assert.equal(r.accepted,10);assert.equal(f.lanes.filter(x=>x==='learner_code').length,5);assert.equal(r.limitReached,true);
 assert.doesNotMatch(JSON.stringify(r),/SYNTHETIC|synthetic@|receipt_|11111111/);
});
test('empty lane never falls through to another send in same scheduled slot',async()=>{
 const f=fixture({empty:true});const r=await f.service.deliver(null,{limit:1});assert.equal(f.claims,1);assert.equal(f.lanes.length,1);assert.equal(f.sends,0);assert.equal(r.empty,true);
});
test('blocked preparation remains distinct from provider rejection and contributes to claimed count',async()=>{
 const f=fixture({blocked:true});await f.service.deliver(null,{limit:1});const before=f.sends;const r=await f.service.deliver(null,{limit:1});assert.equal(r.blocked,1);assert.equal(r.claimed,1);assert.equal(r.accepted,0);assert.equal(r.rejected,0);assert.equal(f.sends,before);
});
test('unknown lane fails closed before any provider or claim',async()=>{
 for(const rpc of [async()=>{throw Error('private')},async()=>({lane:'other'})]){
 let sends=0;const service=nativeConfirmationService({rpc,env:()=> 'fixture',request:()=>sends++});const r=await service.deliver(null,{limit:1});assert.match(r.stopped,/^lane_(unknown|invalid)$/);assert.equal(sends,0);assert.equal(r.claimed,0);
 }
});
test('disabled code lane does not degrade confirmation health, enabled unhealthy lane does',async()=>{
 for(const codeDelivery of [{enabled:false,healthy:false},{enabled:true,healthy:true},{enabled:true,healthy:false}]){
 const service=nativeConfirmationService({rpc:async name=>name==='native_checkout_confirmation_health'?{healthy:true}:codeDelivery,env:()=> 'fixture',request:()=>{}});
 assert.equal((await service.health()).healthy,codeDelivery.enabled===false||codeDelivery.healthy===true);
 }
});
