import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {skillsCheckout,certificateInput} from '../supabase/functions/skills-session-reservation/checkout.mjs';
import {createHandler} from '../supabase/functions/skills-session-reservation/handler.mjs';
import client from '../docs/assets/skills-checkout-client.js';
const root=new URL('../',import.meta.url),load=p=>readFileSync(new URL(p,root),'utf8');
const key='11111111-1111-4111-8111-111111111111';
const quote={registrationId:'reg',orderId:'order',status:'payment_pending',amountCents:5500,currency:'usd',createdAt:new Date().toISOString(),startsAt:'2031-04-05T14:00:00Z',location:':: Wilmington; Shipyard Blvd',instructor:'Fixture Instructor',email:'fixture@example.invalid'};
const checkout={id:'cs_fixture',mode:'payment',client_reference_id:'reg',metadata:{order_id:'order',skills_session:'509474'},amount_total:5500,currency:'usd',status:'open',payment_status:'unpaid',url:'https://checkout.stripe.com/c/pay/fixture'};
test('Stripe gets the canonical quote, stable idempotency and safe return URLs; resume does not create another session',async()=>{
 let bound=false,posts=0;
 const deps={rpc:async(name,args)=>{if(name==='skills_checkout_order')return {...quote,checkoutId:bound?'cs_fixture':null};assert.equal(name,'bind_skills_checkout');assert.equal(args.p_checkout_id,'cs_fixture');bound=true;},stripe:async(method,path,params,idempotency)=>{
  if(method==='POST'){posts++;assert.equal(params.get('line_items[0][price_data][unit_amount]'),'5500');assert.equal(params.get('customer_email'),quote.email);assert.equal(idempotency,'skills-checkout-order');assert.equal(new URL(params.get('cancel_url')).searchParams.get('skillsContext'),'hsi-blended');assert.ok(!params.get('success_url').includes(key));}return checkout;
 }};
 assert.equal((await skillsCheckout(deps,key,'hsi-blended')).checkoutUrl,checkout.url);
 assert.equal((await skillsCheckout(deps,key,'hsi-blended')).checkoutUrl,checkout.url);assert.equal(posts,1);
});
test('return parameters never mark paid; verified paid session reconciles, processing/expired/mismatch never redirect',async()=>{
 let confirms=0;
 for(const variant of [{payment_status:'paid'},{status:'complete'},{status:'expired'},{amount_total:1},{client_reference_id:'forged'},{url:'https://evil.example/' }]){
  const deps={rpc:async name=>name==='skills_checkout_order'?{...quote,checkoutId:'cs_fixture'}:(confirms++,{ok:true}),stripe:async()=>({...checkout,...variant})};
  if(variant.payment_status==='paid')assert.equal((await skillsCheckout(deps,key,'cpr-aed',true)).paymentStatus,'paid');
  else if(variant.status==='complete')assert.equal((await skillsCheckout(deps,key,'cpr-aed')).paymentStatus,'processing');
  else await assert.rejects(skillsCheckout(deps,key,'cpr-aed'));
 }assert.equal(confirms,1);
 await assert.rejects(skillsCheckout({rpc:async()=>({...quote,createdAt:'2020-01-01'}),stripe:()=>assert.fail('must not create an uncertain old checkout')},key,'cpr-aed'),/reconciliation/);
});
test('optional certificates reject spoofed MIME, oversize, empty and invalid base64; no file is valid',async()=>{
 assert.equal(await client.certificate(null),null);
 assert.equal(certificateInput({type:'application/pdf',base64:btoa('%PDF-fixture')}).extension,'pdf');
 for(const c of [{type:'image/png',base64:btoa('%PDF-fixture')},{type:'text/html',base64:btoa('<html>')},{type:'application/pdf',base64:''},{type:'application/pdf',base64:'!'},{type:'application/pdf',base64:'A'.repeat(2796208)}])assert.throws(()=>certificateInput(c));
});
test('certificate endpoint authorizes saved receipt before upload and rejects forged/unknown context',async()=>{
 let uploaded=0;
 const handler=createHandler({enabled:()=>true,rpc:async(name,args)=>{assert.equal(name,'skills_checkout_order');assert.equal(args.p_key,key);if(args.p_context==='arc-blended')throw Error('invalid_request');return quote;},upload:async()=>({documentId:String(++uploaded)})});
 const request=context=>new Request('https://example.invalid/certificate',{method:'POST',headers:{'idempotency-key':key,'content-type':'application/json'},body:JSON.stringify({context,registrationId:'attacker',certificate:{type:'application/pdf',base64:btoa('%PDF-fixture')}})});
 assert.equal((await handler(request('hsi-blended'))).status,200);
 assert.equal((await handler(request('arc-blended'))).status,409);assert.equal(uploaded,1);
});
test('actual database: bound amount/currency, canceled state, paid idempotency, private document attachment and roles',async()=>{
 const {PGlite}=await import(process.env.SKILLS_PGLITE_MODULE||'@electric-sql/pglite');const db=new PGlite();
 try{
  await db.exec(load('tests/helpers/reschedule-production-schema.sql'));
  for(const name of ['20261019175346_registration_self_service_rescheduling.sql','20261019175522_reschedule_confirmation_provider.sql','20261019225039_registration_reschedule_dynamic_offers.sql','20261106180848_skills_session_native_claim.sql'])await db.exec(load('supabase/migrations/'+name));
  await db.exec(load('tests/helpers/skills-native-workspace-guards.sql'));await db.exec(load('tests/helpers/skills-native-synthetic.sql'));
  await db.exec(load('tests/helpers/skills-checkout-documents.sql'));
  await db.exec(load('supabase/migrations/20261108142206_skills_checkout_and_optional_certificate.sql'));
  const scalar=async(sql,args=[])=>Object.values((await db.query(sql,args)).rows[0])[0];
  const receipt=await scalar("select reserve_skills_session_native($1,'cpr-aed',skills_test.offer('checkout',10),skills_test.student(1))",[key]);
  const reg=receipt.registrationId;
  await assert.rejects(scalar("select skills_checkout_order($1,'hsi-blended')",[key]),/invalid_request/);
  assert.equal((await scalar("select skills_checkout_order($1,'cpr-aed')",[key])).amountCents,5500);
  await scalar('select bind_skills_checkout($1,$2)',[reg,'cs_fixture']);
  await assert.rejects(scalar('select bind_skills_checkout($1,$2)',[reg,'cs_other']),/payment_mismatch/);
  const confirm=(id='cs_fixture',amount=5500,currency='usd')=>scalar('select confirm_skills_checkout_payment($1,$2,$3,$4,$5)',[reg,id,amount,currency,'pi_fixture']);
  for(const args of [['cs_other',5500,'usd'],['cs_fixture',1,'usd'],['cs_fixture',5500,'eur'],[null,5500,'usd']])await assert.rejects(confirm(...args),/payment_mismatch/);
  assert.equal((await confirm()).paymentStatus,'paid');assert.equal((await confirm()).idempotentReplay,true);
  const attach=()=>scalar('select attach_skills_certificate($1,$2,$3,$4)',[reg,'a'.repeat(64),'application/pdf',123]);
  assert.equal((await attach()).documentId,(await attach()).documentId);
  assert.equal(await scalar('select count(*) from class_session_documents'),1);
  assert.equal(await scalar("select status from registration_orders where registration_id=$1",[reg]),'paid');
  await db.exec("update storage.buckets set public=true");await assert.rejects(attach(),/certificate_unavailable/);
  await db.query("update registrations set status='canceled' where id=$1",[reg]);await assert.rejects(confirm(),/payment_mismatch/);
  for(const role of ['anon','authenticated'])assert.equal(await scalar(`select has_function_privilege('${role}','public.skills_checkout_order(text,text)','execute')`),false);
 }finally{await db.close();}
});
