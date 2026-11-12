// Immutable creator lineage comes from the stored order, never form snapshots,
// browser parameters or Stripe metadata. Legacy recovery can attach a profile.
export function publicOrderVersion(order){
 const version=order.checkout_runtime_version,snapshot=order.registration_profile_snapshot;
 if(version==='legacy')return 'legacy';
 if(version==='native-v1'&&(snapshot==null||Object.keys(snapshot).length===0||(snapshot.profile?.form_schema?.schemaVersion==='native-checkout.form.v1'&&typeof snapshot.profile.profile_key==='string'&&Number.isInteger(snapshot.profile.version))))return 'native-v1';
 // Old cached projections predate the marker and can only represent an empty
 // legacy snapshot. Never infer native creator lineage from form metadata.
 if(version==null&&(snapshot==null||(typeof snapshot==='object'&&!Array.isArray(snapshot)&&Object.keys(snapshot).length===0)))return 'legacy';
 throw Error('unsupported_order_version');
}
export const publicOrderReturnPath=order=>publicOrderVersion(order)==='native-v1'?'/register/checkout/':'/register/';
export async function settlePublicOrder(rpc,order,session,evidence){
 const version=publicOrderVersion(order);
 if(session?.mode!=='payment'||session.payment_status!=='paid'||session.id!==order.stripe_checkout_session_id||!order.stripe_checkout_session_id
  ||session.metadata?.landerware_order_id!==order.id||!Number.isSafeInteger(session.amount_total)||session.amount_total!==order.total
  ||session.currency!==order.currency||typeof session.payment_intent!=='string'||!session.payment_intent.startsWith('pi_')
  ||(order.stripe_payment_intent_id&&order.stripe_payment_intent_id!==session.payment_intent))throw Error('payment_evidence_mismatch');
 const args={p_order_id:order.id,p_stripe_payment_intent_id:session.payment_intent,p_evidence:evidence};
 // Separate commits intentionally preserve verified receipt when finalization
 // fails. Both namespace finalizers independently revalidate exact evidence.
 await rpc('native_checkout_record_payment',args);
 return rpc(version==='native-v1'?'native_checkout_finalize_order':'native_checkout_finalize_legacy_order',args);
}
