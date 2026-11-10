// Exercises the deployed Deno adapter with fully mocked fetch/config; no network.
import test from 'node:test';
import assert from 'node:assert/strict';
globalThis.Deno={env:{get:name=>({SUPABASE_URL:'https://fixture-db.invalid',SUPABASE_SERVICE_ROLE_KEY:'fixture-only',SKILLS_SESSION_RESERVATIONS_ENABLED:'true'}[name])}};
const {handler}=await import('../supabase/functions/skills-session-reservation/index.ts');
test('deployed adapter uses service RPC, accepts a persisted replay and sends no mail/payment',async()=>{
  const previous=globalThis.fetch,calls=[];
  globalThis.fetch=async(url,init)=>{
    calls.push({url:String(url),init});
    assert.equal(String(url),'https://fixture-db.invalid/rest/v1/rpc/reserve_skills_session_native');
    assert.equal(init.method,'POST');assert.equal(init.headers.apikey,'fixture-only');
    assert.equal(JSON.parse(init.body).p_offer.selectionId,'skills:saved');
    return new Response(JSON.stringify({ok:true,status:'reserved',registrationId:'fixture-registration',sessionId:'fixture-session',idempotentReplay:true,paymentStatus:'pending'}));
  };
  try{
    const response=await handler(new Request('https://test/reserve',{method:'POST',headers:{'idempotency-key':'11111111-1111-4111-8111-111111111111','content-type':'application/json'},body:JSON.stringify({context:'cpr-aed',selectionId:'skills:saved',student:{firstName:'Fixture',lastName:'Student',email:'fixture@example.invalid',onlineCompleted:true}})}));
    assert.equal(response.status,200);assert.equal((await response.json()).idempotentReplay,true);assert.equal(calls.length,1);
  }finally{globalThis.fetch=previous;}
});

test('cached skills forms use the shared per-course policy and payment gate instead of direct uploads',async()=>{
 const previous=globalThis.fetch,calls=[];let disabled=false;
 globalThis.fetch=async(url,init)=>{
  const action=String(url).split('/').at(-1);calls.push(action);assert.match(String(url),/functions\/v1\/public-registration\/generic\//);
  assert.equal(init.headers['idempotency-key'],'11111111-1111-4111-8111-111111111111');
  if(action==='form')return Response.json({ok:true,context:'hsi-blended',profile:{uploads:disabled?[]:[{key:'completion_document',documentType:'online_completion'}]},session:{startsAt:'2031-01-01T14:00:00Z',location:'Fixture'}});
  if(action==='checkout')return Response.json({ok:true,checkoutUrl:'https://checkout.stripe.com/c/pay/fixture'});
  if(action==='upload'){const body=JSON.parse(init.body);assert.equal(body.requirementKey,'completion_document');assert.equal(body.studentIndex,0);assert.equal(body.path,undefined);return Response.json({ok:true,evidenceStatus:'received',approved:false});}
  throw Error('unexpected_action');
 };
 const request=(route,extra={})=>new Request('https://test/'+route,{method:'POST',headers:{'idempotency-key':'11111111-1111-4111-8111-111111111111','content-type':'application/json'},body:JSON.stringify({context:'hsi-blended',...extra})});
 try{
  const checkout=await handler(request('checkout'));assert.equal(checkout.status,200);assert.match((await checkout.json()).checkoutUrl,/checkout.stripe.com/);
  const upload=await handler(request('certificate',{path:'forged',certificate:{type:'application/pdf',base64:btoa('%PDF-fixture')}}));assert.equal(upload.status,200);assert.equal((await upload.json()).approved,false);
  disabled=true;const denied=await handler(request('certificate',{certificate:{}}));assert.equal(denied.status,409);assert.equal((await denied.json()).error,'uploads_disabled');assert.deepEqual(calls,['form','checkout','form','upload','form']);
 }finally{globalThis.fetch=previous;}
});
