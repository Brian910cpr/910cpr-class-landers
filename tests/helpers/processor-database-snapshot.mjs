// Read-only adapter for the already admitted disposable application database.
// Caller must enforce the existing independent loopback/process admission.
export function processorDatabaseSnapshot({query,orderId}){
 if(!/^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(orderId||''))throw Error('invalid_snapshot_order');
 const sql=`select jsonb_build_object(
 'orderId',o.id,'status',o.status,'amountCents',o.total,'currency',o.currency,
 'sessionId',o.stripe_checkout_session_id,'paymentIntent',o.stripe_payment_intent_id,'course',o.course_id,
 'registrationIds',coalesce((select jsonb_agg(r.id order by r.id) from public.landerware_public_order_students st
 join public.registrations r on r.id=st.registration_id
 where st.order_id=o.id and r.class_session_id=o.class_session_id
 and r.registration_source='landerware_native_checkout' and r.status in ('registered','confirmed','active','completed')),'[]'::jsonb),
 'occupiedSeats',(select count(*) from public.landerware_public_order_students st join public.registrations r on r.id=st.registration_id
 where st.order_id=o.id and r.class_session_id=o.class_session_id and r.registration_source='landerware_native_checkout'
 and r.status in ('registered','confirmed','active','completed')),
 'confirmationCount',(select count(*) from public.landerware_messages m where m.template_key='retail-paid-confirmation-v3'
 and exists(select 1 from public.landerware_public_order_students st where st.order_id=o.id
 and m.recipient=st.email and m.idempotency_key='public-order-paid:'||o.id::text||':'||st.email))
 ) as snapshot from public.landerware_public_orders o where o.id='${orderId}'::uuid`;
 return async()=>{
  const result=await query(sql);
  if(result.rows?.length!==1||!result.rows[0].snapshot)throw Error('snapshot_order_not_found');
  return result.rows[0].snapshot;
 };
}
