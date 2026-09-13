const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {stripTypeScriptTypes} = require('node:module');
const base = 'https://example.supabase.co';
const session = '10000000-0000-4000-8000-000000000001';
const docId = '20000000-0000-4000-8000-000000000001';
const doc = {id:docId,file_name:'Roster.pdf',content_type:'application/pdf',storage_bucket:'class-session-docs',storage_path:`${session}/date/${docId}-Roster.pdf`};
function runtime({authenticated=true,document=doc,rpc={ok:true,removed_id:docId},storageStatus=200}={}) {
  const calls=[]; let handler;
  const context = vm.createContext({Request,Response,Headers,URL,TextEncoder,crypto,File,AbortSignal,console:{error(){}},
    Deno:{env:{get:n=>n==='SUPABASE_URL'?base:'server-test-key'},serve:fn=>handler=fn},
    fetch:async(url,options={})=>{
      calls.push({url,options});
      if(url==='https://schedule.910cpr.com/admin/hot-sync')return Response.json({ok:authenticated},{status:authenticated?200:401});
      if(url.includes('/rest/v1/class_session_documents?'))return Response.json(document?[document]:[]);
      if(url.includes('/storage/v1/object/sign/'))return Response.json({signedURL:`/object/sign/class-session-docs/${doc.storage_path}?token=test-signature`},{status:storageStatus});
      if(url.endsWith('/rpc/remove_instructor_document'))return Response.json(rpc);
      throw Error('Unexpected fetch: '+url);
    }});
  let source=fs.readFileSync('supabase/functions/_shared/owner-auth.ts','utf8').replace('export async function authorizedOwner','async function authorized');
  source+='\n'+fs.readFileSync('supabase/functions/instructor-workbench/documents.ts','utf8').replaceAll('export ','');
  source+='\n'+fs.readFileSync('supabase/functions/instructor-workbench/index.ts','utf8').replace(/^import .*\n/gm,'');
  vm.runInContext(stripTypeScriptTypes(source),context);
  const send=(method='GET',body,headers={'x-hot-sync-admin-key':'test-token'},path=`sessions/${session}/documents/${docId}`)=>handler(new Request(`${base}/functions/v1/instructor-workbench/${path}`,{method,headers,...(body!==undefined?{body:JSON.stringify(body)}:{})}));
  return {send,calls};
}
test('no credentials cannot view or remove documents',async()=>{
  const r=runtime();for(const method of ['GET','DELETE'])assert.equal((await r.send(method,undefined,{})).status,401);assert.equal(r.calls.length,0);
});
test('rejected owner key stops before document queries',async()=>{
  const r=runtime({authenticated:false});for(const method of ['GET','DELETE'])assert.equal((await r.send(method,method==='DELETE'?{confirm:true}:undefined)).status,401);assert.ok(r.calls.every(c=>c.url.includes('schedule.910cpr.com/admin/hot-sync')));
});
test('view looks up the exact class/document and signs a private five-minute URL',async()=>{
  const r=runtime(),response=await r.send(),body=await response.json();assert.equal(response.status,200);assert.equal(body.document.url,`${base}/storage/v1/object/sign/class-session-docs/${doc.storage_path}?token=test-signature`);
  assert.ok(r.calls[1].url.includes(`class_session_id=eq.${session}&id=eq.${docId}`));assert.equal(JSON.parse(r.calls[2].options.body).expiresIn,300);
  assert.equal(response.headers.get('cache-control'),'no-store');assert.equal(body.document.storage_path,undefined);
});
test('wrong class/document does not sign a URL',async()=>{
  const r=runtime({document:null});assert.equal((await r.send()).status,404);assert.equal(r.calls.length,2);
});
test('a storage path belonging to another class cannot be signed',async()=>{
  const r=runtime({document:{...doc,storage_path:`other/${docId}.pdf`}});assert.equal((await r.send()).status,503);assert.equal(r.calls.length,2);
});
test('missing storage object has a useful error',async()=>{
  const r=runtime({storageStatus:404}),response=await r.send();assert.equal(response.status,503);assert.equal((await response.json()).error,'document_unavailable');
});
test('remove requires explicit confirmation before calling the transaction',async()=>{
  const r=runtime();assert.equal((await r.send('DELETE',{confirm:false})).status,400);assert.equal(r.calls.length,1);
});
test('confirmed removal passes only exact IDs and server-verified actor to atomic RPC',async()=>{
  const r=runtime(),response=await r.send('DELETE',{confirm:true,storage_path:'do-not-trust'});assert.equal(response.status,200);
  const body=JSON.parse(r.calls[1].options.body);assert.equal(body.p_class_session_id,session);assert.equal(body.p_document_id,docId);assert.equal(body.p_actor_label,'Authenticated LanderWare owner');assert.equal(Object.keys(body).length,3);assert.equal(r.calls.length,2);
});
test('compliance evidence cannot be silently detached',async()=>{
  const r=runtime({rpc:{error:'document_in_use'}}),response=await r.send('DELETE',{confirm:true});assert.equal(response.status,409);assert.equal((await response.json()).error,'document_in_use');
});
test('repeat removal returns success and invalid IDs cannot alter filters',async()=>{
  const r=runtime({rpc:{ok:true,already_removed:true,removed_id:docId}});assert.equal((await r.send('DELETE',{confirm:true})).status,200);
  assert.equal((await r.send('DELETE',{confirm:true},{'x-hot-sync-admin-key':'test-token'},`sessions/${session}/documents/not-a-uuid`)).status,404);
});
test('CORS permits DELETE for the existing login header',async()=>{
  const r=runtime(),response=await r.send('OPTIONS');assert.equal(response.status,204);assert.ok(response.headers.get('access-control-allow-methods').includes('DELETE'));assert.equal(r.calls.length,0);
});

test('corporate sessions never authorize owner document actions',async()=>{
 const r=runtime();for(const method of ['GET','DELETE'])assert.equal((await r.send(method,undefined,{'x-maxim-session':'corporate-token'})).status,401);assert.equal(r.calls.length,0);
});
