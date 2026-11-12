import test from 'node:test';
import {nativeLearnerCodeReceiptVerifier} from '../supabase/functions/_shared/native-learner-code-receipt-verifier.mjs';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {preProfileFiles,profileMigration,fullCourseMigration,codeDeliveryMigration,codeEventMigration} from './helpers/native-checkout-migration-plan.mjs';

const load=p=>readFileSync(new URL('../'+p,import.meta.url),'utf8'),token='SYNTHETIC-LOCAL-DELIVERY-TOKEN-ONLY-123456789';

test('known Resend receipt reconciliation binds exact identity and remains independent of business eligibility',async()=>{
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


  await db.exec(load('supabase/migrations/20261112001500_native_learner_code_receipt_reconciliation.sql'));
  await db.exec("update native_learner_code_runtime set enabled=true;update landerware_checkout_delivery_config set provider='resend';update native_code_delivery_policy set enabled=true");
  const claim=()=>scalar('select native_claim_learner_code()');
  const prepare=j=>scalar('select native_prepare_learner_code($1,$2)',[j.deliveryId,j.lease]);
  await db.exec('alter role service_role nosuperuser bypassrls');
  const asService=async fn=>{await db.exec('set role service_role');try{return await fn();}finally{await db.exec('reset role');}};
  const context=j=>asService(()=>scalar('select native_learner_code_receipt_context($1,$2)',[j.deliveryId,j.lease]));
  const settle=(j,outcome='accepted',id='resend_known_fixture')=>scalar('select native_settle_learner_code($1,$2,$3,$4,null)',[j.deliveryId,j.lease,outcome,id]);
  const o=await order(1);const j=await claim();await prepare(j);
  assert.equal((await context(j)).blocked,true,'a prepared processing attempt without a stored receipt cannot be looked up');
  assert.equal((await scalar('select native_learner_code_receipt_target($1)',[j.deliveryId])).blocked,true);
  await settle(j);assert.deepEqual(await scalar('select native_learner_code_receipt_target($1)',[j.deliveryId]),{deliveryId:j.deliveryId,lease:j.lease});const c=await context(j);assert.equal(c.providerId,'resend_known_fixture');assert.equal(c.recipient,'learner-1@example.invalid');
  const hash=await scalar("select encode(sha256(convert_to($1,'UTF8')),'hex')",[c.code]);
  const args=[j.deliveryId,j.lease,c.providerId,c.recipient,c.product,hash,c.preparedAt,'delivered'];
  const reconcile=a=>asService(()=>scalar('select native_reconcile_learner_code_receipt($1,$2,$3,$4,$5,$6,$7,$8)',a));
  let providerGets=0;
  const verify=nativeLearnerCodeReceiptVerifier({env:()=> 'SYNTHETIC-KEY-NOT-REAL',request:async(url,options)=>{
   providerGets++;assert.equal(url,'https://api.resend.com/emails/resend_known_fixture');assert.equal(options.method,'GET');
   return Response.json({object:'email',id:c.providerId,to:[c.recipient],cc:[],bcc:[],subject:'Your purchased online course access',
    text:`Your purchased online course access code is ready.\n\nProduct: ${c.product}\nCode: ${c.code}\n\nKeep this code private. Complete the online course before your skills session. For help, reply to this email or call 910-395-5193.`,
    created_at:c.preparedAt,last_event:'sent'});
  },rpc:async(name,a)=>{
   if(name==='native_learner_code_receipt_context')return context({deliveryId:a.p_delivery_id,lease:a.p_lease});
   assert.equal(name,'native_reconcile_learner_code_receipt');return reconcile([a.p_delivery_id,a.p_lease,a.p_provider_id,a.p_recipient,a.p_product_key,a.p_code_sha256,a.p_provider_created_at,a.p_status]);
  }});
  const verified=await verify(j.deliveryId,j.lease);assert.deepEqual(verified,{verified:true,status:'sent',actualDeliveryConfirmed:false});assert.equal(providerGets,1);
  assert.doesNotMatch(JSON.stringify(verified),/PRIVATE|learner-|resend_known/);

  for(const [index,value] of [[1,null],[2,'wrong_receipt'],[3,'other@example.invalid'],[4,'wrong_product'],[5,'0'.repeat(64)],[6,'2000-01-01'],[6,'infinity'],[7,'scheduled'],[7,null]]){
   const invalid=[...args];invalid[index]=value;await assert.rejects(reconcile(invalid),/receipt_binding_mismatch|receipt_identity_mismatch|invalid_receipt_evidence/);
  }
  await db.query("update landerware_public_orders set status='refunded' where id=$1",[o.orderId]);
  await db.exec('update native_learner_code_runtime set enabled=false;update landerware_checkout_delivery_config set enabled=false');
  assert.equal((await reconcile(args)).actualDeliveryConfirmed,true,'refund/disabled lane does not erase evidence of an already sent message');
  assert.equal((await reconcile(args)).actualDeliveryConfirmed,true,'safe exact evidence replay');
  assert.equal(await scalar('select count(*) from native_learner_code_receipt_evidence'),1);
  assert.equal(await scalar('select count(*) from product_inventory_units where fulfilled_at is not null'),0);
  assert.equal(await scalar('select proven from native_learner_code_runtime'),false);
  assert.equal(await scalar('select status from landerware_public_orders where id=$1',[o.orderId]),'refunded');
  const health=await scalar('select native_learner_code_health()');assert.equal(health.deliveryConfirmed,1);assert.equal(health.deliveryUnconfirmed,0);assert.equal(health.actualDeliveryConfirmed,false);
  await reconcile([...args.slice(0,7),'complained']);assert.equal((await reconcile(args)).actualDeliveryConfirmed,false,'adverse evidence is sticky across later provider snapshots');
  assert.equal((await scalar('select native_learner_code_health()')).deliveryFailures,1);
  await scalar("select native_learner_code_runtime_tick('poll',true,false)");await scalar("select native_learner_code_runtime_tick('completed',true,false)");
  const adverseHealth=await scalar('select native_learner_code_health()');assert.equal(adverseHealth.deliveryFailures,1);assert.ok(adverseHealth.unresolvedFaults>=1);
  assert.equal((await scalar('select native_learner_code_runtime_readiness()')).ready,false);
  const retained=await scalar("select jsonb_build_object('state',d.state,'exposed',u.exposed_at is not null,'assigned',u.public_order_student_id=d.student_id and u.reserved_for_registration_id is not null,'fulfilled',u.fulfilled_at is not null) from native_learner_code_delivery d join product_inventory_units u on u.id=d.unit_id where d.id=$1",[j.deliveryId]);
  assert.deepEqual(retained,{state:'accepted',exposed:true,assigned:true,fulfilled:false});assert.equal(await scalar('select proven from native_learner_code_runtime'),false);

  await db.query("update landerware_public_order_students set email='changed@example.invalid' where id=(select student_id from native_learner_code_delivery where id=$1)",[j.deliveryId]);
  assert.equal((await context(j)).reason,'assignment_mismatch');await assert.rejects(reconcile(args),/receipt_identity_mismatch/);
  await db.query("update landerware_public_order_students set email=$2 where id=(select student_id from native_learner_code_delivery where id=$1)",[j.deliveryId,c.recipient]);
  await db.exec('update native_learner_code_runtime set enabled=true;update landerware_checkout_delivery_config set enabled=true');
  await order(2);const ambiguous=await claim();await prepare(ambiguous);await settle(ambiguous,'ambiguous',null);
  assert.equal((await context(ambiguous)).reason,'receipt_unavailable');
  const forged=[...args];forged[0]=ambiguous.deliveryId;forged[1]=ambiguous.lease;await assert.rejects(reconcile(forged),/receipt_binding_mismatch/);
  assert.equal((await claim()).empty,true,'no blind retry introduced');
  await db.query("update native_learner_code_delivery set provider_id=$2 where id=$1",[ambiguous.deliveryId,c.providerId]);
  assert.equal((await context(j)).reason,'assignment_mismatch','duplicate stored provider IDs cannot prove identity');
  for(const role of ['anon','authenticated'])for(const sig of ['native_learner_code_receipt_target(uuid)','native_learner_code_receipt_context(uuid,uuid)','native_reconcile_learner_code_receipt(uuid,uuid,text,text,text,text,timestamptz,text)'])assert.equal(await scalar(`select has_function_privilege('${role}',$1,'execute')`,[sig]),false);
 }finally{await db.close();}
});
