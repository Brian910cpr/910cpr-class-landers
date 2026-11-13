const test=require('node:test'),assert=require('node:assert/strict');
const {loadEndpoint}=require('./helpers/canonical_demand_endpoint.cjs');
const now=new Date().toISOString(),later=new Date(Date.parse(now)+900000).toISOString();
const proof={schemaVersion:'native-advanced-publication-policy.v1',observedAt:now,validUntil:later,courses:Object.fromEntries(['241108','209818','209805','251496'].map(c=>[c,{materializationEnabled:false,nativePublicationEnabled:false}]))};
function harness(enabled=true){const calls=[];const api=loadEndpoint(async(url,init={})=>{url=String(url);calls.push(url);
 if(url.includes('/admin/hot-sync'))return new Response('',{status:200});
 if(url.includes('/rpc/native_advanced_publication_policy'))return Response.json(proof);
 if(url.includes('/rpc/native_publish_advanced_offers'))return Response.json(JSON.parse(init.body).p_offers.length);
 if(url.includes('/rpc/enrollware_reconciliation_health'))return Response.json({sessions:[]});
 return Response.json(url.includes('/class_sessions')?[]:{});
},{NATIVE_ADVANCED_PUBLICATION_ENABLED:enabled?'true':'false'});return {api,calls};}
const request=(query,body)=>new Request('https://endpoint.test/?'+query,{headers:{'x-hot-sync-admin-key':'synthetic','content-type':'application/json'},...(body?{method:'POST',body:JSON.stringify(body)}:{})});
test('advanced policy is opt-in, default-off, fresh and read-only',async()=>{
 const h=harness();assert.equal((await h.api.handleRequest(request('from=2030-01-01&to=2030-01-02&native_advanced=1'))).status,200);assert.ok(h.calls.some(u=>u.includes('native_advanced_publication_policy')));assert.equal(h.calls.some(u=>u.includes('native_publish_advanced_offers')),false);
 for(const q of ['native_advanced=0','native_advanced=1&native_advanced=1'])assert.equal((await h.api.handleRequest(request('from=2030-01-01&to=2030-01-02&'+q))).status,400);
 const off=harness(false);assert.equal((await off.api.handleRequest(request('from=2030-01-01&to=2030-01-02&native_advanced=1'))).status,500);assert.equal(off.calls.some(u=>u.includes('native_advanced_publication_policy')),false);
});
test('only explicit authenticated bounded advanced publication action can admit leases',async()=>{
 const h=harness();const body={action:'publish_advanced_offers',offers:[{kind:'synthetic-local-fixture'}]};
 assert.equal((await h.api.handleRequest(request('advanced_publish=1',body))).status,200);
 assert.equal(h.calls.filter(u=>u.includes('native_publish_advanced_offers')).length,1);
 assert.equal((await h.api.handleRequest(request('advanced_publish=1&advanced_publish=1',body))).status,400);
 assert.equal((await h.api.handleRequest(request('advanced_publish=1',{...body,extra:'no'}))).status,400);
 const off=harness(false);assert.equal((await off.api.handleRequest(request('advanced_publish=1',body))).status,400);assert.equal(off.calls.some(u=>u.includes('native_publish_advanced_offers')),false);
 assert.equal((await h.api.handleRequest(new Request('https://endpoint.test/?advanced_publish=1',{method:'POST',body:JSON.stringify(body)}))).status,401);
});
