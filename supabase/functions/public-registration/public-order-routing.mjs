// Version comes only from the stored server-created profile snapshot, never
// browser parameters or Stripe metadata. Empty historical snapshots stay legacy.
export function publicOrderVersion(order){
 const snapshot=order.registration_profile_snapshot;
 if(snapshot==null||(typeof snapshot==='object'&&!Array.isArray(snapshot)&&Object.keys(snapshot).length===0))return 'legacy';
 const profile=snapshot?.profile;
 if(profile?.form_schema?.schemaVersion==='native-checkout.form.v1'&&typeof profile.profile_key==='string'&&Number.isInteger(profile.version)&&profile.version>0)return 'native-v1';
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
