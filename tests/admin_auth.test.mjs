import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { readFileSync } from 'node:fs';

const source = readFileSync(new URL('../docs/admin/admin-auth.js', import.meta.url), 'utf8');
const endpoint = 'https://schedule.910cpr.com/admin';
function storage() {
  const values = new Map();
  return { values, getItem: k => values.get(k) ?? null, setItem: (k, v) => values.set(k, v), removeItem: k => values.delete(k) };
}
function page(store = storage(), fetch = async () => new Response('{}')) {
  const handlers = new Map();
  const window = {
    sessionStorage: store, location: new URL('https://www.910cpr.com/admin/dashboard.html'), fetch,
    addEventListener: (name, fn) => handlers.set(name, fn),
  };
  const context = vm.createContext({ window, URL, Headers, AbortController });
  vm.runInContext(source, context);
  return { auth: window.LanderAdminAuth, store, window, context, emit: (name, event) => handlers.get(name)?.(event) };
}
const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };
const code = expected => error => error.code === expected;
const client = p => p.auth.createClient({ endpoints: [endpoint] });

test('one tab storage reuses canonical key across pages and preserves corporate/draft values', () => {
  const a = page(); a.store.setItem('maximPortalSession', 'synthetic-corp'); a.store.setItem('hotSyncDrafts', '{}');
  a.auth.setKey(' synthetic-owner ');
  const b = page(a.store);
  assert.equal(b.auth.getKey(), 'synthetic-owner');
  b.auth.clearKey();
  assert.equal(a.auth.getKey(), '');
  assert.equal(a.store.getItem('maximPortalSession'), 'synthetic-corp');
  assert.equal(a.store.getItem('hotSyncDrafts'), '{}');
});

test('hooks expose state, never credentials, and unsubscribe or a broken hook does not stop locks', () => {
  const p = page(), seen = [];
  p.auth.subscribe(() => { throw Error('broken page'); });
  const off = p.auth.subscribe(s => seen.push(s));
  p.auth.setKey('synthetic-secret'); p.auth.clearKey(); off(); p.auth.setKey('replacement');
  assert.deepEqual(seen.map(s => s.reason), ['initial', 'unlock', 'lock']);
  assert.equal(JSON.stringify(seen).includes('synthetic-secret'), false);
  assert.equal(seen.at(-1).hasKey, false);
});

test('invalid keys never replace an existing credential', () => {
  const p = page(); p.auth.setKey('synthetic-owner');
  for (const value of [null, {}, 42, '', '  ', 'line\nbreak', 'bad\0key']) assert.throws(() => p.auth.setKey(value), code('INVALID_KEY'));
  assert.equal(p.auth.getKey(), 'synthetic-owner');
});

test('locked requests fail before network access, without corporate fallback', async () => {
  let called = 0;
  const p = page(storage(), async () => { called++; }); p.store.setItem('maximPortalSession', 'synthetic-corp');
  await assert.rejects(client(p).json(endpoint), code('AUTH_REQUIRED'));
  assert.equal(called, 0);
});

test('canonical header is authoritative and request settings cannot enable caching, redirects or cookies', async () => {
  const p = page(storage(), async (url, options) => {
    assert.equal(url, endpoint + '/classes?date=2026-09-13');
    assert.equal(options.headers.get('X-Hot-Sync-Admin-Key'), 'synthetic-owner');
    assert.equal(options.headers.get('content-type'), 'application/json');
    for (const [key, expected] of Object.entries({ cache: 'no-store', credentials: 'omit', redirect: 'error', referrerPolicy: 'no-referrer' })) assert.equal(options[key], expected);
    return new Response('{"count":2}');
  });
  p.auth.setKey('synthetic-owner');
  const result = await client(p).json(endpoint + '/classes?date=2026-09-13', {
    method: 'POST', body: '{}', headers: { 'x-hot-sync-admin-key': 'wrong', 'content-type': 'application/json' },
    cache: 'force-cache', credentials: 'include', redirect: 'follow', referrerPolicy: 'unsafe-url',
  });
  assert.equal(result.commit(data => data.count), 2);
});

test('origin and path boundaries reject credential forwarding before fetch', async () => {
  let called = 0; const p = page(storage(), async () => { called++; }); p.auth.setKey('synthetic-owner');
  for (const url of ['https://evil.example/admin', endpoint + 'ister', endpoint + '/../public',
    'http://schedule.910cpr.com/admin', 'https://schedule.910cpr.com.evil.example/admin',
    'https://user:pass@schedule.910cpr.com/admin', endpoint + '#fragment', '//evil.example/admin',
    endpoint + '/%2e%2e%2fpublic', endpoint + '/%252e%252e%252fpublic', endpoint + '/%5cpublic']) {
    await assert.rejects(client(p).json(url), code('UNTRUSTED_URL'));
  }
  assert.equal(called, 0);
  assert.throws(() => p.auth.createClient(), /endpoints/);
  assert.throws(() => p.auth.createClient({ endpoints: ['https://schedule.910cpr.com/'] }), /API path/);
});

test('corporate or bearer headers cannot enter the admin transport', () => {
  const p = page(); p.auth.setKey('synthetic-owner');
  for (const headers of [{ 'X-Maxim-Session': 'synthetic-corp' }, { Authorization: 'Bearer synthetic' }]) {
    assert.throws(() => client(p).prepare(endpoint, headers), code('MIXED_AUTH'));
  }
});

for (const method of ['GET', 'POST']) for (const status of [401, 403]) {
  test(`${method} ${status} clears the shared key and invokes the denial hook`, async () => {
    const p = page(storage(), async () => new Response('{}', { status })), seen = [];
    p.auth.subscribe(s => seen.push(s.reason)); p.auth.setKey('synthetic-owner');
    await assert.rejects(client(p).json(endpoint, { method }), code('AUTH_DENIED'));
    assert.equal(p.auth.getKey(), ''); assert.equal(seen.at(-1), 'denied');
  });
}

test('late denial for an old credential cannot clear a new credential, even with identical text', async () => {
  for (const replacement of ['replacement', 'synthetic-owner']) {
    const response = deferred(); const p = page(storage(), () => response.promise);
    p.auth.setKey('synthetic-owner'); const request = client(p).json(endpoint);
    p.auth.clearKey(); p.auth.setKey(replacement); response.resolve(new Response('{}', { status: 401 }));
    await assert.rejects(request, code('STALE_AUTH')); assert.equal(p.auth.getKey(), replacement);
  }
});

test('lock aborts pending fetch and discards a late success even if the transport ignores abort', async () => {
  const response = deferred(); let signal;
  const p = page(storage(), (_, opts) => { signal = opts.signal; return response.promise; });
  p.auth.setKey('synthetic-owner'); const request = client(p).json(endpoint);
  p.auth.clearKey(); assert.equal(signal.aborted, true); response.resolve(new Response('{"private":true}'));
  await assert.rejects(request, code('STALE_AUTH'));
});

test('lock during asynchronous JSON decoding prevents rendering private results', async () => {
  const body = deferred(), started = deferred();
  const p = page(storage(), async () => ({ status: 200, ok: true, json: () => { started.resolve(); return body.promise; } }));
  p.auth.setKey('synthetic-owner'); const request = client(p).json(endpoint);
  await started.promise; p.auth.clearKey(); body.resolve({ private: true });
  await assert.rejects(request, code('STALE_AUTH'));
});

test('a consumed result cannot render after a later lock', async () => {
  const p = page(); p.auth.setKey('synthetic-owner'); const result = await client(p).json(endpoint);
  p.auth.clearKey(); let rendered = false;
  assert.equal(result.isCurrent(), false);
  assert.throws(() => result.commit(() => { rendered = true; }), code('STALE_AUTH'));
  assert.equal(rendered, false);
});

test('back/forward restoration forces private state invalidation with an unchanged credential', async () => {
  const p = page(), seen = []; p.auth.subscribe(s => seen.push(s.reason)); p.auth.setKey('synthetic-owner');
  const result = await client(p).json(endpoint);
  p.emit('pageshow', { persisted: true });
  assert.equal(result.isCurrent(), false); assert.equal(seen.at(-1), 'pageshow'); assert.equal(p.auth.getKey(), 'synthetic-owner');
});

test('external same-session storage removal invalidates a prepared XHR ticket', () => {
  const p = page(); p.auth.setKey('synthetic-owner'); const ticket = client(p).prepare(endpoint);
  p.store.removeItem('hotSyncAdminKey'); p.emit('storage', { storageArea: p.store, key: 'hotSyncAdminKey' });
  assert.equal(ticket.signal.aborted, true); assert.throws(() => ticket.handleStatus(200), code('STALE_AUTH')); ticket.finish();
});

test('prepared XHR header/status contract clears only the current denied credential', () => {
  const p = page(); p.auth.setKey('synthetic-owner'); const ticket = client(p).prepare(endpoint);
  assert.equal(ticket.headers.get(p.auth.HEADER_NAME), 'synthetic-owner');
  assert.throws(() => ticket.handleStatus(403), code('AUTH_DENIED'));
  assert.equal(ticket.signal.aborted, true); ticket.finish(); assert.equal(p.auth.getKey(), '');
});

test('network failures and HTTP 503 preserve credentials without displaying remote error bodies', async () => {
  for (const fetch of [async () => { throw Error('offline'); }, async () => new Response('sensitive upstream body', { status: 503 })]) {
    const p = page(storage(), fetch); p.auth.setKey('synthetic-owner');
    await assert.rejects(client(p).json(endpoint), error => !error.message.includes('sensitive upstream body'));
    assert.equal(p.auth.getKey(), 'synthetic-owner');
  }
});

test('caller cancellation preserves credentials and cannot deliver a late result', async () => {
  const response = deferred(), cancel = new AbortController();
  const p = page(storage(), () => response.promise); p.auth.setKey('synthetic-owner');
  const request = client(p).json(endpoint, { signal: cancel.signal }); cancel.abort(); response.resolve(new Response('{}'));
  await assert.rejects(request, code('REQUEST_ABORTED')); assert.equal(p.auth.getKey(), 'synthetic-owner');
});

test('storage read/write failures fail closed; explicit successful set can recover', () => {
  const store = storage(), p = page(store); p.auth.setKey('synthetic-owner');
  const get = store.getItem, set = store.setItem;
  store.getItem = () => { throw Error('blocked'); }; assert.equal(p.auth.getKey(), '');
  store.getItem = get; assert.equal(p.auth.getKey(), '');
  store.setItem = () => { throw Error('quota'); };
  assert.throws(() => p.auth.setKey('new'), code('STORAGE_UNAVAILABLE')); assert.equal(p.auth.getKey(), '');
  store.setItem = set; p.auth.setKey('new'); assert.equal(p.auth.getKey(), 'new');
});

test('failed storage removal locks the current page and explicitly reports persistence failure', () => {
  const p = page(); p.auth.setKey('synthetic-owner'); const ticket = client(p).prepare(endpoint);
  p.store.removeItem = () => { throw Error('blocked'); };
  assert.throws(() => p.auth.clearKey(), code('STORAGE_UNAVAILABLE')); assert.equal(p.auth.getKey(), '');
  assert.equal(ticket.signal.aborted, true); ticket.finish();
});

test('loading helper twice keeps one state owner and performs no network request', () => {
  let calls = 0; const p = page(storage(), () => { calls++; }); const auth = p.auth;
  vm.runInContext(source, p.context); assert.equal(p.window.LanderAdminAuth, auth); assert.equal(calls, 0);
});

test('reentrant lock hook cannot deliver an obsolete unlock event to another page component', () => {
  const p = page(), seen = [];
  p.auth.subscribe(state => { if (state.reason === 'unlock') p.auth.clearKey(); });
  p.auth.subscribe(state => seen.push(state)); p.auth.setKey('synthetic-owner');
  assert.equal(seen.at(-1).hasKey, false); assert.equal(p.auth.getKey(), '');
  assert.equal(seen.some(state => state.reason === 'unlock'), false);
});

test('queued storage events invalidate a ticket even when the latest stored text is unchanged', () => {
  const p = page(); p.auth.setKey('synthetic-owner'); const ticket = client(p).prepare(endpoint);
  // Another same-session document removed and re-entered the key before this event ran.
  p.emit('storage', { storageArea: p.store, key: 'hotSyncAdminKey' });
  assert.equal(ticket.isCurrent(), false); assert.equal(ticket.signal.aborted, true); ticket.finish();
});

test('storage getter failure during event handling locks and notifies without an uncaught error', () => {
  const p = page(), seen = []; p.auth.setKey('synthetic-owner'); p.auth.subscribe(state => seen.push(state));
  Object.defineProperty(p.window, 'sessionStorage', { get: () => { throw Error('browser denied'); } });
  assert.doesNotThrow(() => p.emit('storage', { storageArea: p.store, key: 'hotSyncAdminKey' }));
  assert.equal(p.auth.getKey(), ''); assert.equal(seen.at(-1).reason, 'storage_unavailable');
});
