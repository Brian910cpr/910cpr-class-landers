// Synthetic local SQL + actual shared dispatcher; no hosted clients or sends.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nativeConfirmationService} from '../supabase/functions/_shared/native-confirmation-service.mjs';
import {preProfileFiles,profileMigration,fullCourseMigration,codeDeliveryMigration,codeEventMigration} from './helpers/native-checkout-migration-plan.mjs';
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8');
test('actual default-off code SQL keeps shared dispatcher entirely on confirmation lane; missing migration fails closed',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  for(const f of preProfileFiles)await db.exec(load(f));
  await db.exec("update courses set course_key='skills-session-only' where enrollware_course_id='509474'");
  for(const f of [profileMigration,fullCourseMigration,codeDeliveryMigration,codeEventMigration])await db.exec(load(f));
  const calls=[];let sends=0,claims=0;
  const service=nativeConfirmationService({env:k=>k==='RESEND_API_KEY'?'SYNTHETIC':undefined,
   request:async()=>{sends++;return Response.json({id:'synthetic_receipt_'+sends});},
   rpc:async(name,args)=>{
    calls.push(name);
    if(name==='native_mail_next_lane'||name==='native_learner_code_health')return Object.values((await db.query(`select public.${name}()`)).rows[0])[0];
    if(name==='native_checkout_confirmation_health')return {healthy:true};
    if(name==='native_checkout_claim_confirmation'){claims++;return {messageId:`${String(claims).padStart(8,'0')}-1111-4111-8111-111111111111`,lease:'99999999-1111-4111-8111-111111111111',recipient:'synthetic@example.invalid',subject:'Fixture',body:'Synthetic confirmation',customerTemplate:true,confirmation:{kind:'confirmation',course:'Synthetic course',courseId:'209806',startsAt:'2099-01-01T12:00:00Z'}};}
    if(name==='native_checkout_settle_confirmation')return {settled:true};
    throw Error('unexpected_rpc');
   }});
  const missing=await service.deliver(null,{limit:1});assert.equal(missing.stopped,'lane_unknown');assert.equal(sends,0);assert.equal(claims,0);
  await assert.rejects(service.health());
  await db.exec(load('supabase/migrations/20261111235100_native_learner_code_resend_service.sql'));
  const runtime=(await db.query('select enabled,configured,proven,next_lane from native_learner_code_runtime')).rows[0];
  assert.deepEqual(runtime,{enabled:false,configured:false,proven:false,next_lane:'learner_code'});
  calls.length=0;
  const scheduled=await service.deliver(null,{limit:1});assert.equal(scheduled.accepted,1);assert.equal(sends,1);
  const owner=await service.deliver();assert.equal(owner.accepted,10);assert.equal(sends,11);assert.equal(claims,11);
  assert.equal(calls.filter(n=>n==='native_mail_next_lane').length,11);
  assert.equal(calls.some(n=>/native_(claim|prepare|settle)_learner_code|native_learner_code_runtime_tick/.test(n)),false);
  const health=await service.health();assert.equal(health.healthy,true);assert.equal(health.codeDelivery.enabled,false);
  assert.equal((await db.query('select next_lane from native_learner_code_runtime')).rows[0].next_lane,'learner_code','disabled lane does not consume its turn');
 }finally{await db.close();}
});
