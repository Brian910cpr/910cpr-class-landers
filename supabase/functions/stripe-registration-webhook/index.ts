import { createClient } from "https://esm.sh/@supabase/supabase-js@2.56.0";

const enc = new TextEncoder();
function hex(bytes:ArrayBuffer){return Array.from(new Uint8Array(bytes)).map(byte=>byte.toString(16).padStart(2,"0")).join("")}
function safeEqual(a:string,b:string){if(a.length!==b.length)return false;let difference=0;for(let i=0;i<a.length;i+=1)difference|=a.charCodeAt(i)^b.charCodeAt(i);return difference===0}
async function verify(raw:string,header:string|null,secret:string|null){
  if(!secret||!header)return false;
  const pieces=header.split(",").map(piece=>piece.trim().split("=",2));
  const timestamps=pieces.filter(([name])=>name==="t").map(([,value])=>value);
  const signatures=pieces.filter(([name,value])=>name==="v1"&&/^[a-f0-9]{64}$/.test(value||"")).map(([,value])=>value);
  if(timestamps.length!==1||!/^\d+$/.test(timestamps[0]||"")||!signatures.length)return false;
  const timestamp=Number(timestamps[0]);
  if(!Number.isSafeInteger(timestamp)||Math.abs(Date.now()/1000-timestamp)>300)return false;
  const key=await crypto.subtle.importKey("raw",enc.encode(secret),{name:"HMAC",hash:"SHA-256"},false,["sign"]);
  const signature=hex(await crypto.subtle.sign("HMAC",key,enc.encode(`${timestamps[0]}.${raw}`)));
  return signatures.some(candidate=>safeEqual(signature,candidate));
}
const reply=(body:unknown,status=200)=>new Response(JSON.stringify(body),{status,headers:{"content-type":"application/json","cache-control":"no-store"}});

function paymentEvidence(session:any,event:any){
  return {id:session.id,mode:session.mode,payment_status:session.payment_status,amount_total:session.amount_total,currency:session.currency,
    metadata:{landerware_order_id:session.metadata?.landerware_order_id},stripeEventId:event.id,eventCreated:event.created,livemode:session.livemode};
}
function matchesPayment(order:any,session:any,retail=false){
  return session.mode==="payment" && session.id===order.stripe_checkout_session_id && !!session.id
    && session.amount_total===(retail?order.total_amount_cents:order.total) && session.currency===order.currency
    && session.metadata?.landerware_order_id===order.id && typeof session.payment_intent==="string" && session.payment_intent.startsWith("pi_");
}

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
  const expectedLive=Deno.env.get("STRIPE_EXPECTED_LIVEMODE")!=="false";
  if(event.livemode!==expectedLive||session.livemode!==expectedLive)return reply({ok:false,error:"Stripe mode mismatch"},400);
  const retailOrderId=String(session?.metadata?.landerware_order_id||"").trim();
  const paid=["checkout.session.completed","checkout.session.async_payment_succeeded"].includes(event.type)&&session.payment_status==="paid";

  if(retailOrderId){
    if(!/^[0-9a-f-]{36}$/i.test(retailOrderId))return reply({ok:false,error:"Invalid order reference"},400);
    const [publicResult,retailResult]=await Promise.all([
      db.from("landerware_public_orders").select("id,total,currency,stripe_checkout_session_id,status").eq("id",retailOrderId).maybeSingle(),
      db.from("landerware_retail_orders").select("id,total_amount_cents,currency,stripe_checkout_session_id,status").eq("id",retailOrderId).maybeSingle()
    ]);
    if(publicResult.error||retailResult.error)return reply({ok:false,error:"Order lookup failed"},500);
    if(!!publicResult.data===!!retailResult.data)return reply({ok:false,error:"Missing or ambiguous order"},500);
    const publicOrder=publicResult.data,order=publicOrder||retailResult.data;
    if(session.id!==order.stripe_checkout_session_id)return reply({ok:false,error:"Checkout binding mismatch"},409);
    if(!paid){
      // Failure/expiry cannot downgrade a paid order; holds expire by their own clock.
      // Unpaid events are not used to release a seat early or confirm a registration.
      console.info(JSON.stringify({eventId:event.id,orderId:retailOrderId,eventType:event.type,reconciliation:"not_paid"}));
      return reply({ok:true,ignored:"Checkout not paid"});
    }
    if(!matchesPayment(order,session,!publicOrder))return reply({ok:false,error:"Payment evidence mismatch"},409);
    const {data,error}=publicOrder
      ? await db.rpc("landerware_finalize_public_order",{p_order_id:retailOrderId,p_stripe_payment_intent_id:session.payment_intent,p_evidence:paymentEvidence(session,event)})
      : await db.rpc("confirm_retail_payment",{p_order_id:retailOrderId,p_checkout_session_id:session.id,p_payment_intent_id:session.payment_intent,p_evidence:paymentEvidence(session,event)});
    if(error)return reply({ok:false,error:"Retail payment reconciliation failed"},500);
    return reply({ok:true,orderId:retailOrderId,status:data?.status||"paid",result:data});
  }

  const registrationId=String(session.client_reference_id||"").trim();
  if(!registrationId)return reply({ok:true,ignored:"No registration reference"});
  if(event.type==="checkout.session.async_payment_failed"){
    await db.from("registration_orders").update({status:"payment_failed",stripe_checkout_session_id:session.id||null,stripe_payment_intent_id:session.payment_intent||null,updated_at:new Date().toISOString()}).eq("registration_id",registrationId).neq("status","paid");
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
