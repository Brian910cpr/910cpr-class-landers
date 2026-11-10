import {SITE} from './policy.mjs';

// The receipt UUID is a bearer capability kept in sessionStorage, never a URL.
// Only the server can read the durable quote or bind a provider session to it.
export async function skillsCheckout({rpc,stripe,now=()=>Date.now()},key,context,statusOnly=false) {
  const order=await rpc('skills_checkout_order',{p_key:key,p_context:context});
  const reservation={startsAt:order.startsAt,location:order.location,instructor:order.instructor};
  const state=(paymentStatus,extra={})=>({ok:true,paymentStatus,reservation,...extra});
  if(order.status==='paid')return state('paid');
  if(!['payment_pending','payment_failed'].includes(order.status))throw Error('payment_unavailable');
  let session;
  if(order.checkoutId)session=await stripe('GET',`checkout/sessions/${encodeURIComponent(order.checkoutId)}`);
  else {
    if(statusOnly)return state('pending');
    // Stripe retains idempotency keys for at least 24h. Never recreate an
    // uncertain older checkout with an evicted key.
    if(now()-Date.parse(order.createdAt)>23*3600000)throw Error('payment_reconciliation_required');
    const start=new Date(order.startsAt);
    const parts=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(start).map(p=>[p.type,p.value]));
    const agency={'cpr-aed':'heartsaver','first-aid-cpr-aed':'heartsaver','arc-blended':'arc','hsi-blended':'hsi','bls-skills':'bls'}[context];
    if(!agency||order.amountCents!==5500||order.currency!=='usd')throw Error('payment_mismatch');
    const back=new URL('/register/skills-session/',SITE);
    for(const [k,v] of Object.entries({course:'509474',date:`${parts.year}-${parts.month}-${parts.day}`,startTime:`${parts.hour}:${parts.minute}`,location:order.location,instructor:order.instructor,skillsContext:context,context:agency}))back.searchParams.set(k,v);
    const params=new URLSearchParams({mode:'payment',client_reference_id:order.registrationId,customer_email:order.email,
      integration_identifier:'910cpr_skills_'+Array.from(order.orderId.replace(/-/g,'').slice(0,8).padEnd(8,'x'),c=>String.fromCharCode(97+c.charCodeAt(0)%26)).join(''),
      success_url:back.href+'&payment=return',cancel_url:back.href+'&payment=cancelled',
      'metadata[skills_session]':'509474','metadata[registration_id]':order.registrationId,'metadata[order_id]':order.orderId,
      'line_items[0][price_data][currency]':order.currency,'line_items[0][price_data][unit_amount]':String(order.amountCents),
      'line_items[0][price_data][product_data][name]':'Skills session only (online course not included)','line_items[0][quantity]':'1'});
    session=await stripe('POST','checkout/sessions',params,`skills-checkout-${order.orderId}`);
    if(!session?.id?.startsWith('cs_'))throw Error('payment_unavailable');
    if(session.mode!=='payment'||session.client_reference_id!==order.registrationId||session.metadata?.order_id!==order.orderId||session.metadata?.skills_session!=='509474'||session.amount_total!==order.amountCents||session.currency!==order.currency)throw Error('payment_mismatch');
    await rpc('bind_skills_checkout',{p_registration_id:order.registrationId,p_checkout_id:session.id});
  }
  if(session.mode!=='payment'||session.client_reference_id!==order.registrationId||session.metadata?.order_id!==order.orderId||
      session.metadata?.skills_session!=='509474'||session.amount_total!==order.amountCents||session.currency!==order.currency)throw Error('payment_mismatch');
  if(session.payment_status==='paid'){
    await rpc('confirm_skills_checkout_payment',{p_registration_id:order.registrationId,p_checkout_id:session.id,p_amount_total:session.amount_total,p_currency:session.currency,p_payment_intent:typeof session.payment_intent==='string'?session.payment_intent:null});
    return state('paid');
  }
  if(session.status==='complete')return state('processing');
  if(session.status!=='open')throw Error('payment_reconciliation_required');
  if(typeof session.url!=='string'||!session.url.startsWith('https://checkout.stripe.com/'))throw Error('payment_unavailable');
  return state('pending',statusOnly?{}:{checkoutUrl:session.url});
}

export function certificateInput(value){
  if(!value||typeof value.base64!=='string'||value.base64.length>2796204||value.base64.length%4!==0||!/^[A-Za-z0-9+/]*={0,2}$/.test(value.base64))throw Error('invalid_certificate');
  let decoded;try{decoded=atob(value.base64);}catch{throw Error('invalid_certificate');}
  const bytes=Uint8Array.from(decoded,c=>c.charCodeAt(0));
  if(!bytes.length||bytes.length>2097152)throw Error('invalid_certificate');
  const signatures={'application/pdf':[[37,80,68,70,45],'pdf'],'image/jpeg':[[255,216,255],'jpg'],'image/png':[[137,80,78,71,13,10,26,10],'png']};
  const spec=signatures[value.type];
  if(!spec||!spec[0].every((n,i)=>bytes[i]===n))throw Error('invalid_certificate');
  return {bytes,type:value.type,extension:spec[1]};
}
