// Read-only owner attention adapter. Never select inventory values or recipient data.
export const ORDER_STATUS_QUERY="landerware_public_orders?status=in.(held,checkout_open,expired,cancelled)&or=(reconciliation_error.not.is.null,payment_evidence->>payment_status.eq.paid)&select=id,status,class_session_id,reconciliation_error,created_at,payment_status:payment_evidence->>payment_status&order=created_at.asc&limit=100";
export const CODE_STATUS_QUERY="native_code_delivery_history?select=id,state,attempts,claimed_at,prepared_at,provider_id,provider_delivery_status,provider_event_at,actual_delivery_confirmed,student:landerware_public_order_students(order_id,registration:registrations(class_session_id))&order=claimed_at.desc&limit=100";
export const SKILLS_PAYMENT_QUERY="registration_orders?skills_payment_review_reason=not.is.null&status=neq.refunded&select=id,status,skills_payment_received_at,skills_payment_review_reason,registration:registrations(class_session_id)&order=skills_payment_received_at.asc&limit=100";
const uuid=v=>/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(String(v||''))?String(v):'';
const date=v=>Number.isFinite(Date.parse(v))?new Date(v).toISOString():null;
const link=id=>uuid(id)?'/admin/dashboard.html?session='+encodeURIComponent(id):'/admin/dashboard.html#where-needed';
export async function checkoutAttention(read,now=Date.now()){
 const sources=await Promise.allSettled([read(ORDER_STATUS_QUERY),read(CODE_STATUS_QUERY),read(SKILLS_PAYMENT_QUERY)]),items=[];
 const availability={payments:sources[0].status==='fulfilled'&&Array.isArray(sources[0].value),codes:sources[1].status==='fulfilled'&&Array.isArray(sources[1].value),legacySkills:sources[2].status==='fulfilled'&&Array.isArray(sources[2].value)};
 for(const [index,name] of [[0,'payments'],[1,'codes'],[2,'legacySkills']]){
  if(!availability[name])items.push({key:'native-checkout-unavailable:'+name,severity:'critical',source:'Native checkout',title:'Checkout status unavailable',detail:(index===0?'Payment finalization':index===1?'Code delivery':'Historical skills payment')+' source could not be read. This is not evidence of an empty queue.',count:1,action_url:link(null)});
 }
 if(availability.payments)for(const row of sources[0].value){
  const id=uuid(row.id);if(!id||!['held','checkout_open','expired','cancelled'].includes(row.status))continue;
  const observed=row.payment_status==='paid';if(!observed&&!row.reconciliation_error)continue;
  items.push({key:'native-payment:'+id,severity:'critical',source:'Native checkout',title:observed?'Payment received; registration not finalized':'Payment reconciliation required',
   detail:'Order '+id+'; '+(observed?'payment received':'payment not confirmed')+'; registration not finalized; order '+row.status+'. Review only; no payment or booking action was taken.',count:1,occurred_at:date(row.created_at),action_url:link(row.class_session_id)});
 }
 if(availability.legacySkills)for(const row of sources[2].value){
  const id=uuid(row.id);if(!id||row.status==='refunded'||!row.skills_payment_review_reason||!date(row.skills_payment_received_at))continue;
  items.push({key:'legacy-skills-payment:'+id,severity:'critical',source:'Native checkout',title:'Payment received; skills booking needs review',
   detail:'Historical skills order '+id+'; payment received; registration was not restored. Review the original payment and cancellation. No refund, replacement booking, code or confirmation was issued.',count:1,occurred_at:date(row.skills_payment_received_at),action_url:link(row.registration?.class_session_id)});
 }
 if(availability.codes)for(const row of sources[1].value){
  const id=uuid(row.id);if(!id||!['processing','rejected','ambiguous','accepted','cancelled'].includes(row.state))continue;
  const stale=row.state==='processing'&&(!date(row.claimed_at)||Date.parse(row.claimed_at)<now-300000);
  const attempts=Number.isInteger(row.attempts)&&row.attempts>=0?row.attempts:0;
  let title,detail,severity;
  if(row.state==='accepted'&&row.provider_delivery_status==='delivered'&&row.actual_delivery_confirmed===true){title='Code email delivery confirmed by provider';detail='Recipient-bound provider delivery evidence is recorded. Code activation and course completion are not established.';severity='watch';}
  else if(row.state==='accepted'&&['bounced','failed','rejected','complained'].includes(row.provider_delivery_status)){title=row.provider_delivery_status==='complained'?'Code email complaint recorded':'Code email delivery failed';detail='Provider reported '+row.provider_delivery_status+'. Reconcile the original assigned unit; no resend or replacement was triggered.';severity='critical';}
  else if(row.state==='accepted'&&row.provider_delivery_status==='deferred'){title='Code email delivery deferred';detail='Provider delivery is deferred, not confirmed. Do not automatically resend an accepted message.';severity='due';}
  else if(row.state==='accepted'){title='Code provider accepted; delivery unconfirmed';detail='Provider acceptance is recorded. Recipient delivery and activation are not confirmed.';severity='watch';}
  else if(row.state==='ambiguous'||stale){title='Code delivery outcome unknown';detail='Reconciliation required. Do not infer failure or automatically resend; the original unit remains assigned.';severity='critical';}
  else if(row.state==='rejected'){title='Code send rejected before acceptance';detail=attempts>=5?'Retry limit reached; reconciliation required. No recipient delivery is confirmed.':'Explicit pre-send rejection recorded. Retry is queued under the existing bounded policy; no replacement unit is assigned.';severity=attempts>=5?'critical':'due';}
  else if(row.state==='cancelled'){title='Code delivery stopped';detail=row.actual_delivery_confirmed===true?'Provider delivery evidence exists, but eligibility is terminal. No resend, inventory change or registration revival was performed.':row.provider_id?'A provider receipt exists, but eligibility became terminal. Do not infer delivery or resend.':row.prepared_at?'Eligibility ended after private preparation; the provider outcome is unconfirmed. Do not automatically resend.':'Eligibility ended before private preparation. No successful recipient delivery is recorded.';severity=row.provider_id||row.prepared_at?'critical':'watch';}
  else {title=row.prepared_at?'Code provider result pending':'Code delivery queued';detail=row.prepared_at?'Private preparation occurred; no provider acceptance is recorded. An interrupted attempt must not be blindly resent.':'Delivery is claimed but not yet privately prepared; no provider acceptance or recipient delivery is recorded.';severity='watch';}
  const orderId=uuid(row.student?.order_id);
  items.push({key:'native-code:'+id,severity,source:'Native checkout',title,detail:'Attempt '+id+(orderId?'; order '+orderId:'')+'; '+detail,count:1,occurred_at:date(row.claimed_at),action_url:link(row.student?.registration?.class_session_id)});
 }
 return {items,availability,limitPerSource:100,scope:'bounded read-only status; not a completeness or delivery-health proof'};
}
