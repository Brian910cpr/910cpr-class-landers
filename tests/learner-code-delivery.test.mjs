import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {preProfileFiles,profileMigration,fullCourseMigration,codeDeliveryMigration,codeEventMigration} from './helpers/native-checkout-migration-plan.mjs';
import {dispatchLearnerCodes} from '../worker/learner-code-delivery.mjs';
const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8'),token='SYNTHETIC-LOCAL-DELIVERY-TOKEN-ONLY-123456789';

test('private paid-type delivery uses only its assigned code/learner and durable leases; retries and terminal state never reassign or leak publicly',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  for(const f of preProfileFiles)await db.exec(load(f));await db.exec("update courses set course_key='skills-session-only' where enrollware_course_id='509474'");
  for(const f of [profileMigration,fullCourseMigration,codeDeliveryMigration,codeEventMigration])await db.exec(load(f));
  const scalar=async(sql,args=[])=>Object.values((await db.query(sql,args)).rows[0])[0];
  await db.exec(`update landerware_checkout_delivery_config set enabled=true,token_sha256=encode(sha256(convert_to('${token}','UTF8')),'hex');
   update skills_session_context_config set qualification_course_id=(select id from courses where course_key='fixture-qualification'),enabled=true where context_key='bls-skills';
   update landerware_bls_bundle_policy set enabled=true,verified=true,verification_evidence='SYNTHETIC LOCAL';
   update landerware_registration_catalog set addons=jsonb_set(addons,'{0,active}','true') where course_id='509474';
   insert into products(product_key,active,product_type,customer_price,fulfillment_mode) values('aha-25-3553-heartcode-bls-online',true,'online_program',40,'digital_code');
   insert into product_inventory_units(product_id,secret_value,status) select id,'SYNTHETIC-PRIVATE-CODE-'||n,'available' from products cross join generate_series(1,8) n;`);
  async function order(n,online=true,paid=true){
   const key=`34343434-3434-4434-8434-${String(n).padStart(12,'0')}`,wire={firstName:'Synthetic',lastName:'Learner',email:`learner-${n}@example.invalid`,phone:'2025550100',skillsContext:'bls-skills',learningPath:online?'online-and-skills':'skills-only',onlineCompletionAcknowledged:online,onlineCompleted:!online,addons:online?[{key:'aha_heartcode_bls_online',quantity:1}]:[]};
   const o=await scalar("select reserve_native_checkout_order($1,'native_skills_shared',1,'bls-skills',null,skills_test.offer('code-'||$2,$2::int)||jsonb_build_object('context','bls-skills'),$3::jsonb,$4::jsonb,$5)",[key,n+100,JSON.stringify([wire]),JSON.stringify([{wire,selectedChoices:[online?'online_and_skills':'skills_only']}]),online?9500:5500]);
   if(paid){await db.query("update landerware_public_orders set stripe_checkout_session_id=$2,status='checkout_open' where id=$1",[o.orderId,'cs_fixture'+n]);
    const evidence={id:'cs_fixture'+n,mode:'payment',payment_status:'paid',livemode:false,amount_total:online?9500:5500,currency:'usd',metadata:{landerware_order_id:o.orderId}};
    await scalar('select landerware_record_public_payment($1,$2,$3::jsonb)',[o.orderId,'pi_fixture'+n,JSON.stringify(evidence)]);await scalar('select landerware_finalize_public_order($1,$2,$3::jsonb)',[o.orderId,'pi_fixture'+n,JSON.stringify(evidence)]);}
   return o;
  }
  const claim=()=>scalar('select landerware_claim_learner_code($1)',[token]);
  const prepare=j=>scalar('select landerware_prepare_learner_code($1,$2,$3)',[token,j.deliveryId,j.lease]);
  const settle=(j,outcome='accepted',provider='provider-fixture')=>scalar('select landerware_settle_learner_code($1,$2,$3,$4,$5,$6)',[token,j.deliveryId,j.lease,outcome,provider,null]);
  await order(1,false);await order(2,true,false);const paid=await order(3);
  assert.equal((await claim()).empty,true,'product policy defaults off; plain skills and unpaid bundle never qualify');
  await db.exec('update native_code_delivery_policy set enabled=true');
  const j=await claim();assert.ok(j.deliveryId);assert.equal(JSON.stringify(j).includes('SYNTHETIC-PRIVATE'),false);assert.equal((await claim()).empty,true);
  await assert.rejects(prepare({...j,lease:'00000000-0000-4000-8000-000000000001'}),/invalid_delivery_lease/);
  const code=await prepare(j);assert.equal(code.recipient,'learner-3@example.invalid');assert.match(code.code,/^SYNTHETIC-PRIVATE-CODE-/);
  assert.equal(await scalar('select count(*) from product_inventory_units where exposed_at is not null'),1);
  await assert.rejects(prepare(j),/invalid_delivery_lease/);
  await settle(j,'rejected',null);await db.exec("update native_learner_code_delivery set retry_at=now()-interval '1 minute'");
  const retry=await claim();assert.equal(retry.deliveryId,j.deliveryId);assert.notEqual(retry.lease,j.lease);assert.equal((await prepare(retry)).code,code.code,'known pre-send rejection retries the same unit');
  const event=(eventId,status,recipient='learner-3@example.invalid',age=30000)=>({type:'cf.email.sending.message.'+status,source:{domain:'notify.910cpr.com',type:'email.sending',zoneId:'dafc32f545bccb5fae2ff6f94cec92df'},metadata:{accountId:'9acb24ab8037cc5abe5518f7758455fd',eventTimestamp:new Date(Date.now()-age).toISOString()},payload:{eventId,messageId:'<provider-fixture>',recipient,delivery:{status}}});
  const record=e=>scalar('select landerware_record_email_delivery_event($1,$2::jsonb)',[token,JSON.stringify(e)]);
  const history=()=>scalar("select jsonb_build_object('status',provider_delivery_status,'confirmed',actual_delivery_confirmed) from native_code_delivery_history where id=$1",[retry.deliveryId]);
  await record(event('wrong-recipient','delivered','other@example.invalid'));assert.equal((await history()).confirmed,false);
  await record(event('delivered','delivered'));assert.equal((await history()).confirmed,false,'event before acceptance settlement waits for the exact receipt binding');
  for(const change of [e=>e.source.domain='wrong.invalid',e=>e.source.zoneId='wrong',e=>e.metadata.accountId='wrong',e=>e.type='cf.email.sending.message.bounced']){const e=event('invalid','delivered');change(e);await assert.rejects(record(e),/invalid_email_event_source|invalid_email_event_type/);}
  assert.equal((await settle(retry)).actualDeliveryConfirmed,false);assert.equal((await settle(retry)).replay,true);assert.equal((await claim()).empty,true);
  assert.equal(await scalar('select count(*) from product_inventory_units where fulfilled_at is not null'),0,'acceptance is not actual delivery');
  assert.equal((await history()).confirmed,true);assert.equal((await history()).status,'delivered');
  const inventoryBefore=await scalar("select jsonb_agg(jsonb_build_object('id',id,'status',status,'owner',public_order_student_id,'registration',reserved_for_registration_id,'fulfilled',fulfilled_at) order by id) from product_inventory_units");
  await record(event('older-bounce','bounced','learner-3@example.invalid',60000));await record(event('deferred','deferred','learner-3@example.invalid',0));assert.equal((await history()).confirmed,true,'late deferred or older failure cannot override delivered');
  await record(event('delivered','failed'));assert.equal((await history()).status,'delivered','event ID replay cannot replace earlier evidence');
  assert.deepEqual(await scalar("select jsonb_agg(jsonb_build_object('id',id,'status',status,'owner',public_order_student_id,'registration',reserved_for_registration_id,'fulfilled',fulfilled_at) order by id) from product_inventory_units"),inventoryBefore);
  await record(event('complaint','complained','learner-3@example.invalid',0));assert.equal((await history()).status,'complained');
  assert.equal((await scalar('select landerware_learner_code_health($1)',[token])).deliveryFailures,1);
  const cancelled=await order(4);const jc=await claim();await db.query("update landerware_public_orders set status='refunded' where id=$1",[cancelled.orderId]);assert.equal((await prepare(jc)).blocked,true);
  const changed=await order(5);const jm=await claim();await db.query("update landerware_public_order_students set email='other@example.invalid' where order_id=$1",[changed.orderId]);assert.equal((await prepare(jm)).blocked,true);
  const foreign=await order(6);const jf=await claim();await db.query('update product_inventory_units set reserved_for_registration_id=null where public_order_student_id in(select id from landerware_public_order_students where order_id=$1)',[foreign.orderId]);assert.equal((await prepare(jf)).blocked,true);
  const ambiguous=await order(7);const ja=await claim();await prepare(ja);await settle(ja,'ambiguous',null);assert.equal((await claim()).empty,true,'unknown outcome is not automatically resent');
  const wrongAmount=await order(8);await db.query("update landerware_public_orders set payment_evidence=jsonb_set(payment_evidence,'{amount_total}','1') where id=$1",[wrongAmount.orderId]);assert.equal((await claim()).empty,true);
  const inFlight=await order(9);const ji=await claim();await prepare(ji);await db.query("update landerware_public_orders set status='refunded' where id=$1",[inFlight.orderId]);await settle(ji);assert.equal(await scalar('select state from native_learner_code_delivery where id=$1',[ji.deliveryId]),'cancelled');
  const health=await scalar('select landerware_learner_code_health($1)',[token]);assert.equal(health.actualDeliveryConfirmed,false);assert.equal(JSON.stringify(health).includes('SYNTHETIC-PRIVATE'),false);
  for(const role of ['anon','authenticated'])assert.equal(await scalar(`select has_table_privilege('${role}','native_learner_code_delivery','select')`),false);
  await assert.rejects(scalar('select landerware_claim_learner_code($1)',['not-a-valid-token']),/delivery_unauthorized/);
  assert.equal(await scalar("select count(*) from native_learner_code_delivery where state='accepted'"),1);
 }finally{await db.close();}
});

test('worker sends only private prepared recipient; explicit rejection/unknown/acceptance recovery never leaks a code in its result',async()=>{
 const jobs=[{deliveryId:'j',lease:'l'},{empty:true}],calls=[],sent=[];
 const rpc=async(_env,name,args)=>{calls.push({name,args});if(name==='landerware_claim_learner_code')return jobs.shift();if(name==='landerware_prepare_learner_code')return{recipient:'learner@example.invalid',product:'HeartCode BLS',code:'SYNTHETIC-<PRIVATE>'};return{settled:true};};
 const env={CHECKOUT_CODE_DELIVERY_ENABLED:'true',FROM_EMAIL:'fixture@example.invalid',EMAIL:{send:async m=>{sent.push(m);return{messageId:'provider'};}}};
 const result=await dispatchLearnerCodes(env,rpc);assert.equal(result.accepted,1);assert.equal(result.actualDeliveryConfirmed,false);assert.equal(JSON.stringify(result).includes('PRIVATE'),false);assert.equal(sent[0].to,'learner@example.invalid');assert.match(sent[0].html,/&lt;PRIVATE&gt;/);assert.equal(calls.at(-2).args.p_outcome,'accepted');
 for(const [send,expected] of [[async()=>{throw Object.assign(Error('reject'),{code:'E_RATE_LIMIT_EXCEEDED'});},'rejected'],[async()=>{throw Error('timeout');},'ambiguous'],[async()=>({}),'ambiguous']]){
  let n=0;const settlements=[];await dispatchLearnerCodes({...env,EMAIL:{send}},async(_e,name,args)=>name==='landerware_claim_learner_code'?(n++?{}:{deliveryId:'j',lease:'l'}):name==='landerware_prepare_learner_code'?{recipient:'learner@example.invalid',product:'HeartCode',code:'SYNTHETIC'}:(settlements.push(args),{}));assert.equal(settlements[0].p_outcome,expected);
 }
 assert.deepEqual(await dispatchLearnerCodes({},()=>{throw Error('must_not_poll');}),{disabled:true,accepted:0,failed:0,actualDeliveryConfirmed:false});
});

test('failed acceptance persistence stops without another send; blocked preparation never invokes the provider',async()=>{
 let sends=0,claims=0;const env={CHECKOUT_CODE_DELIVERY_ENABLED:'true',FROM_EMAIL:'fixture@example.invalid',EMAIL:{send:async()=>{sends++;return{messageId:'accepted'};}}};
 const rpc=async(_e,name)=>{if(name==='landerware_claim_learner_code'){claims++;return{deliveryId:'j',lease:'l'};}if(name==='landerware_prepare_learner_code')return{recipient:'learner@example.invalid',product:'HeartCode',code:'SYNTHETIC'};throw Error('persist_failed');};
 await assert.rejects(dispatchLearnerCodes(env,rpc),/persist_failed/);assert.equal(sends,1);assert.equal(claims,1);
 let n=0;sends=0;const blocked=await dispatchLearnerCodes(env,async(_e,name)=>name==='landerware_claim_learner_code'?(n++?{}:{deliveryId:'j',lease:'l'}):{blocked:true});assert.equal(sends,0);assert.equal(blocked.accepted,0);
});
