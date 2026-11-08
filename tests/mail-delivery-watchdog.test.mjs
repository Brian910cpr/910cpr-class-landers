import test from 'node:test';
import assert from 'node:assert/strict';
import {checkMailDelivery,mailHealth,MAIL_WORKFLOW,MAIL_STATE_KEY} from '../worker/mail-delivery-watchdog.mjs';
const now=Date.parse('2026-11-07T12:00:00Z'),iso=m=>new Date(now+m*60000).toISOString();
function setup({runs=[],previous={},token='synthetic-token',fail,status=204}={}){
 const calls=[],writes=[];let saved=previous;
 const env={GITHUB_ACTIONS_TOKEN:token,STATE:{get:async key=>{assert.equal(key,MAIL_STATE_KEY);return saved;},put:async(key,value)=>{assert.equal(key,MAIL_STATE_KEY);saved=JSON.parse(value);writes.push(saved);}}};
 const request=async(url,options)=>{calls.push({url,options});if(fail==='network')throw Error('upstream secret');if(url.includes('/runs?'))return fail==='auth'?new Response('private text',{status:401}):Response.json({workflow_runs:runs});if(fail==='uncertain')throw Error('private timeout');return new Response(null,{status});};
 return {calls,writes,saved:()=>saved,run:()=>checkMailDelivery(env,{now,request})};
}
test('dispatches only existing mail workflow with main ref and existing token',async()=>{
 const t=setup();const s=await t.run();assert.equal(s.action,'delivery_dispatched');assert.equal(t.calls.length,2);
 assert.equal(t.calls[1].url,MAIL_WORKFLOW+'/dispatches');assert.deepEqual(JSON.parse(t.calls[1].options.body),{ref:'main'});
 assert.equal(t.writes[0].action,'dispatch_attempt');assert.equal(mailHealth(s,now).ok,false,'dispatch is not a completed-run proof');
});
test('active and stalled jobs are observed without duplicate dispatch',async()=>{
 for(const age of [-2,-16]){const t=setup({runs:[{id:1,status:'in_progress',created_at:iso(age)}]});const s=await t.run();assert.equal(t.calls.length,1);assert.equal(s.action,'delivery_running');assert.equal(s.error,age===-16?'mail_delivery_stalled':undefined);}
});
test('recent successful job and uncertain-attempt cooldown avoid duplicates',async()=>{
 const t=setup({runs:[{id:2,status:'completed',conclusion:'success',updated_at:iso(-1)}]});const s=await t.run();assert.equal(s.action,'recent_delivery_run');assert.equal(mailHealth(s,now).ok,true);
 const u=setup({previous:{lastDispatchAttemptAt:iso(-1)}});assert.equal((await u.run()).action,'dispatch_cooldown');assert.equal(u.calls.length,1);
 const v=setup({fail:'uncertain'});assert.equal((await v.run()).error,'mail_check_failed');assert.equal(v.saved().lastDispatchAttemptAt,iso(0));
});
test('credentials and arbitrary provider text never reach state; denied auth is not retried',async()=>{
 for(const config of [{token:''},{fail:'auth'},{fail:'network'},{status:403}]){const t=setup(config),s=await t.run();assert.ok(s.error);assert.ok(!JSON.stringify(s).includes('private'));assert.ok(!JSON.stringify(s).includes('synthetic-token'));assert.ok(t.calls.length<=2);}
});
test('observer and mail-run staleness are separate, explicit failures',()=>{
 assert.equal(mailHealth({checkedAt:iso(0),lastSuccessAt:iso(-21)},now).deliveryRunStale,true);
 assert.equal(mailHealth({checkedAt:iso(-13),lastSuccessAt:iso(-1)},now).heartbeatStale,true);
 assert.equal(mailHealth(null,now).ok,false);
});
