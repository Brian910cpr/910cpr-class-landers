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

for (const phase of ['selection','pre_side_effect']) test(`${phase}: snapshot changed while persisting decision cannot return a stale candidate`, async () => {
  for (const mutation of [
    state => { state.resolution_state='handled_manually'; },
    state => { state.version='v2'; },
    state => { state.blocked=true; },
    state => { state.issue_id=371; },
    state => { state.source_state='already_corrected'; },
    state => { state.worker_safe=false; },
    state => { state.authoritative=false; }
  ]) {
    const state={...base}; const events=[];
    const result=await checkLiveDispatch({...request,phase},{
      readSnapshot:async()=>state,
      recordDecision:async event=>{ events.push(event); mutation(state); return true; }
    });
    assert.equal(result.decision,'review');
    assert.equal(result.reason,'canonical_snapshot_changed_during_persistence');
    assert.equal(result.can_execute,false);
    assert.equal(events.length,1);
  }
});

for (const phase of ['selection','pre_side_effect']) {
  test(`${phase}: hung canonical read aborts and durably records a closed decision`, async () => {
    let signal; const events=[];
    const result=await checkLiveDispatch({...request,phase},{timeoutMs:10,
      readSnapshot:(_id,options)=>{signal=options.signal;return new Promise(()=>{});},
      recordDecision:async event=>{events.push(event);return true;}
    });
    assert.equal(signal.aborted,true);
    assert.equal(result.reason,'canonical_read_failed');
    assert.equal(result.can_execute,false);
    assert.equal(events.length,1);
    assert.equal(events[0].decision,'review');
    assert.equal(events[0].observed_version,null);
  });
  test(`${phase}: late persistence acknowledgement cannot revive a timed-out candidate`, async () => {
    let signal; let acknowledge;
    const pending=checkLiveDispatch({...request,phase},{timeoutMs:10,
      readSnapshot:async()=>({...base}),
      recordDecision:(_event,options)=>{signal=options.signal;return new Promise(resolve=>{acknowledge=resolve;});}
    });
    const result=await pending;
    assert.equal(signal.aborted,true);
    assert.equal(result.reason,'decision_not_persisted');
    assert.equal(result.can_execute,false);
    acknowledge(true);
    await Promise.resolve();
    assert.equal(result.decision,'review');
  });
}
test('invalid deadlines fail before adapter side effects', async () => {
  let calls=0;
  for (const timeoutMs of [0,-1,1.5,30001,Infinity,NaN,'10',null]) {
    const result=await checkLiveDispatch(request,{timeoutMs,
      readSnapshot:async()=>{calls++;return base;},recordDecision:async()=>{calls++;return true;}});
    assert.equal(result.reason,'invalid_adapter_deadline');
  }
  assert.equal(calls,0);
});

for (const phase of ['selection','pre_side_effect']) {
  test(`${phase}: throwing canonical version getter produces a persisted closed decision`, async () => {
    const state={...base}; const events=[];
    Object.defineProperty(state,'version',{get(){throw Error('private getter failure');}});
    const result=await checkLiveDispatch({...request,phase},{
      readSnapshot:async()=>state, recordDecision:async event=>{events.push(event);return true;}
    });
    assert.equal(result.reason,'canonical_read_failed');
    assert.equal(result.can_execute,false);
    assert.equal(events.length,1);
    assert.equal(events[0].observed_version,null);
    assert.equal(JSON.stringify(events).includes('private'),false);
  });
  test(`${phase}: unreadable shared snapshot after persistence fails closed`, async () => {
    const state={...base};
    const result=await checkLiveDispatch({...request,phase},{
      readSnapshot:async()=>state,
      recordDecision:async()=>{
        Object.defineProperty(state,'blocked',{get(){throw Error('private drift failure');}});
        return true;
      }
    });
    assert.equal(result.reason,'canonical_snapshot_changed_during_persistence');
    assert.equal(result.can_execute,false);
  });
}
