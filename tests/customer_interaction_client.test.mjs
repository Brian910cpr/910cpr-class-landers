import test from 'node:test';
import assert from 'node:assert/strict';
import {createInteractionClient} from '../docs/admin/customer-interaction-client.mjs';
import {createHandler} from '../supabase/functions/customer-interactions/handler.ts';
function fixture(fetcher,enabled=true){
  let generation=0;const calls=[];
  const auth={get:()=>true,snapshot:()=>generation,current:s=>s===generation,fetch:async(url,options)=>{calls.push({url,options});return fetcher(url,options)}};
  return {client:createInteractionClient(auth,{enabled,uuid:()=> '00000000-0000-4000-8000-000000000001'}),calls,changeSession:()=>generation++};
}
test('flag defaults off and disabled transport never requests private data',async()=>{
  const f=fixture(()=>assert.fail('network'),false);
  assert.throws(()=>f.client.prepare('save',{}),{status:503});
  await assert.rejects(f.client.list(),{status:503});
  assert.throws(()=>createInteractionClient({get:()=>true}).prepare('save',{}),{status:503});
});
test('uncertain network/503/invalid receipt retries preserve exact request and snapshot',async()=>{
  let n=0;const f=fixture(async()=>{n++;if(n===1)throw Error('lost response');if(n===2)return new Response('{}',{status:503});if(n===3)return Response.json({});return Response.json({interaction:{version:1}})});
  const input={document:{notes:'synthetic original'}};const write=f.client.prepare('save',input);input.document.notes='later edit';
  for(let i=0;i<3;i++)await assert.rejects(write.send());
  assert.equal((await write.send()).interaction.version,1);
  assert.equal(new Set(f.calls.map(c=>c.options.body)).size,1);
  assert.equal(JSON.parse(f.calls[0].options.body).input.document.notes,'synthetic original');
  assert.equal(JSON.parse(f.calls[0].options.body).request_id,write.requestId);
  assert.equal(f.calls[0].options.headers['Content-Type'],'application/json');
});
test('double click coalesces; successful receipt is cached and protected from caller edits',async()=>{
  let finish;const f=fixture(()=>new Promise(r=>finish=r));const write=f.client.prepare('save_task',{});
  const first=write.send(),second=write.send();finish(Response.json({task:{version:2}}));
  const result=await first;await second;result.task.version=99;
  assert.equal((await write.send()).task.version,2);assert.equal(f.calls.length,1);
});
test('conflict and invalid writes require reconciliation rather than another write',async()=>{
  for(const status of [400,403,409]){
    const f=fixture(async()=>new Response('{}',{status}));const write=f.client.prepare('resume',{});
    await assert.rejects(write.send(),{status});await assert.rejects(write.send(),{status});assert.equal(f.calls.length,1);
  }
});
test('replacement session cannot retry old request or accept late private receipt',async()=>{
  let finish;const f=fixture(()=>new Promise(r=>finish=r));const write=f.client.prepare('interrupt',{});const send=write.send();
  f.changeSession();finish(Response.json({switch:{previous:{version:2}}}));
  await assert.rejects(send,{reconcile:true});await assert.rejects(write.send(),{reconcile:true});assert.equal(f.calls.length,1);
});
test('reads preserve cursor microseconds, distinguish failure from empty results and reject late session data',async()=>{
  const f=fixture(async()=>Response.json({items:[],next_cursor:null}));
  assert.deepEqual((await f.client.list({collection:'interactions',before:'2026-10-12T12:00:00.123456Z'})).items,[]);
  assert.match(f.calls[0].url,/123456Z/);
  const failed=fixture(async()=>new Response('{}',{status:503}));await assert.rejects(failed.client.list(),{status:503});
  let finish;const late=fixture(()=>new Promise(r=>finish=r));const read=late.client.list();late.changeSession();finish(Response.json({items:[]}));await assert.rejects(read,{status:401});
});
test('transport and real handler retain committed request after lost response, then surface stale conflict',async()=>{
  const receipts=new Map();let version=0,drop=true;
  const handler=createHandler({authorize:async()=>true,actor:async()=> 'synthetic-owner',rest:async(path,options)=>{
    assert.equal(path,'rpc/save_customer_interaction');
    const {p_request_id,p_input}=JSON.parse(options.body);
    if(receipts.has(p_request_id))return receipts.get(p_request_id);
    if(p_input.expected_version!==version)throw Object.assign(Error('stale'),{code:'40001'});
    const saved={...p_input,version:++version};receipts.set(p_request_id,saved);return saved;
  }});
  const f=fixture(async(url,options)=>{
    const response=await handler(new Request(url,{...options,headers:{...options.headers,origin:'https://www.910cpr.com'}}));
    assert.equal(response.headers.get('access-control-allow-origin'),'https://www.910cpr.com');
    if(drop){drop=false;throw Error('response lost after commit')}
    return response;
  });
  const input={id:'00000000-0000-4000-8000-000000000002',case_id:'00000000-0000-4000-8000-000000000003',expected_version:0,kind:'phone',status:'in_progress',source:'manual',source_id:'synthetic-client-test',document:{notes:'synthetic'}};
  const write=f.client.prepare('save',input);await assert.rejects(write.send(),/lost/);
  assert.equal((await write.send()).interaction.version,1);assert.equal(version,1);assert.equal(receipts.size,1);
  // Another browser request ID with an old version must stop for reconciliation.
  const other=createInteractionClient({get:()=>true,snapshot:()=>0,current:()=>true,fetch:async(url,options)=>handler(new Request(url,options))},{enabled:true,uuid:()=> '00000000-0000-4000-8000-000000000004'});
  await assert.rejects(other.prepare('save',input).send(),{status:409,reconcile:true});
});

