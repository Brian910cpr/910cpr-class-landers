import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {randomUUID} from 'node:crypto';
import {setup} from './native-checkout-harness.mjs';
import {dispatchNativeConfirmations} from '../../supabase/functions/_shared/native-confirmation-consumer.mjs';
import {sendNativeCheckoutClaim} from '../../supabase/functions/_shared/native-resend-adapter.mjs';
const read=p=>fs.readFileSync(new URL('../../'+p,import.meta.url),'utf8');
const bridge=read('supabase/migrations/20261110231615_native_checkout_confirmation_bridge_disabled.sql');
const migration=read('supabase/migrations/20261111175721_native_checkout_resend_service_consumer.sql');
const token='synthetic-delivery-token-local-only-123456789';
async function fixture(fn){const h=await setup();try{
 await h.db.exec(`alter table landerware_messages add column created_at timestamptz default now(),add column provider_message_id text,add column sent_at timestamptz,add column failed_at timestamptz,add column failure_detail text;
 alter table landerware_public_orders add column checkout_runtime_version text not null default 'legacy';`);
 await h.db.exec(bridge);await h.db.exec(migration);
 await h.db.query("update landerware_checkout_delivery_config set token_sha256=encode(sha256(convert_to($1,'UTF8')),'hex')",[token]);
 await fn(h);
 }finally{await h.db.close();}}
const claim=(h,id=null)=>h.rpc('native_checkout_claim_confirmation',{p_order_id:id});
const settle=(h,j,args={})=>h.rpc('native_checkout_settle_confirmation',{p_message_id:j.messageId,p_lease:j.lease,p_outcome:'sent',p_provider_id:'resend_receipt_123',p_error:null,...args});
const enable=h=>h.db.exec("update landerware_checkout_delivery_config set provider='resend',enabled=true");
async function paid(h,native=true){const a=await h.create();if(native)await h.db.query("update landerware_public_orders set checkout_runtime_version='native-v1' where id=$1",[a.orderId]);const o=await h.bind(a.orderId);await h.finalize(o);return o;}
test('migration is disabled by default, reapplies without enabling or rewriting scope, and native functions are service-only invoker',()=>fixture(async h=>{
 const before=(await h.db.query('select * from landerware_checkout_delivery_config')).rows[0];assert.equal(before.enabled,false);assert.equal(before.provider,'cloudflare');
 assert.deepEqual(await claim(h),{disabled:true});
 await h.db.exec("update landerware_checkout_delivery_config set course_ids=array['359474'],provider='resend'");await h.db.exec(migration);
 const after=(await h.db.query('select * from landerware_checkout_delivery_config')).rows[0];assert.equal(after.enabled,false);assert.equal(after.provider,'resend');assert.deepEqual(after.course_ids,['359474']);
 const functions=(await h.db.query("select proname,prosecdef,has_function_privilege('anon',oid,'execute') as anon,has_function_privilege('authenticated',oid,'execute') as authenticated,has_function_privilege('service_role',oid,'execute') as service from pg_proc where proname in ('native_checkout_claim_confirmation','native_checkout_settle_confirmation','native_checkout_confirmation_health')")).rows;
 assert.equal(functions.length,3);for(const f of functions){assert.equal(f.prosecdef,false);assert.equal(f.anon,false);assert.equal(f.authenticated,false);assert.equal(f.service,true);}
 await h.db.exec('set role anon');await assert.rejects(claim(h),/permission denied/);await h.db.exec('reset role');
}));
test('native claim excludes legacy, other orders and wrong course while preserving canonical confirmation payload',()=>fixture(async h=>{
 await enable(h);await paid(h,false);const o=await paid(h);assert.deepEqual(await claim(h,randomUUID()),{empty:true});
 await h.db.exec("update landerware_checkout_delivery_config set course_ids=array['509474']");assert.deepEqual(await claim(h),{empty:true});
 await h.db.exec("update landerware_checkout_delivery_config set course_ids=array['359474']");const j=await claim(h,o.id);assert.ok(j.messageId);assert.equal(j.confirmation.courseId,'359474');assert.equal(j.customerTemplate,true);assert.equal((await claim(h)).empty,true);
 assert.equal((await h.db.query('select provider from landerware_checkout_delivery_attempts')).rows[0].provider,'resend');
 assert.equal((await h.db.query('select delivery_provider from landerware_messages where id=$1',[j.messageId])).rows[0].delivery_provider,'resend');
}));
test('old bridge cannot claim, settle or refresh native observer, and native cannot claim in old lane',()=>fixture(async h=>{
 await paid(h);await h.db.exec('update landerware_checkout_delivery_config set enabled=true');assert.equal((await claim(h)).disabled,true);
 await enable(h);await h.db.exec('update landerware_checkout_delivery_config set last_poll_at=null');assert.equal((await h.rpc('landerware_claim_checkout_confirmation',{p_token:token})).disabled,true);
 assert.equal((await h.db.query('select last_poll_at from landerware_checkout_delivery_config')).rows[0].last_poll_at,null);
 const j=await claim(h);await assert.rejects(h.rpc('landerware_settle_checkout_confirmation',{p_token:token,p_message_id:j.messageId,p_lease:j.lease,p_outcome:'sent',p_provider_id:'old_receipt',p_error:null}),/invalid_delivery_lease/);
 assert.equal((await h.rpc('landerware_checkout_confirmation_health',{p_token:token})).healthy,false);
}));
test('settlement requires exact non-null lease, valid receipt, and replays only the same successful receipt',()=>fixture(async h=>{
 await enable(h);await paid(h);const j=await claim(h);
 await assert.rejects(settle(h,j,{p_lease:null}),/invalid_delivery_lease/);await assert.rejects(settle(h,j,{p_lease:randomUUID()}),/invalid_delivery_lease/);
 await assert.rejects(settle(h,j,{p_provider_id:null}),/provider_receipt_required/);
 await assert.rejects(settle(h,j,{p_provider_id:'injected\nreceipt'}),/provider_receipt_required/);
 assert.equal((await settle(h,j)).settled,true);assert.equal((await settle(h,j)).replay,true);
 await assert.rejects(settle(h,j,{p_provider_id:'another_receipt'}),/delivery_already_settled/);
 const m=(await h.db.query('select * from landerware_messages where id=$1',[j.messageId])).rows[0];assert.equal(m.delivery_status,'sent');assert.ok(m.sent_at);assert.equal(m.provider_message_id,'resend_receipt_123');
}));
test('uncertain provider/settlement remains processing or ambiguous and cannot be reclaimed',()=>fixture(async h=>{
 await enable(h);await paid(h);const j=await claim(h);await h.db.exec("update landerware_checkout_delivery_attempts set claimed_at=now()-interval '1 hour'");
 assert.equal((await claim(h)).empty,true);assert.equal((await h.rpc('native_checkout_confirmation_health',{})).stuck,1);
 await settle(h,j,{p_outcome:'ambiguous',p_provider_id:null,p_error:'transport_unknown'});assert.equal((await claim(h)).empty,true);assert.equal((await h.rpc('native_checkout_confirmation_health',{})).failures,1);
}));
test('only explicit rejection retries with same message identity, new lease, delay and hard cap',()=>fixture(async h=>{
 await enable(h);await paid(h);let j=await claim(h);const id=j.messageId,first=j.lease;
 for(let i=0;i<5;i++){await settle(h,j,{p_outcome:'rejected',p_provider_id:null,p_error:'provider_rejected'});assert.equal((await claim(h)).empty,true);await h.db.exec("update landerware_checkout_delivery_attempts set retry_at=now()-interval '1 second'");if(i<4){j=await claim(h);assert.equal(j.messageId,id);assert.notEqual(j.lease,first);}}
 assert.equal((await claim(h)).empty,true);assert.equal((await h.rpc('native_checkout_confirmation_health',{})).failures,1);
}));
test('payment evidence, canonical registered roster, recipient and cutoff all gate claim',()=>fixture(async h=>{
 await enable(h);const o=await paid(h);const restore=async()=>h.db.query("update landerware_public_orders set payment_evidence=$2 where id=$1",[o.id,JSON.stringify(h.evidence(o))]);
 await h.db.query("update landerware_public_orders set payment_evidence='{}' where id=$1",[o.id]);assert.equal((await claim(h)).empty,true);await restore();
 await h.db.exec("update registrations set status='cancelled'");assert.equal((await claim(h)).empty,true);await h.db.exec("update registrations set status='registered'");
 await h.db.exec("update landerware_checkout_delivery_config set not_before=now()+interval '1 hour'");assert.equal((await claim(h)).empty,true);await h.db.exec("update landerware_checkout_delivery_config set not_before=now()-interval '1 hour'");
 await h.db.exec("update landerware_messages set recipient='wrong@example.test' where template_key='retail-paid-confirmation-v3'");assert.equal((await claim(h)).empty,true);
}));
test('native recovery is order-scoped, eligible only before payment/expiry and never drains old recovery',()=>fixture(async h=>{
 await enable(h);const a=await h.create(),b=await h.create();await h.db.query("update landerware_public_orders set checkout_runtime_version='native-v1' where id=$1",[b.orderId]);
 await h.db.exec("insert into landerware_messages(template_key,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key) select 'retail-checkout-recovery-v2',payer_email,'Recovery','Fixture','gmail','pending','public-order-recovery:'||id from landerware_public_orders");
 const j=await claim(h,b.orderId);assert.ok(j.messageId);assert.equal(j.confirmation.kind,'recovery');assert.match(j.confirmation.recoveryUrl,/\/register\/checkout\/\?recover=/);assert.equal((await claim(h,a.orderId)).empty,true);
 await settle(h,j);await h.db.query("update landerware_public_orders set hold_expires_at=now()-interval '1 hour' where id=$1",[b.orderId]);assert.equal((await claim(h,b.orderId)).empty,true);
}));
test('health reads never fabricate a poll, and disabled or stale lanes are unhealthy',()=>fixture(async h=>{
 await enable(h);let health=await h.rpc('native_checkout_confirmation_health',{});assert.equal(health.healthy,false);assert.equal(health.observerFresh,false);
 assert.equal((await claim(h)).empty,true);health=await h.rpc('native_checkout_confirmation_health',{});assert.equal(health.healthy,true);assert.equal(health.provider,'resend');
 await h.db.exec("update landerware_checkout_delivery_config set last_poll_at=now()-interval '4 minutes'");assert.equal((await h.rpc('native_checkout_confirmation_health',{})).healthy,false);
 await h.db.exec("update landerware_checkout_delivery_config set enabled=false");assert.equal((await h.rpc('native_checkout_confirmation_health',{})).healthy,false);
}));

test('actual native queue to canonical renderer to mock Resend receipt settles once without a second send',()=>fixture(async h=>{
 await enable(h);const o=await paid(h);let requests=0;
 const options={apiKey:'fixture-only',from:'910CPR <brian@910cpr.com>',replyTo:'brian@910cpr.com',request:async(url,req)=>{requests++;assert.equal(url,'https://api.resend.com/emails');const body=JSON.parse(req.body);assert.match(body.subject,/registered/i);assert.match(body.text,/BLS Provider Renewal/);assert.ok(body.html);assert.match(req.headers['idempotency-key'],/^native-checkout-/);return Response.json({id:'receipt_fixture_123'});}};
 const run=()=>dispatchNativeConfirmations({orderId:o.id,claim:a=>h.rpc('native_checkout_claim_confirmation',a),settle:a=>h.rpc('native_checkout_settle_confirmation',a),send:j=>sendNativeCheckoutClaim(j,options)});
 const r=await run();assert.equal(r.accepted,1);assert.equal(r.actualDeliveryConfirmed,false);assert.equal(r.stopped,null);assert.equal(requests,1);
 assert.equal((await run()).accepted,0);assert.equal(requests,1);
 const m=(await h.db.query("select delivery_status,provider_message_id from landerware_messages where template_key='retail-paid-confirmation-v3'")).rows[0];assert.deepEqual(m,{delivery_status:'sent',provider_message_id:'receipt_fixture_123'});
}));

test('legacy bridge cannot retry a Resend attempt after provider switch, including recovery',()=>fixture(async h=>{
 await enable(h);const o=await paid(h),j=await claim(h);await settle(h,j,{p_outcome:'rejected',p_provider_id:null,p_error:'provider_rejected'});
 const a=await h.create();await h.db.query("update landerware_public_orders set checkout_runtime_version='native-v1' where id=$1",[a.orderId]);
 await h.db.query("insert into landerware_messages(template_key,recipient,subject,body_text,delivery_provider,delivery_status,idempotency_key) select 'retail-checkout-recovery-v2',payer_email,'Recovery','Fixture','gmail','pending','public-order-recovery:'||id from landerware_public_orders where id=$1",[a.orderId]);
 const r=await claim(h,a.orderId);assert.equal(r.confirmation.kind,'recovery');await settle(h,r,{p_outcome:'rejected',p_provider_id:null,p_error:'provider_rejected'});
 await h.db.exec("update landerware_checkout_delivery_attempts set retry_at=now()-interval '1 second';update landerware_checkout_delivery_config set provider='cloudflare'");
 assert.equal((await h.rpc('landerware_claim_checkout_confirmation',{p_token:token})).empty,true);
}));
test('existing service role can actually claim and settle with its production-equivalent privileges',()=>fixture(async h=>{
 await enable(h);await paid(h);
 // These privileges already exist on the hosted service role, independently verified.
 await h.db.exec("alter role service_role bypassrls;grant select,update,insert on all tables in schema public to service_role;set role service_role");
 try{const j=await claim(h);assert.ok(j.messageId);assert.equal((await settle(h,j)).settled,true);assert.equal((await h.rpc('native_checkout_confirmation_health',{})).healthy,true);}finally{await h.db.exec('reset role');}
}));
