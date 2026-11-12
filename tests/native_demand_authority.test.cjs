const test = require('node:test');
const assert = require('node:assert/strict');
const {loadEndpoint} = require('./helpers/canonical_demand_endpoint.cjs');
const api = loadEndpoint(() => {throw Error('Unexpected network');});
const row = {id:'canonical',external_class_id:'12345',external_course_id:'456',registration_backend:'landerware',
 start_at:'2030-09-01T12:00:00Z',end_at:'2030-09-01T13:00:00Z',consumption_start_at:'2030-09-01T11:30:00Z',consumption_end_at:'2030-09-01T14:00:00Z',
 course_id:'course',resource_id:null,organization_id:null,record_scope:'operational',lead_instructor_id:'instructor',location_id:'location',
 status:'scheduled',registration_status:'open',visibility:'private',registrations:[{status:'registered'},{status:'active'}],
 external_reconciliation:{complete:true,source_observed_at:'2020-01-01T00:00:00Z',active_registration_count:0,active_external_registration_ids:[]},
 landerware_session_authority_events:[{enabled:true,revision:2,session_identity:['course','2030-09-01T12:00:00+00:00','2030-09-01T13:00:00+00:00','2030-09-01T11:30:00+00:00','2030-09-01T14:00:00+00:00','instructor','location',null,null,'12345','operational']}]};
const seats={registrationAuthority:'landerware-session-authority.v1',authorityRevision:2,registered:2,holds:1,unreconciledReserved:3,capacity:10,generatedIdentity:null,sessionIdentity:row.landerware_session_authority_events[0].session_identity,sessionStatus:row.status,registrationStatus:row.registration_status,visibility:row.visibility};
test('explicit native authority uses live occupied counts and preserves inherited reserve, holds and intervals',()=>{
 const result=api.projectDemand(row,seats);
 assert.equal(result.active_registration_count,6);
 assert.equal(result.canonical_recorded_registration_count,2);
 assert.equal(result.unreconciled_reserved_count,3);
 assert.equal(result.held_seat_count,1);
 assert.equal(result.count_available,true);
 assert.equal(result.freshness_minutes,null);
 assert.equal(result.source_observed_at,null);
 assert.equal(result.demand_basis,'native_authoritative_occupied_seats');
 for(const key of ['external_class_id','external_course_id','visibility','consumption_start_at','consumption_end_at','start_at','end_at']) assert.equal(result[key],row[key]);
 assert.equal(result.canonical_session_id,row.id);
 assert.equal('landerware_session_authority_events' in result,false);
});
test('native backend or a supplied seat object alone cannot bypass legacy freshness',()=>{
 for(const events of [undefined,[],[{enabled:false}]]) {
  const result=api.projectDemand({...row,landerware_session_authority_events:events},seats);
  assert.equal(result.count_available,false);
  assert.equal(result.active_registration_count,null);
  assert.equal(result.freshness_minutes,60);
 }
});
test('unknown, malformed, over-capacity and missing native counts fail closed',()=>{
 for(const bad of [null,{}, {...seats,registered:null},{...seats,holds:-1},{...seats,unreconciledReserved:undefined},{...seats,registered:20},{...seats,authorityRevision:0}]) assert.throws(()=>api.projectDemand(row,bad));
 assert.equal(api.projectDemand({...row,registrations:undefined},seats).active_registration_count,6);
});
test('native RPC uses only session ID and service authorization, never external registration service',async()=>{
 let rpc=0;
 const endpoint=loadEndpoint(async(url,options)=>{
  if(String(url).includes('/rpc/native_scheduling_seat_snapshot')) {
   rpc++;
   assert.deepEqual(JSON.parse(options.body),{p_session_id:'canonical'});
   assert.equal(options.headers.authorization,'Bearer fixture-only');
   return Response.json(seats);
  }
  assert.match(String(url),/^https:\/\/database\.test\/rest\/v1\/class_sessions/);
  assert.match(new URL(url).searchParams.get('select'),/authority_events.*\(enabled,revision,session_identity\)/);
  return Response.json([row,{...row,id:'legacy',landerware_session_authority_events:[]}]);
 });
 const result=await endpoint.loadDemand('2030-09-01','2030-09-02');
 assert.equal(result.length,2);assert.equal(rpc,1);
 assert.equal(result[0].active_registration_count,6);assert.equal(result[1].active_registration_count,null);
});
test('RPC rejection, revoked authority and identity changes block snapshot instead of hiding occupied session',async()=>{
 for(const response of [()=>Response.json({error:'native_authority_disabled'},{status:400}),()=>Response.json({error:'native_authority_identity_changed'},{status:400}),()=>Response.json({registered:0})]) {
  const endpoint=loadEndpoint(async url=>String(url).includes('/rpc/')?response():Response.json([row]));
  await assert.rejects(endpoint.loadDemand('2030-09-01','2030-09-02'));
 }
});

test('concurrent readmission cannot combine earlier row bounds with newer valid seat revision',()=>{
 assert.throws(()=>api.projectDemand(row,{...seats,authorityRevision:3}));
});
test('identity drift, missing fields, backend changes, and disabled latest revision fail snapshot',()=>{
 for(const changed of [{start_at:'2030-09-02T12:00:00Z'}, {resource_id:'new'}, {organization_id:'new'}, {course_id:undefined}, {registration_backend:'enrollware'}]) assert.throws(()=>api.projectDemand({...row,...changed},seats));
 assert.throws(()=>api.projectDemand({...row,landerware_session_authority_events:[...row.landerware_session_authority_events,{enabled:false,revision:3,session_identity:row.landerware_session_authority_events[0].session_identity}]},seats));
});
test('identity timestamps compare instants across offsets without losing microseconds or null semantics',()=>{
 assert.equal(api.projectDemand({...row,start_at:'2030-09-01T08:00:00.000000-04:00'},seats).active_registration_count,6);
 assert.throws(()=>api.projectDemand({...row,start_at:'2030-09-01T12:00:00.000001Z'},seats));
 assert.throws(()=>api.projectDemand({...row,resource_id:''},seats));
 const nullable={...row,consumption_start_at:null,landerware_session_authority_events:[{...row.landerware_session_authority_events[0],session_identity:row.landerware_session_authority_events[0].session_identity.map((value,index)=>index===3?null:value)}]};
 assert.equal(api.projectDemand(nullable,{...seats,sessionIdentity:nullable.landerware_session_authority_events[0].session_identity}).active_registration_count,6);
 assert.throws(()=>api.projectDemand({...nullable,consumption_start_at:undefined},seats));
});
test('latest event is selected by revision, not relationship order, and ambiguity fails closed',()=>{
 const current=row.landerware_session_authority_events[0];
 assert.equal(api.projectDemand({...row,landerware_session_authority_events:[current,{...current,revision:1}]},seats).authority_revision,2);
 assert.throws(()=>api.projectDemand({...row,landerware_session_authority_events:[current,current]},seats));
});
test('loadDemand refuses a newer valid readmission rather than publishing old bounds',async()=>{
 const endpoint=loadEndpoint(async url=>String(url).includes('/rpc/')?Response.json({...seats,authorityRevision:3}):Response.json([row]));
 await assert.rejects(endpoint.loadDemand('2030-09-01','2030-09-02'));
});
