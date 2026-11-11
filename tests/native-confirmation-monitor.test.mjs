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
const delivery = patch => ({configured: true, claimed: 0, accepted: 0, rejected: 0, ambiguous: 0, stopped: null, disabled: false, empty: true, actualDeliveryConfirmed: false, ...patch});
function fixture({previous = null, respond, payload = status(), saveFails = false} = {}) {
  let time = baseTime, saved = previous;
  const calls = [], writes = [];
  const input = {ownerKey: 'synthetic-owner-key', now: () => time,
    stateStore: {load: async () => saved, save: async state => {if (saveFails) throw Error('private disk error'); saved = structuredClone(state); writes.push(saved);}},
    request: async (url, options) => {calls.push({url, options, at: time}); if (respond) return respond({url, options, calls, writes, now: time});
      return url.endsWith('/retry') ? Response.json({delivery: delivery(), health: status(time).health}) : Response.json(payload);},
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

test('retry requires both explicit local gate and enabled native server provider', async () => {
  for (const patch of [{}, {configured: false}, {health: {enabled: false, disabled: true}}, {health: {...status().health, provider: 'cloudflare'}}]) {
    const f = fixture({payload: {...status(), ...patch}});
    const r = await checkNativeConfirmations({...f.input, mode: 'retry', retryEnabled: Object.keys(patch).length > 0});
    assert.equal(f.calls.length, 1); assert.notEqual(r.action, 'retry_completed');
  }
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

test('successful bounded retry durably records its attempt before POST and sanitizes response', async () => {
  const f = fixture({respond: ({url, writes, now}) => {
    if (url.endsWith('/status')) return Response.json(status(now - 600_000));
    assert.equal(writes.at(-1).latch, 'retry_outcome_unknown'); assert.equal(writes.at(-1).action, 'retry_pending');
    return Response.json({delivery: delivery({accepted: 1, recipient: 'PRIVATE@example.test', providerId: 'PRIVATE_ID'}), health: {...status(now).health, private: 'PRIVATE'}, arbitrary: 'PRIVATE'});
  }});
  const r = await checkNativeConfirmations({...f.input, mode: 'retry', retryEnabled: true});
  assert.equal(f.calls.length, 2); assert.equal(f.calls[1].options.body, '{}');
  assert.equal(f.calls[1].options.headers['content-type'], 'application/json');
  assert.equal(r.latch, null); assert.equal(r.delivery.accepted, 1); assert.equal(r.monitor.queueHealthy, true);
  assert.doesNotMatch(JSON.stringify(r) + JSON.stringify(f.writes), /PRIVATE|synthetic-owner-key/);
});

test('state persistence failure prevents any POST side effect', async () => {
  const f = fixture({saveFails: true});
  await assert.rejects(checkNativeConfirmations({...f.input, mode: 'retry', retryEnabled: true}));
  assert.equal(f.calls.length, 1);
});

test('one-minute cooldown prevents repeat sends even when multiple processes invoke sequentially', async () => {
  const f = fixture();
  await checkNativeConfirmations({...f.input, mode: 'retry', retryEnabled: true});
  const r = await checkNativeConfirmations({...f.input, mode: 'retry', retryEnabled: true});
  assert.equal(r.action, 'retry_cooldown'); assert.equal(f.calls.filter(c => c.url.endsWith('/retry')).length, 1);
});

test('unknown POST response leaves durable latch and later runs only observe status', async () => {
  const f = fixture({respond: ({url}) => {if (url.endsWith('/retry')) throw Error('PRIVATE lost response'); return Response.json(status());}});
  const first = await checkNativeConfirmations({...f.input, mode: 'retry', retryEnabled: true});
  assert.equal(first.latch, 'retry_outcome_unknown');
  f.advance(300_000);
  const second = await checkNativeConfirmations({...f.input, mode: 'retry', retryEnabled: true});
  assert.equal(second.action, 'review_required'); assert.equal(f.calls.filter(c => c.url.endsWith('/retry')).length, 1);
  assert.doesNotMatch(JSON.stringify(second), /PRIVATE/);
});

test('denied auth is latched and not retried on the next invocation', async () => {
  for (const http of [401, 403]) {
    const f = fixture({respond: () => Response.json({error: 'PRIVATE'}, {status: http})});
    const first = await checkNativeConfirmations(f.input); assert.equal(first.latch, 'authorization_denied');
    await checkNativeConfirmations(f.input); assert.equal(f.calls.length, 1);
    assert.doesNotMatch(JSON.stringify(f.writes), /PRIVATE/);
  }
});

test('503 with a complete delivery result remains known but unhealthy; generic failure remains unknown', async () => {
  for (const complete of [true, false]) {
    const f = fixture({respond: ({url}) => url.endsWith('/status') ? Response.json(status()) : Response.json(complete ? {delivery: delivery({rejected: 1}), health: status(baseTime, {failures: 1, healthy: false}).health} : {error: 'PRIVATE'}, {status: 503})});
    const r = await checkNativeConfirmations({...f.input, mode: 'retry', retryEnabled: true});
    assert.equal(r.latch, complete ? null : 'retry_outcome_unknown'); assert.equal(r.monitor.queueHealthy, false);
  }
});

test('claim or settlement uncertainty from a completed endpoint also latches retry', async () => {
  for (const stopped of ['claim_unknown', 'settlement_unknown']) {
    const f = fixture({respond: ({url}) => url.endsWith('/status') ? Response.json(status()) : Response.json({delivery: delivery({stopped}), health: status().health}, {status: 503})});
    assert.equal((await checkNativeConfirmations({...f.input, mode: 'retry', retryEnabled: true})).latch, 'retry_outcome_unknown');
  }
});

test('oversized or malformed provider status cannot trigger retry', async () => {
  for (const response of [() => new Response('x'.repeat(65537)), () => new Response('invalid JSON'), () => Response.json({health: {enabled: true, provider: 'resend'}})]) {
    const f = fixture({respond: response}); const r = await checkNativeConfirmations({...f.input, mode: 'retry', retryEnabled: true});
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

test('five-tick batch invokes at most once per minute and preserves three-minute queue checks', async () => {
  const f = fixture({respond: ({url, now}) => url.endsWith('/status') ? Response.json(status(now)) : Response.json({delivery: delivery(), health: status(now).health})});
  const result = await runNativeConfirmationBatch({...f.input, sleep: f.sleep, mode: 'retry', retryEnabled: true, ticks: 5});
  assert.equal(result.ticks, 5); assert.equal(result.queueHealthy, true);
  const times = f.calls.filter(c => c.url.endsWith('/retry')).map(c => c.at);
  assert.deepEqual(times, [0, 1, 2, 3, 4].map(n => baseTime + n * 60_000));
});

test('late ticks are skipped without catch-up burst, and an unknown retry stops the batch', async () => {
  const f = fixture({respond: ({url, now}) => url.endsWith('/status') ? Response.json(status(now)) : Response.json({delivery: delivery(), health: status(now).health})});
  const result = await runNativeConfirmationBatch({...f.input, sleep: async ms => f.advance(ms + 125_000), ticks: 5});
  assert.ok(result.skipped > 0); assert.ok(f.calls.length < 5);
  const u = fixture({respond: ({url}) => {if (url.endsWith('/retry')) throw Error('unknown'); return Response.json(status());}});
  const unknown = await runNativeConfirmationBatch({...u.input, sleep: u.sleep, mode: 'retry', retryEnabled: true, ticks: 5});
  assert.equal(unknown.ticks, 1); assert.equal(unknown.queueHealthy, false);
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

test('CLI default is one read-only check, writes sanitized atomic state and leaves no lock', async () => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'native-observer-test-')), file = path.join(dir, 'state.json'), logs = [], calls = [];
  try {
    const code = await main({argv: [`--state-file=${file}`], env: {HOT_SYNC_ADMIN_KEY: 'synthetic-owner-key'}, output: value => logs.push(value), request: async (url, options) => {calls.push({url, options}); return Response.json(status(Date.now()));}});
    assert.equal(code, 0); assert.equal(calls.length, 1); assert.ok(calls[0].url.endsWith('/status'));
    assert.equal(JSON.parse(await fs.readFile(file, 'utf8')).action, 'status_observed');
    await assert.rejects(fs.stat(file + '.lock'), {code: 'ENOENT'});
    assert.doesNotMatch(logs.join(''), /synthetic-owner-key/);
  } finally { await fs.rm(dir, {recursive: true}); }
});

test('existing local lock or unreadable state prevents a second process from sending', async () => {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'native-lock-test-')), file = path.join(dir, 'state.json'); let calls = 0;
  const config = {argv: [`--state-file=${file}`, '--mode=retry'], env: {HOT_SYNC_ADMIN_KEY: 'synthetic', NATIVE_CHECKOUT_RETRY_ENABLED: 'true'}, request: async () => {calls++; throw Error('must not call');}};
  try {
    await fs.mkdir(file + '.lock'); await assert.rejects(main(config), /monitor_lock_unavailable/); assert.equal(calls, 0);
    await fs.rmdir(file + '.lock'); await fs.writeFile(file, 'corrupt'); await assert.rejects(main(config), /monitor_state_unavailable/); assert.equal(calls, 0);
  } finally { await fs.rm(dir, {recursive: true}); }
});

test('workflow preparation is manual-only/default-off and never uses cancelling concurrency', async () => {
  const root = new URL('../.github/workflows/', import.meta.url);
  const retry = await fs.readFile(new URL('native-confirmation-retry.yml', root), 'utf8');
  const health = await fs.readFile(new URL('native-confirmation-health.yml', root), 'utf8');
  const activeLines = retry.split('\n').filter(line => !/^\s*#/.test(line)).join('\n');
  assert.doesNotMatch(activeLines, /^\s*schedule:/m); assert.match(retry, /cancel-in-progress: false/);
  assert.match(retry, /Require explicit retry activation/); assert.match(retry, /test "\$NATIVE_CHECKOUT_RETRY_ENABLED" = 'true'/);
  assert.match(retry, /--ticks=5/); assert.match(retry, /actions: read/); assert.doesNotMatch(retry, /actions: write|contents: write/);
  assert.match(health, /--mode=status --ticks=1/); assert.doesNotMatch(health, /--mode=retry/);
});
