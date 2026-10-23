import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {setup} from './native-checkout-harness.mjs';
const token='local-delivery-events-token-only-123456789';
async function fixture(fn){const h=await setup();try{
 await h.db.exec(`alter table public.landerware_messages add column created_at timestamptz default now(),add column provider_message_id text,add column sent_at timestamptz,add column failed_at timestamptz,add column failure_detail text;`);
 for(const file of ['20261017080000_checkout_confirmation_delivery.sql','20261017200000_message_operational_links.sql','20261017203000_checkout_email_reminders.sql','20261017210000_email_delivery_events.sql'])await h.db.exec(fs.readFileSync(new URL('../../supabase/migrations/'+file,import.meta.url),'utf8'));
 await h.db.query("update public.landerware_checkout_delivery_config set token_sha256=encode(sha256(convert_to($1,'UTF8')),'hex')",[token]);
 const a=await h.create(),o=await h.bind(a.orderId);await h.finalize(o);
 const msg=(await h.db.query("select * from public.landerware_messages where template_key='retail-paid-confirmation-v3'")).rows[0];
 const event=(status,id=status,extra={})=>({type:'cf.email.sending.message.'+status,source:{type:'email.sending',domain:'notify.910cpr.com',zoneId:'dafc32f545bccb5fae2ff6f94cec92df'},payload:{eventId:id,messageId:'provider-test',recipient:msg.recipient,delivery:{status},...extra},metadata:{accountId:'9acb24ab8037cc5abe5518f7758455fd',eventTimestamp:new Date().toISOString()}});
 const record=e=>h.rpc('landerware_record_email_delivery_event',{p_token:token,p_event:e});
 const state=async()=>(await h.db.query('select * from public.landerware_message_history where id=$1',[msg.id])).rows[0];
 await fn(h,msg,event,record,state);
 }finally{await h.db.close()}}
test('early delivery events join after provider settlement, with idempotency and recipient checks',()=>fixture(async(h,msg,event,record,state)=>{
 const delivered=event('delivered');await record(delivered);await record(delivered);assert.equal((await state()).effective_status,'pending');
 await h.db.query("update public.landerware_messages set delivery_provider='cloudflare',delivery_status='sent',provider_message_id='<provider-test>' where id=$1",[msg.id]);
 assert.equal((await state()).effective_status,'delivered');assert.equal((await h.db.query('select count(*)::int n from public.landerware_email_delivery_events')).rows[0].n,1);
 await h.db.query('update public.landerware_messages set recipient=$1 where id=$2',['different@example.test',msg.id]);assert.equal((await state()).effective_status,'sent');
}));
test('late intermediate events cannot overwrite delivery; a spam complaint stays visible',()=>fixture(async(h,msg,event,record,state)=>{
 await h.db.query("update public.landerware_messages set delivery_provider='cloudflare',delivery_status='sent',provider_message_id='provider-test' where id=$1",[msg.id]);
 await record(event('delivered'));await record(event('deferred'));assert.equal((await state()).effective_status,'delivered');assert.equal((await state()).provider_failure_detail,null);
 await record(event('complained'));await record(event('delivered','second-delivery'));assert.equal((await state()).effective_status,'complained');
}));
test('untrusted source, wrong token and anonymous history access are rejected',()=>fixture(async(h,msg,event,record)=>{
 const bad=event('bounced');bad.source.domain='other.example';await assert.rejects(record(bad),/invalid_email_event_source/);
 await assert.rejects(h.rpc('landerware_record_email_delivery_event',{p_token:'bad',p_event:event('delivered')}),/delivery_unauthorized/);
 await h.db.exec('set role anon');await assert.rejects(h.db.exec('select * from public.landerware_message_history'),/permission denied/);await h.db.exec('reset role');
}));

test('checkout health rejects a bounced or complained confirmation despite provider acceptance',()=>fixture(async(h,msg,event,record)=>{
 await h.db.exec('update public.landerware_checkout_delivery_config set enabled=true');
 const job=await h.rpc('landerware_claim_checkout_confirmation',{p_token:token});assert.equal(job.messageId,msg.id);
 await h.rpc('landerware_settle_checkout_confirmation',{p_token:token,p_message_id:msg.id,p_lease:job.lease,p_outcome:'sent',p_provider_id:'provider-test',p_error:null});
 const health=()=>h.rpc('landerware_checkout_confirmation_health',{p_token:token});
 await record(event('bounced'));assert.equal((await health()).healthy,false);assert.equal((await health()).deliveryFailures,1);
 await record(event('delivered','later-delivery'));assert.equal((await health()).deliveryFailures,0);
 await record(event('complained'));assert.equal((await health()).healthy,false);assert.equal((await health()).deliveryFailures,1);
 assert.equal((await h.rpc('landerware_claim_checkout_confirmation',{p_token:token})).empty,true);
}));

test('checkout health flags overdue missing delivery receipts and recovers only on matching evidence',()=>fixture(async(h,msg,event,record)=>{
 await h.db.exec('update public.landerware_checkout_delivery_config set enabled=true');
 const job=await h.rpc('landerware_claim_checkout_confirmation',{p_token:token});
 await h.rpc('landerware_settle_checkout_confirmation',{p_token:token,p_message_id:msg.id,p_lease:job.lease,p_outcome:'sent',p_provider_id:'provider-test',p_error:null});
 await h.db.query("update public.landerware_messages set sent_at=now()-interval '11 minutes' where id=$1",[msg.id]);
 const health=()=>h.rpc('landerware_checkout_confirmation_health',{p_token:token});
 assert.equal((await health()).healthy,false);assert.equal((await health()).deliveryUnconfirmed,1);
 const unrelated=event('delivered','wrong-recipient');unrelated.payload.recipient='other@example.test';await record(unrelated);
 assert.equal((await health()).deliveryUnconfirmed,1);
 await record(event('delivered'));assert.equal((await health()).deliveryUnconfirmed,0);assert.equal((await health()).healthy,true);
 await h.db.exec('set role anon');await assert.rejects(h.rpc('landerware_checkout_confirmation_health',{p_token:'bad'}),/delivery_unauthorized/);await h.db.exec('reset role');
}));
