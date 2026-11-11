const test=require('node:test');const assert=require('node:assert/strict');
const {loadEndpoint}=require('./helpers/canonical_demand_endpoint.cjs');
const api=loadEndpoint(()=>{throw Error('Unexpected network');});
const row={id:'native',course_id:'course',start_at:'2030-01-01T15:00:00Z',end_at:'2030-01-01T17:00:00Z',consumption_start_at:'2030-01-01T15:00:00Z',consumption_end_at:'2030-01-01T17:30:00Z',lead_instructor_id:'instructor',location_id:'venue',resource_id:null,organization_id:null,external_class_id:'lw-11111111-1111-4111-8111-111111111111',record_scope:'operational',registration_backend:'landerware',source:'landerware_event',status:'scheduled',registration_status:'open',visibility:'public',external_session_evidence:{materializedBy:'native_full_course'},registrations:[],landerware_session_authority_events:[],native_checkout_generated_sessions:{identity_hash:'a'.repeat(32),state:'holding'}};
const identity=r=>[r.course_id,r.start_at,r.end_at,r.consumption_start_at,r.consumption_end_at,r.lead_instructor_id,r.location_id,r.resource_id,r.organization_id,r.external_class_id,r.record_scope];
const seats={registrationAuthority:'landerware-generated-session.v1',authorityRevision:null,generatedIdentity:'a'.repeat(32),sessionIdentity:identity(row),sessionStatus:'scheduled',registrationStatus:'open',visibility:'public',capacity:6,registered:1,holds:2,unreconciledReserved:0};
test('new generated sessions without adoption include held seats and active RPC registrations',()=>{
 const result=api.projectDemand(row,seats);assert.equal(result.active_registration_count,3);assert.equal(result.canonical_registered_count,1);assert.equal(result.held_seat_count,2);assert.equal(result.freshness_minutes,null);
 assert.equal(result.registration_authority,'landerware-generated-session.v1');
 assert.equal(api.projectDemand({...row,native_checkout_generated_sessions:[row.native_checkout_generated_sessions]},seats).active_registration_count,3);
});
test('missing/released/ambiguous witness or changed returned identity fails closed',()=>{
 for(const witness of [undefined,null,[],[row.native_checkout_generated_sessions,row.native_checkout_generated_sessions],{...row.native_checkout_generated_sessions,state:'released'}])assert.throws(()=>api.projectDemand({...row,native_checkout_generated_sessions:witness},seats));
 for(const changed of [{generatedIdentity:'b'.repeat(32)},{sessionIdentity:identity({...row,start_at:'2030-01-01T15:00:00.000001Z'})},{sessionStatus:'cancelled'},{registrationStatus:'closed'},{visibility:'private'},{authorityRevision:1}])assert.throws(()=>api.projectDemand(row,{...seats,...changed}));
});
test('materialized provenance routes through snapshot RPC and never falls back to registration-only count',async()=>{
 let calls=0;
 const endpoint=loadEndpoint(async url=>{if(String(url).includes('/rpc/')){assert.match(String(url),/native_scheduling_seat_snapshot$/);calls++;return Response.json(seats);}return Response.json([row]);});
 assert.equal((await endpoint.loadDemand('2030-01-01','2030-01-02'))[0].active_registration_count,3);assert.equal(calls,1);
 const failed=loadEndpoint(async url=>String(url).includes('/rpc/')?Response.json({error:'native_generated_authority_unavailable'},{status:400}):Response.json([{...row,native_checkout_generated_sessions:null}]));
 await assert.rejects(failed.loadDemand('2030-01-01','2030-01-02'));
});
test('canonical booking admission is separate from counts and exact snapshot capacity/profile proof',()=>{
 const session={...row,external_course_id:'209806'};
 const booking={schemaVersion:'native-session-booking.v1',publicCourseId:'209806',profileVersion:3,capacity:6,remaining:3};
 const projected=api.projectDemand(session,{...seats,publicBooking:booking});
 assert.equal(projected.native_booking_admission.remaining,3);
 assert.equal(projected.native_booking_admission.capacity,6);
 assert.equal(api.projectDemand(session,{...seats,publicBooking:null}).active_registration_count,3);
 assert.equal(api.projectDemand(session,{...seats,publicBooking:null}).native_booking_admission,null);
 for(const change of [{remaining:4},{capacity:7},{profileVersion:0},{publicCourseId:'210549'},{publicCourseId:'359474'}])
  assert.throws(()=>api.projectDemand(session,{...seats,publicBooking:{...booking,...change}}));
 assert.throws(()=>api.projectDemand({...session,visibility:'private'},{...seats,visibility:'private',publicBooking:booking}));
});
