import test from 'node:test';
import assert from 'node:assert/strict';
import {createInteractionClient} from '../docs/admin/customer-interaction-client.mjs';
import {createInteractionSwitch,findInteractionInterruption} from '../docs/admin/customer-interaction-switch.mjs';
const input=()=>({previous:{id:'previous',case_id:'case1',expected_version:1,status:'paused',document:{notes:'retained',nested:{b:2,a:1}}},active:{id:'active',case_id:'case2',expected_version:0,status:'in_progress'}});
function fixture(respond){
 const calls=[];const client=createInteractionClient({get:()=>true,snapshot:()=>0,current:()=>true,fetch:async(url,options)=>{const body=JSON.parse(options.body);calls.push(body);return respond(body)}},{enabled:true,uuid:()=> 'request'});
 return {calls,client};
}
const receipt=body=>({switch:{operation:body.operation,request_id:body.request_id,...Object.fromEntries(['previous','active'].map(k=>[k,{...body.input[k],version:body.input[k].expected_version+1}]))}});
test('atomic switch retains both immutable drafts across loss and coalesces retries',async()=>{
 let finish;const f=fixture(()=>new Promise(r=>finish=r));const source=input();
 const pending=createInteractionSwitch(f.client,'interrupt',source);source.previous.status='resolved';
 const a=pending.send(),b=pending.send();finish(new Response('{}',{status:503}));
 await assert.rejects(a);await assert.rejects(b);assert.equal(f.calls.length,1);assert.equal(pending.view().state,'error');
 const retry=pending.send();finish(Response.json(receipt(f.calls[0])));const result=await retry;
 assert.deepEqual(f.calls[0],f.calls[1]);assert.equal(result.previous.status,'paused');
 result.previous.status='external';assert.equal((await pending.send()).previous.status,'paused');
 assert.equal(pending.view().state,'saved');
});
test('wrong pair/version/operation/request/status switch receipts never poison identical retry',async()=>{
 const mutations=[r=>r.switch.previous.id='wrong',r=>r.switch.active.case_id='wrong',r=>r.switch.active.version=0,r=>r.switch.previous.version='2',r=>r.switch.request_id='other',r=>r.switch.operation='resume',r=>r.switch.previous.status='resolved',r=>r.switch.previous.document={},r=>r.switch.active.person_id='wrong-person'];
 for(const mutate of mutations){
  let attempt=0;const f=fixture(async body=>{const data=receipt(body);if(++attempt===1)mutate(data);return Response.json(data)});
  const pending=createInteractionSwitch(f.client,'interrupt',input());await assert.rejects(pending.send(),/atomic switch receipt/);
  assert.equal(pending.view().state,'error');await pending.send();assert.deepEqual(f.calls[0],f.calls[1]);
 }
});
test('atomic conflicts retain both drafts and never create a replacement transaction',async()=>{
 const f=fixture(async()=>new Response('{}',{status:409}));const pending=createInteractionSwitch(f.client,'resume',input());
 await assert.rejects(pending.send(),{status:409});await assert.rejects(pending.send(),{status:409});
 assert.equal(pending.view().state,'conflict');assert.deepEqual(pending.view().input,input());assert.equal(f.calls.length,1);
});
test('recovery follows older pages by immutable IDs and rejects incomplete cursor loops',async()=>{
 const calls=[];const event={request_id:'older',input:{operation:'interrupt',active:{id:'active'}}};
 const cursor={before:'2026-10-13T00:00:00.123456Z',before_id:'older-id'};
 const client={list:async query=>{calls.push(query);return calls.length===1?{items:[{input:{operation:'resume',active:{id:'active'}}}],next_cursor:cursor}:{items:[event],next_cursor:null}}};
 assert.equal((await findInteractionInterruption(client,'active')).request_id,'older');assert.deepEqual(calls[1],{collection:'interruptions',...cursor});
 assert.equal(await findInteractionInterruption({list:async()=>({items:[],next_cursor:null})},'missing'),null);
 await assert.rejects(findInteractionInterruption({list:async()=>({items:[],next_cursor:cursor})},'missing'),/Repeated/);
});
