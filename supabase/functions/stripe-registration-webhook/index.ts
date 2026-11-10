import { createClient } from "https://esm.sh/@supabase/supabase-js@2.56.0";

const enc = new TextEncoder();
function hex(bytes:ArrayBuffer){return Array.from(new Uint8Array(bytes)).map(byte=>byte.toString(16).padStart(2,"0")).join("")}
function safeEqual(a:string,b:string){if(a.length!==b.length)return false;let difference=0;for(let i=0;i<a.length;i+=1)difference|=a.charCodeAt(i)^b.charCodeAt(i);return difference===0}
async function verify(raw:string,header:string|null,secret:string|null){
  if(!secret||!header)return false;
  const pieces=Object.fromEntries(header.split(",").map(piece=>piece.split("=",2) as [string,string]));
  if(!pieces.t||!pieces.v1)return false;
  const key=await crypto.subtle.importKey("raw",enc.encode(secret),{name:"HMAC",hash:"SHA-256"},false,["sign"]);
  const signature=hex(await crypto.subtle.sign("HMAC",key,enc.encode(`${pieces.t}.${raw}`)));
  return safeEqual(signature,pieces.v1);
}
const reply=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{"content-type":"application/json","cache-control":"no-store"}});

Deno.serve(async(request)=>{
  if(request.method!=="POST")return reply({ok:false},405);
  const raw=await request.text();
  const db=createClient(Deno.env.get("SUPABASE_URL")!,Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,{auth:{persistSession:false}});
  const {data:secretRow}=await db.from("landerware_integration_secrets").select("secret_value").eq("secret_key","stripe_registration_webhook").maybeSingle();
  const webhookSecret=secretRow?.secret_value||Deno.env.get("STRIPE_WEBHOOK_SECRET")||null;
  if(!(await verify(raw,request.headers.get("stripe-signature"),webhookSecret)))return reply({ok:false,error:"Invalid signature"},400);

  let event:any;
  try{event=JSON.parse(raw)}catch{return reply({ok:false,error:"Invalid JSON"},400)}
  const session=event?.data?.object||{};
  const retailOrderId=String(session?.metadata?.landerware_order_id||"").trim();
  const paid=event.type==="checkout.session.completed"?session.payment_status==="paid":event.type==="checkout.session.async_payment_succeeded";

  if(retailOrderId){
    // Public class orders share the metadata key with retail. Route by the
    // canonical record before invoking either finalizer; never label a class
    // order paid through the retail-only procedure.
    const {data:publicOrder,error:publicLookupError}=await db.from('landerware_public_orders').select('id').eq('id',retailOrderId).maybeSingle();
    if(publicLookupError)return reply({ok:false,error:'Public payment lookup failed'},500);
    if(publicOrder){
      if(!paid)return reply({ok:true,ignored:'Public checkout not paid'});
      const expectedLive=Deno.env.get('STRIPE_EXPECTED_LIVEMODE')!=='false';
      if(session.mode!=='payment'||session.payment_status!=='paid'||session.livemode!==expectedLive||event.livemode!==expectedLive)return reply({ok:false,error:'Public payment evidence missing'},400);
      const paymentArgs={p_order_id:publicOrder.id,p_stripe_payment_intent_id:typeof session.payment_intent==='string'?session.payment_intent:null,
        p_evidence:{id:session.id,mode:session.mode,payment_status:session.payment_status,amount_total:session.amount_total,currency:session.currency,metadata:{landerware_order_id:retailOrderId},livemode:session.livemode,stripeEventId:event.id}};
      const {error:receiptError}=await db.rpc('landerware_record_public_payment',paymentArgs);
      if(receiptError)return reply({ok:false,error:'Public payment receipt failed'},500);
      const {data,error}=await db.rpc('landerware_finalize_public_order',paymentArgs);
      if(error)return reply({ok:false,error:'Public payment reconciliation failed'},500);
      return reply({ok:true,orderId:publicOrder.id,status:data?.status});
    }
    if(!paid)return reply({ok:true,ignored:"Retail checkout not paid"});
    const {data,error}=await db.rpc("confirm_retail_payment",{p_order_id:retailOrderId,p_checkout_session_id:session.id||null,p_payment_intent_id:session.payment_intent||null,p_evidence:{stripeEventId:event.id,paymentStatus:session.payment_status}});
    if(error)return reply({ok:false,error:"Retail payment reconciliation failed"},500);
    return reply({ok:true,orderId:retailOrderId,status:"paid",result:data});
  }

  const registrationId=String(session.client_reference_id||"").trim();
  if(!registrationId)return reply({ok:true,ignored:"No registration reference"});
  const {data:skillsReceipt,error:skillsLookupError}=await db.from('skills_session_claim_receipts').select('registration_id').eq('registration_id',registrationId).maybeSingle();
  if(skillsLookupError)return reply({ok:false,error:'Skills payment lookup failed'},500);
  if(skillsReceipt){
    // Route by canonical provenance before the permissive legacy handler.
    // Failed/expired or delayed events must never overwrite a paid order.
    if(!paid)return reply({ok:true,ignored:'Skills checkout not paid'});
    if(session.mode!=='payment'||session.payment_status!=='paid'||session.metadata?.skills_session!=='509474')return reply({ok:false,error:'Skills payment evidence missing'},400);
    const {data,error}=await db.rpc('confirm_skills_checkout_payment',{p_registration_id:registrationId,p_checkout_id:session.id||null,
      p_amount_total:session.amount_total??null,p_currency:session.currency||null,p_payment_intent:typeof session.payment_intent==='string'?session.payment_intent:null});
    if(error||!data?.ok)return reply({ok:false,error:'Skills payment reconciliation failed'},500);
    return reply({ok:true,status:'paid'});
  }
  // Pool payments use one atomic confirmation with exact order/session binding.
  // Keep this before generic failure/paid mutations; metadata alone cannot route
  // a pool registration into the less restrictive legacy path.
  const {data:poolPrimary,error:poolLookupError}=await db.from("registrations")
    .select("id,idempotency_key").eq("id",registrationId).maybeSingle();
  if(poolLookupError)return reply({ok:false,error:"Registration lookup failed"},500);
  if(poolPrimary?.idempotency_key?.startsWith("pool2027:")){
    if(event.type==="checkout.session.expired"){
      const {error}=await db.rpc("expire_pool_registration",{p_registration_id:registrationId,p_checkout_session_id:session.id||null});
      if(error)return reply({ok:false,error:"Pool checkout expiry reconciliation failed"},500);
      return reply({ok:true,status:"expired"});
    }
    if(!paid)return reply({ok:true,ignored:"Pool checkout not paid"});
    if(session.mode!=="payment"||session.payment_status!=="paid")return reply({ok:false,error:"Pool checkout payment evidence missing"},400);
    const {data,error}=await db.rpc("confirm_pool_registration_payment",{
      p_registration_id:registrationId,p_checkout_session_id:session.id||null,
      p_amount_total:session.amount_total??null,p_currency:session.currency||null,
      p_payment_intent_id:typeof session.payment_intent==="string"?session.payment_intent:null
    });
    if(error||!data?.ok)return reply({ok:false,error:"Pool payment reconciliation failed"},500);
    return reply({ok:true,status:"paid",...data});
  }
  if(event.type==="checkout.session.async_payment_failed"){
    await db.from("registration_orders").update({status:"payment_failed",stripe_checkout_session_id:session.id||null,stripe_payment_intent_id:session.payment_intent||null,updated_at:new Date().toISOString()}).eq("registration_id",registrationId);
    return reply({ok:true,status:"payment_failed"});
  }
  if(!paid)return reply({ok:true,ignored:"Checkout not paid"});

  const now=new Date().toISOString();
  const {data:primary}=await db.from("registrations").select("id,optional_survey").eq("id",registrationId).maybeSingle();
  const configuredIds=Array.isArray(primary?.optional_survey?.groupRegistrationIds)?primary.optional_survey.groupRegistrationIds.filter((x:unknown)=>typeof x==="string"):[];
  const groupIds=[...new Set([registrationId,...configuredIds])];

  const {data:order,error:orderError}=await db.from("registration_orders").update({
    status:"paid",stripe_checkout_session_id:session.id||null,stripe_payment_intent_id:session.payment_intent||null,paid_at:now,updated_at:now
  }).eq("registration_id",registrationId).select("id").maybeSingle();
  if(orderError||!order)return reply({ok:false,error:"Order not found"},500);

  await db.from("registrations").update({status:"registered",updated_at:now}).in("id",groupIds);
  await db.from("registration_order_items").update({fulfillment_status:"awaiting_attention",updated_at:now}).eq("order_id",order.id).eq("fulfillment_status","awaiting_payment");

  if(primary?.optional_survey){
    await db.from("registrations").update({optional_survey:{...primary.optional_survey,stripePaidAmount:session.amount_total??null,stripeCheckoutSessionId:session.id||null,stripePaidAt:now},updated_at:now}).eq("id",registrationId);
  }
  return reply({ok:true,registrationId,groupRegistrationIds:groupIds,orderId:order.id,status:"paid"});
});
