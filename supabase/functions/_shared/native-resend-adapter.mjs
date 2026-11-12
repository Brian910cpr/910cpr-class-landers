// Provider-only native confirmation adapter. Does not claim, settle, or enable queues.
// Caller must supply an authenticated, validated durable claim and persist the outcome.
import { renderNativeCheckoutClaim } from './native-checkout-email.mjs';
const ENDPOINT = 'https://api.resend.com/emails';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const EMAIL = /^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$/;
const SAFE_ID = /^[A-Za-z0-9_-]{1,128}$/;
const MAX_RESPONSE = 64 * 1024;

function outcome(state, errorCode = null, providerId = null) {
  return { outcome: state, providerId, errorCode };
}

function validSender(value) {
  if (typeof value !== 'string' || value.length > 320 || /[\r\n]/.test(value)) return false;
  if (EMAIL.test(value)) return true;
  const named = value.match(/^[^<>]+<([^<>]+)>$/);
  return Boolean(named && EMAIL.test(named[1]));
}

function validClaim(claim) {
  return claim && UUID.test(claim.messageId || '') &&
    typeof claim.recipient === 'string' && claim.recipient.length <= 254 && EMAIL.test(claim.recipient) &&
    typeof claim.subject === 'string' && claim.subject.length > 0 && claim.subject.length <= 998 &&
    !/[\r\n]/.test(claim.subject) && typeof claim.body === 'string' &&
    claim.body.length > 0 && new TextEncoder().encode(claim.body).byteLength <= 256 * 1024;
}

async function boundedJSON(response) {
  if (!response.body) throw Error('empty_response');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let size = 0, body = '';
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_RESPONSE) throw Error('response_too_large');
      body += decoder.decode(value, { stream: true });
    }
    return JSON.parse(body + decoder.decode());
  } finally {
    try { await reader.cancel(); } catch { /* Outcome remains unknown. */ }
  }
}

export async function sendNativeConfirmation(claim, options = {}) {
  // Legacy provider-only contract stays text-only. An arbitrary claim.html field
  // is ignored; only the structured native entry point may generate HTML.
  return sendNativeContent(claim, { subject: claim?.subject, text: claim?.body }, options);
}

export async function sendNativeCheckoutClaim(claim, options = {}) {
  let content;
  try { content = renderNativeCheckoutClaim(claim); }
  catch { return outcome('rejected', 'native_mail_invalid_confirmation'); }
  return sendNativeContent(claim, content, options);
}

async function sendNativeContent(claim, content, options) {
  const { apiKey, from, replyTo, request } = options;
  // No default network function: tests and callers must explicitly provide one.
  if (typeof request !== 'function' || typeof apiKey !== 'string' || !apiKey.trim() || /[\r\n]/.test(apiKey) ||
      !validSender(from) ||
      (replyTo !== undefined && (typeof replyTo !== 'string' || !EMAIL.test(replyTo)))) {
    return outcome('rejected', 'native_mail_not_configured');
  }
  const renderedClaim = { ...claim, subject: content.subject, body: content.text };
  if (!validClaim(renderedClaim) || (content.html !== undefined &&
      (typeof content.html !== 'string' || new TextEncoder().encode(content.html).byteLength > 256 * 1024))) {
    return outcome('rejected', 'native_mail_invalid_claim');
  }
  const payload = { from, to: [claim.recipient], subject: content.subject, text: content.text };
  if (content.html !== undefined) payload.html = content.html;
  if (replyTo) payload.reply_to = replyTo;
  let response;
  try {
    response = await request(ENDPOINT, {
      method: 'POST', redirect: 'error', signal: AbortSignal.timeout(12_000),
      headers: {
        authorization: `Bearer ${apiKey}`, 'content-type': 'application/json',
        'idempotency-key': `native-checkout-${claim.messageId}`,
      },
      body: JSON.stringify(payload),
    });
  } catch {
    // A send may have been accepted before a timeout/disconnect; never blind-retry.
    return outcome('ambiguous', 'native_mail_request_unknown');
  }
  if (!response || !Number.isInteger(response.status)) {
    return outcome('ambiguous', 'native_mail_response_unknown');
  }
  const status = response.status;
  if (status < 200 || status >= 300) {
    // Explicit ordinary 4xx is a rejection. Timeout/concurrency/5xx is uncertain.
    if (status >= 400 && status < 500 && status !== 408 && status !== 409) {
      return outcome('rejected', `native_mail_http_${status}`);
    }
    return outcome('ambiguous', `native_mail_http_${status}`);
  }
  try {
    const result = await boundedJSON(response);
    if (typeof result?.id !== 'string' || !SAFE_ID.test(result.id)) {
      return outcome('ambiguous', 'native_mail_receipt_missing');
    }
    return outcome('sent', null, result.id);
  } catch {
    return outcome('ambiguous', 'native_mail_receipt_unreadable');
  }
}
