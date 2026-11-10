import {publicOrderVersion,publicOrderReturnPath,settlePublicOrder} from '../supabase/functions/public-registration/public-order-routing.mjs';
// Run the actual HTTP adapter with only mocked service/Stripe fetches.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {stripTypeScriptTypes} from 'node:module';
import {readFileSync} from 'node:fs';
import {webcrypto} from 'node:crypto';
import {genericCheckout,boundedCheckoutJSON,fullAppointmentSession} from '../supabase/functions/public-registration/generic.mjs';
const source=readFileSync(new URL('../supabase/functions/public-registration/index.ts',import.meta.url),'utf8').replace(/^import .*;\r?\n/gm,'');
const key='11111111-1111-4111-8111-111111111111';
function harness({legacyURL=null,course='fixture-course'}={}){
 const calls=[];let handler,order,receipt,required=false,sessionResponse;
 const profile={profile_key:'fixture_generic',version:1,active:true,course_id:'fixture-course',display_name:'Fixture title',requirements:[],form_schema:{schemaVersion:'native-checkout.form.v1',inventory_kind:'scheduled_session_v1',fields:[{key:'first_name',wire:'firstName',type:'text',required:true},{key:'email',wire:'email',type:'email',required:true}],option_groups:[],driver_rules:[{driver:'native_order'}],default_choices:[]}};
 const catalog={course_id:'fixture-course',course_name:'Fixture title',unit_amount:7500,currency:'usd',addons:[],billing_codes:[{code:'PRIVATE'}]};
 const packet={profile,physicalCourseId:'fixture-course',catalog};
 const ctx=vm.createContext({publicOrderVersion,publicOrderReturnPath,settlePublicOrder,genericCheckout,boundedCheckoutJSON,fullAppointmentSession,URL,URLSearchParams,Request,Response,Headers,Date,Error,Set,Promise,JSON,Object,Array,Number,String,Uint8Array,crypto:webcrypto,AbortSignal,console,
  Deno:{env:{get:k=>({SUPABASE_URL:'https://fixture-db.invalid',SUPABASE_SERVICE_ROLE_KEY:'server-only-fixture',STRIPE_SECRET_KEY:'sk_test_fixture'})[k]},serve:fn=>handler=fn},
  fetch:async(url,init={})=>{
   const u=String(url),body=init.body&&typeof init.body==='string'?JSON.parse(init.body):null;calls.push({url:u,init});
   if(u.startsWith('https://api.stripe.com/')){const p=new URLSearchParams(init.body);if(init.method==='POST'){assert.equal(p.get('line_items[0][price_data][unit_amount]'),'7500');assert.equal(init.headers['idempotency-key'],'landerware-public-'+order.id);assert.equal(new URL(p.get('success_url')).pathname,publicOrderReturnPath(order));assert.equal(new URL(p.get('cancel_url')).pathname,publicOrderReturnPath(order));assert.ok(+p.get('expires_at')*1000-Date.now()>30*60000,'upload delays must not produce an invalid Stripe expiration');}return Response.json(sessionResponse||{id:'cs_fixture',url:'https://checkout.stripe.com/c/pay/fixture',mode:'payment',status:'open',payment_status:'unpaid',livemode:false,amount_total:7500,currency:'usd',metadata:{landerware_order_id:'fixture-order'}});}
   if(u.endsWith('/data/schedule_future.json'))return Response.json({sessions:[{session_id:'123456',course_id:'209806',start_at:'2031-01-01T14:00:00Z',end_at:'2031-01-01T16:00:00Z',public_direct_booking:true,registration_status:'open',registration_url:legacyURL}]});
   assert.equal(init.headers.apikey,'server-only-fixture');
   if(u.includes('/class_sessions?')&&legacyURL)return Response.json([]);
   if(u.includes('/class_sessions?'))return Response.json([{id:'class',registration_backend:'landerware',registration_status:'open',visibility:'public',status:'scheduled',start_at:'2031-01-01T14:00:00Z',end_at:'2031-01-01T16:00:00Z',record_scope:'operational',external_class_id:'123456',courses:{enrollware_course_id:course,name:'Fixture title'},locations:{name:'Fixture location'}}]);
   if(u.includes('/landerware_registration_catalog?'))return Response.json([catalog]);
   if(u.includes('/landerware_public_orders?')){if(init.method==='PATCH'){Object.assign(order,body);return Response.json([order]);}return Response.json([order]);}
   const rpc=u.split('/rpc/')[1];
   if(rpc==='native_checkout_record_payment'){order.payment_evidence=body.p_evidence;return Response.json({recorded:true});}
   if(rpc==='native_checkout_finalize_legacy_order'||rpc==='native_checkout_finalize_order'){order.status='paid';return Response.json({status:'paid'});}
   if(rpc==='native_checkout_profile')return Response.json(packet);
   if(rpc==='assert_public_registration_open')return Response.json(true);
   if(rpc==='landerware_public_seat_state')return Response.json({remaining:2});
   if(rpc==='native_checkout_receipt')return receipt?Response.json(receipt):Response.json({message:'reservation_not_found'},{status:400});
   if(rpc==='native_checkout_payment_allowed')return Response.json(!required);
   if(rpc==='reserve_native_checkout_order'){
    assert.equal(body.p_expected_total,7500);assert.equal(body.p_students[0].amountCents,undefined);
    receipt={kind:'public_order',orderId:'fixture-order',status:'held',amountCents:7500,currency:'usd',holdExpiresAt:'2031-01-01T13:00:00Z',students:[{}],profileSnapshot:{...packet,inputs:body.p_inputs,context:''}};
    order={id:'fixture-order',idempotency_key:'public-order:'+key,status:'held',total:7500,currency:'usd',payer_email:'fixture@example.invalid',hold_expires_at:new Date(Date.now()+5*60000).toISOString(),recovery_token:'fixture-recovery',registration_profile_snapshot:receipt.profileSnapshot,landerware_public_order_students:[{}]};return Response.json(receipt);
   }throw Error('unexpected_fixture_request:'+rpc);
  }});
 vm.runInContext(stripTypeScriptTypes(source),ctx);
 const send=(action,body,origin='https://www.910cpr.com')=>handler(new Request('https://fixture.invalid/public-registration/generic/'+action,{method:body?'POST':'GET',headers:{origin,'content-type':'application/json',...(action.startsWith('form?')?{}:{'idempotency-key':key})},...(body?{body:JSON.stringify(body)}:{})}));
 return {send,calls,saved:v=>order=v,required:v=>required=v,stripe:v=>sessionResponse=v};
}
test('deployed HTTP form/claim/Stripe adapter keeps service credentials and contact fields private and gates payment',async()=>{
 const h=harness();const form=await h.send('form?session=123456');const m=await form.json();assert.equal(form.status,200,JSON.stringify(m));assert.equal(m.profile.baseCents,7500);assert.equal(JSON.stringify(m).includes('PRIVATE'),false);
 const r=await h.send('reserve',{selection:{session:'123456'},profileKey:'fixture_generic',profileVersion:1,students:[{fields:{first_name:'Fixture',email:'fixture@example.invalid',amountCents:1},selectedChoices:[]}]});assert.equal(r.status,200);assert.equal(JSON.stringify(await r.json()).includes('fixture@example.invalid'),false);
 h.required(true);assert.equal((await h.send('checkout',{})).status,400);assert.equal(h.calls.some(c=>c.url.startsWith('https://api.stripe.com')),false);
 h.required(false);const checkout=await h.send('checkout',{});assert.equal(checkout.status,200);assert.match((await checkout.json()).checkoutUrl,/checkout.stripe.com/);
 assert.equal(h.calls.some(c=>c.url.includes('messages')),false);
});
test('HTTP adapter rejects foreign origins and malformed/oversize bodies before a claim',async()=>{
 const h=harness();assert.equal((await h.send('reserve',{},'https://other.invalid')).status,403);assert.equal(h.calls.length,0);
 const large=await h.send('reserve',{padding:'x'.repeat(40000)});assert.equal(large.status,413);assert.equal(h.calls.length,0);
});
test('actual fallback contract permits only the published matching concrete-session destination without a native claim',async()=>{
 const legacyURL='https://coastalcprtraining.enrollware.com/enroll?id=123456',h=harness({legacyURL});
 const response=await h.send('form?session=123456');assert.equal(response.status,200);const m=await response.json();assert.equal(m.nativeReady,false);assert.equal(m.fallbackRegistrationUrl,legacyURL);assert.equal(m.profile,undefined);
 const reserve=await h.send('reserve',{selection:{session:'123456'},profileKey:'fixture_generic',profileVersion:1,students:[]});assert.equal(reserve.status,400);assert.equal(h.calls.some(c=>c.url.includes('reserve_native_checkout_order')),false);
 for(const bad of ['https://unapproved.invalid/enroll?id=123456','https://coastalcprtraining.enrollware.com/enroll?id=999999']){const no=harness({legacyURL:bad});assert.equal((await no.send('form?session=123456')).status,400);}
});

test('actual appointment adapter queries canonical inventory and revalidates the resulting session before form display',async()=>{
 const h=harness({course:'209806'}),r=await h.send('form?course=209806&date=2031-01-01&startTime=09%3A00&location=Fixture%20location');
 assert.equal(r.status,200);assert.equal((await r.json()).selection.session,'123456');
 assert.equal(h.calls.filter(c=>c.url.includes('/class_sessions?')).length,2);
 const query=h.calls.find(c=>c.url.includes('courses.enrollware_course_id=eq.209806')).url;
 assert.match(query,/courses!inner/);assert.match(query,/limit=201/);
 assert.equal(h.calls.some(c=>c.url.includes('reserve_native_checkout_order')),false);
 assert.equal((await h.send('form?course=209806&date=2031-01-01&startTime=10%3A00')).status,400);
 const stale=harness({legacyURL:'https://coastalcprtraining.enrollware.com/enroll?id=123456'});
 assert.equal((await stale.send('form?course=209806&date=2031-01-01&startTime=09%3A00')).status,400);
});


test('existing-session appointment matcher supports configured non-BLS identity without accepting course or schedule tampering',()=>{
 const selection={course:'241108',date:'2031-01-01',startTime:'09:00',location:'Fixture room',instructor:'Qualified fixture'};
 const row={courses:{enrollware_course_id:'241108'},registration_backend:'landerware',record_scope:'operational',visibility:'public',registration_status:'open',status:'scheduled',external_class_id:'canonical-acls-fixture',start_at:'2031-01-01T14:00:00Z',locations:{name:'Fixture room'},people:{display_name:'Qualified fixture'}};
 assert.equal(fullAppointmentSession([row],selection,Date.parse('2030-01-01')),'canonical-acls-fixture');
 for(const change of [{course:'209805'},{startTime:'10:00'},{location:'other'},{instructor:'other'},{skillsContext:'bls-skills'},{course:'241108&override=true'}])assert.throws(()=>fullAppointmentSession([row],{...selection,...change},Date.parse('2030-01-01')),/invalid_session|session_not_available/);
 assert.throws(()=>fullAppointmentSession([row,row],selection,Date.parse('2030-01-01')),/session_not_available/);
});

test('stored profile version selects native versus legacy finalizer and rejects unknown snapshots',async()=>{
 const base={id:'order-fixture',total:5500,currency:'usd',stripe_checkout_session_id:'cs_fixture',registration_profile_snapshot:{}};
 const session={id:'cs_fixture',mode:'payment',payment_status:'paid',amount_total:5500,currency:'usd',payment_intent:'pi_fixture',metadata:{landerware_order_id:base.id}};
 const calls=[],rpc=async(name,args)=>{calls.push({name,args});return{status:'paid'};};
 assert.equal(publicOrderVersion(base),'legacy');assert.equal(publicOrderReturnPath(base),'/register/');await settlePublicOrder(rpc,base,session,session);
 assert.deepEqual(calls.map(c=>c.name),['native_checkout_record_payment','native_checkout_finalize_legacy_order']);
 const native={...base,registration_profile_snapshot:{profile:{profile_key:'fixture',version:1,form_schema:{schemaVersion:'native-checkout.form.v1'}}}};
 assert.equal(publicOrderReturnPath(native),'/register/checkout/');calls.length=0;await settlePublicOrder(rpc,native,session,session);assert.deepEqual(calls.map(c=>c.name),['native_checkout_record_payment','native_checkout_finalize_order']);
 for(const change of [{stripe_checkout_session_id:'cs_other'},{total:1},{currency:'eur'},{stripe_payment_intent_id:'pi_other'},{registration_profile_snapshot:{profile:{form_schema:{schemaVersion:'future'}}}}]){calls.length=0;await assert.rejects(settlePublicOrder(rpc,{...native,...change},session,session));assert.equal(calls.length,0);}
 for(const change of [{payment_status:'unpaid'},{id:'cs_other'},{payment_intent:null},{metadata:{landerware_order_id:'other'}},{amount_total:'5500'}]){calls.length=0;await assert.rejects(settlePublicOrder(rpc,native,{...session,...change},session));assert.equal(calls.length,0);}
 // A committed verified receipt is not discarded when finalization needs retry.
 let received=0,attempts=0;const retry=async(name)=>{if(name==='native_checkout_record_payment'){received++;return{};}if(++attempts===1)throw Error('transient_finalize');return{status:'paid',idempotentReplay:true};};
 await assert.rejects(settlePublicOrder(retry,native,session,session),/transient_finalize/);
 assert.equal((await settlePublicOrder(retry,native,session,session)).status,'paid');assert.equal(received,2);
});

test('shared recovery page resumes historical orders and verifies paid receipts without recreating a checkout',async()=>{
 const h=harness(),id='22222222-2222-4222-8222-222222222222',token='33333333-3333-4333-8333-333333333333';
 const order={id,idempotency_key:'public-order:'+key,status:'checkout_open',total:7500,currency:'usd',payer_email:'fixture@example.invalid',stripe_checkout_session_id:'cs_fixture',hold_expires_at:new Date(Date.now()+5*60000).toISOString(),recovery_token:token,registration_profile_snapshot:{},landerware_public_order_students:[{}]};
 h.saved(order);h.stripe({id:'cs_fixture',url:'https://checkout.stripe.com/c/pay/fixture',mode:'payment',status:'open',payment_status:'unpaid',livemode:false,amount_total:7500,currency:'usd',metadata:{landerware_order_id:id}});
 const response=await h.send('form?recover='+token),model=await response.json();assert.equal(response.status,200);assert.match(model.legacyRecovery.checkoutUrl,/checkout.stripe.com/);assert.equal(h.calls.some(c=>c.url.includes('reserve_native_checkout_order')),false);
 order.payment_evidence={payment_status:'paid'};order.hold_expires_at='2020-01-01T00:00:00Z';
 h.stripe({id:'cs_fixture',mode:'payment',payment_status:'paid',payment_intent:'pi_fixture',livemode:false,amount_total:7500,currency:'usd',metadata:{landerware_order_id:id}});
 const paid=await (await h.send('form?recover='+token)).json();assert.equal(paid.legacyRecovery.status,'paid');assert.ok(h.calls.some(c=>c.url.endsWith('/rpc/native_checkout_finalize_legacy_order')));
 order.status='refunded';const before=h.calls.filter(c=>c.url.startsWith('https://api.stripe.com')).length;assert.equal((await (await h.send('form?recover='+token)).json()).legacyRecovery.status,'refunded');assert.equal(h.calls.filter(c=>c.url.startsWith('https://api.stripe.com')).length,before);
});
