import {nativeConfirmationService} from "../_shared/native-confirmation-service.mjs";
import {nativeConfirmationPostcommit} from "../_shared/native-confirmation-postcommit.mjs";
import {publicOrderVersion,publicOrderReturnPath,settlePublicOrder} from "./public-order-routing.mjs";
import {genericCheckout,boundedCheckoutJSON,fullAppointmentSession} from "./generic.mjs";
import {skillsCheckout} from "../skills-session-reservation/checkout.mjs";

const ORIGIN="https://www.910cpr.com",ALLOWED=new Set([ORIGIN,"https://910cpr.com"]),STRIPE_API="https://api.stripe.com/v1";
const cors=(origin:string)=>({"access-control-allow-origin":ALLOWED.has(origin)?origin:ORIGIN,"access-control-allow-headers":"content-type,idempotency-key","access-control-allow-methods":"GET,POST,OPTIONS","cache-control":"no-store",vary:"Origin"});
const json=(origin:string,data:unknown,status=200)=>new Response(JSON.stringify(data),{status,headers:{...cors(origin),"content-type":"application/json; charset=utf-8"}});
function cfg(){const url=Deno.env.get("SUPABASE_URL"),raw=Deno.env.get("SUPABASE_SECRET_KEYS"),key=raw?JSON.parse(raw).default:Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");if(!url||!key)throw Error("server_configuration");return{url,key}}
async function db(path:string,init:RequestInit={}){const{url,key}=cfg(),r=await fetch(`${url}/rest/v1/${path}`,{...init,redirect:"error",signal:AbortSignal.timeout(20000),headers:{apikey:key,authorization:`Bearer ${key}`,"content-type":"application/json",prefer:"return=representation",...(init.headers||{})}}),p=await r.json().catch(()=>({}));if(!r.ok)throw Error(p?.message||`database_${r.status}`);return p}
async function rpc(name:string,body:unknown){const p=await db(`rpc/${name}`,{method:"POST",body:JSON.stringify(body)});return Array.isArray(p)?p[0]:p}
async function afterNativeCommit(orderId:string){await nativeConfirmationPostcommit({
 service:nativeConfirmationService({rpc,env:(name:string)=>Deno.env.get(name),request:fetch,report:(r:unknown)=>console.error(JSON.stringify(r))}),
 waitUntil:typeof EdgeRuntime!=="undefined"?(p:Promise<unknown>)=>EdgeRuntime.waitUntil(p):undefined,
 report:(r:unknown)=>console.error(JSON.stringify(r))
})(orderId);}
async function scheduleSession(id:string,newRegistration=true){
 if(!/^(?:\d+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})$/.test(id))throw Error("invalid_session");
 const native=await db(`class_sessions?external_class_id=eq.${encodeURIComponent(id)}&record_scope=eq.operational&select=*,courses(enrollware_course_id,name),locations(name),people!class_sessions_lead_instructor_id_fkey(display_name)&limit=2`);
 if(native.length===1&&native[0].registration_backend==="landerware"&&native[0].registration_status==="open"&&native[0].visibility==="public"&&["scheduled","active"].includes(native[0].status)&&Date.parse(native[0].start_at)>Date.now()){
  const n=native[0];if(newRegistration)await rpc("assert_public_registration_open",{p_start:n.start_at,p_end:n.end_at,p_external_id:id});
  try{const seats=await rpc("landerware_public_seat_state",{p_session_id:n.id});return {...n,session_id:id,course_id:n.courses.enrollware_course_id,course_name:n.courses.name,location_name:n.locations.name,lead_instructor_name:n.people?.display_name,nativeReady:true,seats}}
  catch(error){if(!["external_reconciliation_required","unverified_capacity"].includes(error instanceof Error?error.message:""))throw error}
 }
 const r=await fetch(`${ORIGIN}/data/schedule_future.json`,{headers:{accept:"application/json"}});if(!r.ok)throw Error("public_schedule_unavailable");const p=await r.json(),rows=Array.isArray(p)?p:p.sessions||[],s=rows.find((x:any)=>String(x.session_id)===id&&x.public_direct_booking===true&&x.registration_status==="open");if(!s)throw Error("session_not_open");if(newRegistration)await rpc("assert_public_registration_open",{p_start:s.consumption_start_at||s.start_at,p_end:s.consumption_end_at||s.end_at,p_external_id:id});return {...s,nativeReady:false};
}
async function catalog(courseId:string){const rows=await db(`landerware_registration_catalog?course_id=eq.${encodeURIComponent(courseId)}&active=eq.true&select=course_id,course_name,unit_amount,currency,addons,billing_codes&limit=1`);if(!rows[0])throw Error("price_catalog_missing");
 const c=rows[0];
 c.addons=await Promise.all((Array.isArray(c.addons)?c.addons:[]).map(async(a:any)=>{
  const state=await rpc("landerware_public_addon_state",{p_addon:a,p_currency:c.currency});
  // Return display metadata, never inventory codes or an internal product row.
  return {...a,active:a.active!==false&&state.available===true};
 }));return c}
// Unconverted clients retain the existing server catalog/manual-fulfillment
// contract. New configured profiles cannot enter this creator below.
async function legacyCatalog(courseId:string){const rows=await db(`landerware_registration_catalog?course_id=eq.${encodeURIComponent(courseId)}&active=eq.true&select=course_id,course_name,unit_amount,currency,addons,billing_codes&limit=1`);if(!rows[0])throw Error('price_catalog_missing');return rows[0];}
function stripeKey(){const k=Deno.env.get("STRIPE_SECRET_KEY");if(!k)throw Error("stripe_unavailable");return k}
async function stripe(path:string,params:URLSearchParams,idempotencyKey:string){const r=await fetch(`${STRIPE_API}/${path}`,{method:"POST",redirect:"error",signal:AbortSignal.timeout(15000),headers:{authorization:`Bearer ${stripeKey()}`,"content-type":"application/x-www-form-urlencoded","idempotency-key":idempotencyKey},body:params}),p=await r.json().catch(()=>({}));if(!r.ok)throw Error(p?.error?.message||`stripe_${r.status}`);return p}
async function stripeGet(path:string){const r=await fetch(`${STRIPE_API}/${path}`,{redirect:"error",signal:AbortSignal.timeout(15000),headers:{authorization:`Bearer ${stripeKey()}`}}),p=await r.json().catch(()=>({}));if(!r.ok)throw Error(p?.error?.message||`stripe_${r.status}`);return p}
async function order(id:string){const rows=await db(`landerware_public_orders?id=eq.${encodeURIComponent(id)}&select=*,landerware_public_order_students(*)&limit=1`);if(!rows[0])throw Error("order_not_found");return rows[0]}
function checkoutParams(o:any,c:any){const p=new URLSearchParams();p.set("line_items[0][price_data][currency]",o.currency);p.set("line_items[0][price_data][product_data][name]",`${o.registration_profile_snapshot?.profile?.display_name||c.course_name} registration (${o.landerware_public_order_students.length} students)`);p.set("line_items[0][price_data][unit_amount]",String(o.total));p.set("line_items[0][quantity]","1");p.set("mode","payment");p.set("customer_email",o.payer_email);p.set("payment_intent_data[receipt_email]",o.payer_email);p.set("success_url",`${ORIGIN}${publicOrderReturnPath(o)}?recover=${o.recovery_token}&paid=1`);p.set("cancel_url",`${ORIGIN}${publicOrderReturnPath(o)}?recover=${o.recovery_token}&cancelled=1`);
 // Stable across retries, including time spent uploading. Stripe requires at
 // least 30 minutes from Checkout creation, so expire 31 minutes after the
 // immutable SQL hold deadline. The seat hold stays 30 minutes; late payment
 // must atomically revalidate seats and reserved code stock.
 // https://docs.stripe.com/api/checkout/sessions/create#expires_at
 p.set("expires_at",String(Math.floor(Date.parse(o.hold_expires_at)/1000)+31*60));p.set("metadata[landerware_order_id]",o.id);p.set("metadata[landerware_order_type]","public");p.set("integration_identifier",`910cpr_public_${o.id.replace(/[^a-z]/g,"").slice(0,8).padEnd(8,"x")}`);return p}
async function createCheckout(o:any,c:any){
 if(o.status==="paid")return {url:`${ORIGIN}${publicOrderReturnPath(o)}?recover=${o.recovery_token}&paid=1`};
 if(o.reconciliation_error)throw Error("payment_reconciliation_required");
 if(!["held","checkout_open"].includes(o.status)||Date.parse(o.hold_expires_at)<=Date.now())throw Error("hold_expired");
 // A closure published after the hold must still block a new payment path.
 // Already-paid recovery is handled above, preserving existing paid bookings.
 await rpc("assert_public_registration_open",{p_start:null,p_end:null,p_external_id:o.external_class_id});
 const current=await db(`class_sessions?id=eq.${encodeURIComponent(o.class_session_id)}&select=id,status,registration_status,start_at,record_scope&limit=1`);
 if(current.length!==1||current[0].record_scope!=="operational"||!["scheduled","active"].includes(current[0].status)||current[0].registration_status!=="open"||Date.parse(current[0].start_at)<=Date.now())throw Error("session_not_open");
 if(o.registration_profile_snapshot?.profile&&!await rpc("native_checkout_payment_allowed",{p_key:o.idempotency_key.replace(/^public-order:/,"")}))throw Error("required_document_missing");
 const checkout=o.stripe_checkout_session_id?await stripeGet(`checkout/sessions/${encodeURIComponent(o.stripe_checkout_session_id)}`):await stripe("checkout/sessions",checkoutParams(o,c),`landerware-public-${o.id}`);
 const expectedLive=!stripeKey().startsWith("sk_test_")&&!stripeKey().startsWith("rk_test_");
 if(typeof checkout.id!=="string"||!checkout.id.startsWith("cs_")||checkout.livemode!==expectedLive||checkout.mode!=="payment"||checkout.amount_total!==o.total||checkout.currency!==o.currency||checkout.metadata?.landerware_order_id!==o.id)throw Error("payment_mismatch");
 if(checkout.payment_status==="paid")throw Error("payment_processing");
 if(checkout.status!=="open"||typeof checkout.url!=="string"||!checkout.url.startsWith("https://checkout.stripe.com/"))throw Error("payment_reconciliation_required");
 const rows=await db(`landerware_public_orders?id=eq.${o.id}&status=in.(held,checkout_open)`,{method:"PATCH",body:JSON.stringify({status:"checkout_open",stripe_checkout_session_id:checkout.id,checkout_url:checkout.url,updated_at:new Date().toISOString()})});
 if(rows.length!==1)throw Error("payment_reconciliation_required");return checkout;
}
async function queueEmail(recipient:string,subject:string,body:string,template:string,idempotencyKey:string){await db("landerware_messages",{method:"POST",headers:{prefer:"resolution=ignore-duplicates,return=minimal"},body:JSON.stringify({template_key:template,channel:"email",recipient,subject,body_text:body,delivery_provider:"gmail",delivery_status:"pending",idempotency_key:idempotencyKey})})}
async function sendRecovery(o:any,s:any){const link=`${ORIGIN}/register/?recover=${o.recovery_token}`;await queueEmail(o.payer_email,`Complete your ${s.course_name||"910CPR"} registration`,`We saved your class selection for 30 minutes. Complete payment here:\n${link}\n\nIf the hold expires, the same link will recheck availability before payment.`,`retail-checkout-recovery-v2`,`public-order-recovery:${o.id}`)}
async function paidEmails(o:any,s:any){const students=o.landerware_public_order_students||[],names=students.map((x:any)=>`${x.first_name} ${x.last_name}`).join(", "),selected=students.flatMap((x:any)=>(x.selected_addons||[]).map((a:any)=>`${x.first_name} ${x.last_name}: ${a.key} x${a.quantity||1}`)),manualNote=students.some((x:any)=>["physical","own-copy"].includes(x.selected_options?.manualChoice))?`\n\nBLS manual reminder: A current BLS Provider Manual must be available for class. If you selected a physical manual, buy it directly from AHA: https://shopcpr.heart.org/all-products?associated_course=49&format=84\n\nThis confirmation records that we provided the official purchase link.`:"",recipients:string[]=[...new Set<string>(students.map((x:any):string=>String(x.email)))];await Promise.all(recipients.map((to:string)=>queueEmail(to,`Registration confirmed — ${s.course_name}`,`Your registration is confirmed for ${s.course_name}.\n\n${new Date(s.start_at).toLocaleString("en-US",{timeZone:"America/New_York"})}\n${s.location_display||s.location_name||""}\n\nStudents: ${names}${manualNote}`,`retail-paid-confirmation-v3`,`public-order-paid:${o.id}:${to.toLowerCase()}`)));if(selected.length)await queueEmail(Deno.env.get("FULFILLMENT_EMAIL")||"brian@910cpr.com",`Paid add-ons require fulfillment — ${s.course_name}`,`Order ${o.id} is paid. Do not auto-release codes or materials.\n\n${selected.join("\n")}`,`retail-addon-fulfillment-v2`,`public-order-fulfillment:${o.id}`)}
async function publishedSession(id:string,newRegistration=true){if(!/^(?:\d+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})$/.test(id))throw Error("invalid_session");const r=await fetch(`${ORIGIN}/data/schedule_future.json`,{headers:{accept:"application/json"}});if(!r.ok)throw Error("public_schedule_unavailable");const p=await r.json(),rows=Array.isArray(p)?p:p.sessions||[],s=rows.find((x:any)=>String(x.session_id)===id&&x.public_direct_booking===true&&x.registration_status==="open");if(!s)throw Error("session_not_open");if(newRegistration)await rpc("assert_public_registration_open",{p_start:s.consumption_start_at||s.start_at,p_end:s.consumption_end_at||s.end_at,p_external_id:id});return s}
async function legacyPaidConfirmation(o:any){
 const rows=await db(`class_sessions?id=eq.${encodeURIComponent(o.class_session_id)}&select=id,status,start_at,courses(name),locations(name)&limit=1`),s=rows[0];
 if(!s)throw Error('session_not_available');
 if(!['scheduled','active'].includes(s.status))return;
 const students=o.landerware_public_order_students||[],ids=students.map((st:any)=>st.registration_id).filter((id:unknown)=>typeof id==='string'&&/^[0-9a-f-]{36}$/i.test(id));
 if(!ids.length)return;
 const registrations=await db(`registrations?id=in.(${ids.join(',')})&select=id,status`),active=new Set(registrations.filter((r:any)=>['registered','confirmed','completed','active'].includes(r.status)).map((r:any)=>r.id));
 const eligible=students.filter((st:any)=>active.has(st.registration_id));if(!eligible.length)return;
 await paidEmails({...o,landerware_public_order_students:eligible},{course_name:s.courses?.name||'910CPR class',start_at:s.start_at,location_name:s.locations?.name||''});
}
async function ensureLegacyConfirmation(o:any,strict:boolean){try{await legacyPaidConfirmation(o);}catch(error){console.error(JSON.stringify({orderId:o.id,error:'legacy_confirmation_enqueue_failed'}));if(strict)throw Error('legacy_confirmation_pending');}}
function materializedOffer(s:any,id:string){if(String(s.course_id||s.course_number||"")!=="209806")return {};const start=String(s.start_at||""),end=String(s.end_at||"");if(!start||!end||!String(s.location_display||s.location_name||"").includes("Shipyard Blvd"))return {};return{kind:"bls_initial_offer",external_class_id:id,start_at:start,end_at:end,location_label:String(s.location_display||s.location_name||""),capacity:6}}
async function start(req:Request,origin:string){
 const b=await req.json(),id=String(b.sessionId||"").trim(),s=await publishedSession(id);
 const c=await legacyCatalog(String(s.course_id||s.course_number||"")),students=Array.isArray(b.students)?b.students:[],key=(req.headers.get("idempotency-key")||"").trim();if(!key||key.length>160)throw Error("invalid_order");stripeKey();
 const previous=await db(`landerware_public_orders?idempotency_key=eq.${encodeURIComponent('public-order:'+key)}&select=registration_profile_snapshot,recovery_token&limit=1`);
 if(previous[0]&&publicOrderVersion(previous[0])==='native-v1')return json(origin,{error:'generic_checkout_required',nativeCheckoutUrl:`${ORIGIN}/register/checkout/?recover=${previous[0].recovery_token}`},409);
 if(!previous[0]){
  let configured=false;
  try{await rpc('native_checkout_profile',{p_public_course_id:c.course_id,p_context:null});configured=true;}
  catch(error){if(!(error instanceof Error)||error.message!=='native_profile_not_configured')throw error;}
  if(configured)return json(origin,{error:'generic_checkout_required',nativeCheckoutUrl:`${ORIGIN}/register/checkout/?session=${encodeURIComponent(id)}`},409);
 }
 const result=await rpc("landerware_create_public_order",{p_idempotency_key:`public-order:${key}`,p_external_class_id:id,p_course_id:c.course_id,p_payer_email:String(b.payerEmail||students[0]?.email||""),p_payer_phone:String(b.payerPhone||students[0]?.phone||""),p_students:students,p_billing_code:String(b.billingCode||"")||null,p_offer:materializedOffer(s,id)}),o=await order(result.orderId);
 if(o.status!=="paid"&&(!["held","checkout_open"].includes(o.status)||Date.parse(o.hold_expires_at)<=Date.now()))throw Error("hold_expired");
 if(o.total===0&&publicOrderVersion(o)==='legacy'){
  await rpc('landerware_finalize_public_order',{p_order_id:o.id,p_stripe_payment_intent_id:'no_payment_required'});
  await paidEmails(await order(o.id),s);
  return json(origin,{ok:true,orderId:o.id,holdExpiresAt:o.hold_expires_at,checkoutUrl:`${ORIGIN}/register/?order=${o.id}&paid=1`,recoveryUrl:`${ORIGIN}/register/?recover=${o.recovery_token}`});
 }
 const checkout=await createCheckout(o,c);
 if(!result.idempotentReplay)try{await sendRecovery(o,s)}catch{console.error(JSON.stringify({orderId:o.id,error:"recovery_message_enqueue_failed"}))}
 return json(origin,{ok:true,orderId:o.id,holdExpiresAt:o.hold_expires_at,checkoutUrl:checkout.url,recoveryUrl:`${ORIGIN}/register/?recover=${o.recovery_token}`});
}
async function recover(token:string,origin:string){if(!/^[0-9a-f-]{36}$/i.test(token))throw Error("invalid_recovery_token");const rows=await db(`landerware_public_orders?recovery_token=eq.${encodeURIComponent(token)}&select=*&limit=1`),o=rows[0];if(!o)throw Error("order_not_found");const version=publicOrderVersion(o);if(o.payment_evidence?.payment_status==="paid"&&o.status!=="paid")return verifyPaid(o.id,origin);if(["cancelled","refunded"].includes(o.status))return json(origin,{ok:false,status:o.status},409);if(version==="native-v1")return json(origin,{ok:true,status:o.status,nativeRecovery:true});if(o.stripe_checkout_session_id&&o.status!=="paid"){const observed=await verifyPaid(o.id,origin),state=await observed.clone().json();if(state.status!=="payment_pending")return observed;}if(o.status==="paid")return json(origin,{ok:true,status:"paid",orderId:o.id});if(o.reconciliation_error)return json(origin,{ok:false,status:"payment_review"},409);if(!["held","checkout_open"].includes(o.status)||Date.parse(o.hold_expires_at)<=Date.now())return json(origin,{ok:false,status:"expired",sessionId:o.external_class_id},409);const c=await catalog(o.course_id),full=await order(o.id),checkout=await createCheckout(full,c);return json(origin,{ok:true,status:o.status,checkoutUrl:checkout.url,holdExpiresAt:o.hold_expires_at})}
async function verifyPaid(id:string,origin:string,requireDelivery=false){
 if(!/^[0-9a-f-]{36}$/i.test(id))throw Error("order_not_found");const o=await order(id);const version=publicOrderVersion(o);if(["cancelled","refunded"].includes(o.status))return json(origin,{ok:false,status:o.status},409);if(o.status==="paid"){if(version==='legacy')await ensureLegacyConfirmation(o,requireDelivery);else await afterNativeCommit(o.id);return json(origin,{ok:true,status:"paid"});}
 if(!o.stripe_checkout_session_id)return json(origin,{ok:false,status:"payment_pending"},409);
 const checkout=await stripeGet(`checkout/sessions/${encodeURIComponent(o.stripe_checkout_session_id)}`);
 if(checkout.payment_status!=="paid")return json(origin,{ok:false,status:"payment_pending"},409);
 const expectedLive=!stripeKey().startsWith("sk_test_")&&!stripeKey().startsWith("rk_test_");
 if(checkout.livemode!==expectedLive)throw Error("stripe_mode_mismatch");
 const evidence={id:checkout.id,mode:checkout.mode,payment_status:checkout.payment_status,amount_total:checkout.amount_total,currency:checkout.currency,metadata:{landerware_order_id:checkout.metadata?.landerware_order_id},livemode:checkout.livemode,verificationSource:"stripe_api_recovery"};
 const result=await settlePublicOrder(rpc,o,checkout,evidence);
 if(version==='legacy'&&result.status==='paid')await ensureLegacyConfirmation(await order(o.id),requireDelivery);
 if(version==='native-v1'&&result.status==='paid')await afterNativeCommit(o.id);
 return json(origin,{ok:result.status==="paid",status:result.status},result.status==="paid"?200:409);
}

function fallbackUrl(s:any,id:string){try{const u=new URL(String(s.registration_url||""));return u.origin==="https://coastalcprtraining.enrollware.com"&&u.pathname==="/enroll"&&u.searchParams.get("id")===id?u.toString():null}catch{return null}}
const generic=genericCheckout({rpc,afterCommit:afterNativeCommit,catalog,scheduleSession,fallbackUrl,fullEnabled:()=>Deno.env.get("BLS_NATIVE_FULL_MATERIALIZATION_ENABLED")==="true",
 async appointmentSession(selection:any){
  if(!/^\d{1,12}$/.test(String(selection.course||''))||selection.skillsContext)throw Error('invalid_session');
  const rows=await db(`class_sessions?record_scope=eq.operational&registration_backend=eq.landerware&registration_status=eq.open&visibility=eq.public&courses.enrollware_course_id=eq.${selection.course}&start_at=gt.${encodeURIComponent(new Date().toISOString())}&select=*,courses!inner(enrollware_course_id),locations(name),people!class_sessions_lead_instructor_id_fkey(display_name)&order=start_at.asc&limit=201`);
  return fullAppointmentSession(rows,selection);
 },enabled:()=>Deno.env.get("SKILLS_SESSION_RESERVATIONS_ENABLED")!=="false",
 async legacyPayment(key:string,context:string,statusOnly:boolean){return skillsCheckout({rpc,stripe:async(method:string,path:string,params?:URLSearchParams,idempotencyKey?:string)=>method==="GET"?stripeGet(path):stripe(path,params!,idempotencyKey!)},key,context,statusOnly)},
 async publication(page:string){const r=await fetch(`${ORIGIN}/data/block-selector-availability/${page}.json`,{redirect:"error",cache:"no-store",signal:AbortSignal.timeout(15000)});if(!r.ok)throw Error("calendar_refresh_required");return r.json()},
 async checkout(id:string,snapshot:any){const o=await order(id);return createCheckout(o,snapshot?.catalog||await catalog(o.course_id))},
 async verify(id:string){const response=await verifyPaid(id,ORIGIN);if(response.status!==409&&!response.ok)throw Error("payment_unavailable")},
 async hash(bytes:Uint8Array){return Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",Uint8Array.from(bytes).buffer)),n=>n.toString(16).padStart(2,"0")).join("")},
 async store(intent:any,file:any){const{url,key}=cfg();const r=await fetch(`${url}/storage/v1/object/${intent.storage_bucket}/${intent.storage_path}`,{method:"POST",redirect:"error",signal:AbortSignal.timeout(20000),headers:{apikey:key,authorization:`Bearer ${key}`,"content-type":file.type,"x-upsert":"false"},body:file.bytes});if(!r.ok){const e=await r.json().catch(()=>({}));if(r.status!==409&&!['Duplicate','ResourceAlreadyExists'].includes(e.error)&&String(e.statusCode)!=='409')throw Error("document_storage_pending")}}
});
async function genericRoute(req:Request,route:string[],origin:string){
 const action=route[1],url=new URL(req.url),key=req.headers.get("idempotency-key")||"";
 if(req.method==="GET"&&action==="form"){
  const recoverToken=url.searchParams.get("recover");
  if(recoverToken){if(!/^[0-9a-f-]{36}$/i.test(recoverToken))throw Error("invalid_recovery_token");const rows=await db(`landerware_public_orders?recovery_token=eq.${recoverToken}&select=idempotency_key,checkout_runtime_version,registration_profile_snapshot&limit=1`);if(!rows[0])throw Error("order_not_found");if(publicOrderVersion(rows[0])==='legacy'){const response=await recover(recoverToken,origin);return json(origin,{legacyRecovery:await response.json()});}const recovered=rows[0].idempotency_key.replace(/^public-order:/,"");return json(origin,{...await generic.resume(recovered),key:recovered})}
  return json(origin,key&&!url.searchParams.has("session")&&!url.searchParams.has("course")?await generic.resume(key):await generic.model(Object.fromEntries(url.searchParams)));
 }
 if(req.method==="GET"&&action==="status")return json(origin,await generic.status(key));
 if(req.method!=="POST")throw Error("invalid_request");
 const body=await boundedCheckoutJSON(req,action==="upload"?14000000:32768);
 if(action==="reserve")return json(origin,await generic.reserve(key,body));
 if(action==="checkout")return json(origin,await generic.checkout(key));
 if(action==="upload")return json(origin,await generic.upload(key,body));
 return json(origin,{error:"not_found"},404);
}
Deno.serve(async req=>{const origin=req.headers.get("origin")||"",parts=new URL(req.url).pathname.split("/").filter(Boolean),route=parts.slice(parts.indexOf("public-registration")+1);if(origin&&!ALLOWED.has(origin))return json(origin,{error:"origin_not_allowed"},403);if(req.method==="OPTIONS")return new Response(null,{status:204,headers:cors(origin)});try{if(route[0]==="generic")return await genericRoute(req,route,origin);if(req.method==="GET"&&route[0]==="session"&&route[1]){const s=await publishedSession(route[1]),c=await legacyCatalog(String(s.course_id||s.course_number||""));return json(origin,{ok:true,session:{id:String(s.session_id),courseId:c.course_id,course:c.course_name,startsAt:s.start_at,endsAt:s.end_at||null,location:s.location_display||s.location_name||"",price:c.unit_amount/100,currency:c.currency,addons:c.addons,nativeReady:s.nativeReady,seats:s.seats||null,instructor:s.lead_instructor_name||null,fallbackRegistrationUrl:fallbackUrl(s,route[1])}})}if(req.method==="GET"&&route[0]==="recover"&&route[1])return await recover(route[1],origin);if(req.method==="GET"&&route[0]==="order"&&route[1])return await verifyPaid(route[1],origin,new URL(req.url).searchParams.get("requireDelivery")==="1");if(req.method==="POST"&&route[0]==="start")return await start(req,origin);return json(origin,{error:"not_found"},404)}catch(e){const raw=e instanceof Error?e.message:"unexpected_error",m=route[0]==="generic"?(/^[a-z_]{3,80}$/.test(raw)?raw:"service_unavailable"):raw,bad=["reservation_not_found","generic_checkout_required","required_document_missing","profile_changed","invalid_request","invalid_registration_field","invalid_checkout_profile","invalid_course_option","option_unavailable","uploads_disabled","invalid_document","session_not_available","invalid_context","calendar_refresh_required","invalid_session","session_not_open","price_catalog_missing","invalid_order","required_registration_field_missing","invalid_addon","physical_manual_unavailable","duplicate_addon","invalid_addon_quantity","invalid_addon_price","addon_fulfillment_unavailable","addon_inventory_exhausted","duplicate_product_addon","invalid_course_option","online_completion_ack_required","invalid_billing_code","insufficient_seats","invalid_recovery_token","order_not_found","native_registration_unavailable","hold_expired","idempotency_conflict","already_registered","student_already_held","duplicate_student","billing_approval_required","external_reconciliation_required","course_session_mismatch"].includes(m);return json(origin,{error:m},m==="request_too_large"?413:m==="registration_date_closed"?409:bad?400:500)}});

