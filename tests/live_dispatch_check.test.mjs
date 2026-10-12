import test from 'node:test';
import assert from 'node:assert/strict';
import {checkLiveDispatch} from '../supabase/functions/production-board/live-dispatch-check.mjs';
const base = {issue_id:297, authoritative:true, version:'v1', resolution_state:'unresolved', blocked:false, source_state:'action_required', worker_safe:true};
const request = {issue_id:297, expectedVersion:'v1', phase:'selection'};

for (const phase of ['selection','pre_side_effect']) {
  test(`${phase}: fresh blocked #297 never becomes executable; decision is persisted`, async () => {
    const events=[];
    const result=await checkLiveDispatch({...request,phase},{readSnapshot:async id=>({...base,issue_id:id,blocked:true}),recordDecision:async event=>{events.push(event);return true;}});
    assert.equal(result.reason,'blocked_requires_explicit_reconciliation');
    assert.equal(result.can_execute,false);
    assert.equal(events.length,1); assert.equal(events[0].phase,phase);
  });
}
test('owner resolution between selection and mutation requires another live read', async () => {
  let reads=0; const events=[];
  const adapter={readSnapshot:async()=>++reads===1?base:{...base,version:'v2',resolution_state:'handled_manually'},recordDecision:async e=>{events.push(e);return true;}};
  assert.equal((await checkLiveDispatch(request,adapter)).decision,'candidate');
  const result=await checkLiveDispatch({...request,phase:'pre_side_effect'},adapter);
  assert.equal(result.reason,'recorded_resolution'); assert.equal(result.can_execute,false);
  assert.equal(reads,2); assert.equal(events[1].observed_version,'v2');
});
test('stale version, wrong identity, missing state and read failure fail closed', async () => {
  for (const [readSnapshot,reason] of [
    [async()=>({...base,version:'v2'}),'version_changed_or_missing'],
    [async()=>({...base,issue_id:371}),'canonical_identity_mismatch'],
    [async()=>null,'canonical_identity_mismatch'],
    [async()=>{throw new Error('private failure');},'canonical_read_failed']]) {
    const events=[];
    const result=await checkLiveDispatch(request,{readSnapshot,recordDecision:async e=>{events.push(e);return true;}});
    assert.equal(result.reason,reason); assert.equal(result.can_execute,false);
    assert.equal(events.length,1);
  }
});
test('missing or failed durable acknowledgement cannot return candidate or successful skip', async () => {
  for (const blocked of [false,true]) for (const recordDecision of [async()=>false,async()=>undefined,async()=>{throw Error('private');}]) {
    const result=await checkLiveDispatch(request,{readSnapshot:async()=>({...base,blocked}),recordDecision});
    assert.equal(result.reason,'decision_not_persisted'); assert.equal(result.can_execute,false);
  }
});
test('invalid request or missing adapters performs no read', async () => {
  let reads=0; const adapter={readSnapshot:async()=>{reads++;return base;},recordDecision:async()=>true};
  for (const bad of [null,{...request,issue_id:'297'},{...request,expectedVersion:''},{...request,phase:'launch'}]) assert.equal((await checkLiveDispatch(bad,adapter)).reason,'invalid_request');
  assert.equal((await checkLiveDispatch(request,{readSnapshot:adapter.readSnapshot})).reason,'adapter_required');
  assert.equal(reads,0);
});
test('audit envelope excludes private evidence and input cannot gain permission', async () => {
  let event;
  const result=await checkLiveDispatch(request,{readSnapshot:async()=>({...base,evidence:'secret',can_execute:true}),recordDecision:async e=>{event=e;return true;}});
  assert.equal(result.can_execute,false); assert.equal(Object.isFrozen(event),true);
  assert.deepEqual(Object.keys(event),['issue_id','phase','expected_version','observed_version','decision','reason','can_execute']);
  assert.equal(JSON.stringify(event).includes('secret'),false);
});
