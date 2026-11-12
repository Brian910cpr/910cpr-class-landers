const test=require('node:test'),assert=require('node:assert/strict');
const {loadEndpoint}=require('./helpers/canonical_demand_endpoint.cjs');
const request=(body,headers={})=>new Request('https://endpoint.test/',{method:'POST',headers:{'content-type':'application/json','x-hot-sync-admin-key':'owner-fixture',...headers},body});
test('maintenance requires existing owner authentication and exact bounded action; no callback token or arbitrary RPC',async()=>{
 let calls=[];const api=loadEndpoint(async(url,options)=>{
  calls.push({url:String(url),options});
  if(String(url).includes('/admin/hot-sync'))return Response.json({});
  assert.match(String(url),/\/rpc\/native_publication_release_expired$/);
  assert.equal(options.headers.authorization,'Bearer fixture-only');assert.deepEqual(JSON.parse(options.body),{});
  return Response.json({schemaVersion:'native-publication-maintenance.v1',released:1,examined:1,batchLimit:32,observedAt:'2030-01-01T00:00:00Z'});
 });
 assert.equal((await api.handleRequest(request('{"action":"release_expired_native_holds"}',{'x-hot-sync-admin-key':''}))).status,401);assert.equal(calls.length,0);
 for(const body of ['{}','{"action":"other"}','{"action":"release_expired_native_holds","session":"other"}','x'.repeat(129),'not json']){
  calls=[];assert.equal((await api.handleRequest(request(body))).status,400);assert.equal(calls.filter(c=>c.url.includes('/rpc/')).length,0);
 }
 calls=[];const result=await api.handleRequest(request('{"action":"release_expired_native_holds"}'));assert.equal(result.status,200);assert.equal((await result.json()).released,1);assert.equal(calls.filter(c=>c.url.includes('/rpc/')).length,1);
});
test('ordinary demand GET never scans release history or invokes mutation',async()=>{
 let mutated=false;
 const api=loadEndpoint(async url=>{
  if(String(url).includes('/admin/hot-sync'))return Response.json({});
  if(String(url).includes('/rpc/native_publication_release_expired')){mutated=true;throw Error('GET mutation');}
  if(String(url).includes('/rpc/native_released_scheduling_sessions'))throw Error('unrequested history scan');
  if(String(url).includes('/rpc/'))return Response.json({sessions:[]});
  return Response.json([]);
 });
 const result=await api.handleRequest(new Request('https://endpoint.test/',{headers:{'x-hot-sync-admin-key':'owner-fixture'}}));
 assert.equal(result.status,200);assert.equal(mutated,false);assert.deepEqual((await result.json()).released_native_sessions,[]);
});
const nativeId=n=>`lw-${String(n).padStart(8,'0')}-aaaa-4aaa-8aaa-aaaaaaaaaaaa`;
const proofRequest=ids=>new Request('https://endpoint.test/?'+new URLSearchParams({projection:'native-release-proof',release_ids:ids.join(',')}),{headers:{'x-hot-sync-admin-key':'owner-fixture'}});
const proofBody=ids=>({schema_version:'910cpr-native-release-proof.v1',generated_at:'2030-01-01T00:00:00Z',complete:true,requested_external_class_ids:ids,released_native_sessions:[]});
test('release proof GET requests only exact retained IDs without active-demand scans or mutations',async()=>{
 const ids=Array.from({length:64},(_,i)=>nativeId(i));let calls=[];
 const api=loadEndpoint(async(url,options)=>{
  calls.push(String(url));
  if(String(url).includes('/admin/hot-sync'))return Response.json({});
  assert.match(String(url),/\/rpc\/native_released_scheduling_sessions$/);
  assert.equal(options.method,'POST');assert.equal(options.redirect,'error');
  assert.deepEqual(JSON.parse(options.body),{p_external_class_ids:ids});
  return Response.json(proofBody(ids));
 });
 const result=await api.handleRequest(proofRequest(ids));
 assert.equal(result.status,200);assert.deepEqual((await result.json()).requested_external_class_ids,ids);assert.equal(calls.length,2);
});
test('release proof input bounds, invalid IDs, duplicates, and missing auth reject before RPC',async()=>{
 let reads=0;
 const api=loadEndpoint(async url=>{if(String(url).includes('/admin/hot-sync'))return Response.json({});reads++;throw Error('must not reach database');});
 for(const ids of [[],['legacy'],['lw-invalid'],[nativeId(1),nativeId(1)],Array.from({length:65},(_,i)=>nativeId(i))])
  assert.equal((await api.handleRequest(proofRequest(ids))).status,400);
 for(const tail of ['&projection=native-release-proof','&release_ids='+nativeId(1),'&from=2030-01-01'])
  assert.equal((await api.handleRequest(new Request(proofRequest([nativeId(1)]).url+tail,{headers:{'x-hot-sync-admin-key':'owner-fixture'}}))).status,400);
 const noAuth=new Request(proofRequest([nativeId(1)]).url);
 assert.equal((await api.handleRequest(noAuth)).status,401);assert.equal(reads,0);
});
test('release proof never substitutes empty success for RPC failure or incomplete coverage',async()=>{
 const ids=[nativeId(1)];
 for(const result of [Response.json({}, {status:503}),Response.json([]),Response.json({...proofBody(ids),complete:false}),
    Response.json({...proofBody(ids),requested_external_class_ids:[]}),
    Response.json({...proofBody(ids),released_native_sessions:[{external_class_id:nativeId(2)}]})]){
  const api=loadEndpoint(async url=>String(url).includes('/admin/hot-sync')?Response.json({}):result);
  assert.equal((await api.handleRequest(proofRequest(ids))).status,500);
 }
});
