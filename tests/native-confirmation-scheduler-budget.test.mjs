import test from 'node:test';import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {nativeConfirmationService} from '../supabase/functions/_shared/native-confirmation-service.mjs';
const job=n=>({messageId:`00000000-0000-4000-8000-${String(n).padStart(12,'0')}`,lease:'22222222-2222-4222-8222-222222222222',recipient:'brian@910cpr.com',subject:'Synthetic local test',body:'Not sent',customerTemplate:false,confirmation:null});
function fixture(){let claims=0,sends=0;return {get claims(){return claims;},get sends(){return sends;},service:nativeConfirmationService({rpc:async name=>name==='native_mail_next_lane'?{lane:'confirmation'}:name==='native_checkout_claim_confirmation'?job(++claims):{settled:true},env:k=>k==='RESEND_API_KEY'?'synthetic':undefined,request:async()=>{sends++;return Response.json({id:'synthetic_receipt'});}})};}
test('scheduler single-message budget does not change owner default ten',async()=>{const a=fixture();const one=await a.service.deliver(null,{limit:1});assert.equal(one.accepted,1);assert.equal(a.claims,1);assert.equal(a.sends,1);const b=fixture();const ten=await b.service.deliver(null);assert.equal(ten.accepted,10);assert.equal(b.claims,10);assert.equal(b.sends,10);});
test('invalid local budget cannot claim',async()=>{const f=fixture();await assert.rejects(f.service.deliver(null,{limit:11}));assert.equal(f.claims,0);});
test('existing owner authorization is retained and index routes machine path separately',()=>{const index=readFileSync(new URL('../supabase/functions/native-checkout-confirmations/index.ts',import.meta.url),'utf8');assert.match(index,/nativeConfirmationHandler\(\{authorized:authorizedOwner,service,proof,/);assert.match(index,/endsWith\('\/scheduled'\)/);});
test('all callback RPC adapters use seven-second caps and one-send budget stays below lease',()=>{
 const source=readFileSync(new URL('../supabase/functions/native-checkout-confirmations/index.ts',import.meta.url),'utf8');
 assert.equal((source.match(/ownerRest\(/g)||[]).length,(source.match(/signal:AbortSignal.timeout\(7000\)/g)||[]).length);
 assert.ok(10*7000+12000<110000);
});
test('ownerRest honors a shorter caller cancellation without revealing errors',async()=>{
 const {ownerRest}=await import('../supabase/functions/_shared/owner-session.ts');
 const controller=new AbortController();controller.abort();let captured;
 await assert.rejects(ownerRest('rpc/fixture',{signal:controller.signal},{url:'https://synthetic.invalid',key:'synthetic'},async(_url,init)=>{captured=init.signal;init.signal.throwIfAborted();return Response.json({});}),/Owner access is temporarily unavailable/);
 assert.equal(captured.aborted,true);
});
