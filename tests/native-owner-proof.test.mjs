import test from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';
const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');
import {nativeOwnerProof} from '../supabase/functions/_shared/native-owner-proof.mjs';
import {nativeConfirmationHandler} from '../supabase/functions/native-checkout-confirmations/handler.mjs';
const id='12345678-1234-4234-8234-123456789abc';
// No URL or directory: every fixture is an isolated in-memory database.
const db=new PGlite();await db.exec('create role anon; create role authenticated; create role service_role;');
await db.exec(await readFile(new URL('../supabase/migrations/20261111190819_native_owner_transport_proof.sql',import.meta.url),'utf8'));
async function seed(){await db.exec('reset role;truncate public.native_owner_transport_proof;');await db.query("insert into public.native_owner_transport_proof(slot,proof_id) values('owner_transport_once',$1)",[id]);}
const rpc=async(name,args)=>{const vals=Object.values(args),marks=vals.map((_,i)=>`$${i+1}`).join(',');return (await db.query(`select public.${name}(${marks}) as value`,vals)).rows[0].value;};
const env=n=>n==='RESEND_API_KEY'?'mock-key':undefined;
function req(path='/proof',body={},origin='https://www.910cpr.com'){return new Request('https://example.invalid/native-checkout-confirmations'+path,{method:'POST',headers:{'content-type':'application/json',origin},body:JSON.stringify(body)});}
test('unauthorized, wrong origin, arbitrary body and query never reach proof',async()=>{
 let calls=0;const proof=async()=>{calls++;return {state:'accepted'};};
 let h=nativeConfirmationHandler({authorized:async()=>false,service:{},proof});assert.equal((await h(req())).status,401);
 h=nativeConfirmationHandler({authorized:async()=>true,service:{},proof});assert.equal((await h(req('/proof',{},'https://evil.invalid'))).status,403);
 for(const payload of [{recipient:'other@example.com'},{from:'other@example.com'},{body:'anything'},{orderId:id},{proofId:id}])assert.equal((await h(req('/proof',payload))).status,400);
 assert.equal((await h(req('/proof?recipient=x'))).status,400);assert.equal(calls,0);
});
test('empty authorization table sends nothing',async()=>{let calls=0;const p=nativeOwnerProof({rpc,env,request:async()=>{calls++;}});assert.equal((await p()).state,'not_authorized');assert.equal(calls,0);});
test('one durable provider attempt; fixed recipient/body; receipt and replay',async()=>{
 await seed();let calls=0;const p=nativeOwnerProof({rpc,env,request:async(url,init)=>{calls++;assert.equal(url,'https://api.resend.com/emails');const b=JSON.parse(init.body);assert.deepEqual(b.to,['brian@910cpr.com']);assert.match(b.subject,/TEST ONLY/);assert.match(b.text,/No student was registered/);assert.equal(b.html,undefined);return new Response(JSON.stringify({id:'receipt_123'}),{status:200});}});
 const results=await Promise.all([p(),p(),p()]);assert.equal(calls,1);assert.equal(results.filter(x=>x.state==='accepted').length>=1,true);
 assert.equal((await p()).replay,true);assert.equal(calls,1);assert.equal((await p()).actualDeliveryConfirmed,false);
});
test('timeout unknown never retries',async()=>{await seed();let calls=0;const p=nativeOwnerProof({rpc,env,request:async()=>{calls++;throw Error('timeout');}});assert.equal((await p()).state,'unknown');await p();assert.equal(calls,1);});
test('2xx without receipt remains unknown',async()=>{await seed();let calls=0;const p=nativeOwnerProof({rpc,env,request:async()=>{calls++;return new Response('{}',{status:200});}});assert.equal((await p()).state,'unknown');await p();assert.equal(calls,1);});
test('unknown settlement keeps attempted and never repeats provider',async()=>{await seed();let calls=0,reported=0;const p=nativeOwnerProof({rpc:(n,a)=>n.endsWith('_settle')?Promise.reject(Error('connection')):rpc(n,a),env,report:()=>{reported++;},request:async()=>{calls++;return new Response('{"id":"receipt_456"}',{status:200});}});assert.equal((await p()).state,'settlement_unknown');assert.equal((await p()).state,'attempted');assert.equal(calls,1);assert.equal(reported,1);});
test('RPC invoker grants restrict anon/authenticated; service role works; no reset settlement',async()=>{await seed();for(const role of ['anon','authenticated']){await db.exec(`set role ${role}`);await assert.rejects(()=>rpc('native_owner_transport_claim',{}),/permission denied/);await assert.rejects(()=>db.query('select * from public.native_owner_transport_proof'),/permission denied/);await db.exec('reset role');}await db.exec('set role service_role');assert.equal((await rpc('native_owner_transport_claim',{})).claimed,true);await assert.rejects(()=>rpc('native_owner_transport_settle',{p_proof_id:id,p_state:'pending',p_provider_id:null,p_error_code:null}),/invalid outcome/);assert.equal((await rpc('native_owner_transport_claim',{})).claimed,false);await db.exec('reset role');});
test.after(async()=>{await db.close();});
