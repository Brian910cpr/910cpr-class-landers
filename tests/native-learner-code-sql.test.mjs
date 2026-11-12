import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {preProfileFiles,profileMigration,fullCourseMigration,codeDeliveryMigration,codeEventMigration} from './helpers/native-checkout-migration-plan.mjs';

const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8'),token='SYNTHETIC-LOCAL-DELIVERY-TOKEN-ONLY-123456789';

test('private paid-type delivery uses only its assigned code/learner and durable leases; retries and terminal state never reassign or leak publicly',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  for(const f of preProfileFiles)await db.exec(load(f));await db.exec("update courses set course_key='skills-session-only' where enrollware_course_id='509474'");
  for(const f of [profileMigration,fullCourseMigration,codeDeliveryMigration,codeEventMigration,'supabase/migrations/20261111235100_native_learner_code_resend_service.sql'])await db.exec(load(f));
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

  await db.exec('alter role service_role nosuperuser bypassrls');
  const asService=async fn=>{await db.exec('set role service_role');try{return await fn();}finally{await db.exec('reset role');}};
  const claim=()=>asService(()=>scalar('select native_claim_learner_code()'));
  const prepare=j=>asService(()=>scalar('select native_prepare_learner_code($1,$2)',[j.deliveryId,j.lease]));
  const settle=(j,outcome='accepted',provider='resend_fixture')=>asService(()=>scalar('select native_settle_learner_code($1,$2,$3,$4,null)',[j.deliveryId,j.lease,outcome,provider]));
  assert.equal((await scalar('select native_learner_code_runtime_readiness()')).ready,false);
  assert.equal((await claim()).disabled,true);
  await db.exec("update native_learner_code_runtime set enabled=true; update landerware_checkout_delivery_config set provider='resend'; update native_code_delivery_policy set enabled=true");
  await order(1,false);await order(2,true,false);await order(3);
  assert.equal((await scalar('select landerware_claim_learner_code($1)',[token])).disabled,true);
  assert.equal((await scalar('select native_learner_code_health()')).unclaimedEligible,1);
  const j=await claim();assert.ok(j.deliveryId);assert.equal((await claim()).empty,true);
  await assert.rejects(prepare({...j,lease:null}),/invalid_delivery_lease/);
  await assert.rejects(scalar('select landerware_prepare_learner_code($1,$2,$3)',[token,j.deliveryId,j.lease]),/invalid_delivery_lease/);
  const code=await prepare(j);assert.equal(code.recipient,'learner-3@example.invalid');
  assert.equal(await scalar('select count(*) from product_inventory_units where exposed_at is not null'),1);
  await settle(j,'rejected',null);await db.exec("update native_learner_code_delivery set retry_at=now()-interval '1 minute'");
  const retry=await claim();assert.equal(retry.deliveryId,j.deliveryId);assert.notEqual(retry.lease,j.lease);assert.equal((await prepare(retry)).code,code.code);
  await db.exec("update native_learner_code_runtime set enabled=false;update landerware_checkout_delivery_config set provider='cloudflare';update landerware_public_orders set status='refunded' where status='paid'");
  assert.equal((await settle(retry)).settled,true);assert.equal((await settle(retry)).replay,true);
  assert.equal(await scalar('select state from native_learner_code_delivery where id=$1',[retry.deliveryId]),'accepted');
  await assert.rejects(settle({...retry,lease:null}),/invalid_delivery_lease/);
  assert.equal(await scalar('select count(*) from product_inventory_units where fulfilled_at is not null'),0);
  await db.exec("update native_learner_code_runtime set enabled=true;update landerware_checkout_delivery_config set provider='resend'");
  await order(4);const uncertain=await claim();await prepare(uncertain);await settle(uncertain,'ambiguous',null);assert.equal((await claim()).empty,true);
  assert.equal((await scalar('select native_learner_code_health()')).unresolvedFaults,1);
  await scalar("select native_learner_code_runtime_tick('poll',true,true)");await scalar("select native_learner_code_runtime_tick('poll',true,false)");assert.equal(await scalar('select fault from native_learner_code_runtime'),true,'poll does not clear failure');
  await scalar("select native_learner_code_runtime_tick('poll',true,false)");await scalar("select native_learner_code_runtime_tick('completed',true,false)");
  const ready=await scalar('select native_learner_code_runtime_readiness()');assert.equal(ready.ready,false);assert.equal(ready.proven,false);assert.equal(ready.observerFresh,false);
  assert.equal(JSON.stringify(ready).includes('SYNTHETIC-PRIVATE'),false);
  for(const role of ['anon','authenticated'])for(const f of ['native_claim_learner_code(uuid)','native_prepare_learner_code(uuid,uuid)','native_settle_learner_code(uuid,uuid,text,text,text)','native_learner_code_runtime_readiness()'])assert.equal(await scalar(`select has_function_privilege('${role}',$1,'execute')`,[f]),false);
  await order(5);const cancelled=await claim();await db.exec('update native_learner_code_runtime set enabled=false');assert.equal((await prepare(cancelled)).blocked,true);
  await db.exec('update native_learner_code_runtime set enabled=true');assert.equal((await claim()).empty,true);assert.equal((await scalar('select native_learner_code_health()')).unclaimedEligible,1,'cancelled eligible assignment cannot disappear from readiness');
  assert.equal((await scalar('select native_mail_next_lane()')).lane,'learner_code');assert.equal((await scalar('select native_mail_next_lane()')).lane,'confirmation');
  await db.exec('update native_learner_code_runtime set enabled=false');assert.equal((await scalar('select native_mail_next_lane()')).lane,'confirmation');
 }finally{await db.close();}
});
