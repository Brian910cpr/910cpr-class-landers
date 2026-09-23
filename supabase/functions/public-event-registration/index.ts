import { createClient } from "https://esm.sh/@supabase/supabase-js@2.56.0";

const cors={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"authorization,x-client-info,apikey,content-type","Access-Control-Allow-Methods":"GET,POST,OPTIONS"};
const json=(b:unknown,s=200)=>new Response(JSON.stringify(b),{status:s,headers:{...cors,"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"}});
const clean=(v:unknown,m=200)=>String(v??"").trim().slice(0,m);
const emailOk=(v:string)=>/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
const EARL="nseaswim-earl-jackson-2026-10-04";
const JACKSON="earl-jackson-family-friends-2026-10-04";
const EVENT_SLUGS=[EARL,JACKSON];
const HANDS_ON_CAPACITY=29;
const HOLD_MINUTES=30;
const BLS_PAYMENT_LINK="https://book.stripe.com/9B6cN4dEz0yUeJecC9dIA10";

function parseGuestNames(value:unknown){
  if(Array.isArray(value)) return value.map(v=>clean(v,120)).filter(Boolean).slice(0,28);
  return clean(value,3000).split(/\n|,/).map(v=>v.trim()).filter(Boolean).slice(0,28);
}
function splitName(full:string){
  const parts=full.trim().split(/\s+/).filter(Boolean);
  if(parts.length<2)return {firstName:parts[0]||"Guest",lastName:"Guest"};
  return {firstName:parts[0],lastName:parts.slice(1).join(" ")};
}

Deno.serve(async(req)=>{
  if(req.method==="OPTIONS")return new Response("ok",{headers:cors});
  if(!["GET","POST"].includes(req.method))return json({ok:false,error:"Method not allowed"},405);
  const body=req.method==="POST"?await req.json().catch(()=>({})):{};
  const url=new URL(req.url);
  const slug=clean(url.searchParams.get("event")||body.event,120);
  if(!EVENT_SLUGS.includes(slug))return json({ok:false,error:"Event not found"},404);

  const db=createClient(Deno.env.get("SUPABASE_URL")!,Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,{auth:{persistSession:false}});
  const {data:sessions,error:se}=await db.from("class_sessions")
    .select("id,external_class_id,start_at,end_at,timezone,max_students,registration_backend,visibility,registration_status,price,registration_url,public_notes,course:courses!class_sessions_course_id_fkey(name,course_key,certifying_body),location:locations!class_sessions_location_id_fkey(name,address_line1,address_line2,city,state,postal_code),instructor:people!class_sessions_lead_instructor_id_fkey(display_name)")
    .in("external_class_id",EVENT_SLUGS).eq("visibility","public");
  if(se)return json({ok:false,error:"Unable to load event"},500);
  const session=(sessions||[]).find((s:any)=>s.external_class_id===slug);
  if(!session)return json({ok:false,error:"Event not found"},404);

  const ids=(sessions||[]).map((s:any)=>s.id);
  const cutoff=new Date(Date.now()-HOLD_MINUTES*60*1000).toISOString();
  const [{count:registeredCount},{count:holdCount}]=await Promise.all([
    db.from("registrations").select("id",{count:"exact",head:true}).in("class_session_id",ids).eq("status","registered"),
    db.from("registrations").select("id",{count:"exact",head:true}).in("class_session_id",ids).eq("status","payment_pending").gte("updated_at",cutoff)
  ]);
  const registered=registeredCount||0,checkoutHolds=holdCount||0,occupied=registered+checkoutHolds;
  const remaining=Math.max(0,HANDS_ON_CAPACITY-occupied);
  if(req.method==="GET")return json({ok:true,event:{...session,registered,checkoutHolds,occupied,remaining,handsOnCapacity:HANDS_ON_CAPACITY,capacityReason:"shared_manikin_pool",holdMinutes:HOLD_MINUTES}});

  if(session.registration_backend!=="landerware"||session.registration_status!=="open")return json({ok:false,error:"Registration is not open"},409);
  if(clean(body.company,80))return json({ok:true,bot:true});
  const firstName=clean(body.firstName,80),lastName=clean(body.lastName,80),email=clean(body.email,160).toLowerCase(),phone=clean(body.phone,40);
  if(!firstName||!lastName||!emailOk(email))return json({ok:false,error:"First name, last name, and a valid email are required"},400);

  const guestNames=parseGuestNames(body.guestNames||body.additionalGuests||body.attendees);
  const requestedCount=Math.max(1,Math.min(HANDS_ON_CAPACITY,Number(body.attendeeCount||body.numberAttending||1)));
  if(requestedCount!==1+guestNames.length)return json({ok:false,error:"Please provide a name for each additional attendee"},400);
  if(requestedCount>remaining)return json({ok:false,error:`Only ${remaining} hands-on spot${remaining===1?" is":"s are"} still available across both Earl Jackson sessions.`},409);

  async function upsertCustomer(fn:string,ln:string,mail:string|null,tel:string|null){
    if(mail){
      const {data:existing}=await db.from("customers").select("id").ilike("email",mail).limit(1).maybeSingle();
      if(existing?.id){await db.from("customers").update({first_name:fn,last_name:ln,phone:tel||null,updated_at:new Date().toISOString()}).eq("id",existing.id);return existing.id;}
    }
    const {data:created,error}=await db.from("customers").insert({first_name:fn,last_name:ln,email:mail,phone:tel||null}).select("id").single();
    if(error||!created)throw new Error("customer_create_failed");
    return created.id as string;
  }

  const primaryCustomerId=await upsertCustomer(firstName,lastName,email,phone||null);
  const groupKey=crypto.randomUUID();
  const sourcePrefix=slug===EARL?"public_landerware_event:bls":"public_landerware_event:friends_family";
  const newRegistrationIds:string[]=[];

  const {data:primaryReg,error:pre}=await db.from("registrations").insert({
    customer_id:primaryCustomerId,class_session_id:session.id,
    status:slug===EARL?"payment_pending":"registered",
    registration_source:`${sourcePrefix}:group:${groupKey}`,
    optional_survey:{}
  }).select("id").single();
  if(pre||!primaryReg)return json({ok:false,error:"Unable to create registration"},500);
  newRegistrationIds.push(primaryReg.id);

  for(const guest of guestNames){
    const n=splitName(guest);
    const cid=await upsertCustomer(n.firstName,n.lastName,null,null);
    const {data:gr,error:ge}=await db.from("registrations").insert({
      customer_id:cid,class_session_id:session.id,
      status:slug===EARL?"payment_pending":"registered",
      registration_source:`${sourcePrefix}:guest:${groupKey}`,
      optional_survey:{hostRegistrationId:primaryReg.id}
    }).select("id").single();
    if(ge||!gr)return json({ok:false,error:"Unable to create all attendee registrations"},500);
    newRegistrationIds.push(gr.id);
  }

  const survey=body.survey&&typeof body.survey==="object"?body.survey:{};
  await db.from("registrations").update({
    optional_survey:{...survey,groupRegistrationIds:newRegistrationIds,attendeeCount:requestedCount,guestNames}
  }).eq("id",primaryReg.id);

  if(slug===JACKSON){
    return json({ok:true,confirmed:true,registrationId:primaryReg.id,groupRegistrationIds:newRegistrationIds,event:{remaining:Math.max(0,remaining-requestedCount),handsOnCapacity:HANDS_ON_CAPACITY}},201);
  }

  const ebookQty=Math.max(0,Math.min(29,Number(body.ebookQty??1)));
  const courseAmount=12*requestedCount,materialsAmount=20*ebookQty,totalAmount=courseAmount+materialsAmount;
  const {data:order,error:oe}=await db.from("registration_orders").upsert({
    registration_id:primaryReg.id,status:"payment_pending",currency:"usd",
    course_amount:courseAmount,materials_amount:materialsAmount,total_amount:totalAmount,updated_at:new Date().toISOString()
  },{onConflict:"registration_id"}).select("id").single();
  if(oe||!order)return json({ok:false,error:"Unable to create payment order"},500);

  await db.from("registration_order_items").delete().eq("order_id",order.id);
  const items:any[]=[{order_id:order.id,item_type:"course",product_id:null,description:"AHA BLS Provider - Earl Jackson community registration",quantity:requestedCount,unit_amount:12,fulfillment_status:"not_required"}];
  if(ebookQty>0){
    const {data:product}=await db.from("products").select("id").eq("product_key","aha-bls-2025-emanual").eq("active",true).maybeSingle();
    if(product?.id)items.push({order_id:order.id,item_type:"material",product_id:product.id,description:"2025 AHA BLS Provider eManual",quantity:ebookQty,unit_amount:20,fulfillment_status:"awaiting_payment"});
  }
  const {error:ie}=await db.from("registration_order_items").insert(items);
  if(ie)return json({ok:false,error:"Unable to create order items"},500);

  const qs=new URLSearchParams({client_reference_id:primaryReg.id,prefilled_email:email});
  return json({ok:true,paymentPending:true,registrationId:primaryReg.id,groupRegistrationIds:newRegistrationIds,orderId:order.id,checkoutUrl:`${BLS_PAYMENT_LINK}?${qs.toString()}`,event:{remaining:Math.max(0,remaining-requestedCount),handsOnCapacity:HANDS_ON_CAPACITY,holdMinutes:HOLD_MINUTES}},201);
});
