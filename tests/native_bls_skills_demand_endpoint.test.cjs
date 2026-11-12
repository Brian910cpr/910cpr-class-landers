const test=require('node:test'),assert=require('node:assert/strict');
const {loadEndpoint}=require('./helpers/canonical_demand_endpoint.cjs');
const req=q=>new Request(`https://endpoint.test/?from=2030-01-01&to=2030-01-02${q}`,{headers:{'x-hot-sync-admin-key':'synthetic'}});
function proof(){const now=Date.now();return {schemaVersion:'native-bls-skills-publication-policy.v1',observedAt:new Date(now).toISOString(),validUntil:new Date(now+900000).toISOString(),nativeScopeId:'brian-shipyard-b.v1',physicalCourseId:'509474',context:'bls-skills',profileKey:'native_skills_shared',profileVersion:null,skillsEnabled:false,bundleEnabled:false,qualificationValidThrough:null,instructionMinutes:45,cleanupMinutes:15,capacity:2,skillsCents:5500,bundleCents:9500};}
test('BLS proof is opt-in and fails closed for missing/schema/tampered policy without changing ordinary demand',async()=>{
 let calls=0,p=proof(),missing=false;
 const api=loadEndpoint(async url=>{
  if(String(url).includes('native_bls_skills_publication_policy')){calls++;return Response.json(missing?{}:p,{status:missing?404:200});}
  return Response.json(String(url).includes('enrollware_reconciliation_health')?{sessions:[]}:String(url).includes('/class_sessions')?[]:{});
 });
 assert.equal((await api.handleRequest(req(''))).status,200);assert.equal(calls,0);
 for(const q of ['&native_bls_skills=0','&native_bls_skills=1&native_bls_skills=1'])assert.equal((await api.handleRequest(req(q))).status,400);
 const response=await api.handleRequest(req('&native_bls_skills=1'));assert.equal(response.status,200);assert.deepEqual((await response.json()).native_bls_skills_policy_proof,p);
 for(const patch of [{physicalCourseId:'210549'},{bundleEnabled:true},{profileVersion:2},{extra:'secret-like-data'},{capacity:6},{skillsCents:0},{skillsEnabled:true},
  {validUntil:'2099-01-01T00:00:00Z'}]){p={...proof(),...patch};assert.equal((await api.handleRequest(req('&native_bls_skills=1'))).status,500);}
 missing=true;assert.equal((await api.handleRequest(req('&native_bls_skills=1'))).status,500);assert.equal((await api.handleRequest(req(''))).status,200);
});
