import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {stripTypeScriptTypes} from 'node:module';
import {publishIntake} from '../supabase/functions/production-board/publish-intake.mjs';
const id='00000000-0000-4000-8000-000000000001';
const body={issue_id:380,expected_version:'1',request_id:id,blocked:true,source_state:'unknown',
 worker_safe:false,source_ref:'synthetic owner declaration',checked_at:'2026-10-13T00:00:00.000Z'};
const ack={request_id:id,version:'2',replayed:false,can_execute:false};
test('publisher maps typed declaration; commit acknowledgement allowlists output',async()=>{
 const r=await publishIntake(id,body,p=>{assert.equal(p.p_card,id);assert.equal(p.p_blocked,true);
   assert.equal(p.p_checked_at,body.checked_at);return {...ack,private_data:'must not echo'};});
 assert.equal(r.body.committed,true);assert.equal(r.body.provenance,'owner_assertion_not_source_verification');
 assert.equal(r.body.can_execute,false);assert.equal(r.body.private_data,undefined);
});
test('publisher rejects malformed inputs and client actor/permission before RPC',async()=>{
 for(const change of [{actor:'Brian'},{can_execute:true},{blocked:'false'},{worker_safe:1},
  {source_state:'verified'},{source_ref:''},{checked_at:'2026-02-30T00:00:00.000Z'},
  {checked_at:'tomorrow'},{expected_version:1},{issue_id:0},{request_id:'bad'}]){
  assert.equal((await publishIntake(id,{...body,...change},()=>{throw Error('must not call');})).status,400);
 }
});
test('publisher waits for acknowledgement and handles uncertain outcomes privately',async()=>{
 let finish;const pending=publishIntake(id,body,()=>new Promise(r=>finish=r));
 finish(ack);assert.equal((await pending).body.committed,true);
 for(const rpc of [()=>{throw Error('private SQL detail');},()=>null,()=>({...ack,can_execute:true}),()=>({...ack,request_id:'wrong'})]){
  const r=await publishIntake(id,body,rpc);assert.equal(r.status,503);assert.equal(r.body.committed,false);
  assert.equal(r.body.can_execute,false);assert.ok(!JSON.stringify(r).includes('private SQL'));
 }
});
function service(allow,fail=false){
 let handler;const calls=[];
 const source=fs.readFileSync(new URL('../supabase/functions/production-board/index.ts',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'');
 const context=vm.createContext({Request,Response,URL,AbortSignal,TextEncoder,Uint8Array,crypto,publishIntake,
 authorized:async()=>allow,Deno:{env:{get:k=>k==='SUPABASE_URL'?'https://database.invalid':k==='SUPABASE_SERVICE_ROLE_KEY'?'fixture-secret':undefined},serve:fn=>handler=fn},
 fetch:async(url,options)=>{calls.push({url,options});if(fail)throw Error('private outage');return Response.json(ack);}});
 vm.runInContext(stripTypeScriptTypes(source),context);
 return {calls,request:()=>handler(new Request('https://edge.invalid/production-board/'+id+'/dispatch-intake',
 {method:'POST',body:JSON.stringify(body)}))};
}
test('actual publisher route authenticates before database access',async()=>{
 const s=service(false);assert.equal((await s.request()).status,401);assert.equal(s.calls.length,0);
});
test('actual route uses one server-authenticated transaction and no-store',async()=>{
 const s=service(true);const r=await s.request();assert.equal(r.status,200);assert.equal((await r.json()).committed,true);
 assert.equal(r.headers.get('cache-control'),'no-store');assert.equal(s.calls.length,1);
 assert.equal(s.calls[0].url,'https://database.invalid/rest/v1/rpc/production_board_publish_intake');
 assert.equal(s.calls[0].options.headers.authorization,'Bearer fixture-secret');
});
test('actual route cannot confirm transport failure',async()=>{
 const r=await service(true,true).request();assert.equal(r.status,503);assert.equal((await r.json()).committed,false);
});

test('known transaction conflicts give clear errors without claiming commit',async()=>{
 for(const reason of ['stale_card_version','card_resolved','intake_issue_immutable','idempotency_conflict','source_check_stale']){
  const r=await publishIntake(id,body,()=>{throw Error(reason);});
  assert.equal(r.status,409);assert.equal(r.body.error,reason);assert.equal(r.body.committed,false);
 }
});
