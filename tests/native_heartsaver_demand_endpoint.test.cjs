const test=require('node:test'),assert=require('node:assert/strict');
const {loadEndpoint}=require('./helpers/canonical_demand_endpoint.cjs');
const api=loadEndpoint(()=>{throw Error('Unexpected network');});
const id='lw-11111111-1111-4111-8111-111111111111';
const row={id:'session',course_id:'306bc81a-0e09-49e1-8910-e05501222eb4',external_course_id:'344085',start_at:'2030-01-01T15:00:00Z',end_at:'2030-01-01T16:30:00Z',consumption_start_at:'2030-01-01T15:00:00Z',consumption_end_at:'2030-01-01T16:45:00Z',lead_instructor_id:'brian',location_id:'shipyard',resource_id:null,organization_id:null,external_class_id:id,record_scope:'operational',registration_backend:'landerware',source:'landerware_event',status:'scheduled',registration_status:'open',visibility:'public',external_session_evidence:{materializedBy:'native_full_course'},native_checkout_generated_sessions:{identity_hash:'a'.repeat(32),state:'holding'}};
const booking={schemaVersion:'native-heartsaver-session-booking.v1',publicCourseId:'344085',canonicalCourseId:row.course_id,coursePolicyKey:'heartsaver-full:344085.v1',profileKey:'native_heartsaver_344085_draft',profileVersion:1,sourceSessionId:id,identityWitness:'a'.repeat(32),capacity:3,remaining:1,instructionMinutes:90,cleanupMinutes:15};
const seats={registrationAuthority:'landerware-generated-session.v1',authorityRevision:null,generatedIdentity:'a'.repeat(32),sessionIdentity:[row.course_id,row.start_at,row.end_at,row.consumption_start_at,row.consumption_end_at,row.lead_instructor_id,row.location_id,null,null,id,'operational'],sessionStatus:'scheduled',registrationStatus:'open',visibility:'public',capacity:3,registered:1,holds:1,unreconciledReserved:0,heartsaverBooking:booking};
test('exact Heartsaver DTO rejects aliases, extra fields, identity and geometry drift without losing occupancy',()=>{
 assert.equal(api.projectDemand(row,seats).native_heartsaver_booking_admission.remaining,1);
 assert.equal(api.projectDemand(row,{...seats,heartsaverBooking:null}).active_registration_count,2);
 for(const patch of [{publicCourseId:'209808'},{canonicalCourseId:'bad'},{profileKey:'bls'},{profileVersion:0},{capacity:6},{remaining:2},{identityWitness:'b'.repeat(32)},{instructionMinutes:120},{cleanupMinutes:30},{extra:true}])assert.throws(()=>api.projectDemand(row,{...seats,heartsaverBooking:{...booking,...patch}}));
});
const req=q=>new Request(`https://endpoint.test/?from=2030-01-01&to=2030-01-02${q}`,{headers:{'x-hot-sync-admin-key':'synthetic'}});
test('optional policy RPC is never fetched on ordinary demand and missing RPC fails only opted-in request',async()=>{
 let policyCalls=0;const endpoint=loadEndpoint(async url=>{
  if(String(url).includes('native_heartsaver_publication_policy')){policyCalls++;return Response.json({error:'missing'},{status:404});}
  if(String(url).includes('enrollware_reconciliation_health'))return Response.json({sessions:[]});
  return Response.json(String(url).includes('/class_sessions')?[]:{});
 });
 assert.equal((await endpoint.handleRequest(req(''))).status,200);assert.equal(policyCalls,0);
 assert.equal((await endpoint.handleRequest(req('&native_heartsaver=0'))).status,400);assert.equal(policyCalls,0);
 assert.equal((await endpoint.handleRequest(req('&native_heartsaver=1&native_heartsaver=1'))).status,400);assert.equal(policyCalls,0);
 assert.equal((await endpoint.handleRequest(req('&native_heartsaver=1'))).status,500);assert.equal(policyCalls,1);
});
test('optional proof returns database lease and exact independent course scopes',async()=>{
 const courses=Object.fromEntries(['209809','344085'].map(c=>[c,{materializationEnabled:false,nativePublicationEnabled:false,nativeScopeId:'brian-shipyard-b.v1',coursePolicyKey:`heartsaver-full:${c}.v1`,canonicalCourseId:c==='209809'?'23dfcfa7-4224-46ed-8d45-64d43d5425db':row.course_id,pageKey:'heartsaver',instructionMinutes:c==='209809'?120:90,cleanupMinutes:c==='209809'?30:15,maxStudents:null,qualificationValidThrough:null}]));
 const observed=Date.now()+1000;
 const proof={schemaVersion:'native-heartsaver-publication-policy.v1',observedAt:new Date(observed).toISOString(),validUntil:new Date(observed+900000).toISOString(),courses};
 const endpoint=loadEndpoint(async url=>Response.json(String(url).includes('native_heartsaver_publication_policy')?proof:String(url).includes('enrollware_reconciliation_health')?{sessions:[]}:String(url).includes('/class_sessions')?[]:{}));
 const response=await endpoint.handleRequest(req('&native_heartsaver=1'));assert.equal(response.status,200);const body=await response.json();assert.deepEqual(body.native_heartsaver_policy_proof,proof);
 assert.ok(Date.parse(body.generated_at)<Date.parse(proof.observedAt),'later policy observation does not replace demand acquisition timestamp');
 courses['344085'].nativePublicationEnabled=true;assert.equal((await endpoint.handleRequest(req('&native_heartsaver=1'))).status,500);
});
