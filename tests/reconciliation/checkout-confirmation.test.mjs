import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {setup} from './native-checkout-harness.mjs';
import {dispatch} from '../../worker/checkout-confirmation.mjs';
const migration=fs.readFileSync(new URL('../../supabase/migrations/20261108153759_checkout_confirmation_delivery_gate.sql',import.meta.url),'utf8');
const token='synthetic-delivery-token-local-only-123456789';
async function fixture(fn){const h=await setup();try{
 // The older checkout fixture omits delivery columns present in production.
 await h.db.exec(`alter table public.landerware_messages
   add column if not exists created_at timestamptz default now(),
   add column if not exists provider_message_id text,
   add column if not exists sent_at timestamptz,
   add column if not exists failed_at timestamptz,
   add column if not exists failure_detail text;`);
 await h.db.exec(migration);
 await h.db.query("update public.landerware_checkout_delivery_config set token_sha256=encode(sha256(convert_to($1,'UTF8')),'hex')",[token]);
 await fn(h);
}finally{await h.db.close()}}
async function paid(h){const a=await h.create(),o=await h.bind(a.orderId);await h.finalize(o);return o;}
async function paidSkills(h){
 await h.db.exec(`insert into courses(course_key,name,enrollware_course_id,duration_minutes,cleanup_buffer_minutes,max_students_default,base_price) values('skills-session-only','Skills Session Only','509474',45,15,2,55);
  insert into landerware_registration_catalog(course_id,course_name,unit_amount,currency) values('509474','Skills Session Only',5500,'usd');
  create table skills_session_context_config(context_key text,course_id uuid,enabled boolean,capacity_policy_verified boolean);
  insert into skills_session_context_config select 'cpr-aed',id,true,true from courses where enrollware_course_id='509474';`);
 await h.db.query("update class_sessions set course_id=(select id from courses where enrollware_course_id='509474'),max_students=2,end_at=start_at+interval '45 minutes',consumption_end_at=start_at+interval '60 minutes' where id=$1",[h.id]);
 const a=await h.create([{...h.students(1)[0],learningPath:'skills-only',skillsContext:'cpr-aed',onlineCompleted:true}],undefined,{p_course_id:'509474'}),o=await h.bind(a.orderId);await h.finalize(o);return o;
}
const claim=h=>h.rpc('landerware_claim_checkout_confirmation',{p_token:token});
const settle=(h,j,args={})=>h.rpc('landerware_settle_checkout_confirmation',{p_token:token,p_message_id:j.messageId,p_lease:j.lease,p_outcome:'sent',p_provider_id:'provider-test-id',p_error:null,...args});
test('delivery starts disabled and invalid tokens cannot claim recipient data',()=>fixture(async h=>{
 const cfg=(await h.db.query('select enabled,course_ids from landerware_checkout_delivery_config')).rows[0];assert.equal(cfg.enabled,false);assert.deepEqual(cfg.course_ids,['209806','359474','210549','509474']);
 await paid(h);assert.equal((await claim(h)).disabled,true);
 await assert.rejects(h.rpc('landerware_claim_checkout_confirmation',{p_token:'bad'}),/delivery_unauthorized/);
}));
test('physical skills509474 is eligible after explicit fixture activation, without claiming an eCard or delivering a code',()=>fixture(async h=>{
 await paidSkills(h);assert.equal((await claim(h)).disabled,true);
 await h.db.exec('update landerware_checkout_delivery_config set enabled=true');
 const j=await claim(h);assert.equal(j.confirmation.courseId,'509474');assert.equal(j.confirmation.course,'Skills Session Only');assert.equal(j.customerTemplate,true);
 assert.equal(j.confirmation.selections.skillsContext,'cpr-aed');assert.equal(JSON.stringify(j).includes('secret_value'),false);
}));
test('explicit delivery course overrides survive migration reapplication and exclude509474 or unrelated courses',()=>fixture(async h=>{
 const o=await paidSkills(h);await h.db.exec("update landerware_checkout_delivery_config set enabled=false,course_ids=array['359474']");
 await h.db.exec(migration);const cfg=(await h.db.query('select enabled,course_ids from landerware_checkout_delivery_config')).rows[0];assert.equal(cfg.enabled,false);assert.deepEqual(cfg.course_ids,['359474']);
 await h.db.exec('update landerware_checkout_delivery_config set enabled=true');assert.equal((await claim(h)).empty,true);
 await h.db.exec("update landerware_checkout_delivery_config set course_ids=array['509474']");
 await h.db.query("update landerware_public_orders set course_id='unapproved-course' where id=$1",[o.id]);assert.equal((await claim(h)).empty,true);
 await h.db.query("update landerware_public_orders set course_id='509474' where id=$1",[o.id]);assert.ok((await claim(h)).messageId);
}));
test('claim leases a verified paid confirmation once; provider receipt is required and replay is inert',()=>fixture(async h=>{
 await h.db.exec('update public.landerware_checkout_delivery_config set enabled=true');await paid(h);
 const j=await claim(h);assert.ok(j.messageId);assert.ok(j.recipient);assert.equal((await claim(h)).empty,true);
 await assert.rejects(settle(h,j,{p_lease:'00000000-0000-4000-8000-000000000001'}),/invalid_delivery_lease/);
 await assert.rejects(settle(h,j,{p_provider_id:null}),/provider_receipt_required/);
 assert.equal((await settle(h,j)).settled,true);assert.equal((await settle(h,j)).replay,true);
 assert.equal((await claim(h)).empty,true);
 const rows=await h.db.query("select delivery_status,provider_message_id from public.landerware_messages where id=$1",[j.messageId]);
 assert.equal(rows.rows[0].delivery_status,'sent');assert.equal(rows.rows[0].provider_message_id,'provider-test-id');
}));
test('ambiguous sends cannot be automatically retried even when old',()=>fixture(async h=>{
 await h.db.exec('update public.landerware_checkout_delivery_config set enabled=true');await paid(h);const j=await claim(h);
 await settle(h,j,{p_outcome:'ambiguous',p_provider_id:null,p_error:'provider_result_unknown'});
 await h.db.exec("update public.landerware_checkout_delivery_attempts set claimed_at=now()-interval '1 hour'");
 assert.equal((await claim(h)).empty,true);
 const health=await h.rpc('landerware_checkout_confirmation_health',{p_token:token});assert.equal(health.failures,1);assert.equal(health.healthy,false);
}));
test('only explicit rejection can retry, with a bounded count',()=>fixture(async h=>{
 await h.db.exec('update public.landerware_checkout_delivery_config set enabled=true');await paid(h);
 for(let i=0;i<5;i++){
  const j=await claim(h);assert.ok(j.messageId);
  await settle(h,j,{p_outcome:'rejected',p_provider_id:null,p_error:'E_RATE_LIMIT_EXCEEDED'});
  assert.equal((await claim(h)).empty,true);
  await h.db.exec("update public.landerware_checkout_delivery_attempts set retry_at=now()-interval '1 second'");
 }
 assert.equal((await claim(h)).empty,true);
}));
test('unverified payment evidence and pre-cutover confirmations are excluded',()=>fixture(async h=>{
 await h.db.exec('update public.landerware_checkout_delivery_config set enabled=true');const o=await paid(h);
 await h.db.query("update public.landerware_public_orders set payment_evidence='{}' where id=$1",[o.id]);assert.equal((await claim(h)).empty,true);
 await h.db.exec("update public.landerware_checkout_delivery_config set not_before=now()+interval '1 hour'");assert.equal((await claim(h)).empty,true);
}));
test('queue tables and token checker are inaccessible to anonymous readers',()=>fixture(async h=>{
 await h.db.exec('set role anon');
 await assert.rejects(h.db.exec('select * from public.landerware_checkout_delivery_config'),/permission denied/);
 await assert.rejects(h.db.exec("select public.landerware_check_checkout_delivery_token('bad')"),/permission denied/);
 await h.db.exec('reset role');
}));
test('canonical confirmation payload excludes operational IDs and keeps purchased option snapshots',()=>fixture(async h=>{
 await h.db.exec('update public.landerware_checkout_delivery_config set enabled=true');const o=await paid(h);
 const j=await claim(h);assert.equal(j.customerTemplate,true);assert.equal(j.confirmation.courseId,'359474');
 assert.ok(j.confirmation.startsAt);assert.equal(j.confirmation.course,'AHA BLS Provider Renewal');
 assert.doesNotMatch(JSON.stringify(j.confirmation),new RegExp(o.id));
 const body=(await h.db.query('select body_text from public.landerware_messages where id=$1',[j.messageId])).rows[0].body_text;
 assert.doesNotMatch(body,/Order:|Registration:|America\/New_York/);
 await h.db.exec('set role anon');await assert.rejects(h.db.query('select public.landerware_checkout_email_data($1)',[j.messageId]),/permission denied/);await h.db.exec('reset role');
}));
test('cancelled registrations and refunded orders cannot send a stale paid confirmation',()=>fixture(async h=>{
 await h.db.exec('update public.landerware_checkout_delivery_config set enabled=true');const o=await paid(h);
 await h.db.query("update public.registrations set status='cancelled' where class_session_id=$1",[h.id]);assert.equal((await claim(h)).empty,true);
 await h.db.query("update public.registrations set status='registered' where class_session_id=$1",[h.id]);
 await h.db.query("update public.landerware_public_orders set status='refunded' where id=$1",[o.id]);assert.equal((await claim(h)).empty,true);
}));
test('paid service fulfillment is leased only to the owner with exact purchased products',()=>fixture(async h=>{
 await h.db.exec('update public.landerware_checkout_delivery_config set enabled=true');
 await h.db.exec(`insert into public.products(product_key,active,product_type,customer_price,fulfillment_mode) values('synthetic-service',true,'service',17.49,'manual');
 update public.landerware_registration_catalog set addons='[{"key":"synthetic-consultation","product_key":"synthetic-service","unit_amount":1749,"display_name":"Synthetic consultation","active":true}]' where course_id='359474';`);
 // Synthetic manual service exercises the existing fulfillment lease; it does
 // not authorize selling an actual digital product without a stock reservation.
 const a=await h.create([{...h.students(1)[0],addons:[{key:'synthetic-consultation'}]}]);const o=await h.bind(a.orderId);await h.finalize(o);
 const jobs=[await claim(h),await claim(h)];const owner=jobs.find(j=>j.recipient==='brian@910cpr.com');assert.ok(owner);assert.equal(owner.customerTemplate,false);
 assert.match(owner.body,/Synthetic consultation/);assert.match(owner.body,/Manual fulfillment required/);
 assert.equal((await claim(h)).empty,true);
}));
test('unpaid recovery leases once to the payer; paid and expired orders cannot produce recovery',()=>fixture(async h=>{
 await h.db.exec('update public.landerware_checkout_delivery_config set enabled=true');const a=await h.create();
 await h.db.query("insert into public.landerware_messages(template_key,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key) select 'retail-checkout-recovery-v2',payer_email,'Recovery','Legacy recovery','cloudflare','pending','public-order-recovery:'||id from public.landerware_public_orders where id=$1",[a.orderId]);
 assert.equal((await h.rpc('landerware_checkout_confirmation_health',{p_token:token})).queued,1);
 const j=await claim(h);assert.equal(j.customerTemplate,true);assert.equal(j.confirmation.kind,'recovery');assert.match(j.confirmation.recoveryUrl,/^https:\/\/www\.910cpr\.com\/register\/\?recover=/);assert.equal((await claim(h)).empty,true);
 await h.db.query('delete from public.landerware_checkout_delivery_attempts where message_id=$1',[j.messageId]);
 await h.db.query("update public.landerware_public_orders set hold_expires_at=now()-interval '1 second' where id=$1",[a.orderId]);assert.equal((await claim(h)).empty,true);
}));
test('native creator recovery links use the shared checkout without upgrading legacy orders',()=>fixture(async h=>{
 await h.db.exec("alter table landerware_public_orders add column checkout_runtime_version text not null default 'legacy'");
 const a=await h.create();
 await h.db.query("insert into landerware_messages(template_key,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key) select 'retail-checkout-recovery-v2',payer_email,'Recovery','Fixture','cloudflare','pending','public-order-recovery:'||id from landerware_public_orders where id=$1",[a.orderId]);
 const id=(await h.db.query("select id from landerware_messages where idempotency_key=$1",['public-order-recovery:'+a.orderId])).rows[0].id;
 const read=async()=>(await h.db.query('select landerware_checkout_recovery_data($1) r',[id])).rows[0].r;
 assert.equal(new URL((await read()).recoveryUrl).pathname,'/register/');
 await h.db.query("update landerware_public_orders set checkout_runtime_version='native-v1' where id=$1",[a.orderId]);
 assert.equal(new URL((await read()).recoveryUrl).pathname,'/register/checkout/');
 assert.equal((await h.db.query('select enabled from landerware_checkout_delivery_config')).rows[0].enabled,false);
}));

test('real queue-to-bridge mock sender recovers an explicit rejection once and records acceptance, not recipient delivery',async t=>fixture(async h=>{
 await paidSkills(h);await h.db.exec('update landerware_checkout_delivery_config set enabled=true');
 t.mock.method(globalThis,'fetch',async(url,init)=>{const name=String(url).split('/').at(-1);try{return Response.json(await h.rpc(name,JSON.parse(init.body)));}catch{return new Response('',{status:503});}});
 let rejected=true,sends=0;
 const env={CHECKOUT_DELIVERY_ENABLED:'true',SUPABASE_URL:'https://fixture-db.invalid',SUPABASE_PUBLISHABLE_KEY:'fixture-only',CHECKOUT_DELIVERY_TOKEN:token,FROM_EMAIL:'sender@example.invalid',EMAIL:{send:async m=>{sends++;assert.match(m.text,/skills session only/i);if(rejected)throw Object.assign(Error('fixture rejection'),{code:'E_RATE_LIMIT_EXCEEDED'});return {messageId:'fixture-provider-accepted'};}}};
 assert.deepEqual(await dispatch(env),{accepted:0,failed:1,actualDeliveryConfirmed:false});
 assert.equal((await dispatch(env)).accepted,0);assert.equal(sends,1);
 await h.db.exec("update landerware_checkout_delivery_attempts set retry_at=now()-interval '1 second'");rejected=false;
 const result=await dispatch(env);assert.equal(result.accepted,1);assert.equal(result.actualDeliveryConfirmed,false);
 assert.equal((await dispatch(env)).accepted,0);assert.equal(sends,2);
 const rows=(await h.db.query('select delivery_status,provider_message_id from landerware_messages')).rows;
 assert.deepEqual(rows.map(r=>[r.delivery_status,r.provider_message_id]),[['sent','fixture-provider-accepted']]);
}));
test('confirmation and manual fulfillment jobs never expose another assigned inventory unit or mark a code delivered',()=>fixture(async h=>{
 await h.db.exec(`insert into products(product_key,active,product_type,customer_price,fulfillment_mode) values('fixture-code',true,'online_program',20,'digital_code');
 insert into product_inventory_units(product_id,secret_value,status) select id,'SYNTHETIC-PRIVATE-CODE','available' from products;
 update landerware_registration_catalog set addons='[{"key":"fixture-code","product_key":"fixture-code","unit_amount":2000,"display_name":"Fixture access","active":true}]' where course_id='359474';
 update landerware_checkout_delivery_config set enabled=true;`);
 const a=await h.create([{...h.students(1)[0],addons:[{key:'fixture-code',quantity:1}]}]);await h.finalize(await h.bind(a.orderId));
 const jobs=[await claim(h),await claim(h)];assert.equal(jobs.filter(j=>j.customerTemplate===true).length,1);assert.equal(jobs.filter(j=>j.customerTemplate===false).length,1);
 assert.doesNotMatch(JSON.stringify(jobs),/SYNTHETIC-PRIVATE-CODE|secret_value/);
 const unit=(await h.db.query('select * from product_inventory_units')).rows[0];assert.ok(unit.reserved_for_registration_id);assert.equal(unit.exposed_at,null);assert.equal(unit.fulfilled_at,null);
}));
