import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {setup} from './native-checkout-harness.mjs';
const migration=fs.readFileSync(new URL('../../supabase/migrations/20261017080000_checkout_confirmation_delivery.sql',import.meta.url),'utf8');
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
const claim=h=>h.rpc('landerware_claim_checkout_confirmation',{p_token:token});
const settle=(h,j,args={})=>h.rpc('landerware_settle_checkout_confirmation',{p_token:token,p_message_id:j.messageId,p_lease:j.lease,p_outcome:'sent',p_provider_id:'provider-test-id',p_error:null,...args});
test('delivery starts disabled and invalid tokens cannot claim recipient data',()=>fixture(async h=>{
 await paid(h);assert.equal((await claim(h)).disabled,true);
 await assert.rejects(h.rpc('landerware_claim_checkout_confirmation',{p_token:'bad'}),/delivery_unauthorized/);
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
