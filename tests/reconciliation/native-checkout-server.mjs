// Isolated synthetic proof server. No production Supabase credentials or mail sender.
// Stripe transport is bridged through the authorized test-mode connector; requests
// remain pending until a real connector response is supplied. Never simulate payment.
import {setup} from './native-checkout-harness.mjs';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import vm from 'node:vm';
import {stripTypeScriptTypes} from 'node:module';
import {webcrypto,randomUUID} from 'node:crypto';
const root=new URL('../../',import.meta.url),read=p=>fs.readFileSync(new URL(p,root),'utf8');
const local='http://127.0.0.1:8791';
const h=await setup(12),pending=new Map(),deliveries=[];let webhookSecret='';
// Clone the actual validated Renewal offer into the isolated test database only.
// Synthetic daytime fixture, not a production class or a time copied from execution.
const proofStart=new Date(Date.now()+7*86400000);proofStart.setUTCHours(14,0,0,0);
const proofEnd=new Date(proofStart.getTime()+120*60000),proofOccupiedEnd=new Date(proofStart.getTime()+150*60000);
await h.db.query('update public.class_sessions set start_at=$2,end_at=$3,consumption_start_at=$2,consumption_end_at=$4 where id=$1',[h.id,proofStart.toISOString(),proofEnd.toISOString(),proofOccupiedEnd.toISOString()]);
const deliveryToken=process.env.CHECKOUT_PROOF_TOKEN||'';
if(deliveryToken){
 await h.db.exec(`alter table public.landerware_messages add column if not exists created_at timestamptz default now(),add column if not exists provider_message_id text,add column if not exists sent_at timestamptz,add column if not exists failed_at timestamptz,add column if not exists failure_detail text;`);
 await h.db.exec(read('supabase/migrations/20261017080000_checkout_confirmation_delivery.sql'));
 for(const file of ['20261017200000_message_operational_links.sql','20261017203000_checkout_email_reminders.sql','20261017210000_email_delivery_events.sql'])await h.db.exec(read('supabase/migrations/'+file));
 await h.db.query("update public.landerware_checkout_delivery_config set enabled=true,token_sha256=encode(sha256(convert_to($1,'UTF8')),'hex')",[deliveryToken]);
}
const response=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'content-type':'application/json'}});
async function fixtureFetch(url,init={}){
 const u=new URL(String(url));
 if(u.hostname==='api.stripe.com'){
   const id=randomUUID(),params=Object.fromEntries(new URLSearchParams(init.body));
   const result=await new Promise((resolve,reject)=>{const timer=setTimeout(()=>{pending.delete(id);reject(Error('connector_bridge_timeout'))},300000);pending.set(id,{id,path:u.pathname,method:init.method||'GET',params,resolve:value=>{clearTimeout(timer);pending.delete(id);resolve(value)}})});
   return response(result);
 }
 if(u.hostname!=='fixture-db.test')throw Error('External fetch forbidden in isolated proof');
 try{
  const table=u.pathname.split('/').at(-1),body=init.body?JSON.parse(init.body):{},id=(u.searchParams.get('id')||'').replace(/^eq\./,'');
  // Only synthetic local sessions are used; this stub is not production calendar proof.
  if(table==='assert_public_registration_open')return response(true);
  if(u.pathname.includes('/rpc/'))return response(await h.rpc(table,body));
  if(table==='class_sessions')return response((await h.db.query(`select s.*,jsonb_build_object('enrollware_course_id',c.enrollware_course_id,'name',c.name) courses,jsonb_build_object('name',l.name) locations,jsonb_build_object('display_name',p.display_name) people from public.class_sessions s join public.courses c on c.id=s.course_id join public.locations l on l.id=s.location_id join public.people p on p.id=s.lead_instructor_id where s.external_class_id=$1`,[(u.searchParams.get('external_class_id')||'').replace(/^eq\./,'')])).rows);
  if(table==='landerware_registration_catalog')return response((await h.db.query('select * from public.landerware_registration_catalog where course_id=$1',[(u.searchParams.get('course_id')||'').replace(/^eq\./,'')])).rows);
  if(table==='landerware_public_orders'){
   if(init.method==='PATCH'){
    const keys=Object.keys(body);if(keys.some(k=>!['status','stripe_checkout_session_id','checkout_url','updated_at'].includes(k)))throw Error('unexpected_patch');
    return response((await h.db.query(`update public.landerware_public_orders set ${keys.map((k,i)=>`${k}=$${i+2}`).join(',')} where id=$1 and status in ('held','checkout_open') returning *`,[id,...Object.values(body)])).rows);
   }
   const token=(u.searchParams.get('recovery_token')||'').replace(/^eq\./,'');
   return response((await h.db.query(`select o.*,coalesce((select jsonb_agg(s) from public.landerware_public_order_students s where s.order_id=o.id),'[]') landerware_public_order_students from public.landerware_public_orders o where ${token?'recovery_token':'id'}=$1`,[token||id])).rows);
  }
  if(table==='landerware_messages'){
   const keys=Object.keys(body);await h.db.query(`insert into public.landerware_messages(${keys.join(',')}) values(${keys.map((_,i)=>`$${i+1}`).join(',')}) on conflict(idempotency_key) do nothing`,Object.values(body));return response([]);
  }
  throw Error('unsupported_fixture_route');
 }catch(e){return response({message:e.message},400)}
}
let publicHandler,webhookHandler;
const context={Date,TextEncoder,URL,URLSearchParams,Request,Response,crypto:webcrypto,console,fetch:fixtureFetch,Deno:{env:{get:k=>({SUPABASE_URL:'http://fixture-db.test',SUPABASE_SERVICE_ROLE_KEY:'local_fixture',STRIPE_SECRET_KEY:'sk_test_transport_bridge'})[k]},serve:fn=>publicHandler=fn}};
vm.runInContext(stripTypeScriptTypes(read('supabase/functions/public-registration/index.ts').replace(/^import .*;\r?\n/gm,'').replaceAll('https://www.910cpr.com',local)),vm.createContext(context));
const client={from(table){let id;return {select(){return this},eq(_key,v){id=v;return this},async maybeSingle(){if(table==='landerware_integration_secrets')return {data:{secret_value:webhookSecret}};return {data:(await h.db.query(`select * from public.${table} where id=$1`,[id])).rows[0]||null}}}},async rpc(name,args){try{return {data:await h.rpc(name,args)}}catch(e){return {error:{message:e.message}}}}};
vm.runInContext(stripTypeScriptTypes(read('supabase/functions/stripe-registration-webhook/index.ts').replace(/^import .*;\r?\n/gm,'')),vm.createContext({Date,TextEncoder,Request,Response,crypto:webcrypto,console,createClient:()=>client,Deno:{env:{get:k=>k==='STRIPE_EXPECTED_LIVEMODE'?'false':''},serve:fn=>webhookHandler=fn}}));
const bytes=async req=>{const chunks=[];for await(const x of req)chunks.push(x);return Buffer.concat(chunks)};
const send=async(res,r)=>{res.writeHead(r.status,Object.fromEntries(r.headers));res.end(Buffer.from(await r.arrayBuffer()))};
async function state(){return {sessionId:h.external,canonicalSessionId:h.id,seats:await h.seats(),orders:(await h.db.query('select id,status,total,stripe_checkout_session_id,stripe_payment_intent_id,paid_at,payment_evidence,reconciliation_error from public.landerware_public_orders')).rows,registrations:(await h.db.query('select r.*,c.first_name,c.last_name,c.email from public.registrations r join public.customers c on c.id=r.customer_id')).rows,messages:(await h.db.query('select * from public.landerware_messages')).rows,deliveries}}
http.createServer(async(req,res)=>{try{
 const u=new URL(req.url,local),raw=await bytes(req);
 if(u.pathname==='/control/pending')return send(res,response([...pending.values()].map(({resolve,...x})=>x)));
 if(u.pathname.startsWith('/control/response/')){const item=pending.get(u.pathname.split('/').at(-1));if(!item)return send(res,response({error:'missing_request'},404));item.resolve(JSON.parse(raw));return send(res,response({ok:true}))}
 if(u.pathname==='/control/secret'){webhookSecret=JSON.parse(raw).secret;return send(res,response({ok:true}))}
 if(u.pathname==='/control/state')return send(res,response(await state()));
 if(u.pathname.startsWith('/public-registration'))return send(res,await publicHandler(new Request(local+u.pathname+u.search,{method:req.method,headers:req.headers,...(raw.length?{body:raw}:{} )})));
 if(u.pathname==='/proof/')return send(res,new Response(`<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><script src="/assets/inline-registration.js" defer></script><style>body{font:16px Arial;background:#f5f8fa;padding:20px}main{max-width:960px;margin:auto}.course{padding:20px;border:1px solid #d9e0e8;border-radius:12px;background:white}.register-link{display:inline-block;padding:12px 24px;background:#d64045;color:white;border-radius:8px}</style></head><body><main><p>STRIPE TEST MODE — synthetic class; no real charge or enrollment.</p><div id="course-list"><article class="course"><h1>AHA BLS Provider Renewal</h1><p>${proofStart.toLocaleString('en-US',{timeZone:'America/New_York'})}</p><p>910CPR test location</p><a class="register-link" href="/register/?session=${h.external}">Register</a></article></div></main></body></html>`,{headers:{'content-type':'text/html'}}));
 if(u.pathname==='/register/'||u.pathname==='/')return send(res,new Response(read('docs/register/index.html').replace('https://wktwgcnwdvbebcobgyey.supabase.co/functions/v1/public-registration',local+'/public-registration'),{headers:{'content-type':'text/html'}}));
 if(/^\/(assets|images)\/[a-zA-Z0-9_./-]+$/.test(u.pathname)&&!u.pathname.includes('..')){const file=new URL('docs'+u.pathname,root);if(fs.existsSync(file))return send(res,new Response(fs.readFileSync(file),{headers:{'content-type':u.pathname.endsWith('.css')?'text/css':u.pathname.endsWith('.js')?'text/javascript':'image/png'}}))}
 return send(res,response({error:'not_found'},404));
 }catch(e){return send(res,response({error:e.message},500))}}).listen(8791,'127.0.0.1');
// Public tunnel can reach only this signature-verified test webhook, never controls.
http.createServer(async(req,res)=>{
 if(req.method==='POST'&&/^\/rest\/v1\/rpc\/landerware_(?:claim_checkout_confirmation|settle_checkout_confirmation|checkout_confirmation_health|prepare_checkout_reminders|record_email_delivery_event)$/.test(req.url||'')){
  try{const args=JSON.parse(await bytes(req));if(!deliveryToken||args.p_token!==deliveryToken)return send(res,response({error:'unauthorized'},401));return send(res,response(await h.rpc(req.url.split('/').at(-1),args)))}catch{return send(res,response({error:'proof_queue_error'},500))}
 }
 if(req.method!=='POST'||req.url!=='/webhook'){res.writeHead(404);res.end();return}try{const raw=await bytes(req),r=await webhookHandler(new Request('https://isolated.test/webhook',{method:'POST',headers:req.headers,body:raw}));deliveries.push({at:new Date().toISOString(),status:r.status,eventId:JSON.parse(raw).id});await send(res,r)}catch(e){res.writeHead(500);res.end('test_webhook_error')}}).listen(8793,'127.0.0.1');
console.log(JSON.stringify({mode:'isolated_stripe_test',url:`${local}/register/?session=${h.external}`,canonicalSessionId:h.id,emailDelivery:'disabled',webhookPort:8793}));
