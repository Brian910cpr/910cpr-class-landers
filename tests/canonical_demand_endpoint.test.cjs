const test = require('node:test');
const assert = require('node:assert/strict');
const {loadEndpoint} = require('./helpers/canonical_demand_endpoint.cjs');

const api = loadEndpoint(() => { throw Error('Unexpected network call'); });
for (const [day, expected] of [
  ['2026-01-15','2026-01-15T05:00:00.000Z'],
  ['2026-07-15','2026-07-15T04:00:00.000Z'],
  ['2026-11-01','2026-11-01T04:00:00.000Z'],
  ['2026-11-02','2026-11-02T05:00:00.000Z'],
  ['2027-03-14','2027-03-14T05:00:00.000Z'],
  ['2027-03-15','2027-03-15T04:00:00.000Z'],
]) test(`New York midnight ${day}`, () => assert.equal(api.localMidnight(day), expected));

test('DST days span 25 and 23 hours, and default date is local', () => {
  for (const [from,to,hours] of [['2026-11-01','2026-11-02',25],['2027-03-14','2027-03-15',23]]) {
    const range = api.demandRange(new URLSearchParams({from,to}));
    assert.equal((Date.parse(range.stop)-Date.parse(range.start))/3600000,hours);
  }
  assert.equal(api.localDate(new Date('2026-11-02T02:00:00Z')),'2026-11-01');
});

test('malformed, reversed, impossible, and oversized date ranges fail', () => {
  for (const query of ['from=wrong','from=2026-02-30','from=2026-11-01&to=2026-10-31','from=2026-11-01&to=2028-11-01']) {
    assert.throws(() => api.demandRange(new URLSearchParams(query)));
  }
});

test('OPTIONS has the same allowed CORS contract and no body or auth access', async () => {
  const result = await api.handleRequest(new Request('https://endpoint.test', {method:'OPTIONS',headers:{origin:'https://www.910cpr.com'}}));
  assert.equal(result.status,204);
  assert.equal(await result.text(),'');
  assert.equal(result.headers.get('access-control-allow-origin'),'https://www.910cpr.com');
  assert.equal(result.headers.get('access-control-allow-methods'),'GET,OPTIONS');
  assert.match(result.headers.get('access-control-allow-headers'),/x-hot-sync-admin-key/);
  assert.match(result.headers.get('cache-control'),/no-store/);
});

test('untrusted origins and unauthenticated reads fail closed', async () => {
  assert.equal((await api.handleRequest(new Request('https://endpoint.test'))).status,401);
  assert.equal((await api.handleRequest(new Request('https://endpoint.test',{method:'OPTIONS',headers:{origin:'https://evil.test'}}))).status,403);
});

test('only active canonical registrations count; missing and external bridge are unknown', () => {
  const row = {id:'fixture',registration_backend:'landerware',registrations:[{status:'registered'},{status:'confirmed'},{status:'completed'},{status:'canceled'},{status:'rescheduled'},{status:'no_show'}]};
  assert.equal(api.projectDemand(row).active_registration_count,3);
  assert.equal(api.projectDemand({...row,registrations:[]}).active_registration_count,0);
  assert.equal(api.projectDemand({...row,registrations:null}).active_registration_count,null);
  assert.equal(api.projectDemand({...row,registration_backend:'enrollware'}).active_registration_count,null);
});

test('HTTP endpoint uses DST bounds, paginates, and excludes participant fields', async () => {
  const calls = [];
  const endpoint = loadEndpoint(async url => {
    if (String(url).includes('/admin/hot-sync')) return new Response('{}');
    if (String(url).includes('/rpc/')) return Response.json({sessions:[]});
    const query = new URL(url).searchParams;
    calls.push(query);
    const count = query.get('offset') === '0' ? 500 : 1;
    return Response.json(Array.from({length:count},(_,i)=>({id:`session-${query.get('offset')}-${i}`,registration_backend:'landerware',registrations:[],external_course_id:'359474'})));
  });
  const response = await endpoint.handleRequest(new Request('https://endpoint.test/?from=2026-11-01&to=2026-11-02',{headers:{'x-hot-sync-admin-key':'fixture'}}));
  assert.equal(response.status,200);
  const body = await response.json();
  assert.equal(body.sessions.length,501);
  assert.deepEqual(calls[0].getAll('start_at'),['gte.2026-11-01T04:00:00.000Z','lt.2026-11-02T05:00:00.000Z']);
  assert.equal(calls[1].get('offset'),'500');
  assert.doesNotMatch(calls[0].get('select'),/customers|email|phone/);
  assert.equal(body.sessions[0].external_course_id,'359474');
});

test('classification source failure or canonical conflict blocks the whole publication snapshot', async () => {
  for (const health of [{error:'unavailable'}, {sessions:[{status:'non_session_conflicting_canonical_session'}]}]) {
    const endpoint = loadEndpoint(async url => Response.json(String(url).includes('/admin/hot-sync') ? {} : String(url).includes('/rpc/') ? health : []));
    const response = await endpoint.handleRequest(new Request('https://endpoint.test/?from=2026-09-27',{headers:{'x-hot-sync-admin-key':'fixture'}}));
    assert.equal(response.status,500);
    assert.equal((await response.json()).sessions,undefined);
  }
});
