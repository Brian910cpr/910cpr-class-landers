// Owner-only projection of the existing outbox. No sending or retry side effects.
const UUID = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i;
export async function messageHistory(params: URLSearchParams, rest: (path: string) => Promise<any>) {
  const registration = params.get('registration_id') || '';
  const person = params.get('customer_id') || '';
  if ((registration && !UUID.test(registration)) || (person && !UUID.test(person))) throw Error('invalid_message_filter');
  const offset = Number(params.get('offset') || 0);
  if (!Number.isInteger(offset) || offset < 0 || offset > 10000) throw Error('invalid_message_filter');
  const state = params.get('status') || '';
  if (state && !['pending','sent','failed','delivered','bounced','scheduled','suppressed','deferred','rejected','complained'].includes(state)) throw Error('invalid_message_filter');
  const filters = [registration ? `operational_registration_id=eq.${registration}` : '', person ? `customer_id=eq.${person}` : ''].filter(Boolean);
  if(state==='failed')filters.push('effective_status=in.(failed,bounced,rejected,complained)');
  else if(state)filters.push(`effective_status=eq.${state}`);
  const fields = 'id,customer_id,operational_registration_id,template_key,channel,recipient,subject,body_text,delivery_provider,delivery_status,provider_message_id,sent_at,failed_at,failure_detail,created_at,scheduled_for,suppressed_at,suppression_reason,effective_status,provider_delivery_status,provider_event_at,provider_failure_detail';
  const rows = await rest(`landerware_message_history?select=${fields}&order=created_at.desc,id.desc&limit=101&offset=${offset}${filters.length?'&'+filters.join('&'):''}`);
  return {messages:rows.slice(0,100),hasMore:rows.length>100,offset,checkedAt:new Date().toISOString()};
}
