import {nativeConfirmationService} from "../_shared/native-confirmation-service.mjs";
import {nativeConfirmationPostcommit} from "../_shared/native-confirmation-postcommit.mjs";
import {publicOrderVersion,settlePublicOrder} from "../public-registration/public-order-routing.mjs";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2.56.0";

const enc = new TextEncoder();
const SIGNATURE_TOLERANCE_SECONDS=300;
async function verify(raw:string,header:string|null,secret:string|null){
  if(!secret||!header||header.length>4096)return false;
  const pieces=header.split(",");
  if(pieces.length>32)return false;
  let timestamp:string|null=null;
  const signatures:string[]=[];
  for(const piece of pieces){
    const match=/^([a-zA-Z0-9]+)=([^\s=,]+)$/.exec(piece.trim());
    if(!match)return false;
    const [,scheme,value]=match;
    if(scheme==="t"){
      // One unambiguous integer timestamp; never silently choose a duplicate.
      if(timestamp!==null||!/^(0|[1-9][0-9]{0,15})$/.test(value)||!Number.isSafeInteger(Number(value)))return false;
      timestamp=value;
    }else if(scheme==="v1"){
      if(!/^[0-9a-f]{64}$/i.test(value))return false;
      signatures.push(value);
    }
    // Ignore other well-formed schemes, as Stripe may include older versions.
  }
  if(timestamp===null||signatures.length===0)return false;
  // Stripe signs retries with a fresh delivery timestamp. Event/receipt
  // idempotency remains the durable database's responsibility.
  const now=Math.floor(Date.now()/1000);
  if(!Number.isSafeInteger(now)||Math.abs(now-Number(timestamp))>SIGNATURE_TOLERANCE_SECONDS)return false;
  const key=await crypto.subtle.importKey("raw",enc.encode(secret),{name:"HMAC",hash:"SHA-256"},false,["verify"]);
  const payload=enc.encode(`${timestamp}.${raw}`);
  let matched=false;
  for(const signature of signatures){
    const bytes=new Uint8Array(32);
    for(let i=0;i<bytes.length;i+=1)bytes[i]=parseInt(signature.slice(i*2,i*2+2),16);
    // Web Crypto verifies each candidate without a handwritten digest compare.
    // Evaluate every bounded candidate, including signatures after a match.
    matched=(await crypto.subtle.verify("HMAC",key,bytes,payload))||matched;
  }
  return matched;
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
    const {data:publicOrder,error:publicLookupError}=await db.from('landerware_public_orders').select('id,status,total,currency,stripe_checkout_session_id,stripe_payment_intent_id,registration_profile_snapshot,checkout_runtime_version').eq('id',retailOrderId).maybeSingle();
    if(publicLookupError)return reply({ok:false,error:'Public payment lookup failed'},500);
    if(publicOrder){
      if(!paid)return reply({ok:true,ignored:'Public checkout not paid'});
      const expectedLive=Deno.env.get('STRIPE_EXPECTED_LIVEMODE')!=='false';
      if(session.mode!=='payment'||session.payment_status!=='paid'||session.livemode!==expectedLive||event.livemode!==expectedLive)return reply({ok:false,error:'Public payment evidence missing'},400);
      const evidence={id:session.id,mode:session.mode,payment_status:session.payment_status,amount_total:session.amount_total,currency:session.currency,metadata:{landerware_order_id:retailOrderId},livemode:session.livemode,stripeEventId:event.id};
      try{
       const result=await settlePublicOrder(async(name:string,args:Record<string,unknown>)=>{const {data,error}=await db.rpc(name,args);if(error)throw Error('payment_rpc_failed');return data;},publicOrder,session,evidence);
       if(result?.status==='paid'&&publicOrderVersion(publicOrder)==='legacy'){
        const confirmation=await fetch(`${Deno.env.get('SUPABASE_URL')}/functions/v1/public-registration/order/${publicOrder.id}?requireDelivery=1`,{redirect:'error',signal:AbortSignal.timeout(20000)});
        if(!confirmation.ok)throw Error('legacy_confirmation_pending');
       }
       if(result?.status==='paid'&&publicOrderVersion(publicOrder)==='native-v1'){
        const rpc=async(name:string,args:unknown)=>{const {data,error}=await db.rpc(name,args);if(error)throw Error('confirmation_rpc_failed');return data;};
        const notify=nativeConfirmationPostcommit({
         service:nativeConfirmationService({rpc,env:(name:string)=>Deno.env.get(name),request:fetch,report:(r:unknown)=>console.error(JSON.stringify(r))}),
         waitUntil:typeof EdgeRuntime!=="undefined"?(p:Promise<unknown>)=>EdgeRuntime.waitUntil(p):undefined,
         report:(r:unknown)=>console.error(JSON.stringify(r))
        });
        await notify(publicOrder.id);
       }
       return reply({ok:true,orderId:publicOrder.id,status:result?.status});
      }catch{return reply({ok:false,error:'Public payment reconciliation failed'},500);}

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
    const expectedLive=Deno.env.get('STRIPE_EXPECTED_LIVEMODE')!=='false';
    if(session.mode!=='payment'||session.payment_status!=='paid'||session.metadata?.skills_session!=='509474'||session.metadata?.registration_id!==registrationId||session.livemode!==expectedLive||event.livemode!==expectedLive||typeof session.payment_intent!=='string'||!/^pi_[A-Za-z0-9_]+$/.test(session.payment_intent))return reply({ok:false,error:'Skills payment evidence missing'},400);
    const {data:skillsOrder,error:skillsOrderError}=await db.from('registration_orders').select('id').eq('registration_id',registrationId).maybeSingle();
    if(skillsOrderError)return reply({ok:false,error:'Skills payment lookup failed'},500);
    if(!skillsOrder||session.metadata?.order_id!==skillsOrder.id)return reply({ok:false,error:'Skills payment evidence missing'},400);
    const {data,error}=await db.rpc('confirm_skills_checkout_payment',{p_registration_id:registrationId,p_checkout_id:session.id||null,
      p_amount_total:session.amount_total??null,p_currency:session.currency||null,p_payment_intent:typeof session.payment_intent==='string'?session.payment_intent:null});
    if(error||!data?.ok)return reply({ok:false,error:'Skills payment reconciliation failed'},500);
    if(!['paid','payment_review','refunded','cancelled'].includes(data.paymentStatus))return reply({ok:false,error:'Skills payment state unavailable'},500);
    return reply({ok:true,status:data.paymentStatus});
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

