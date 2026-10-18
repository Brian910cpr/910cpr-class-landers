// Owner-only projection of the existing outbox. No sending or retry side effects.
const UUID = /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i;
export async function messageHistory(params: URLSearchParams, rest: (path: string) => Promise<any>) {
  const registration = params.get('registration_id') || '';
  const person = params.get('customer_id') || '';
  if ((registration && !UUID.test(registration)) || (person && !UUID.test(person))) throw Error('invalid_message_filter');
  const offset = Number(params.get('offset') || 0);
  if (!Number.isInteger(offset) || offset < 0 || offset > 10000) throw Error('invalid_message_filter');
  const state = params.get('status') || '';
  if (state && !['pending','sent','failed','delivered','bounced','scheduled','suppressed'].includes(state)) throw Error('invalid_message_filter');
  const filters = [registration ? `operational_registration_id=eq.${registration}` : '', person ? `customer_id=eq.${person}` : '', state ? `delivery_status=eq.${state}` : ''].filter(Boolean);
  const fields = 'id,customer_id,operational_registration_id,template_key,channel,recipient,subject,body_text,delivery_provider,delivery_status,provider_message_id,sent_at,failed_at,failure_detail,created_at';
  const rows = await rest(`landerware_messages?select=${fields}&order=created_at.desc,id.desc&limit=101&offset=${offset}${filters.length?'&'+filters.join('&'):''}`);
  return {messages:rows.slice(0,100),hasMore:rows.length>100,offset,checkedAt:new Date().toISOString()};
}
