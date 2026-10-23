// Dispatch only verified paid-order confirmations from the canonical message queue.
import {renderCheckoutEmail} from './checkout-email-template.mjs';
const BUILD = 'checkout-confirmation-20261018.1';
const reply = (data, status = 200) => new Response(JSON.stringify(data), {
  status, headers: {'content-type':'application/json', 'cache-control':'no-store'}
});
async function rpc(env, name, args = {}) {
  if (!env.SUPABASE_URL || !env.SUPABASE_PUBLISHABLE_KEY || !env.CHECKOUT_DELIVERY_TOKEN) throw Error('delivery_configuration_missing');
  const res = await fetch(`${env.SUPABASE_URL}/rest/v1/rpc/${name}`, {
    method:'POST', headers:{'content-type':'application/json', apikey:env.SUPABASE_PUBLISHABLE_KEY},
    body:JSON.stringify({p_token:env.CHECKOUT_DELIVERY_TOKEN, ...args})
  });
  if (!res.ok) throw Error(`delivery_database_${res.status}`);
  return res.json();
}
async function authorized(request, env) {
  const value = request.headers.get('authorization') || '';
  if (!env.CHECKOUT_DELIVERY_TOKEN || !value.startsWith('Bearer ')) return false;
  const digest = async s => new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)));
  const [a,b] = await Promise.all([digest(value.slice(7)), digest(env.CHECKOUT_DELIVERY_TOKEN)]);
  return a.reduce((n,v,i) => n | (v ^ b[i]),0) === 0;
}
export async function dispatch(env) {
  if (!env.EMAIL || !env.FROM_EMAIL) throw Error('email_binding_missing');
  await rpc(env,'landerware_prepare_checkout_reminders');
  let sent = 0, failed = 0;
  for (let i=0;i<10;i++) {
    const job = await rpc(env,'landerware_claim_checkout_confirmation');
    if (!job?.messageId) break;
    if (job.customerTemplate && !job.confirmation) throw Error('confirmation_class_data_missing');
    const content = job.confirmation ? renderCheckoutEmail(job.confirmation) : {subject:job.subject,text:job.body};
    let result;
    try {
      result = await env.EMAIL.send({from:{email:env.FROM_EMAIL,name:'910CPR'},
        ...(env.REPLY_TO_EMAIL ? {replyTo:env.REPLY_TO_EMAIL} : {}),
        to:job.recipient,...content});
    } catch (error) {
      // Only explicit pre-send rejection codes may retry. Other outcomes are unknown.
      const known = ['E_SENDER_NOT_VERIFIED','E_RATE_LIMIT_EXCEEDED'].includes(error?.code);
      await rpc(env,'landerware_settle_checkout_confirmation',{
        p_message_id:job.messageId,p_lease:job.lease,p_outcome:known?'rejected':'ambiguous',
        p_provider_id:null,p_error:known?error.code:'provider_result_unknown'
      });
      failed++;
      continue;
    }
    if (!result?.messageId) {
      await rpc(env,'landerware_settle_checkout_confirmation',{
        p_message_id:job.messageId,p_lease:job.lease,p_outcome:'ambiguous',
        p_provider_id:null,p_error:'provider_receipt_missing'
      });
      failed++;
      continue;
    }
    // If recording acceptance fails, leave the lease unresolved; do not resend.
    await rpc(env,'landerware_settle_checkout_confirmation',{
      p_message_id:job.messageId,p_lease:job.lease,p_outcome:'sent',
      p_provider_id:result.messageId,p_error:null
    });
    sent++;
  }
  return {sent,failed};
}
export default {
  async queue(batch,env) {
    for (const message of batch.messages) {
      try {
        await rpc(env,'landerware_record_email_delivery_event',{p_event:message.body});
        message.ack();
      } catch {
        console.error(JSON.stringify({build:BUILD,error:'email_delivery_event_record_failed'}));
        message.retry();
      }
    }
  },
  async scheduled(_event,env,ctx) {
    ctx.waitUntil(dispatch(env).catch(() => console.error(JSON.stringify({build:BUILD,error:'confirmation_dispatch_failed'}))));
  },
  async fetch(request,env) {
    const path = new URL(request.url).pathname;
    if (path==='/health' && request.method==='GET') return reply({build:BUILD});
    if (!await authorized(request,env)) return reply({error:'unauthorized'},401);
    try {
      if (path==='/status' && request.method==='GET') return reply(await rpc(env,'landerware_checkout_confirmation_health'));
      if (path==='/run' && request.method==='POST') return reply(await dispatch(env));
      return reply({error:'not_found'},404);
    } catch { return reply({error:'confirmation_service_unavailable'},503); }
  }
};
