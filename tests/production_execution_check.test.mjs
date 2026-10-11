import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
import vm from 'node:vm';
import {executionCheck} from '../supabase/functions/production-board/execution-check.mjs';

const id='00000000-0000-4000-8000-000000000001',version='2026-10-11T20:00:00Z';
const card={id,updated_at:version,lane:'doing'};
for(const resolution_state of ['handled_manually','verified_resolved']) {
  test(`${resolution_state} skips even a stale claimed version`,async()=>{
    const result=await executionCheck(id,'old',async()=>({...card,resolution_state}));
    assert.equal(result.body.decision,'skip');assert.equal(result.body.can_execute,false);
    assert.equal(result.body.reason,'recorded_resolution');
  });
}
for(const lane of ['doing','next','decision','parked']) {
  test(`${lane} never proves failure or authorizes execution`,async()=>{
    const result=await executionCheck(id,version,async()=>({...card,lane,flags:['RESOLVED'],details:'Already handled'}));
    assert.equal(result.body.decision,'review');assert.equal(result.body.can_execute,false);
    assert.equal(result.body.reason,'authoritative_source_check_required');
  });
}
test('missing, stale and unavailable versions fail closed',async()=>{
  for(const [expected,row,status,reason] of [[null,card,428,'expected_version_required'],['old',card,409,'card_changed'],[version,{id},409,'card_version_unavailable']]) {
    const result=await executionCheck(id,expected,async()=>row);
    assert.equal(result.status,status);assert.equal(result.body.reason,reason);assert.equal(result.body.can_execute,false);
  }
});
test('invalid IDs never reach the database; deleted cards skip',async()=>{
  assert.equal((await executionCheck('bad&select=secret',version,()=>assert.fail('no query'))).status,400);
  assert.equal((await executionCheck(id,version,async()=>null)).body.reason,'card_not_found');
});
test('database failures and wrong-card responses cannot expose data or grant execution',async()=>{
  const failed=await executionCheck(id,version,async()=>{throw Error('private secret')});
  assert.equal(failed.status,503);assert.ok(!JSON.stringify(failed).includes('private secret'));
  assert.equal((await executionCheck(id,version,async()=>({...card,id:'wrong'}))).status,503);
});

function service({allow=true,row=card,fail=false}={}) {
  let handler;const calls=[];
  const source=readFileSync(new URL('../supabase/functions/production-board/index.ts',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'');
  const context=vm.createContext({Request,Response,URL,TextEncoder,Uint8Array,crypto,executionCheck,
    authorized:async()=>allow,Deno:{env:{get:name=>name==='SUPABASE_URL'?'https://database.invalid':name==='SUPABASE_SERVICE_ROLE_KEY'?'synthetic':undefined},serve:fn=>handler=fn},
    fetch:async(url,options)=>{calls.push({url,options});assert.equal(options.method,undefined,'read-only request');if(fail)throw Error('private outage');return Response.json(row?[row]:[]);}});
  vm.runInContext(stripTypeScriptTypes(source),context);
  return {calls,request:path=>handler(new Request('https://edge.invalid/production-board/'+path))};
}
test('actual route checks owner authorization before accessing card data',async()=>{
  const s=service({allow:false});assert.equal((await s.request(id+'/execution-check')).status,401);assert.equal(s.calls.length,0);
});
test('actual route reads the exact card once, with no mutations and no-store response',async()=>{
  const s=service();const response=await s.request(id+'/execution-check?expected_updated_at='+encodeURIComponent(version));
  assert.equal(response.status,200);assert.equal((await response.json()).can_execute,false);
  assert.equal(response.headers.get('cache-control'),'no-store');assert.equal(s.calls.length,1);
  const query=new URL(s.calls[0].url);assert.equal(query.searchParams.get('id'),'eq.'+id);assert.equal(query.searchParams.get('limit'),'1');
});
test('actual route fails closed on outages, malformed IDs and unsupported paths',async()=>{
  const s=service({fail:true});const r=await s.request(id+'/execution-check?expected_updated_at='+encodeURIComponent(version));
  assert.equal(r.status,503);assert.ok(!(await r.text()).includes('private outage'));
  const invalid=service();assert.equal((await invalid.request('bad/execution-check')).status,400);assert.equal(invalid.calls.length,0);
  assert.equal((await invalid.request(id+'/execution-check/extra')).status,404);
});
