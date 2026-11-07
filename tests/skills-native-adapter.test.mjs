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
