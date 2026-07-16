const JSON_HEADERS = { 'content-type': 'application/json; charset=utf-8' };
const COURSE_MAP = {
  'bls-initial': { courseId: '209806', credentialKey: 'aha_bls_provider' },
  'bls-renewal': { courseId: '359474', credentialKey: 'aha_bls_provider' },
  'bls-heartcode': { courseId: '210549', credentialKey: 'aha_bls_provider' },
  'hs-in-person': { courseId: '209809', credentialKey: 'aha_heartsaver_fa_cpr_aed' },
  'hs-online-skills': { courseId: '329495', credentialKey: 'aha_heartsaver_fa_cpr_aed' }
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: JSON_HEADERS });
}
function id(prefix) {
  return `${prefix}_${crypto.randomUUID().replaceAll('-', '')}`;
}
function token() {
  const bytes = new Uint8Array(9);
  crypto.getRandomValues(bytes);
  return btoa(String.fromCharCode(...bytes)).replaceAll('+', '').replaceAll('/', '').replaceAll('=', '').slice(0, 12);
}
async function body(request) {
  try { return await request.json(); } catch { return null; }
}

async function createGoToken(request, env) {
  const data = await body(request);
  if (!data?.renewalId) return json({ error: 'renewalId is required' }, 400);
  const renewal = await env.DB.prepare(`SELECT r.*, p.first_name, p.last_name, p.email, p.phone FROM renewal_cycles r JOIN people p ON p.person_id=r.person_id WHERE r.renewal_id=?`).bind(data.renewalId).first();
  if (!renewal) return json({ error: 'Renewal not found' }, 404);
  const existing = await env.DB.prepare(`SELECT token FROM go_tokens WHERE renewal_id=? AND state='active' ORDER BY created_at DESC LIMIT 1`).bind(data.renewalId).first();
  const code = existing?.token || token();
  if (!existing) {
    await env.DB.prepare(`INSERT INTO go_tokens(token,intent_type,person_id,renewal_id,corporate_customer,billing_account,credential_key,state,expires_at) VALUES(?,?,?,?,?,?,?,?,datetime('now','+18 months'))`)
      .bind(code,'corporate_renewal',renewal.person_id,renewal.renewal_id,renewal.corporate_customer,renewal.billing_account,renewal.credential_key,'active').run();
  }
  await env.DB.batch([
    env.DB.prepare(`UPDATE renewal_cycles SET status='link_sent',updated_at=CURRENT_TIMESTAMP WHERE renewal_id=? AND status!='registered'`).bind(data.renewalId),
    env.DB.prepare(`INSERT INTO portal_events(event_id,person_id,renewal_id,event_type,actor_type,payload_json) VALUES(?,?,?,?,?,?)`).bind(id('evt'),renewal.person_id,renewal.renewal_id,'scheduling_link_sent','corporate_user',JSON.stringify({ token: code }))
  ]);
  return json({ token: code, url: `${env.PUBLIC_ORIGIN}/go/${code}`, state: 'active' });
}

async function resolveGoToken(code, env) {
  const row = await env.DB.prepare(`SELECT g.*, p.first_name,p.last_name,p.email,p.phone FROM go_tokens g LEFT JOIN people p ON p.person_id=g.person_id WHERE g.token=?`).bind(code).first();
  if (!row) return json({ error: 'Link not found' }, 404);
  if (row.state !== 'active') return json({ state: row.state, message: 'This scheduling link is no longer active.' }, 410);
  if (row.expires_at && new Date(row.expires_at) < new Date()) return json({ state: 'expired', message: 'This scheduling link has expired.' }, 410);
  return json({
    token: code,
    intentType: row.intent_type,
    person: { firstName: row.first_name, lastName: row.last_name, email: row.email, phone: row.phone },
    corporateCustomer: row.corporate_customer,
    billingAccount: row.billing_account,
    credentialKey: row.credential_key,
    renewalId: row.renewal_id
  });
}

async function skipRenewal(request, env, renewalId) {
  await env.DB.batch([
    env.DB.prepare(`UPDATE renewal_cycles SET status='skipped',skipped_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE renewal_id=?`).bind(renewalId),
    env.DB.prepare(`UPDATE go_tokens SET state='revoked',revoked_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE renewal_id=? AND state='active'`).bind(renewalId),
    env.DB.prepare(`INSERT INTO portal_events(event_id,renewal_id,event_type,actor_type) VALUES(?,?,?,?)`).bind(id('evt'),renewalId,'renewal_skipped','corporate_user')
  ]);
  return json({ ok: true, renewalId, status: 'skipped' });
}

async function history(env, personId) {
  const registrations = await env.DB.prepare(`SELECT * FROM registrations WHERE person_id=? ORDER BY starts_at DESC`).bind(personId).all();
  const renewals = await env.DB.prepare(`SELECT * FROM renewal_cycles WHERE person_id=? ORDER BY expiration_date DESC`).bind(personId).all();
  const events = await env.DB.prepare(`SELECT * FROM portal_events WHERE person_id=? ORDER BY created_at DESC LIMIT 100`).bind(personId).all();
  return json({ registrations: registrations.results, renewals: renewals.results, events: events.results });
}

async function createRegistration(request, env) {
  const data = await body(request);
  const offer = COURSE_MAP[data?.offerKey];
  if (!data?.personId || !offer || !data?.startsAt) return json({ error: 'personId, offerKey and startsAt are required' }, 400);
  // This endpoint intentionally requires the caller to supply a verified availability proof once the shared availability service is exposed.
  if (!data.availabilityProof) return json({ error: 'Authoritative availability proof required; booking not written.' }, 409);
  const registrationId = id('reg');
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO registrations(registration_id,person_id,renewal_id,corporate_customer,billing_account,course_id,credential_key,class_id,starts_at,status) VALUES(?,?,?,?,?,?,?,?,?,'registered')`)
      .bind(registrationId,data.personId,data.renewalId||null,data.corporateCustomer||'MAXIM',data.billingAccount||null,offer.courseId,offer.credentialKey,data.classId||null,data.startsAt),
    data.renewalId ? env.DB.prepare(`UPDATE renewal_cycles SET status='registered',updated_at=CURRENT_TIMESTAMP WHERE renewal_id=?`).bind(data.renewalId) : env.DB.prepare(`SELECT 1`),
    data.renewalId ? env.DB.prepare(`UPDATE go_tokens SET state='consumed',consumed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE renewal_id=? AND state='active'`).bind(data.renewalId) : env.DB.prepare(`SELECT 1`),
    env.DB.prepare(`INSERT INTO portal_events(event_id,person_id,renewal_id,registration_id,event_type,actor_type,payload_json) VALUES(?,?,?,?,?,?,?)`)
      .bind(id('evt'),data.personId,data.renewalId||null,registrationId,'registration_created',data.actorType||'corporate_user',JSON.stringify({ offerKey:data.offerKey, startsAt:data.startsAt }))
  ]);
  return json({ ok: true, registrationId });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: { 'access-control-allow-origin': env.PUBLIC_ORIGIN, 'access-control-allow-methods': 'GET,POST,OPTIONS', 'access-control-allow-headers': 'content-type' } });
    let response;
    if (request.method === 'POST' && url.pathname === '/api/corp/maxim/go-links') response = await createGoToken(request, env);
    else if (request.method === 'GET' && url.pathname.startsWith('/api/go/')) response = await resolveGoToken(url.pathname.split('/').pop(), env);
    else if (request.method === 'POST' && /^\/api\/corp\/maxim\/renewals\/[^/]+\/skip$/.test(url.pathname)) response = await skipRenewal(request, env, url.pathname.split('/')[5]);
    else if (request.method === 'GET' && /^\/api\/corp\/maxim\/people\/[^/]+\/history$/.test(url.pathname)) response = await history(env, url.pathname.split('/')[5]);
    else if (request.method === 'POST' && url.pathname === '/api/corp/maxim/registrations') response = await createRegistration(request, env);
    else if (request.method === 'GET' && url.pathname.startsWith('/go/')) {
      const code = url.pathname.split('/').pop();
      return Response.redirect(`${env.PUBLIC_ORIGIN}${env.PORTAL_PATH}?go=${encodeURIComponent(code)}`, 302);
    } else response = json({ error: 'Not found' }, 404);
    const headers = new Headers(response.headers);
    headers.set('access-control-allow-origin', env.PUBLIC_ORIGIN);
    headers.set('cache-control', 'no-store');
    return new Response(response.body, { status: response.status, headers });
  }
};
