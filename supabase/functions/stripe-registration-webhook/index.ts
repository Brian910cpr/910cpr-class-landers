import { createClient } from "https://esm.sh/@supabase/supabase-js@2.56.0";
// Dockmaster: webhook credentials belong to the Edge Function secret store, never the repository.
const WEBHOOK_SECRET=Deno.env.get("STRIPE_WEBHOOK_SECRET")||"";
const enc=new TextEncoder();
function hex(bytes:ArrayBuffer){return Array.from(new Uint8Array(bytes)).map(b=>b.toString(16).padStart(2,"0")).join("")}
function safeEq(a:string,b:string){if(a.length!==b.length)return false;let x=0;for(let i=0;i<a.length;i++)x|=a.charCodeAt(i)^b.charCodeAt(i);return x===0}
async function verify(raw:string,header:string|null){if(!WEBHOOK_SECRET||!header)return false;const parts=Object.fromEntries(header.split(",").map(p=>p.split("=",2) as [string,string]));const t=parts.t,v1=parts.v1;if(!t||!v1)return false;const key=await crypto.subtle.importKey("raw",enc.encode(WEBHOOK_SECRET),{name:"HMAC",hash:"SHA-256"},false,["sign"]);const sig=hex(await crypto.subtle.sign("HMAC",key,enc.encode(`${t}.${raw}`)));return safeEq(sig,v1)}
const reply=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{"content-type":"application/json","cache-control":"no-store"}});
Deno.serve(async req=>{if(req.method!=="POST")return reply({ok:false},405);const raw=await req.text();if(!(await verify(raw,req.headers.get("stripe-signature"))))return reply({ok:false,error:"Invalid signature"},400);let evt:any;try{evt=JSON.parse(raw)}catch{return reply({ok:false,error:"Invalid JSON"},400)};
 const session=evt?.data?.object||{};const registrationId=String(session.client_reference_id||"").trim();if(!registrationId)return reply({ok:true,ignored:"No registration reference"});
 const db=createClient(Deno.env.get("SUPABASE_URL")!,Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,{auth:{persistSession:false}});
 const paid=evt.type==="checkout.session.completed"?session.payment_status==="paid":evt.type==="checkout.session.async_payment_succeeded";
 if(evt.type==="checkout.session.async_payment_failed"){await db.from("registration_orders").update({status:"payment_failed",stripe_checkout_session_id:session.id||null,stripe_payment_intent_id:session.payment_intent||null,updated_at:new Date().toISOString()}).eq("registration_id",registrationId);return reply({ok:true,status:"payment_failed"});}
 if(!paid)return reply({ok:true,ignored:"Checkout not paid"});
 const now=new Date().toISOString();const {data:order,error:oe}=await db.from("registration_orders").update({status:"paid",stripe_checkout_session_id:session.id||null,stripe_payment_intent_id:session.payment_intent||null,paid_at:now,updated_at:now}).eq("registration_id",registrationId).select("id").maybeSingle();if(oe||!order)return reply({ok:false,error:"Order not found"},500);
 await db.from("registrations").update({status:"registered",updated_at:now}).eq("id",registrationId);
 await db.from("registration_order_items").update({fulfillment_status:"awaiting_attention",updated_at:now}).eq("order_id",order.id).eq("fulfillment_status","awaiting_payment");
 return reply({ok:true,registrationId,orderId:order.id,status:"paid"});
});
