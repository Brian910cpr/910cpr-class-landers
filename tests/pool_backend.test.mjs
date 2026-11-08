import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {createHandler} from '../supabase/functions/public-event-registration/handler.ts';
import {normalizeInput,checkoutMatches,fingerprint,FAMILY,BLS} from '../supabase/functions/public-event-registration/contract.ts';

const requestId='e2c2be7e-4254-4dd4-8e14-5e302fbdb701';
const input={requestId,firstName:'Test',lastName:'Person',email:'example@example.test',phone:'',attendeeCount:2,guestNames:['Test Guest'],ebookQty:1};
test('validation rejects malformed quantities and enforces optional zero default',()=>{
  for(const attendeeCount of [0,31,1.5,'2',NaN]) assert.throws(()=>normalizeInput({...input,attendeeCount},BLS));
  for(const ebookQty of [-1,3,1.5,'1',NaN]) assert.throws(()=>normalizeInput({...input,ebookQty},BLS));
  assert.throws(()=>normalizeInput({...input,guestNames:[]},BLS));
  assert.throws(()=>normalizeInput({...input,requestId:'not-a-uuid'},BLS));
  assert.throws(()=>normalizeInput(input,FAMILY));
  assert.equal(normalizeInput({...input,ebookQty:undefined},BLS).ebookQty,0);
  assert.equal(normalizeInput({...input,attendeeCount:30,guestNames:Array(29).fill('Guest Person')},BLS).guestNames.length,29);
});
test('survey cannot override payment/group metadata and fingerprint binds content',async()=>{
  const normalized=normalizeInput({...input,survey:{groupRegistrationIds:'malicious',stripePaidAmount:999}},BLS);
  assert.equal(normalized.groupRegistrationIds,undefined);
  assert.notEqual(await fingerprint(normalized,BLS),await fingerprint({...normalized,ebookQty:0},BLS));
});
test('payment requires exact session, order, reference, amount, currency and mode',()=>{
  const order={id:'order',stripe_checkout_session_id:'cs_test',total_amount:68.51};
  const checkout={id:'cs_test',client_reference_id:'reg',amount_total:6851,currency:'usd',mode:'payment',metadata:{order_id:'order'}};
  assert.ok(checkoutMatches(checkout,order,'reg'));
  for(const delta of [{id:'other'},{amount_total:6850},{currency:'eur'},{client_reference_id:'other'},{mode:'subscription'},{metadata:{order_id:'other'}}]) assert.ok(!checkoutMatches({...checkout,...delta},order,'reg'));
});

function mock({free=false,checkoutId=null,capacityError=false,providerStatus='open',providerPaid=false,providerAmount=6851,saveError=false,fetchError=false,clockOffset=0,providerError=null}={}){
  const now=Date.parse('2026-11-07T12:00:00Z');
  const calls=[];
  const registration={id:'reg',status:free?'registered':'payment_pending',optional_survey:{groupRegistrationIds:['reg','guest'],attendeeCount:2,ebookQty:1,contactEmail:input.email,holdExpiresAt:new Date(now+35*60*1000).toISOString()}};
  const order={id:'order',status:'payment_pending',total_amount:68.51,currency:'usd',stripe_checkout_session_id:checkoutId};
  const session={id:'session',external_class_id:free?FAMILY:BLS,registration_backend:'landerware',registration_status:'open',visibility:free?'public':'unlisted',start_at:'2027-02-15T16:00:00Z'};
  const db={from(table){let update; const query={select(){return query},eq(){return query},is(){return query},in(){return query},update(value){update=value;return query},maybeSingle(){return query},single(){return query},then(resolve){calls.push(['query',table,update]);resolve({data:table==='class_sessions'?[session]:table==='registrations'?registration:order,error:null});}};return query;},async rpc(name,args){calls.push([name,args]);if(name==='bind_pool_checkout'&&!saveError)order.stripe_checkout_session_id=args.p_checkout_session_id;return {data:name==='pool_event_capacity'?{remaining:28,occupied:2}:{ok:true},error:(capacityError&&name==='pool_event_capacity')||(saveError&&name==='bind_pool_checkout')?{}:null};}};
  const fetch=async(url,options)=>{calls.push(['fetch',url,options]);if(fetchError)throw new Error('mock-network-failure');if(providerError)return new Response(JSON.stringify({error:providerError}),{status:400});return new Response(JSON.stringify({id:'cs_test',url:providerStatus==='open'?'https://checkout.stripe.com/c/pay/test':null,status:providerStatus,payment_status:providerPaid?'paid':'unpaid',amount_total:providerAmount,currency:'usd',mode:'payment',client_reference_id:'reg',metadata:{order_id:'order'}}));};
  return {handler:createHandler({db:()=>db,stripeKey:()=> 'fake-local-test-key',fetch,now:()=>now+clockOffset}),calls};
}
const post=(body)=>new Request('https://local.test/public-event-registration',{method:'POST',body:JSON.stringify(body)});
test('free confirmation survives capacity observer failure',async()=>{
  const {handler,calls}=mock({free:true,capacityError:true});
  const response=await handler(post({...input,event:FAMILY,ebookQty:0}));
  assert.equal(response.status,200);assert.equal((await response.json()).confirmed,true);assert.ok(!calls.some(c=>c[0]==='fetch'));
});
test('cached legacy submit receives a UUID; malformed IDs and status without ID fail',async()=>{
  const legacy=mock({free:true});const response=await legacy.handler(post({...input,requestId:undefined,event:FAMILY,ebookQty:0}));
  assert.equal(response.status,200);assert.match((await response.json()).requestId,/^[0-9a-f-]{36}$/);
  for(const payload of [{...input,requestId:'bad',event:BLS},{action:'status',event:BLS}]) {
    const m=mock();assert.equal((await m.handler(post(payload))).status,400);assert.ok(!m.calls.some(c=>c[0]==='reserve_pool_registration'));
  }
});
test('checkout charges $25 + $18.51, binds recovery, saves session and stable provider key',async()=>{
  const {handler,calls}=mock();const response=await handler(post({...input,event:BLS}));
  assert.equal(response.status,200);assert.equal((await response.json()).paymentPending,true);
  const request=calls.find(c=>c[0]==='fetch')[2];
  assert.equal(request.body.get('line_items[1][price_data][unit_amount]'),'1851');
  assert.equal(request.body.get('line_items[0][price_data][unit_amount]'),'2500');
  assert.match(request.body.get('success_url'),/session_id=\{CHECKOUT_SESSION_ID\}&request_id=/);
  assert.equal(request.headers['idempotency-key'],`pool2027-${requestId}`);
  assert.ok(calls.some(c=>c[0]==='bind_pool_checkout'&&c[1]?.p_checkout_session_id==='cs_test'));
});
test('paid=1 alone cannot confirm and actual Stripe paid evidence reconciles atomically',async()=>{
  const pending=mock({checkoutId:'cs_test'});const p=await pending.handler(post({action:'status',event:BLS,requestId,paid:1}));assert.equal((await p.json()).confirmed,false);
  const paid=mock({checkoutId:'cs_test',providerStatus:'complete',providerPaid:true,capacityError:true});const r=await paid.handler(post({action:'status',event:BLS,requestId}));assert.equal((await r.json()).confirmed,true);assert.ok(paid.calls.some(c=>c[0]==='confirm_pool_registration_payment'));
});
test('wrong totals never confirm; provider failures and save ambiguity return 503',async()=>{
  const mismatch=mock({checkoutId:'cs_test',providerPaid:true,providerAmount:7000});const r=await mismatch.handler(post({action:'status',event:BLS,requestId}));assert.equal(r.status,409);assert.ok(!mismatch.calls.some(c=>c[0]==='confirm_pool_registration_payment'));
  for(const settings of [{fetchError:true},{saveError:true}]){const m=mock(settings);const r=await m.handler(post({...input,event:BLS}));assert.equal(r.status,503);}
});
test('Stripe expiration is verified and released before allowing a new attempt',async()=>{
  const m=mock({checkoutId:'cs_test',providerStatus:'expired'});const r=await m.handler(post({action:'status',event:BLS,requestId}));assert.equal((await r.json()).expired,true);assert.ok(m.calls.some(c=>c[0]==='expire_pool_registration'));
});
test('lost create response recovers the same paid checkout rather than charging again',async()=>{
  const m=mock({providerStatus:'complete',providerPaid:true});const r=await m.handler(post({action:'status',event:BLS,requestId}));
  assert.equal((await r.json()).confirmed,true);
  assert.equal(m.calls.filter(c=>c[0]==='fetch'&&c[2].method==='POST').length,1);
  assert.ok(m.calls.some(c=>c[0]==='confirm_pool_registration_payment'));
});
test('no-session expiry requires Stripe evidence and only within idempotency retention',async()=>{
  const m=mock({clockOffset:36*60000,providerError:{type:'invalid_request_error',param:'expires_at'}});
  const r=await m.handler(post({action:'status',event:BLS,requestId}));assert.equal((await r.json()).expired,true);
  assert.ok(m.calls.some(c=>c[0]==='expire_pool_registration'&&c[1].p_checkout_session_id===null));
  const stale=mock({clockOffset:25*60*60000});const sr=await stale.handler(post({action:'status',event:BLS,requestId}));assert.equal(sr.status,409);assert.ok(!stale.calls.some(c=>c[0]==='fetch'||c[0]==='expire_pool_registration'));
});
test('local hold expiry never releases an open provider checkout',async()=>{
  const m=mock({checkoutId:'cs_test',clockOffset:36*60000});const r=await m.handler(post({action:'status',event:BLS,requestId}));
  const result=await r.json();assert.equal(result.paymentPending,true);assert.equal(result.processing,true);assert.notEqual(result.expired,true);
  assert.ok(!m.calls.some(c=>c[0]==='expire_pool_registration'));
});

test('isolated PostgreSQL executes atomic group, retry, price, capacity and rollback invariants',async(t)=>{
  if(!process.env.POOL_PGLITE_MODULE){t.skip('Set POOL_PGLITE_MODULE to an installed @electric-sql/pglite dist/index.js');return;}
  const {PGlite}=await import(pathToFileURL(process.env.POOL_PGLITE_MODULE).href);
  const db=new PGlite();
  try{
    await db.exec(`create role anon;create role authenticated;create role service_role;
      create table public.class_sessions(id uuid primary key default gen_random_uuid(),external_class_id text unique,registration_backend text,registration_status text,visibility text,start_at timestamptz,public_notes text);
      create table public.customers(id uuid primary key default gen_random_uuid(),first_name text,last_name text,email text,phone text);
      create table public.registrations(id uuid primary key default gen_random_uuid(),customer_id uuid references customers,class_session_id uuid references class_sessions,status text,registration_source text,optional_survey jsonb default '{}',idempotency_key text unique,canceled_at timestamptz,created_at timestamptz default now(),updated_at timestamptz default now(),unique(customer_id,class_session_id));
      create table public.products(id uuid primary key default gen_random_uuid(),product_key text,active boolean);
      create table public.registration_orders(id uuid primary key default gen_random_uuid(),registration_id uuid unique references registrations,status text,currency text,course_amount numeric,materials_amount numeric,total_amount numeric,stripe_checkout_session_id text,stripe_payment_intent_id text,paid_at timestamptz,updated_at timestamptz default now());
      create table public.registration_order_items(id uuid primary key default gen_random_uuid(),order_id uuid references registration_orders,item_type text,product_id uuid references products,description text,quantity integer check(quantity>0),unit_amount numeric,fulfillment_status text,updated_at timestamptz default now());
      insert into public.class_sessions(external_class_id,registration_backend,registration_status,visibility,start_at) values ('${FAMILY}','landerware','open','public','2027-02-15T16:00Z'),('${BLS}','landerware','open','unlisted','2027-02-15T16:00Z');
      insert into public.products(product_key,active) values ('aha-bls-2025-emanual',true);`);
    try { await db.exec(await readFile(new URL('../supabase/migrations/20261107125340_pool_registration_atomic_checkout.sql',import.meta.url),'utf8')); }
    catch (error) { console.error({position:error.position,internalPosition:error.internalPosition,internalQuery:error.internalQuery,where:error.where}); throw error; }
    const reserve=async(event,key,payload,hash='fingerprint')=>(await db.query('select public.reserve_pool_registration($1,$2,$3,$4::jsonb) as result',[event,key,hash,JSON.stringify(payload)])).rows[0].result;
    const first=await reserve(BLS,requestId,input);assert.equal(first.ok,true);
    assert.equal((await db.query('select count(*)::integer as n from registrations')).rows[0].n,2);
    assert.equal((await db.query('select total_amount::text from registration_orders')).rows[0].total_amount,'68.51');
    const replay=await reserve(BLS,requestId,input);assert.equal(replay.replayed,true);
    assert.equal((await reserve(BLS,requestId,input,'different')).code,'request_conflict');
    assert.equal((await reserve(BLS,crypto.randomUUID(),input)).code,'duplicate_registration');
    const countBefore=(await db.query('select count(*)::integer as n from customers')).rows[0].n;
    await db.exec("create function reject_guest_test() returns trigger language plpgsql as $$ begin if new.first_name='Reject' then raise exception 'test_rollback'; end if;return new;end;$$;create trigger reject_guest_test before insert on customers for each row execute function reject_guest_test();");
    await assert.rejects(reserve(FAMILY,crypto.randomUUID(),{...input,email:'rollback@example.test',ebookQty:0,guestNames:['Reject Guest']}));
    assert.equal((await db.query('select count(*)::integer as n from customers')).rows[0].n,countBefore);
    const big=await reserve(FAMILY,crypto.randomUUID(),{...input,email:'big@example.test',ebookQty:0,attendeeCount:28,guestNames:Array(27).fill('More Guests')});assert.equal(big.ok,true);
    assert.equal((await reserve(FAMILY,crypto.randomUUID(),{...input,email:'full@example.test',ebookQty:0})).code,'capacity');
    assert.equal((await db.query('select public.pool_event_capacity() as c')).rows[0].c.remaining,0);
    await db.query("update registration_orders set stripe_checkout_session_id='cs_expired_test'");
    await db.query("select public.expire_pool_registration($1,'cs_expired_test')",[first.registrationId]);
    assert.equal((await db.query('select public.pool_event_capacity() as c')).rows[0].c.remaining,2);
    const retry=await reserve(BLS,crypto.randomUUID(),input);assert.equal(retry.ok,true);assert.equal(retry.registrationId,first.registrationId);
    assert.equal((await db.query("select count(*)::integer as n from registrations where status='canceled'")).rows[0].n,1);
    assert.equal((await db.query("select optional_survey->'previousAttempts'->0->'order'->>'stripe_checkout_session_id' as old from registrations where id=$1",[first.registrationId])).rows[0].old,'cs_expired_test');
    await assert.rejects(db.query("select public.bind_pool_checkout($1,$2,'cs_stale_attempt')",[first.registrationId,requestId]));
    await assert.rejects(db.query("select public.confirm_pool_registration_payment($1,'cs_expired_test',6851,'usd','pi_test')",[first.registrationId]));
    await db.query("update registration_orders set stripe_checkout_session_id='cs_sql_test'");
    await assert.rejects(db.query("select public.confirm_pool_registration_payment($1,'wrong',6851,'usd','pi_test')",[first.registrationId]));
    await assert.rejects(db.query("select public.confirm_pool_registration_payment($1,'cs_sql_test',6850,'usd','pi_test')",[first.registrationId]));
    const confirmed=(await db.query("select public.confirm_pool_registration_payment($1,'cs_sql_test',6851,'usd','pi_test') as r",[first.registrationId])).rows[0].r;assert.equal(confirmed.ok,true);
    assert.equal((await db.query("select count(*)::integer as n from registrations where status='registered'")).rows[0].n,30);
    assert.equal((await db.query("select public.confirm_pool_registration_payment($1,'cs_sql_test',6851,'usd','pi_test') as r",[first.registrationId])).rows[0].r.alreadyConfirmed,true);
    await assert.rejects(db.query("select public.expire_pool_registration($1,'cs_sql_test')",[first.registrationId]));
    assert.equal((await db.query("select has_function_privilege('anon','public.reserve_pool_registration(text,uuid,text,jsonb)','execute') as allowed")).rows[0].allowed,false);
    // A no-session reservation cannot be released while its hold remains active.
    await db.exec("update registrations set status='canceled';update registration_orders set status='canceled';");
    const single=await reserve(BLS,crypto.randomUUID(),{...input,email:'single@example.test',attendeeCount:1,guestNames:[],ebookQty:0});assert.equal(single.ok,true);
    assert.equal(single.groupRegistrationIds.length,1);
    await assert.rejects(db.query('select public.expire_pool_registration($1,null)',[single.registrationId]));
    await db.query("update registrations set optional_survey=jsonb_set(optional_survey,'{holdExpiresAt}',to_jsonb((now()-interval '1 minute')::text)) where id=$1",[single.registrationId]);
    await db.query('select public.expire_pool_registration($1,null)',[single.registrationId]);
    assert.equal((await reserve(BLS,crypto.randomUUID(),{...input,email:'single@example.test',attendeeCount:1,guestNames:[],ebookQty:0})).ok,true);
  } finally {await db.close();}
});
