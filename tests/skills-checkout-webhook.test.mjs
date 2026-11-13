import {settleBasket} from '../supabase/functions/public-registration/basket.mjs';
import {nativeConfirmationService} from '../supabase/functions/_shared/native-confirmation-service.mjs';
import {nativeConfirmationPostcommit} from '../supabase/functions/_shared/native-confirmation-postcommit.mjs';
import {publicOrderVersion,publicOrderReturnPath,settlePublicOrder} from '../supabase/functions/public-registration/public-order-routing.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {stripTypeScriptTypes} from 'node:module';
import {createHmac,webcrypto} from 'node:crypto';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../supabase/functions/stripe-registration-webhook/index.ts',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'');
test('real webhook handler verifies signature and skills provenance; failures never reach generic paid-state writes',async()=>{
 const calls=[];let handler;
 const db={from(table){assert.ok(['landerware_integration_secrets','skills_session_claim_receipts'].includes(table),'must not reach legacy mutation');const q={select:()=>q,eq:()=>q,maybeSingle:async()=>({data:table==='landerware_integration_secrets'?{secret_value:'fixture-secret'}:{registration_id:'reg'}})};return q;},rpc:async(name,args)=>{calls.push({name,args});return args.p_amount_total===5500?{data:{ok:true}}:{error:'mismatch'};}};
 const context=vm.createContext({settleBasket,nativeConfirmationService,nativeConfirmationPostcommit,publicOrderVersion,publicOrderReturnPath,settlePublicOrder,AbortSignal,fetch:async url=>{assert.match(String(url),/public-registration\/order\/.*requireDelivery=1/);deliveryCalls++;return Response.json({ok:!deliveryFail},{status:deliveryFail?503:200});},createClient:()=>db,TextEncoder,Uint8Array,ArrayBuffer,Date,JSON,Request,Response,crypto:webcrypto,Deno:{serve:fn=>handler=fn,env:{get:()=> 'fixture'}}});
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

test('actual signed public webhook selects stored order version; replay/failure events cannot reach retail or bypass verified receipt',async()=>{
 const calls=[],notifications=[];let handler,fail=false,deliveryFail=false,deliveryCalls=0;
 const order={id:'11111111-1111-4111-8111-111111111111',status:'held',total:5500,currency:'usd',stripe_checkout_session_id:'cs_public',registration_profile_snapshot:{}};
 const db={from(table){assert.ok(['landerware_integration_secrets','landerware_public_orders'].includes(table),'no retail or generic mutation');const q={select:()=>q,eq:()=>q,maybeSingle:async()=>({data:table==='landerware_integration_secrets'?{secret_value:'fixture-secret'}:order})};return q;},rpc:async(name,args)=>{calls.push(name);if(name.includes('finalize')&&fail)return{error:'fixture_failure'};return{data:{status:order.status==='refunded'?'refunded':'paid'}};}};
 const context=vm.createContext({settleBasket,nativeConfirmationService,nativeConfirmationPostcommit:options=>{const notify=nativeConfirmationPostcommit(options);return async id=>{notifications.push({id,after:calls.at(-1)});return notify(id);};},publicOrderVersion,publicOrderReturnPath,settlePublicOrder,AbortSignal,fetch:async url=>{assert.match(String(url),/public-registration\/order\/.*requireDelivery=1/);deliveryCalls++;return Response.json({ok:!deliveryFail},{status:deliveryFail?503:200});},createClient:()=>db,TextEncoder,Uint8Array,ArrayBuffer,Date,JSON,Request,Response,crypto:webcrypto,Deno:{serve:fn=>handler=fn,env:{get:k=>k==='RESEND_API_KEY'?undefined:k==='STRIPE_EXPECTED_LIVEMODE'?'false':'fixture'}}});vm.runInContext(stripTypeScriptTypes(source),context);
 const send=async(type,changes={})=>{const raw=JSON.stringify({id:'evt_public',type,livemode:false,data:{object:{id:'cs_public',mode:'payment',payment_status:'paid',livemode:false,payment_intent:'pi_public',amount_total:5500,currency:'usd',metadata:{landerware_order_id:order.id},...changes}}});const t=String(Math.floor(Date.now()/1000)),v=createHmac('sha256','fixture-secret').update(t+'.'+raw).digest('hex');return handler(new Request('https://fixture.invalid',{method:'POST',headers:{'stripe-signature':`t=${t},v1=${v}`},body:raw}));};
 assert.equal((await send('checkout.session.completed')).status,200);assert.deepEqual(calls,['native_checkout_record_payment','native_checkout_finalize_legacy_order']);assert.equal(deliveryCalls,1);deliveryFail=true;assert.equal((await send('checkout.session.completed')).status,500,'queue failure must ask Stripe to retry after a committed payment');deliveryFail=false;assert.equal((await send('checkout.session.completed')).status,200);assert.equal(deliveryCalls,3);assert.equal(notifications.length,0);
 order.checkout_runtime_version='native-v1';order.registration_profile_snapshot={profile:{profile_key:'fixture',version:1,form_schema:{schemaVersion:'native-checkout.form.v1'}}};calls.length=0;
 fail=true;assert.equal((await send('checkout.session.completed')).status,500);assert.equal(calls[0],'native_checkout_record_payment');assert.equal(notifications.length,0);fail=false;
 assert.equal((await send('checkout.session.async_payment_succeeded')).status,200);assert.equal(calls.at(-1),'native_checkout_finalize_order');assert.deepEqual(notifications,[{id:order.id,after:'native_checkout_finalize_order'}]);
 calls.length=0;for(const type of ['checkout.session.expired','checkout.session.async_payment_failed'])assert.equal((await send(type)).status,200);assert.equal(calls.length,0);
 for(const changes of [{amount_total:1},{currency:'eur'},{id:'cs_other'},{livemode:true},{payment_intent:'pi_other',metadata:{landerware_order_id:'other'}}]){assert.ok((await send('checkout.session.completed',changes)).status>=400);assert.equal(calls.length,0);}
 order.status='refunded';assert.equal((await (await send('checkout.session.completed')).json()).status,'refunded');assert.equal(notifications.length,1);
});

test('signed native webhook uses enabled mocked background delivery after commit and preserves paid response across provider outcomes',async()=>{
 for(const outcome of ['accepted','rejected','timeout']){
  const events=[],background=[],logs=[];let handler,claimed=false,providerCalls=0;
  const id='33333333-3333-4333-8333-333333333333',order={id,checkout_runtime_version:'native-v1',registration_profile_snapshot:{},status:'checkout_open',total:5500,currency:'usd',stripe_checkout_session_id:'cs_native'};
  const db={from(table){assert.ok(['landerware_integration_secrets','landerware_public_orders'].includes(table));const q={select:()=>q,eq:()=>q,maybeSingle:async()=>({data:table==='landerware_integration_secrets'?{secret_value:'fixture-secret'}:order})};return q;},rpc:async(name,args)=>{
   events.push(name);
   if(name==='native_checkout_record_payment')return{data:{recorded:true}};
   if(name==='native_checkout_finalize_order'){order.status='paid';return{data:{status:'paid'}};}
   if(name==='native_checkout_claim_confirmation'){
    assert.equal(order.status,'paid');assert.equal(args.p_order_id,id);if(claimed)return{data:{empty:true}};claimed=true;
    return{data:{messageId:'44444444-4444-4444-8444-444444444444',lease:'55555555-5555-4555-8555-555555555555',recipient:'fixture@example.invalid',customerTemplate:true,confirmation:{kind:'confirmation',firstName:'Fixture',course:'Skills Session Only',courseId:'509474',startsAt:'2031-01-01T14:00:00Z',endsAt:'2031-01-01T14:45:00Z',venue:'Fixture location',selectedOptions:[]}}};
   }
   if(name==='native_checkout_settle_confirmation'){assert.equal(args.p_outcome,{accepted:'sent',rejected:'rejected',timeout:'ambiguous'}[outcome]);assert.equal(args.p_provider_id,outcome==='accepted'?'fixture_receipt':null);return{data:{settled:true}};}
   throw Error('unexpected RPC');
  }};
  const context=vm.createContext({settleBasket,nativeConfirmationService,nativeConfirmationPostcommit,publicOrderVersion,settlePublicOrder,createClient:()=>db,TextEncoder,Uint8Array,ArrayBuffer,Date,JSON,Request,Response,AbortSignal,crypto:webcrypto,console:{error:x=>logs.push(x)},EdgeRuntime:{waitUntil:p=>background.push(p)},
   fetch:async(url,init)=>{assert.equal(url,'https://api.resend.com/emails');events.push('provider');providerCalls++;const body=JSON.parse(init.body);assert.equal(body.to[0],'fixture@example.invalid');assert.match(body.text,/Skills Session Only/);if(outcome==='timeout')throw Error('PRIVATE transport diagnostic');return outcome==='accepted'?Response.json({id:'fixture_receipt'}):Response.json({message:'PRIVATE provider body'},{status:400});},
   Deno:{serve:fn=>handler=fn,env:{get:k=>({SUPABASE_URL:'https://fixture.invalid',SUPABASE_SERVICE_ROLE_KEY:'fixture-only',STRIPE_EXPECTED_LIVEMODE:'false',RESEND_API_KEY:'fixture-mail-key'})[k]}}});
  vm.runInContext(stripTypeScriptTypes(source),context);
  const raw=JSON.stringify({id:'evt_native',type:'checkout.session.completed',livemode:false,data:{object:{id:'cs_native',mode:'payment',payment_status:'paid',livemode:false,payment_intent:'pi_native',amount_total:5500,currency:'usd',metadata:{landerware_order_id:id}}}}),t=String(Math.floor(Date.now()/1000)),v=createHmac('sha256','fixture-secret').update(t+'.'+raw).digest('hex');
  const send=()=>handler(new Request('https://fixture.invalid',{method:'POST',headers:{'stripe-signature':`t=${t},v1=${v}`},body:raw}));
  const response=await send();assert.equal(response.status,200);const body=await response.json();assert.equal(body.status,'paid');assert.doesNotMatch(JSON.stringify(body),/fixture-mail-key|fixture_receipt|fixture@example|PRIVATE/);assert.equal(background.length,1);await Promise.all(background);
  assert.ok(events.indexOf('native_checkout_finalize_order')<events.indexOf('native_checkout_claim_confirmation'));assert.ok(events.indexOf('provider')<events.indexOf('native_checkout_settle_confirmation'));assert.equal(providerCalls,1);assert.equal(order.status,'paid');assert.doesNotMatch(logs.join(''),/PRIVATE|fixture@example/);
  assert.equal((await send()).status,200);await Promise.all(background);assert.equal(providerCalls,1,'replayed payment cannot resend a leased message');
 }
});
