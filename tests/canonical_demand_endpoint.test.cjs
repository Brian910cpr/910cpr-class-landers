const test = require('node:test');
const assert = require('node:assert/strict');
const {loadEndpoint} = require('./helpers/canonical_demand_endpoint.cjs');

const api = loadEndpoint(() => { throw Error('Unexpected network call'); });
test('projection reports missing or stale workspace and carries explicit occupied window',()=>{
  const row={id:'canonical',start_at:'2030-10-03T16:30:00Z',end_at:'2030-10-03T17:00:00Z',
    consumption_end_at:'2030-10-03T17:30:00Z',people:{display_name:'Instructor'},registrations:[],registration_backend:'landerware'};
  assert.equal(api.projectDemand(row).workspace_projection_status,'missing');
  assert.equal(api.projectDemand({...row,landerware_sessions:[{id:'workspace',starts_at:'2030-10-03T14:00:00Z',ends_at:row.end_at}]}).workspace_projection_status,'stale');
  const current=api.projectDemand({...row,landerware_sessions:[{id:'workspace',starts_at:row.start_at,ends_at:row.end_at}]});
  assert.equal(current.workspace_projection_status,'current');
  assert.equal(current.lead_instructor_name,'Instructor');
  assert.equal(current.consumption_end_at,'2030-10-03T17:30:00Z');
});
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
  const row = {id:'fixture',registration_backend:'landerware',registrations:[{status:'registered'},{status:'confirmed'},{status:'completed'},{status:'active'},{status:'canceled'},{status:'rescheduled'},{status:'no_show'}]};
  assert.equal(api.projectDemand(row).active_registration_count,4);
  assert.equal(api.projectDemand(row).canonical_recorded_registration_count,4);
  assert.equal(api.projectDemand({...row,registrations:[]}).active_registration_count,0);
  assert.equal(api.projectDemand({...row,registrations:null}).active_registration_count,null);
  assert.equal(api.projectDemand({...row,registration_backend:'enrollware'}).active_registration_count,null);
});

test('numeric legacy identity with native active seats signals occupied demand without inventing a known external roster', () => {
  // Synthetic numeric/legacy source shape: LanderWare-owned active rows
  // can coexist with a numeric legacy ID and absent external reconciliation.
  const row = {id:'numeric-native',status:'scheduled',source:'landerware_public_offer',
    visibility:'private',registration_status:'closed',registration_backend:'landerware',
    external_class_id:'80001',
    registrations:[{status:'active',registration_source:'landerware_native_checkout',external_registration_id:null}]};
  const projection=api.projectDemand(row);
  assert.equal(projection.count_available,false);
  assert.equal(projection.active_registration_count,null);
  assert.equal(projection.canonical_recorded_registration_count,1);
  assert.equal(projection.demand_basis,'unknown');
  assert.equal(projection.operational_has_active_seat,true);
  assert.equal(projection.visibility,'private');
  assert.equal(projection.registration_status,'closed');
  assert.equal(Object.hasOwn(projection,'registrations'),false);
  assert.equal(Object.hasOwn(projection,'customers'),false);

  const mixed=api.projectDemand({...row,registrations:[
    {status:'registered',registration_source:'enrollware_email_confirmation',external_registration_id:null},
    {status:'active',registration_source:'landerware_native_checkout',external_registration_id:null},
    {status:'active',registration_source:'landerware_native_checkout',external_registration_id:null},
    {status:'active',registration_source:'landerware_native_checkout',external_registration_id:null}
  ]});
  assert.equal(mixed.active_registration_count,null);
  assert.equal(mixed.canonical_recorded_registration_count,4);
  assert.equal(mixed.operational_has_active_seat,true);

  for(const change of [
    {registrations:[{status:'registered',registration_source:'enrollware_email_confirmation'}]},
    {registrations:[{status:'canceled',registration_source:'landerware_native_checkout'}]},
    {registrations:[{status:'active',registration_source:'enrollware'}]},
    {registration_backend:'enrollware'},
    {source:'enrollware_reconciled'},
    {status:'canceled'}
  ]) {
    const unproven=api.projectDemand({...row,...change});
    assert.equal(unproven.operational_has_active_seat,false);
    assert.equal(unproven.active_registration_count,null);
  }
});

test('verified email-confirmed private intake is internal occupancy, not external roster or a public seat', () => {
  const fixture = {id:'synthetic-private-intake',status:'scheduled',
    source:'confirmed_booking_intake',registration_backend:'landerware',
    visibility:'private',registration_status:'closed',external_class_id:'80002',
    external_session_evidence:{kind:'registration_confirmation',gmail_message_id:'0123456789abcdef'},
    registrations:[{status:'registered',registration_source:'enrollware_email_confirmation',external_registration_id:null}]};
  const projected = api.projectDemand(fixture);
  assert.equal(projected.operational_has_active_seat,true);
  assert.equal(projected.count_available,false);
  assert.equal(projected.active_registration_count,null);
  assert.equal(projected.demand_basis,'unknown');
  assert.equal(projected.canonical_recorded_registration_count,1);
  assert.equal(projected.visibility,'private');
  assert.equal(projected.registration_status,'closed');
  assert.equal(Object.hasOwn(projected,'registrations'),false);
  assert.equal(Object.hasOwn(projected,'external_session_evidence'),false);

  for (const change of [
    {source:'manual'},
    {registration_backend:'enrollware'},
    {status:'canceled'},
    {external_session_evidence:{kind:'registration_confirmation'}},
    {external_session_evidence:{kind:'owner_confirmed_booking',gmail_message_id:'0123456789abcdef'}},
    {registrations:[{status:'canceled',registration_source:'enrollware_email_confirmation'}]},
    {registrations:[{status:'registered',registration_source:'owner_voice_fragment'}]},
    {registrations:null}
  ]) {
    const unverified = api.projectDemand({...fixture,...change});
    assert.equal(unverified.operational_has_active_seat,false,JSON.stringify(change));
    assert.equal(unverified.active_registration_count,null);
  }
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
