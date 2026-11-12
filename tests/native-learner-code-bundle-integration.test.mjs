// LOCAL synthetic integration only: actual BLS publication and code-readiness SQL.
// The external scheduler observer alone is simulated. No hosted clients or sends.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const bundleRoot=process.env.BLS_BUNDLE_CANDIDATE_ROOT||root;
// Final bundle artifact migration is pinned; reject an accidentally moving candidate.
assert.equal(createHash('sha256').update(readFileSync(resolve(bundleRoot,'supabase/migrations/20261111233504_native_bls_skills_publication_disabled.sql'))).digest('hex'),
 '9ce785c0f8b3989a3b9ee4ef543610875de18c52f934c2dba834043bbcccc7d2');
const {setupBlsSkills,enableSkills,makeOffer,request,claim,scalar,service}=await import(pathToFileURL(resolve(bundleRoot,'tests/native-bls-skills-proof.mjs')));
const load=p=>readFileSync(resolve(root,p),'utf8');
for(const full of [false,true])test(`real bundle + code lane integration (${full?'full':'BLS-only'}), synthetic observer only`,async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  await setupBlsSkills(db,{full});await enableSkills(db);
  for(const p of ['20261109130000_native_learner_code_delivery.sql','20261109140000_native_code_delivery_events.sql','20261111235100_native_learner_code_resend_service.sql'])await db.exec(load('supabase/migrations/'+p));
  await db.exec(`update native_bls_skills_publication_policy set bundle_enabled=true,bundle_verified=true,bundle_evidence='LOCAL SYNTHETIC ONLY';
   update landerware_checkout_delivery_config set enabled=true,provider='resend';
   update native_code_delivery_policy set enabled=true;
   update landerware_bls_bundle_policy set enabled=true,verified=true,verification_evidence='LOCAL SYNTHETIC ONLY';
   update landerware_registration_catalog set addons=jsonb_set(addons,'{0,active}','true') where course_id='509474';
   insert into products(product_key,active,product_type,customer_price,fulfillment_mode) values('aha-25-3553-heartcode-bls-online',true,'online_program',40,'digital_code');
   insert into product_inventory_units(product_id,secret_value,status) select id,'SYNTHETIC-PRIVATE-CODE-'||n,'available' from products cross join generate_series(1,4) n;
   grant select,update on products,landerware_bls_bundle_policy,landerware_checkout_delivery_config to service_role;`);
  const ready=()=>scalar(db,'select native_bls_bundle_ready()');
  const codeReady=()=>scalar(db,'select native_learner_code_runtime_readiness()');
  const opt=o=>service(db,()=>scalar(db,"select skills_session_native_option('bls-skills',$1::jsonb)",[JSON.stringify(o)]));
  const bundle=await makeOffer(db,45,{bundle:true}),skills=await makeOffer(db,46);
  assert.equal(await ready(),false);assert.equal((await codeReady()).enabled,false);assert.equal(await opt(bundle),null);assert.ok(await opt(skills));
  await db.exec("update landerware_checkout_delivery_config set last_poll_at=now(),last_accepted_at=now()");
  assert.equal(await ready(),false,'confirmation polling never proves code runtime');
  // Only external observer status is stubbed; actual native code readiness is never replaced.
  await db.exec(`create schema synthetic_code_observer;
   create table synthetic_code_observer.state(fresh boolean not null);insert into synthetic_code_observer.state values(true);
   grant usage on schema synthetic_code_observer to service_role;grant select on synthetic_code_observer.state to service_role;
   create or replace function public.native_checkout_scheduler_status() returns jsonb language sql stable security invoker set search_path='' as $$
   select jsonb_build_object('enabled',true,'latched',false,'observerFresh',fresh,'callbackFresh',fresh,'lastObservedAt',case when fresh then statement_timestamp() else statement_timestamp()-interval '1 hour' end,'lastCompletedAt',case when fresh then statement_timestamp() else statement_timestamp()-interval '1 hour' end) from synthetic_code_observer.state $$;
   revoke all on function public.native_checkout_scheduler_status() from public,anon,authenticated;
   grant execute on function public.native_checkout_scheduler_status() to service_role;
   update native_learner_code_runtime set enabled=true,configured=true,proven=true,proof_at=now(),proof_reference='LOCAL SYNTHETIC PROOF ONLY';`);
  assert.equal(await ready(),false,'proof/config alone lacks code cadence');
  await scalar(db,"select native_learner_code_runtime_tick('poll',true,false)");
  await scalar(db,"select native_learner_code_runtime_tick('completed',true,false)");
  assert.equal(await ready(),true);assert.ok(await opt(bundle));
  for(const [disable,restore] of [
   ['update native_learner_code_runtime set enabled=false','update native_learner_code_runtime set enabled=true'],
   ["update native_learner_code_runtime set last_completed_at=now()-interval '4 minutes'","update native_learner_code_runtime set last_completed_at=now()"],
   ['update native_learner_code_runtime set fault=true','update native_learner_code_runtime set fault=false'],
   ['update synthetic_code_observer.state set fresh=false','update synthetic_code_observer.state set fresh=true'],
   ['update native_learner_code_runtime set proven=false','update native_learner_code_runtime set proven=true'],
  ]){await db.exec(disable);assert.equal(await ready(),false,disable);assert.equal(await opt(bundle),null,disable);assert.ok(await opt(skills),'$55 unaffected');await db.exec(restore);}
  const held=await claim(db,request(bundle,full?8201:8101));assert.equal(held.amountCents,9500);
  const checkout='cs_synthetic_code_bundle',intent='pi_synthetic_code_bundle';
  await db.query('update landerware_public_orders set stripe_checkout_session_id=$2 where id=$1',[held.orderId,checkout]);
  const evidence={id:checkout,mode:'payment',payment_status:'paid',amount_total:9500,currency:'usd',metadata:{landerware_order_id:held.orderId}};
  await service(db,()=>scalar(db,'select native_checkout_record_payment($1,$2,$3::jsonb)',[held.orderId,intent,JSON.stringify(evidence)]));
  assert.equal((await service(db,()=>scalar(db,'select native_checkout_finalize_order($1,$2,$3::jsonb)',[held.orderId,intent,JSON.stringify(evidence)]))).status,'paid');
  assert.equal((await codeReady()).unclaimedEligible,1);assert.equal(await ready(),false,'paid unclaimed backlog closes further bundle admission');assert.ok(await opt(skills));
  const job=await service(db,()=>scalar(db,'select native_claim_learner_code()'));assert.ok(job.deliveryId,'closed admission does not deadlock consumer');
  const prepared=await service(db,()=>scalar(db,'select native_prepare_learner_code($1,$2)',[job.deliveryId,job.lease]));
  assert.match(prepared.code,/^SYNTHETIC-PRIVATE-CODE-/);assert.match(prepared.recipient,/@example.invalid$/);
  assert.equal(await ready(),false,'processing remains unresolved');
  const settled=await service(db,()=>scalar(db,"select native_settle_learner_code($1,$2,'accepted','synthetic_resend_receipt',null)",[job.deliveryId,job.lease]));assert.equal(settled.actualDeliveryConfirmed,false);
  assert.equal(await ready(),true,'accepted synthetic assignment drains backlog without fabricating actual delivery');
  assert.equal((await codeReady()).deliveryUnconfirmed,1);
  assert.equal(await scalar(db,'select count(*) from product_inventory_units where fulfilled_at is not null'),0);
  assert.ok(!JSON.stringify(await codeReady()).includes('SYNTHETIC-PRIVATE-CODE'));
 }finally{await db.close();}
});
