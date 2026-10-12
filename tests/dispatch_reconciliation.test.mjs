import test from 'node:test';
import assert from 'node:assert/strict';
import {reconcileDispatch, rankDispatchCandidates} from '../supabase/functions/production-board/dispatch-reconciliation.mjs';
const base = {authoritative:true, version:'v1', resolution_state:'unresolved', blocked:false, source_state:'action_required', worker_safe:true};
for (const phase of ['selection', 'pre_side_effect']) {
  test(`${phase}: blocked #297 is suppressed while #371 and new P0 remain eligible`, () => {
    const entries = [
      {id:297, priority:'P1', state:{...base, blocked:true}},
      {id:371, priority:'P1', state:base},
      {id:900, priority:'P0', state:base},
    ].map(c => ({...c, expectedVersion:'v1', check:reconcileDispatch(c.state,'v1',phase)}));
    assert.equal(entries[0].check.reason,'blocked_requires_explicit_reconciliation');
    assert.deepEqual(rankDispatchCandidates(entries,371).map(c=>c.id),[900,371]);
    assert.ok(entries.every(c=>c.check.can_execute === false));
  });
  test(`${phase}: unchanged or changed signature never silently clears blocker`, () => {
    for (const source_signature of ['old','new']) assert.equal(reconcileDispatch({...base,blocked:true,source_signature},'v1',phase).decision,'skip');
  });
  test(`${phase}: unavailable, ambiguous, stale and non opted-in states fail closed`, () => {
    for (const state of [null, {...base,authoritative:false}, {...base,version:'v2'}, {...base,blocked:null}, {...base,worker_safe:false}, {...base,source_state:'unknown'}, {...base,resolution_state:null}]) {
      const check=reconcileDispatch(state,'v1',phase);
      assert.equal(check.decision,'review'); assert.equal(check.can_execute,false);
    }
  });
}
test('owner resolves after selection: fresh pre-side-effect snapshot stops worker', () => {
  assert.equal(reconcileDispatch(base,'v1','selection').decision,'candidate');
  const check=reconcileDispatch({...base,version:'v2',resolution_state:'handled_manually'},'v1','pre_side_effect');
  assert.equal(check.decision,'skip'); assert.equal(check.reason,'recorded_resolution');
});
test('external fix proposes verification without silently resolving or executing', () => {
  assert.equal(reconcileDispatch({...base,source_state:'already_corrected'},'v1','selection').reason,'propose_verified_resolved');
});
test('invalid phase and missing version cannot become candidates', () => {
  assert.equal(reconcileDispatch(base,'v1','launch').decision,'review');
  assert.equal(reconcileDispatch({...base,version:''},'','selection').decision,'review');
});

const candidate = (id, priority = 'P1', state = base) => ({id, priority, state, expectedVersion:'v1', check:{decision:'candidate'}});
test('ranking rejects cached candidate checks after resolution, blocker or version change', () => {
  const entries = [candidate(297,'P0',{...base,blocked:true}),
    candidate(380,'P0',{...base,resolution_state:'handled_manually'}),
    candidate(900,'P0',{...base,version:'v2'}), candidate(371)];
  assert.deepEqual(rankDispatchCandidates(entries,371).map(c=>c.id),[371]);
});
test('ranking requires a snapshot and expected version even with forged candidate check', () => {
  assert.deepEqual(rankDispatchCandidates([{id:297,priority:'P0',check:{decision:'candidate'}}],297),[]);
  assert.deepEqual(rankDispatchCandidates([{...candidate(371),expectedVersion:undefined}],371),[]);
});
test('ranking rejects ambiguous identities and malformed priorities', () => {
  const entries = [candidate(297),candidate(297,'P0'),candidate('371'),candidate(-1),
    candidate(0),candidate(1.5),candidate(900,'urgent'),null,candidate(371)];
  assert.deepEqual(rankDispatchCandidates(entries,371).map(c=>c.id),[371]);
  assert.deepEqual(rankDispatchCandidates(null,371),[]);
});
test('ranking keeps P0 ahead of owner priority and stable ties without mutating inputs', () => {
  const entries = [candidate(12,'P2'),candidate(371),candidate(901,'P0'),candidate(902,'P0'),candidate(13,'P3')];
  const before=structuredClone(entries);
  assert.deepEqual(rankDispatchCandidates(entries,371).map(c=>c.id),[901,902,371,12,13]);
  assert.deepEqual(entries,before);
});
