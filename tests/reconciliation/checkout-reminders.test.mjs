import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {setup} from './native-checkout-harness.mjs';
const token='local-reminder-test-token-only-123456789';
const read=name=>fs.readFileSync(new URL('../../supabase/migrations/'+name,import.meta.url),'utf8');
async function fixture(fn){const h=await setup();try{
 await h.db.exec(`alter table public.landerware_messages add column created_at timestamptz default now(),add column provider_message_id text,add column sent_at timestamptz,add column failed_at timestamptz,add column failure_detail text;`);
 for(const file of ['20261017080000_checkout_confirmation_delivery.sql','20261017200000_message_operational_links.sql','20261017203000_checkout_email_reminders.sql'])await h.db.exec(read(file));
 await h.db.query("update public.landerware_checkout_delivery_config set enabled=true,token_sha256=encode(sha256(convert_to($1,'UTF8')),'hex')",[token]);
 const a=await h.create(),o=await h.bind(a.orderId);await h.finalize(o);
 await h.db.exec("update public.landerware_messages set delivery_status='sent' where template_key='retail-paid-confirmation-v3'");
 const prepare=()=>h.rpc('landerware_prepare_checkout_reminders',{p_token:token});
 const claim=()=>h.rpc('landerware_claim_checkout_confirmation',{p_token:token});
 await fn(h,prepare,claim);
 }finally{await h.db.close()}}
test('one reminder is scheduled 24 hours before class and cannot send early',()=>fixture(async(h,prepare,claim)=>{
 assert.equal((await prepare()).scheduled,1);assert.equal((await prepare()).scheduled,0);assert.equal((await claim()).empty,true);
 assert.equal((await h.rpc('landerware_checkout_confirmation_health',{p_token:token})).queued,0);
 const r=(await h.db.query("select m.scheduled_for=s.start_at-interval '24 hours' as correct from public.landerware_messages m join public.class_sessions s on s.id=$1 where m.template_key='retail-class-reminder-24h-v1'",[h.id])).rows[0];assert.equal(r.correct,true);
}));
test('registration inside the 24-hour window gets no reminder',()=>fixture(async(h,prepare)=>{
 await h.db.exec("update public.class_sessions set start_at=now()+interval '23 hours'");assert.equal((await prepare()).scheduled,0);
}));
test('an eligible due reminder is leased once, with the original confirmation kept separate',()=>fixture(async(h,prepare,claim)=>{
 await h.db.exec("update public.class_sessions set start_at=now()+interval '23 hours';update public.registrations set created_at=now()-interval '2 days'");
 assert.equal((await prepare()).scheduled,1);assert.ok((await claim()).messageId);assert.equal((await claim()).empty,true);
 assert.equal((await h.rpc('landerware_checkout_confirmation_health',{p_token:token})).queued,1);
}));
test('cancellation suppresses an unsent reminder',()=>fixture(async(h,prepare,claim)=>{
 await prepare();await h.db.exec("update public.registrations set status='canceled'");assert.equal((await prepare()).suppressed,1);assert.equal((await claim()).empty,true);
}));
test('rescheduling suppresses the obsolete reminder and creates one for the new time',()=>fixture(async(h,prepare)=>{
 await prepare();await h.db.exec("update public.class_sessions set start_at=now()+interval '3 days'");
 const r=await prepare();assert.equal(r.suppressed,1);assert.equal(r.scheduled,1);
 const rows=(await h.db.query("select count(*) filter(where suppressed_at is null)::int pending,count(*) filter(where suppressed_at is not null)::int suppressed from public.landerware_messages where template_key='retail-class-reminder-24h-v1'")).rows[0];assert.equal(rows.pending,1);assert.equal(rows.suppressed,1);
}));
