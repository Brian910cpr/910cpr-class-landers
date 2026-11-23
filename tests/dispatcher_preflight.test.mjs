import test from 'node:test';
import assert from 'node:assert/strict';
import {preflight} from '../ops/operator/dispatcher-preflight.mjs';

const now = '2026-10-10T23:00:00Z';
function worker(id, types = ['selftest.ping']) {
  const identity = {worker_id: id, worker_name: `WORKER-${id}`, worker_version: '0.2.3',
    repository: 'Brian910cpr/910cpr-class-landers', capabilities: types.map(x => `job.${x}`)};
  return {identity, heartbeat: {...identity, state: 'idle', observed_at_utc: now},
    profile: {disabled: false, active_job_ids: []}};
}
const job = (type = 'site.healthcheck', id = 'health-001') =>
  ({job_id: id, job_type: type, source: 'explicit', worker_safe: true});
const run = (workers, queue = [job()]) => preflight({workers, queue, now});

test('two distinct workers: only advertised capability is eligible, no execution authorization', () => {
  const result = run([worker('a'), worker('b', ['site.healthcheck'])]);
  assert.deepEqual(result.preview[0].eligible_worker_ids, ['b']);
  assert.equal(result.dispatch_enabled, false);
  assert.equal(result.fleet.length, 2);
});
test('unsupported typed job stays blocked', () => {
  const result = run([worker('a', ['shell.run'])], [job('shell.run')]);
  assert.equal(result.preview[0].blocker, 'unsupported_job_type');
  assert.deepEqual(result.preview[0].eligible_worker_ids, []);
});
test('one active job defaults to busy; explicit concurrency permits another', () => {
  const a = worker('a', ['site.healthcheck']); a.profile.active_job_ids = ['other'];
  assert.equal(run([a]).fleet[0].state, 'busy');
  a.profile.max_concurrency = 2;
  assert.equal(run([a]).fleet[0].state, 'idle');
  a.heartbeat.state = 'working';
  assert.equal(run([a]).fleet[0].state, 'busy');
});
test('disable isolation and stale/future heartbeat fail closed', () => {
  const a = worker('a', ['site.healthcheck']), b = worker('b', ['site.healthcheck']);
  a.profile.disabled = true;
  assert.deepEqual(run([a,b]).preview[0].eligible_worker_ids, ['b']);
  for (const stamp of ['2026-10-10T22:57:00Z', '2026-10-11T00:00:00Z']) {
    b.heartbeat.observed_at_utc = stamp;
    assert.equal(run([a,b]).fleet[1].state, 'stale');
  }
});
test('identity collisions, spoofed heartbeat, and wrong repository rejected', () => {
  assert.throws(() => run([worker('a'), worker('a')]), /Duplicate worker/);
  const a = worker('a'); a.heartbeat.worker_id = 'other';
  assert.throws(() => run([a]), /mismatch/);
  a.heartbeat.worker_id = 'a'; a.identity.repository = 'other/repo';
  assert.throws(() => run([a]), /Wrong repository/);
});
test('unapproved sources and duplicate durable IDs rejected', () => {
  assert.throws(() => run([], [{...job(), source: 'backlog'}]), /Unapproved/);
  assert.throws(() => run([], [{...job(), worker_safe: false}]), /Unapproved/);
  assert.throws(() => run([], [job(), job()]), /Duplicate queued/);
});
test('invalid profile and timestamps fail closed', () => {
  const a = worker('a'); a.profile.max_concurrency = 0;
  assert.throws(() => run([a]), /concurrency/);
  a.profile.max_concurrency = 1; delete a.profile.disabled;
  assert.throws(() => run([a]), /disabled/);
  assert.throws(() => preflight({workers: [], queue: [], now: '2026-10-10'}), /timezone/);
});
test('idle/no-delta invocation is deterministic and does not mutate inputs', () => {
  const snapshot = {workers: [worker('a')], queue: [], now};
  const before = structuredClone(snapshot);
  assert.deepEqual(preflight(snapshot), preflight(structuredClone(snapshot)));
  assert.deepEqual(snapshot, before);
  assert.equal(preflight(snapshot).queue_depth, 0);
});

test('queued active job cannot become eligible on another idle worker', () => {
  const a = worker('a', ['site.healthcheck']), b = worker('b', ['site.healthcheck']);
  a.profile.active_job_ids = ['health-001'];
  a.profile.max_concurrency = 2;
  const result = run([a, b], [job(), job('site.healthcheck', 'health-002')]);
  assert.equal(result.preview[0].blocker, 'job_already_active');
  assert.deepEqual(result.preview[0].eligible_worker_ids, []);
  assert.deepEqual(result.preview[1].eligible_worker_ids, ['a', 'b']);
  assert.equal(result.dispatch_enabled, false);
});

test('disabled and stale active owners still block duplicate execution', () => {
  for (const state of ['disabled', 'stale']) {
    const a = worker('a'), b = worker('b', ['site.healthcheck']);
    a.profile.active_job_ids = ['health-001'];
    if (state === 'disabled') a.profile.disabled = true;
    else a.heartbeat.observed_at_utc = '2026-10-10T22:57:00Z';
    const result = run([a, b]);
    assert.equal(result.preview[0].blocker, 'job_already_active');
    assert.deepEqual(result.preview[0].eligible_worker_ids, []);
  }
});

test('conflicting active ownership rejects the entire snapshot', () => {
  const a = worker('a'), b = worker('b');
  a.profile.active_job_ids = b.profile.active_job_ids = ['same-job'];
  b.profile.disabled = true;
  assert.throws(() => run([a, b]), /multiple worker owners/);
});
