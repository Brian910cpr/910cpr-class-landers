import test from 'node:test';
import assert from 'node:assert/strict';
import {readCanonicalGitHubSource} from '../ops/operator/read-canonical-github-source.mjs';
const card='12345678-1234-1234-1234-123456789abc';
const binding=()=>({decision:'review',reason:'underlying_source_check_required',can_execute:false,
  card_id:card,issue_id:380,version:'2',source_ref:'https://github.com/Brian910cpr/910cpr-class-landers/issues/380'});
const issue=()=>({number:380,id:123,node_id:'I_test',state:'closed',updated_at:'2026-10-14T11:00:00Z',
  html_url:binding().source_ref,url:'https://api.github.com/repos/Brian910cpr/910cpr-class-landers/issues/380',body:'SECRET'});
function adapter(rows=[binding(),binding()]) {
  const calls=[];
  return {calls,execute:async(command,args,options)=>{
    calls.push({command,args,options});
    return {stdout:JSON.stringify(command==='psql'?rows.shift():issue())};
  }};
}
test('explicit service read-only binding, GH GET, then canonical recheck; never publishes',async()=>{
  const a=adapter();const result=await readCanonicalGitHubSource(card,'collector_local',a);
  assert.deepEqual(a.calls.map(c=>c.command),['psql','gh','psql']);
  for(const c of a.calls.filter(c=>c.command==='psql')) {
    assert.deepEqual(c.args.slice(0,3),['--dbname','service=collector_local','-X']);
    assert.ok(c.args.includes('--no-password'));assert.ok(c.args.includes('ON_ERROR_STOP=1'));
    assert.match(c.args.at(-1),/^begin read only; set local role production_board_collector;/);
    assert.equal(c.options.timeout,5000);assert.equal(c.options.maxBuffer,16384);assert.equal(c.options.windowsHide,true);
  }
  assert.equal(result.source_kind,'github_issue_lifecycle');assert.equal(result.source_state,'unknown');
  assert.equal(result.can_execute,false);assert.equal(result.worker_safe,false);
  assert.ok(!JSON.stringify(result).includes('SECRET'));
});
test('invalid card/service prevents all subprocesses',async()=>{
  for(const [id,service] of [['bad','collector'],[card,''],[card,'host=evil'],[card,'x;select'],[card,'a'.repeat(65)]]) {
    const a=adapter();assert.equal((await readCanonicalGitHubSource(id,service,a)).can_execute,false);assert.equal(a.calls.length,0);
  }
});
test('resolved card skips before GH read and after concurrent resolution',async()=>{
  const resolved={decision:'skip',reason:'card_resolved',can_execute:false,private:'SECRET'};
  for(const rows of [[resolved],[binding(),resolved]]) {
    const expectedCalls=rows.length===1?1:3;const a=adapter(rows);assert.deepEqual(await readCanonicalGitHubSource(card,'collector',a),
      {decision:'skip',reason:'card_resolved',can_execute:false});
    assert.equal(a.calls.length,expectedCalls);
  }
});
test('missing, malformed and identity-swapped DB response cannot acquire source',async()=>{
  for(const row of [null,{}, {...binding(),can_execute:true},{...binding(),card_id:'other'},
    {decision:'review',reason:'canonical_binding_missing',can_execute:false}]) {
    const a=adapter([row]);const r=await readCanonicalGitHubSource(card,'collector',a);
    assert.equal(r.can_execute,false);assert.equal(a.calls.length,1);
  }
});
test('every canonical drift discards acquired source',async()=>{
  for(const patch of [{version:'3'},{issue_id:371},{source_ref:'other'},{card_id:'other'},
    {decision:'review',reason:'canonical_binding_missing'},{can_execute:true}]) {
    const a=adapter([binding(),{...binding(),...patch}]);const r=await readCanonicalGitHubSource(card,'collector',a);
    assert.equal(r.reason,'canonical_binding_changed');assert.equal(r.source_id,undefined);
  }
});
test('DB/auth/JSON/recheck errors suppress diagnostics and never grant execution',async()=>{
  for(const failAt of [1,2,3]) {
    let calls=0;const a=adapter();const execute=async(...args)=>{
      if(++calls===failAt) throw new Error('SECRET credentials');return a.execute(...args);
    };
    const r=await readCanonicalGitHubSource(card,'collector',{execute});
    assert.equal(r.can_execute,false);assert.ok(!JSON.stringify(r).includes('SECRET'));assert.equal(r.source_id,undefined);
  }
  assert.equal((await readCanonicalGitHubSource(card,'collector',{execute:async()=>({stdout:'SECRET'})})).reason,
    'canonical_source_acquisition_failed');
});

