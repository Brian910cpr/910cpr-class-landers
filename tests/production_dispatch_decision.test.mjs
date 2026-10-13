import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {stripTypeScriptTypes} from 'node:module';
import {dispatchDecision} from '../supabase/functions/production-board/dispatch-decision.mjs';
const id='00000000-0000-4000-8000-000000000001';
const body={issue_id:380,expected_version:'2',request_id:id,phase:'selection'};
test('gateway binds RPC parameters and waits for commit acknowledgement', async()=>{
  let complete;
  const pending=dispatchDecision(id,body,params=>{
    assert.deepEqual(params,{p_card:id,p_issue:380,p_version:'2',p_request:id,p_phase:'selection',p_reservation:null});
    return new Promise(resolve=>{complete=resolve;});
  });
  complete({request_id:id,decision:'reserved',reason:'runtime_fence_required',version:'2',replayed:false,can_execute:false});
  assert.deepEqual((await pending).body.committed,true);
});
test('client cannot forge canonical intake, actor or permission',async()=>{
  for(const extra of [{blocked:false},{worker_safe:true},{actor:'Brian'},{can_execute:true},{source_state:'action_required'}]){
    assert.equal((await dispatchDecision(id,{...body,...extra},()=>{throw Error('must not call');})).status,400);
  }
});
test('invalid identities/version/phase/reservation rejected before RPC',async()=>{
  for(const change of [{issue_id:0},{expected_version:2},{expected_version:'-1'},{request_id:'bad'},
      {phase:'launch'},{phase:'pre_side_effect'},{reservation_id:id}]){
    assert.equal((await dispatchDecision(id,{...body,...change},()=>{throw Error('must not call');})).status,400);
  }
});
test('transport failure or malformed acknowledgement never confirms commit or permission',async()=>{
  for(const rpc of [()=>{throw Error('private database detail');},()=>null,
    ()=>({request_id:id,can_execute:true}),()=>({request_id:'wrong',can_execute:false})]){
    const r=await dispatchDecision(id,body,rpc);
    assert.equal(r.status,503);assert.equal(r.body.committed,false);assert.equal(r.body.can_execute,false);
    assert.ok(!JSON.stringify(r).includes('private database'));
  }
});
test('route is behind owner authentication and calls only the transactional RPC',()=>{
  const source=fs.readFileSync(new URL('../supabase/functions/production-board/index.ts',import.meta.url),'utf8');
  assert.ok(source.indexOf('await authorized(req)')<source.indexOf('route[1]==="dispatch-decision"'));
  assert.ok(source.includes('rpc/production_board_dispatch_decide'));
  assert.ok(source.includes('signal:AbortSignal.timeout(10000)'));
});

function service(allow=true, fail=false) {
  let handler; const calls=[];
  const source=fs.readFileSync(new URL('../supabase/functions/production-board/index.ts',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'');
  const context=vm.createContext({Request,Response,URL,AbortSignal,TextEncoder,Uint8Array,crypto,dispatchDecision,
    authorized:async()=>allow,Deno:{env:{get:key=>key==='SUPABASE_URL'?'https://database.invalid':key==='SUPABASE_SERVICE_ROLE_KEY'?'fixture-secret':undefined},serve:fn=>handler=fn},
    fetch:async(url,options)=>{calls.push({url,options});if(fail)throw Error('private outage');
      return Response.json({request_id:id,decision:'skip',reason:'recorded_resolution',version:'3',replayed:false,can_execute:false});}});
  vm.runInContext(stripTypeScriptTypes(source),context);
  return {calls,request:()=>handler(new Request('https://edge.invalid/production-board/'+id+'/dispatch-decision',
    {method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)}))};
}
test('actual POST route denies unauthenticated requests before RPC',async()=>{
  const s=service(false);assert.equal((await s.request()).status,401);assert.equal(s.calls.length,0);
});
test('actual POST route makes one server-authenticated RPC and returns committed skip',async()=>{
  const s=service();const response=await s.request();assert.equal(response.status,200);
  const result=await response.json();assert.equal(result.committed,true);assert.equal(result.can_execute,false);
  assert.equal(result.decision,'skip');assert.equal(response.headers.get('cache-control'),'no-store');
  assert.equal(s.calls.length,1);assert.equal(s.calls[0].url,'https://database.invalid/rest/v1/rpc/production_board_dispatch_decide');
  assert.equal(s.calls[0].options.headers.authorization,'Bearer fixture-secret');
  assert.equal(JSON.parse(s.calls[0].options.body).p_card,id);
});
test('actual POST route hides outage details and cannot acknowledge uncertain commit',async()=>{
  const response=await service(true,true).request();assert.equal(response.status,503);
  const result=await response.json();assert.equal(result.committed,false);assert.equal(result.can_execute,false);
  assert.ok(!JSON.stringify(result).includes('private outage'));
});
