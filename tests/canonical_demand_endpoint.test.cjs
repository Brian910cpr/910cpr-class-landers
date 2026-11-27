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
  assert.equal(projection.operational_has_stale_commitment,false);
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
  assert.deepEqual(calls[0].getAll('start_at'),['lt.2026-11-02T05:00:00.000Z']);
  assert.equal(calls[0].get('or'),'(start_at.gte.2026-11-01T04:00:00.000Z,consumption_end_at.gt.2026-11-01T04:00:00.000Z,and(consumption_end_at.is.null,end_at.gt.2026-11-01T04:00:00.000Z))');
  assert.equal(calls[1].get('offset'),'500');
  assert.doesNotMatch(calls[0].get('select'),/customers|email|phone/);
  assert.match(calls[0].get('select'), /courses!class_sessions_course_id_fkey\(course_key,name,enrollware_course_id\)/);
  assert.equal(body.sessions[0].external_course_id,'359474');
  assert.equal(body.sessions[0].catalog_course_id,null);
});

test('classification source failure or canonical conflict blocks the whole publication snapshot', async () => {
  for (const health of [{error:'unavailable'}, {sessions:[{status:'non_session_conflicting_canonical_session'}]}]) {
    const endpoint = loadEndpoint(async url => Response.json(String(url).includes('/admin/hot-sync') ? {} : String(url).includes('/rpc/') ? health : []));
    const response = await endpoint.handleRequest(new Request('https://endpoint.test/?from=2026-09-27',{headers:{'x-hot-sync-admin-key':'fixture'}}));
    assert.equal(response.status,500);
    assert.equal((await response.json()).sessions,undefined);
  }
});

test('authenticated HTTP response exposes an occupancy bit, never raw intake provenance or participant data', async () => {
  const messageId = 'dafefeed12345678';
  const privateEmail = 'intake-privacy-canary@example.test';
  const endpoint = loadEndpoint(async url => {
    if (String(url).includes('/admin/hot-sync')) return Response.json({});
    if (String(url).includes('/rpc/')) return Response.json({sessions:[]});
    return Response.json([{
      id:'synthetic-intake', status:'scheduled', source:'confirmed_booking_intake',
      registration_backend:'landerware', visibility:'private', registration_status:'closed',
      external_class_id:'80003', courses:{course_key:'fixture-bls',enrollware_course_id:209806}, start_at:'2026-11-01T15:00:00Z', end_at:'2026-11-01T16:00:00Z',
      consumption_start_at:'2026-11-01T15:00:00Z', consumption_end_at:'2026-11-01T16:00:00Z',
      location_id:'facility', lead_instructor_id:null, email:privateEmail,
      external_session_evidence:{kind:'registration_confirmation',gmail_message_id:messageId,email:privateEmail},
      registrations:[{status:'registered',registration_source:'enrollware_email_confirmation',
                      external_registration_id:null, email:privateEmail, customers:[{email:privateEmail}]}],
    }]);
  });
  const response = await endpoint.handleRequest(new Request(
    'https://endpoint.test/?from=2026-11-01&to=2026-11-02', {headers:{'x-hot-sync-admin-key':'fixture'}}));
  assert.equal(response.status,200);
  assert.match(response.headers.get('cache-control'),/no-store/);
  const body = await response.json();
  assert.deepEqual(Object.keys(body).sort(), [
    'active_registration_statuses','generated_at','non_session_sources','schema_version','sessions',
  ].sort());
  const row = body.sessions[0];
  assert.equal(row.external_course_id,null);
  assert.equal(row.catalog_course_id,'209806');
  assert.equal(row.course_key,'fixture-bls');
  assert.deepEqual(Object.keys(row).sort(), [
    'canonical_session_id','external_class_id','external_course_id','catalog_course_id','course_key','start_at','end_at',
    'consumption_start_at','consumption_end_at','location_id','location_name','lead_instructor_id',
    'lead_instructor_name','course_name','visibility','registration_backend','registration_status',
    'workspace_projection_status','workspace_session_id','operational_has_active_seat','operational_has_stale_commitment',
    'canonical_recorded_registration_count','source','session_status','active_registration_count',
    'count_available','demand_status','source_observed_at','reconciled_at','source_sha256',
    'freshness_minutes','demand_basis',
  ].sort());
  assert.equal(row.operational_has_active_seat,true);
  assert.equal(row.operational_has_stale_commitment,false);
  assert.equal(row.visibility,'private');
  assert.equal(row.registration_status,'closed');
  assert.equal(row.active_registration_count,null);
  assert.equal(row.count_available,false);
  assert.doesNotMatch(JSON.stringify(body), new RegExp(
    [messageId, 'privacy-canary', 'gmail_message_id','external_session_evidence','registration_confirmation'].join('|')));
});

test('catalog course ID is additive, strict, and never hides a disagreement with the session ID', () => {
  const base = {external_course_id:'359474',courses:{course_key:'bls',enrollware_course_id:'209806'}};
  const projected=api.projectDemand(base);
  assert.equal(projected.external_course_id,'359474');
  assert.equal(projected.catalog_course_id,'209806');
  assert.equal(projected.course_key,'bls');
  for (const invalid of [null, undefined, false, {}, ' 209806 ', 'BLS', '0', 0, -1, 0.1, Number.MAX_SAFE_INTEGER+1]) {
    assert.equal(api.projectDemand({...base,courses:{...base.courses,enrollware_course_id:invalid}}).catalog_course_id,null);
  }
});


test('HTTP demand includes ongoing carry-in until exclusive consumption end, without duplicate rows', async () => {
  const start='2026-11-01T04:00:00.000Z', stop='2026-11-02T05:00:00.000Z';
  const prior='2026-11-01T02:00:00.000Z', later='2026-11-01T05:00:00.000Z';
  const rows=[
    {id:'cleanup-carry-in',start_at:prior,end_at:start,consumption_end_at:later},
    {id:'instruction-carry-in',start_at:prior,end_at:later,consumption_end_at:null},
    {id:'cleanup-exact-end',start_at:prior,end_at:prior,consumption_end_at:start},
    {id:'instruction-exact-end',start_at:prior,end_at:start,consumption_end_at:null},
    {id:'in-range',start_at:start,end_at:later,consumption_end_at:later},
    {id:'in-range-missing-end',start_at:later,end_at:null,consumption_end_at:null},
    {id:'stop-boundary',start_at:stop,end_at:stop,consumption_end_at:stop}
  ];
  const calls=[];
  const endpoint=loadEndpoint(async url=>{
    if(String(url).includes('/admin/hot-sync')) return Response.json({});
    if(String(url).includes('/rpc/')) return Response.json({sessions:[]});
    const query=new URL(url).searchParams;
    calls.push(query);
    const bounds=query.getAll('start_at');
    const carry=query.get('or');
    // Simulate the PostgREST logic expression; the old lower start filter excludes carry-ins.
    const included=rows.filter(row=>row.start_at<stop &&
      (!bounds.includes('gte.'+start)||row.start_at>=start) &&
      (!carry||row.start_at>=start||(row.consumption_end_at??row.end_at)>start));
    return Response.json(included.map(row=>({...row,status:'scheduled',registration_backend:'landerware',registrations:[]})));
  });
  const response=await endpoint.handleRequest(new Request('https://endpoint.test/?from=2026-11-01&to=2026-11-02',{headers:{'x-hot-sync-admin-key':'fixture'}}));
  assert.equal(response.status,200);
  const body=await response.json();
  assert.deepEqual(body.sessions.map(row=>row.canonical_session_id).sort(),['cleanup-carry-in','in-range','in-range-missing-end','instruction-carry-in']);
  assert.equal(calls.length,1);
  assert.deepEqual(calls[0].getAll('start_at'),['lt.'+stop]);
  assert.equal(calls[0].get('or'),`(start_at.gte.${start},consumption_end_at.gt.${start},and(consumption_end_at.is.null,end_at.gt.${start}))`);
  assert.equal(body.sessions.find(row=>row.canonical_session_id==='cleanup-carry-in').consumption_end_at,later);
});

test('expired exact external roster retains operational commitment without certifying public seats', () => {
  const observed = new Date(Date.now() - 2 * 3600000).toISOString();
  const fixture = {id:'synthetic-stale',status:'scheduled',source:'enrollware_reconciled',
    registration_backend:'enrollware',external_class_id:'80004',visibility:'unlisted',
    registration_status:'closed',
    external_reconciliation:{complete:true,source_observed_at:observed,
      active_external_registration_ids:['fixture-reg'],active_registration_count:1},
    registrations:[{status:'registered',registration_source:'enrollware_reconciled',
      external_registration_id:'fixture-reg',canceled_at:null}]};
  const out=api.projectDemand(fixture);
  assert.equal(out.operational_has_active_seat,false);
  assert.equal(out.operational_has_stale_commitment,true);
  assert.equal(out.demand_status,'stale_reconciliation');
  assert.equal(out.count_available,false);
  assert.equal(out.active_registration_count,null);
  assert.equal(out.demand_basis,'unknown');
  assert.equal(out.visibility,'unlisted');
  assert.equal(out.registration_status,'closed');
  assert.equal(Object.hasOwn(out,'registrations'),false);
  assert.doesNotMatch(JSON.stringify(out),/fixture-reg/);

  for (const change of [
    {source:'manual'},
    {external_class_id:'non-numeric'},
    {status:'canceled'},
    {registrations:null},
    {registrations:[]},
    {registrations:[{...fixture.registrations[0],status:'canceled'}]},
    {registrations:[{...fixture.registrations[0],canceled_at:observed}]},
    {registrations:[{...fixture.registrations[0],external_registration_id:'different'}]},
    {registrations:[fixture.registrations[0],fixture.registrations[0]]},
    {external_reconciliation:{...fixture.external_reconciliation,complete:false}},
    {external_reconciliation:{...fixture.external_reconciliation,active_registration_count:2}},
    {external_reconciliation:{...fixture.external_reconciliation,active_external_registration_ids:['fixture-reg','fixture-reg'],active_registration_count:2}},
    {external_reconciliation:{...fixture.external_reconciliation,source_observed_at:new Date(Date.now()+2*3600000).toISOString()}}
  ]) {
    const denied=api.projectDemand({...fixture,...change});
    assert.equal(denied.operational_has_active_seat,false,JSON.stringify(change));
    assert.equal(denied.operational_has_stale_commitment,false,JSON.stringify(change));
    assert.equal(denied.active_registration_count,null);
  }
});
