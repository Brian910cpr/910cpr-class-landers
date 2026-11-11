import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {ENDPOINT, assessNativeQueue, assessMonitorState, checkNativeConfirmations} from '../worker/native-confirmation-monitor.mjs';
import {runNativeConfirmationBatch} from '../worker/native-confirmation-batch.mjs';
import {priorRetryRunGuard, fetchPriorRetryGuard, RUNS_URL} from '../worker/native-confirmation-run-guard.mjs';
import {main} from '../scripts/check-native-confirmations.mjs';

const baseTime = Date.parse('2026-11-11T19:00:00Z');
const status = (now = baseTime, patch = {}) => ({configured: true, health: {enabled: true, provider: 'resend', observerFresh: true, healthy: true,
  lastPollAt: new Date(now).toISOString(), lastAcceptedAt: null, queued: 0, late: 0, stuck: 0, failures: 0, ...patch}});
function fixture({previous = null, respond, payload = status(), saveFails = false} = {}) {
  let time = baseTime, saved = previous;
  const calls = [], writes = [];
  const input = {ownerKey: 'synthetic-owner-key', now: () => time,
    stateStore: {load: async () => saved, save: async state => {if (saveFails) throw Error('private disk error'); saved = structuredClone(state); writes.push(saved);}},
    request: async (url, options) => {calls.push({url, options, at: time}); if (respond) return respond({url, options, calls, writes, now: time});
      return Response.json(payload);},
  };
  return {input, calls, writes, saved: () => saved, advance: ms => {time += ms;}, sleep: async ms => {time += ms;}};
}

test('default is read-only owner status with fixed endpoint and no implicit sender', async () => {
  const f = fixture(); const r = await checkNativeConfirmations(f.input);
  assert.equal(f.calls.length, 1); assert.equal(f.calls[0].url, ENDPOINT + '/status');
  assert.equal(f.calls[0].options.method, 'GET'); assert.equal(f.calls[0].options.redirect, 'error');
  assert.equal(r.queue.queueHealthy, true); assert.equal(r.actualDeliveryConfirmed, undefined); assert.equal(r.monitor.actualDeliveryConfirmed, false);
  assert.equal(f.calls.some(c => c.url.endsWith('/retry')), false);
});

test('freshness keeps exact three-minute boundary and rejects false-green or future timestamps', () => {
  for (const age of [180_000, 600_000, -31_000]) {
    const r = assessNativeQueue(status(baseTime - age), baseTime);
    assert.equal(r.queueHealthy, false); assert.equal(r.reason, 'consumer_stale');
  }
  assert.equal(assessNativeQueue(status(baseTime - 179_999), baseTime).queueHealthy, true);
  assert.equal(assessNativeQueue(status(baseTime, {lastPollAt: null}), baseTime).observerFresh, false);
});

test('disabled, unconfigured, malformed, stuck, late and failed queues cannot be green', () => {
  for (const patch of [{enabled: false}, {provider: 'cloudflare'}, {queued: '0'}, {stuck: 1}, {late: 1}, {failures: 1}, {healthy: false}]) {
    assert.equal(assessNativeQueue(status(baseTime, patch), baseTime).queueHealthy, false);
  }
  assert.equal(assessNativeQueue({configured: false, health: status().health}, baseTime).queueHealthy, false);
});

test('denied auth is latched and not retried on the next invocation', async () => {
  for (const http of [401, 403]) {
    const f = fixture({respond: () => Response.json({error: 'PRIVATE'}, {status: http})});
    const first = await checkNativeConfirmations(f.input); assert.equal(first.latch, 'authorization_denied');
    await checkNativeConfirmations(f.input); assert.equal(f.calls.length, 1);
    assert.doesNotMatch(JSON.stringify(f.writes), /PRIVATE/);
  }
});

test('historical retry uncertainty remains latched while new observer only reads',async()=>{
 const f=fixture({previous:{latch:'retry_outcome_unknown'}});const r=await checkNativeConfirmations(f.input);
 assert.equal(r.latch,'retry_outcome_unknown');assert.equal(r.action,'review_required');assert.equal(f.calls.length,1);assert.equal(f.calls[0].options.method,'GET');
});

test('oversized or malformed status remains unhealthy', async () => {
  for (const response of [() => new Response('x'.repeat(65537)), () => new Response('invalid JSON'), () => Response.json({health: {enabled: true, provider: 'resend'}})]) {
    const f = fixture({respond: response}); const r = await checkNativeConfirmations(f.input);
    assert.equal(f.calls.length, 1); assert.equal(r.monitor.queueHealthy, false);
  }
});

test('missing credential, denied saved state and corrupt state never perform network operations', async () => {
  const f = fixture(); await checkNativeConfirmations({...f.input, ownerKey: undefined}); assert.equal(f.calls.length, 0);
  const denied = fixture({previous: {latch: 'authorization_denied', private: 'PRIVATE'}}); await checkNativeConfirmations(denied.input); assert.equal(denied.calls.length, 0);
  assert.doesNotMatch(JSON.stringify(denied.writes), /PRIVATE/);
  await assert.rejects(checkNativeConfirmations({...f.input, stateStore: {load: async () => {throw Error('PRIVATE');}, save: async () => {}}}), /monitor_state_unavailable/);
});

test('observer health expires independently of a formerly green consumer result', () => {
  const state = {observerCheckedAt: new Date(baseTime).toISOString(), queue: assessNativeQueue(status(), baseTime)};
  assert.equal(assessMonitorState(state, baseTime).queueHealthy, true);
  const later = assessMonitorState(state, baseTime + 180_000);
  assert.equal(later.observerStale, true); assert.equal(later.consumerStale, true); assert.equal(later.queueHealthy, false);
});

test('batch cannot exceed five ticks or run without an explicit sleep dependency', async () => {
  const f = fixture();
  for (const patch of [{ticks: 6}, {ticks: 0}, {sleep: undefined}]) await assert.rejects(runNativeConfirmationBatch({...f.input, sleep: f.sleep, ...patch}), /batch_configuration_invalid/);
  assert.equal(f.calls.length, 0);
});

const run = (id, conclusion = 'success', status = 'completed') => ({id, head_branch: 'main', conclusion, status});
test('prior-run guard accepts first run or prior success, never current/future or other-branch evidence', async () => {
  assert.equal((await priorRetryRunGuard({currentRunId: 10, runs: [], totalCount: 0})).allowed, true);
  assert.equal((await priorRetryRunGuard({currentRunId: 10, runs: [run(10, null, 'in_progress'), run(9), run(11)], totalCount: 3})).allowed, true);
  assert.equal((await priorRetryRunGuard({currentRunId: 10, runs: [{...run(9, 'failure'), head_branch: 'untrusted'}], totalCount: 1})).reason, 'first_run');
  assert.equal((await priorRetryRunGuard({currentRunId: 10, runs: [run(10), run(11)], totalCount: 25})).reason, 'run_history_incomplete');
});

test('failed, cancelled, timed-out and unresolved prior retry jobs block unless explicitly reviewed', async () => {
  for (const conclusion of ['failure', 'cancelled', 'timed_out', null, 'skipped']) {
    const input = {currentRunId: 10, runs: [run(9, conclusion)], totalCount: 1};
    assert.equal((await priorRetryRunGuard(input)).allowed, false);
    assert.equal((await priorRetryRunGuard({...input, manual: true, reviewedPreviousFailure: true})).allowed, true);
    assert.equal((await priorRetryRunGuard({...input, manual: false, reviewedPreviousFailure: true})).allowed, false);
  }
  assert.equal((await priorRetryRunGuard({currentRunId: 10, runs: [run(9, null, 'in_progress')], totalCount: 1, manual: true, reviewedPreviousFailure: true})).allowed, false);
});

test('rerunning the same Actions run cannot evade its earlier uncertain attempt', async () => {
  const r = await priorRetryRunGuard({currentRunId: 10, currentAttempt: 2, runs: [run(8)], totalCount: 1, manual: true, reviewedPreviousFailure: true});
  assert.equal(r.allowed, false); assert.equal(r.reason, 'rerun_requires_new_reviewed_dispatch');
});

test('history fetch uses only existing read-only repository API and never exposes token or errors', async () => {
  const calls = [];
  const good = await fetchPriorRetryGuard({currentRunId: 10, token: 'synthetic-actions-token', request: async (url, options) => {calls.push({url, options}); return Response.json({workflow_runs: [run(9)], total_count: 1});}});
  assert.equal(good.allowed, true); assert.equal(calls[0].url, RUNS_URL); assert.equal(calls[0].options.method, 'GET'); assert.equal(calls[0].options.redirect, 'error');
  for (const request of [async () => {throw Error('PRIVATE');}, async () => Response.json({message: 'PRIVATE'}, {status: 403}), async () => new Response('x'.repeat(1024 * 1024 + 1))]) {
    const r = await fetchPriorRetryGuard({currentRunId: 10, token: 'synthetic-actions-token', request});
    assert.equal(r.allowed, false); assert.doesNotMatch(JSON.stringify(r), /PRIVATE|synthetic-actions-token/);
  }
});

test('missing, invalid or contradictory total count never proves a first run', async () => {
  for (const totalCount of [undefined, null, -1, 0.5, '0', Infinity, Number.MAX_SAFE_INTEGER + 1]) {
    const result = await priorRetryRunGuard({currentRunId: 10, runs: [], totalCount, manual: true, reviewedPreviousFailure: true});
    assert.deepEqual(result, {allowed: false, reason: 'run_history_invalid'});
  }
  assert.equal((await priorRetryRunGuard({currentRunId: 10, runs: [run(9)], totalCount: 0})).reason, 'run_history_invalid');
  assert.equal((await priorRetryRunGuard({currentRunId: 10, runs: [], totalCount: 1})).reason, 'run_history_incomplete');
});

test('malformed run entries fail closed rather than being filtered into first-run evidence', async () => {
  const malformed = [null, [], {}, {id: 9}, {...run(9), id: 0}, {...run(9), id: -1}, {...run(9), id: 1.5}, {...run(9), id: '9'},
    {...run(9), id: Number.MAX_SAFE_INTEGER + 1}, {...run(9), head_branch: null}, {...run(9), head_branch: ''}, {...run(9), head_branch: ' '}, {...run(9), head_branch: 'main\n'},
    {...run(9), status: undefined}, {...run(9), status: 'unrecognized'}, {...run(9), conclusion: undefined}, {...run(9), conclusion: 'unrecognized'}];
  for (const value of malformed) {
    const result = await priorRetryRunGuard({currentRunId: 10, runs: [value], totalCount: 1, manual: true, reviewedPreviousFailure: true});
    assert.deepEqual(result, {allowed: false, reason: 'run_history_invalid'});
  }
});

test('all history rows are validated before legitimate branch and run-position exclusions', async () => {
  for (const malformed of [{...run(9), head_branch: 'other', conclusion: undefined}, {...run(10), status: null}, {...run(11), id: '11'}]) {
    assert.equal((await priorRetryRunGuard({currentRunId: 10, runs: [run(8), malformed], totalCount: 2})).reason, 'run_history_invalid');
  }
  assert.equal((await priorRetryRunGuard({currentRunId: 10, runs: [run(9), run(9, 'failure')], totalCount: 2})).reason, 'run_history_invalid');
  assert.equal((await priorRetryRunGuard({currentRunId: 10, runs: [run(10, null, 'in_progress'), run(11, null, 'queued'), {...run(9), head_branch: 'other'}], totalCount: 3})).reason, 'first_run');
});

test('HTTP200 history without trustworthy count and rows cannot authorize retry', async () => {
  const bodies = [{workflow_runs: []}, {workflow_runs: [], total_count: null}, {workflow_runs: [], total_count: -1}, {workflow_runs: [], total_count: '0'},
    {workflow_runs: [null], total_count: 1}, {workflow_runs: [{}], total_count: 1}, {workflow_runs: [run(9)], total_count: 0},
    {workflow_runs: [run(9)]}, {workflow_runs: [run(9)], total_count: 0.5}, {}, [], null];
  for (const payload of bodies) {
    let calls = 0;
    const result = await fetchPriorRetryGuard({currentRunId: 10, token: 'synthetic-actions-token', manual: true, reviewedPreviousFailure: true,
      request: async () => {calls++; return Response.json(payload);}});
    assert.equal(calls, 1); assert.equal(result.allowed, false);
  }
  const first = await fetchPriorRetryGuard({currentRunId: 10, token: 'synthetic-actions-token', request: async () => Response.json({workflow_runs: [], total_count: 0})});
  assert.deepEqual(first, {allowed: true, reason: 'first_run'});
});

test('current run ID must be a positive safe integer and invalid IDs cause no history request', async () => {
  for (const currentRunId of [undefined, null, 0, -1, 1.5, '10', NaN, Infinity, Number.MAX_SAFE_INTEGER + 1]) {
    let calls = 0;
    const direct = await priorRetryRunGuard({currentRunId, runs: [], totalCount: 0});
    const fetched = await fetchPriorRetryGuard({currentRunId, token: 'synthetic-actions-token', request: async () => {calls++; return Response.json({workflow_runs: [], total_count: 0});}});
    assert.deepEqual(direct, {allowed: false, reason: 'run_history_invalid'});
    assert.deepEqual(fetched, {allowed: false, reason: 'run_history_invalid'}); assert.equal(calls, 0);
  }
});

test('CLI default is read-only and legacy queue-only status cannot exit healthy', async () => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'native-observer-test-')), file = path.join(dir, 'state.json'), logs = [], calls = [];
  try {
    const code = await main({argv: [`--state-file=${file}`], env: {HOT_SYNC_ADMIN_KEY: 'synthetic-owner-key'}, output: value => logs.push(value), request: async (url, options) => {calls.push({url, options}); return Response.json(status(Date.now()));}});
    assert.equal(code, 1); assert.equal(calls.length, 1); assert.ok(calls[0].url.endsWith('/status'));
    assert.equal(JSON.parse(await fs.readFile(file, 'utf8')).action, 'status_observed');
    await assert.rejects(fs.stat(file + '.lock'), {code: 'ENOENT'});
    assert.doesNotMatch(logs.join(''), /synthetic-owner-key/);
  } finally { await fs.rm(dir, {recursive: true}); }
});

test('retired retry never calls status or sends even with missing metadata and explicit enable flags',async()=>{
 for(const payload of [status(),{...status(),scheduler:null},{...status(),scheduler:{enabled:false,latched:false}}]){
  const f=fixture({payload});const r=await checkNativeConfirmations({...f.input,mode:'retry',retryEnabled:true});assert.equal(r.action,'retry_retired');assert.equal(r.error,'external_retry_retired');assert.equal(f.calls.length,0);assert.equal(r.monitor.confirmationHealthy,false);
 }
});
test('CLI retired retry returns clear failure before any API, state file, or history read',async()=>{
 let calls=0;const logs=[];const code=await main({argv:['--mode=retry'],env:{HOT_SYNC_ADMIN_KEY:'synthetic',GITHUB_ACTIONS:'true',NATIVE_CHECKOUT_RETRY_ENABLED:'true'},request:async()=>{calls++;throw Error('must not call');},output:x=>logs.push(x)});assert.equal(code,2);assert.equal(calls,0);assert.match(logs.join(''),/external_retry_retired/);
});
test('five-tick status batch is read-only and late ticks never catch up in a burst',async()=>{
 const f=fixture({respond:({now})=>Response.json(status(now))});const result=await runNativeConfirmationBatch({...f.input,sleep:f.sleep,ticks:5});assert.equal(result.ticks,5);assert.ok(f.calls.every(c=>c.options.method==='GET'));assert.equal(result.confirmationHealthy,false);
 const late=fixture();const r=await runNativeConfirmationBatch({...late.input,sleep:async ms=>late.advance(ms+125000),ticks:5});assert.ok(r.skipped>0);assert.ok(late.calls.length<5);
});
test('existing lock and corrupt state prevent read-only observer calls',async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'native-observer-lock-')),file=path.join(dir,'state.json');let calls=0;const config={argv:[`--state-file=${file}`],env:{HOT_SYNC_ADMIN_KEY:'synthetic'},request:async()=>{calls++;throw Error('must not call');}};
 try{await fs.mkdir(file+'.lock');await assert.rejects(main(config),/monitor_lock_unavailable/);assert.equal(calls,0);await fs.rmdir(file+'.lock');await fs.writeFile(file,'corrupt');await assert.rejects(main(config),/monitor_state_unavailable/);assert.equal(calls,0);}finally{await fs.rm(dir,{recursive:true,force:true});}
});
test('workflows remain manual-only and retired sender workflow has no credentials or executable retry',async()=>{
 const root=new URL('../.github/workflows/',import.meta.url),retry=await fs.readFile(new URL('native-confirmation-retry.yml',root),'utf8'),health=await fs.readFile(new URL('native-confirmation-health.yml',root),'utf8');
 for(const s of [retry,health])assert.doesNotMatch(s.split('\n').filter(x=>!/^\s*#/.test(x)).join('\n'),/^\s*schedule:/m);
 assert.match(retry,/External retry is retired/);assert.match(retry,/exit 1/);assert.doesNotMatch(retry,/secrets\.|--mode=retry|--ticks=5|HOT_SYNC_ADMIN_KEY/);assert.match(health,/--mode=status --ticks=1/);assert.doesNotMatch(health,/--mode=retry/);
});
