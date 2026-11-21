// Deliberately not wired to an endpoint until source joins and owner actions are proven.
// A registration is participation evidence, never payment evidence.
type OrderEvidence = {
  id: string;
  registration_id: string;
  status: string;
  stripe_payment_intent_id?: string | null;
  stripe_checkout_session_id?: string | null;
};

export function paymentSummary(registrationId: string, orders: OrderEvidence[]) {
  // Caller supplies rows through public_order_students.registration_id, not email/name.
  const linked = orders.filter(row => registrationId && row.registration_id === registrationId);
  const byId = new Map<string, OrderEvidence>();
  for (const row of linked) {
    if (!row.id) return unknown('invalid_source_record');
    const previous = byId.get(row.id);
    if (previous && (previous.status !== row.status ||
        previous.stripe_payment_intent_id !== row.stripe_payment_intent_id ||
        previous.stripe_checkout_session_id !== row.stripe_checkout_session_id)) {
      return unknown('conflicting_source_records');
    }
    byId.set(row.id, row);
  }
  if (!byId.size) return unknown('no_linked_payment_evidence');
  // Do not hide another invoice/order by choosing the newest or most favorable state.
  if (byId.size !== 1) return unknown('multiple_orders_require_reconciliation');
  const order = [...byId.values()][0];
  const hasStripeReference = Boolean(order.stripe_payment_intent_id || order.stripe_checkout_session_id);
  const provider = hasStripeReference ? 'Stripe' : 'LanderWare';
  // Native orders have no partial-payment, waiver or QBO evidence contract yet.
  const status = order.status === 'paid' ? 'paid' :
    order.status === 'refunded' ? 'refunded' : 'unknown_unreconciled';
  return {provider, status, evidence: 'native_order', reason:
    status === 'unknown_unreconciled' ? 'order_state_does_not_prove_balance_due' : null};
}

function unknown(reason: string) {
  return {provider: 'unknown', status: 'unknown_unreconciled', evidence: 'unreconciled', reason};
}
