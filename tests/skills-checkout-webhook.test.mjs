import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {stripTypeScriptTypes} from 'node:module';
import {createHmac,webcrypto} from 'node:crypto';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../supabase/functions/stripe-registration-webhook/index.ts',import.meta.url),'utf8').replace(/^import .*;\r?\n/,'');
test('real webhook handler verifies signature and skills provenance; failures never reach generic paid-state writes',async()=>{
 const calls=[];let handler;
 const db={from(table){assert.ok(['landerware_integration_secrets','skills_session_claim_receipts'].includes(table),'must not reach legacy mutation');const q={select:()=>q,eq:()=>q,maybeSingle:async()=>({data:table==='landerware_integration_secrets'?{secret_value:'fixture-secret'}:{registration_id:'reg'}})};return q;},rpc:async(name,args)=>{calls.push({name,args});return args.p_amount_total===5500?{data:{ok:true}}:{error:'mismatch'};}};
 const context=vm.createContext({createClient:()=>db,TextEncoder,Uint8Array,ArrayBuffer,Date,JSON,Request,Response,crypto:webcrypto,Deno:{serve:fn=>handler=fn,env:{get:()=> 'fixture'}}});
 vm.runInContext(stripTypeScriptTypes(source),context);
 const send=async(type,overrides={},valid=true)=>{
  const raw=JSON.stringify({id:'evt_fixture',type,data:{object:{id:'cs_fixture',client_reference_id:'reg',mode:'payment',payment_status:'paid',amount_total:5500,currency:'usd',metadata:{skills_session:'509474'},...overrides}}});
  const time=String(Math.floor(Date.now()/1000)),signature=createHmac('sha256','fixture-secret').update(time+'.'+raw).digest('hex');
  return handler(new Request('https://fixture.invalid',{method:'POST',headers:{'stripe-signature':`t=${time},v1=${valid?signature:'invalid'}`},body:raw}));
 };
 assert.equal((await send('checkout.session.completed',{},false)).status,400);assert.equal(calls.length,0);
 for(const type of ['checkout.session.expired','checkout.session.async_payment_failed'])assert.equal((await send(type)).status,200);
 assert.equal((await send('checkout.session.completed',{payment_status:'unpaid'})).status,200);assert.equal(calls.length,0);
 assert.equal((await send('checkout.session.async_payment_succeeded',{payment_status:'unpaid'})).status,400);
 assert.equal((await send('checkout.session.completed')).status,200);assert.equal(calls[0].name,'confirm_skills_checkout_payment');
 assert.equal((await send('checkout.session.async_payment_succeeded')).status,200);
 assert.equal((await send('checkout.session.completed',{amount_total:1})).status,500);
});
