import {receiptView} from './generic.mjs';
const KEY=/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
export function basketView(r,now=Date.now()){
 const status=r.status==='paid'||['refunded','cancelled','payment_review'].includes(r.status)?r.status:r.paymentObserved?'processing':Date.parse(r.holdExpiresAt)<=now?'expired':r.status;
 return {kind:'course_basket',basketId:r.basketId,status,amountCents:r.amountCents,currency:r.currency,lines:r.lines,holdExpiresAt:r.holdExpiresAt,
  items:(r.items||[]).map(i=>({position:i.position,courseNumber:i.courseNumber,orderId:i.orderId,receipt:receiptView(i.receipt,now)}))};
}
export function nativeBasketCheckout({generic,rpc,checkout,verify,afterCommit,now=()=>Date.now()}){
 const receipt=key=>{if(!KEY.test(key||''))throw Error('invalid_request');return rpc('native_checkout_basket_receipt',{p_key:key});};
 const notify=async r=>{if(r.status==='paid')for(const i of r.items||[])try{await afterCommit?.(i.orderId);}catch{/* Durable outboxes retain retry state. */}};
 return {
  async choices(course){if(!/^\d+$/.test(course||''))throw Error('invalid_course');return {ok:true,choices:await rpc('native_checkout_basket_choices',{p_primary_course:course})};},
  async reserve(key,body){
   if(!KEY.test(key||'')||!Array.isArray(body.items)||body.items.length<2||body.items.length>3||['amountCents','total','discount','discountBps','price'].some(k=>Object.hasOwn(body,k)))throw Error('invalid_request');
   let old;try{old=await rpc('native_checkout_basket_replay',{p_key:key,p_request:body});}catch(e){if(e.message!=='reservation_not_found')throw e;}
   if(old){await notify(old);return {ok:true,receipt:basketView(old,now())};}
   const items=[];
   for(const item of body.items){
    const {m,wire,inputs,expected}=await generic.prepare(item);
    items.push({courseNumber:m.selection.course,profileKey:m.view.profileKey,profileVersion:m.view.profileVersion,context:m.context,
     externalId:m.selection.session||null,offer:m.offer||{},students:wire,inputs,expectedTotal:expected});
   }
   const r=await rpc('reserve_native_checkout_basket',{p_key:key,p_items:items,p_request:body});
   return {ok:true,receipt:basketView(r,now())};
  },
  async status(key){let r=await receipt(key);if(!['paid','cancelled','refunded'].includes(r.status)){try{await verify(r.basketId);}catch(e){r=await receipt(key);if(!r.paymentObserved)throw e;}r=await receipt(key);}await notify(r);return {ok:true,receipt:basketView(r,now())};},
  async checkout(key){const r=await receipt(key),view=basketView(r,now());if(['paid','processing','cancelled','refunded','payment_review'].includes(view.status)){await notify(r);return {ok:true,receipt:view};}if(view.status==='expired')throw Error('hold_expired');return {ok:true,checkoutUrl:(await checkout(r.basketId)).url};},
  async owned(key){return receipt(key);}
 };
}
export function basketCheckoutParams(b,origin){
 if(!b||b.currency!=='usd'||!Number.isSafeInteger(b.total)||b.total<=0||!Array.isArray(b.lines)||b.lines.reduce((n,l)=>n+l.totalCents,0)!==b.total)throw Error('ambiguous_price_allocation');
 const p=new URLSearchParams({mode:'payment',customer_email:b.payer_email,'payment_intent_data[receipt_email]':b.payer_email,
  success_url:`${origin}/register/checkout/?basket=${b.request_key}&paid=1`,cancel_url:`${origin}/register/checkout/?basket=${b.request_key}&cancelled=1`,
  expires_at:String(Math.floor(Date.parse(b.hold_expires_at)/1000)+31*60),'metadata[landerware_basket_id]':b.id,'metadata[landerware_order_type]':'course_basket'});
 b.lines.forEach((l,i)=>{if(!Number.isSafeInteger(l.totalCents)||l.totalCents<=0||!['session','heartcode_access','paper_book','ebook'].includes(l.kind)||l.kind!=='session'&&l.discountCents!==0||l.primary&&l.discountCents!==0)throw Error('ambiguous_price_allocation');p.set(`line_items[${i}][price_data][currency]`,'usd');p.set(`line_items[${i}][price_data][unit_amount]`,String(l.totalCents));p.set(`line_items[${i}][quantity]`,'1');p.set(`line_items[${i}][price_data][product_data][name]`,`${l.courseNumber} ${l.kind.replaceAll('_',' ')}${l.discountCents?' (10% added-session discount)':''}`);});return p;
}
export async function settleBasket(rpc,b,session,evidence){
 if(!b||session?.mode!=='payment'||session.payment_status!=='paid'||session.id!==b.stripe_checkout_session_id||!b.stripe_checkout_session_id||session.metadata?.landerware_basket_id!==b.id||session.metadata?.landerware_order_id||session.amount_total!==b.total||!Number.isSafeInteger(session.amount_total)||session.currency!==b.currency||typeof session.payment_intent!=='string'||!session.payment_intent.startsWith('pi_')||b.stripe_payment_intent_id&&b.stripe_payment_intent_id!==session.payment_intent)throw Error('payment_evidence_mismatch');
 const args={p_basket_id:b.id,p_intent:session.payment_intent,p_evidence:evidence};
 await rpc('native_checkout_basket_record_payment',args);
 return rpc('native_checkout_basket_finalize',args);
}
