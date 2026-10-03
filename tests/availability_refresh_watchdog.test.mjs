import test from 'node:test';
import assert from 'node:assert/strict';
import worker, { checkAndRefresh, health, publicationState, WORKFLOW } from '../worker/availability-refresh-watchdog.mjs';

const now = Date.parse('2026-10-03T12:00:00Z');
const iso = minutes => new Date(now + minutes * 60_000).toISOString();
const feed = minutes => ({ generatedAt: iso(-30), validUntil: iso(minutes), dates: [{ startTimes: [{ courses: [{ courseId: '209806' }] }] }] });
function setup({ minutes = 50, runs = [], previous = null, token = 'test-only', fail, dispatchStatus = 204 } = {}) {
  let saved = previous;
  const calls = [];
  const env = { GITHUB_ACTIONS_TOKEN: token, STATE: {
    get: async () => saved,
    put: async (_key, value) => { saved = JSON.parse(value); },
  } };
  const request = async (url, options) => {
    calls.push({ url, options });
    if (fail === 'network') throw new Error('secret-bearing upstream exception');
    if (url.includes('/dispatches')) return new Response(null, { status: dispatchStatus });
    if (url.includes('/runs?')) return fail === 'auth' ? new Response('secret', { status: 401 }) : Response.json({ workflow_runs: runs });
    if (fail === 'feed') return new Response('unavailable', { status: 503 });
    if (fail === 'oversize') return new Response('x'.repeat(8 * 1024 * 1024 + 1));
    return Response.json(feed(minutes));
  };
  return { env, calls, run: () => checkAndRefresh(env, { now, request }), saved: () => saved };
}

test('fresh publication makes no GitHub call', async () => {
  const t = setup({ minutes: 75 });
  const result = await t.run();
  assert.equal(result.action, 'fresh'); assert.equal(t.calls.length, 1);
  assert.equal(health(result, now).ok, true);
});
test('refreshes well before expiry using only existing main workflow', async () => {
  const t = setup(); const result = await t.run();
  assert.equal(result.action, 'refresh_dispatched');
  assert.equal(t.calls[2].url, `${WORKFLOW}/dispatches`);
  assert.deepEqual(JSON.parse(t.calls[2].options.body), { ref: 'main' });
  assert.equal(t.saved().lastDispatchAt, iso(0));
});
test('expired publication triggers recovery but health remains red until actual new feed', async () => {
  const t = setup({ minutes: -1 }); const result = await t.run();
  assert.equal(result.action, 'refresh_dispatched'); assert.equal(health(result, now).ok, false);
});
test('never queues duplicate while a refresh is active', async () => {
  for (const status of ['queued', 'in_progress', 'waiting', 'pending']) {
    const t = setup({ runs: [{ id: 123, status, created_at: iso(-5) }] });
    assert.equal((await t.run()).action, 'refresh_running'); assert.equal(t.calls.length, 2);
  }
});
test('hung refresh reports failure without cancelling it', async () => {
  const t = setup({ runs: [{ id: 123, status: 'queued', created_at: iso(-31) }] });
  assert.equal((await t.run()).error, 'refresh_stalled'); assert.equal(t.calls.length, 2);
});
test('KV cooldown covers GitHub dispatch visibility delay', async () => {
  const t = setup({ previous: { lastDispatchAt: iso(-5) } });
  assert.equal((await t.run()).action, 'dispatch_cooldown'); assert.equal(t.calls.length, 1);
});
test('missing token and rejected dispatch are recorded, not reported successful', async () => {
  assert.equal((await setup({ token: '' }).run()).error, 'github_token_missing');
  const t = setup({ dispatchStatus: 403 }); const result = await t.run();
  assert.equal(result.error, 'dispatch_http_403'); assert.equal(result.lastDispatchAt, null);
});
test('auth and network errors cannot leak arbitrary upstream data', async () => {
  assert.equal((await setup({ fail: 'auth' }).run()).error, 'http_401');
  const result = await setup({ fail: 'network' }).run();
  assert.equal(result.error, 'refresh_check_failed');
  assert.ok(!JSON.stringify(result).includes('secret'));
});
test('invalid or oversized public feed invokes bounded recovery and fails health', async () => {
  for (const fail of ['feed', 'oversize']) {
    const result = await setup({ fail }).run();
    assert.equal(result.action, 'refresh_dispatched'); assert.equal(health(result, now).ok, false);
  }
});
test('monitor health ages independently of the publication lease', () => {
  const state = { checkedAt: iso(-13), publication: publicationState(feed(75), now) };
  assert.equal(health(state, now).heartbeatStale, true);
  assert.equal(health(null, now).ok, false);
});
test('health re-evaluates expiration even if stored observation was fresh', () => {
  const state = { checkedAt: iso(0), publication: publicationState(feed(1), now) };
  assert.equal(health(state, now + 2 * 60_000).publicationExpired, true);
});
test('public HTTP interface cannot dispatch refreshes', async () => {
  const t = setup();
  const result = await worker.fetch(new Request('https://example.test/health', { method: 'POST' }), t.env);
  assert.equal(result.status, 404); assert.equal(t.calls.length, 0);
});
