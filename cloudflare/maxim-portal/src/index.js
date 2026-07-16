const JSON_HEADERS = { 'content-type': 'application/json; charset=utf-8' };
const COURSE_MAP = {
  'bls-initial': { courseId: '209806', credentialKey: 'aha_bls_provider' },
  'bls-renewal': { courseId: '359474', credentialKey: 'aha_bls_provider' },
  'bls-heartcode': { courseId: '210549', credentialKey: 'aha_bls_provider' },
  'hs-in-person': { courseId: '209809', credentialKey: 'aha_heartsaver_fa_cpr_aed' },
  'hs-online-skills': { courseId: '329495', credentialKey: 'aha_heartsaver_fa_cpr_aed' }
};
const COURSE_ID_TO_OFFER = Object.fromEntries(Object.entries(COURSE_MAP).map(([offerKey, value]) => [value.courseId, { offerKey, ...value }]));

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

function authFailure(request, env) {
  const requireAuth = env.REQUIRE_MAXIM_PORTAL_AUTH === 'true' || Boolean(env.MAXIM_PORTAL_AUTH_TOKEN);
  if (!requireAuth) return null;
  if (!env.MAXIM_PORTAL_AUTH_TOKEN) return json({ error: 'MAXIM portal auth token is not configured.' }, 503);
  const authorization = request.headers.get('authorization') || '';
  const bearer = authorization.startsWith('Bearer ') ? authorization.slice(7) : '';
  const tokenHeader = request.headers.get('x-maxim-portal-token') || '';
  if (bearer === env.MAXIM_PORTAL_AUTH_TOKEN || tokenHeader === env.MAXIM_PORTAL_AUTH_TOKEN) return null;
  return json({ error: 'Unauthorized' }, 401);
}

function normalizePerson(data) {
  const firstName = String(data?.firstName || '').trim();
  const lastName = String(data?.lastName || '').trim();
  if (!firstName || !lastName) return null;
  return {
    personId: String(data.personId || `maxim_${firstName}_${lastName}`.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '')).slice(0, 80),
    firstName,
    lastName,
    email: String(data.email || '').trim() || null,
    phone: String(data.phone || '').trim() || null
  };
}

function rowMatchesAvailability(row, data, offer) {
  return String(row?.session_id) === String(data.classId)
    && String(row?.course_id) === String(offer.courseId)
    && String(row?.start_at || row?.start || row?.start_datetime) === String(data.startsAt)
    && String(row?.registration_status || 'open').toLowerCase() === 'open'
    && row?.public_direct_booking !== false
    && Boolean(row?.registration_url);
}

async function authoritativeAvailabilityRow(data, offer, env) {
  if (env.AVAILABILITY?.check) return env.AVAILABILITY.check(data, offer);
  if (env.SCHEDULE_FUTURE_JSON) {
    const payload = typeof env.SCHEDULE_FUTURE_JSON === 'string' ? JSON.parse(env.SCHEDULE_FUTURE_JSON) : env.SCHEDULE_FUTURE_JSON;
    return (payload.sessions || []).find((row) => rowMatchesAvailability(row, data, offer)) || null;
  }
  const origin = env.PUBLIC_ORIGIN || 'https://www.910cpr.com';
  const response = await fetch(`${origin}/data/schedule_future.json`, { cf: { cacheTtl: 0 } });
  if (!response.ok) return null;
  const payload = await response.json();
  return (payload.sessions || []).find((row) => rowMatchesAvailability(row, data, offer)) || null;
}

async function d1CreateRegistration(env, data, person, offer, availabilityRow) {
  const existing = await env.DB.prepare(`SELECT * FROM registrations WHERE person_id=? AND corporate_customer=? AND credential_key=? AND status='registered' AND superseded_by IS NULL ORDER BY created_at DESC LIMIT 1`)
    .bind(person.personId, data.corporateCustomer || 'MAXIM', offer.credentialKey).first();
  if (existing && !data.moveFromRegistrationId) return { error: 'duplicate_active_registration', existingRegistration: existing, status: 409 };
  if (data.moveFromRegistrationId && existing && existing.registration_id !== data.moveFromRegistrationId) return { error: 'duplicate_active_registration', existingRegistration: existing, status: 409 };

  const registrationId = id('reg');
  const sourceRenewalRef = data.renewalId || data.sourceRenewalId || null;
  const sourcePersonRef = data.sourcePersonReference || null;
  const renewal = sourceRenewalRef
    ? await env.DB.prepare(`SELECT renewal_id FROM renewal_cycles WHERE renewal_id=?`).bind(sourceRenewalRef).first()
    : null;
  const renewalId = renewal?.renewal_id || null;
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO people(person_id,first_name,last_name,email,phone) VALUES(?,?,?,?,?) ON CONFLICT(person_id) DO UPDATE SET first_name=excluded.first_name,last_name=excluded.last_name,email=excluded.email,phone=excluded.phone,updated_at=CURRENT_TIMESTAMP`)
      .bind(person.personId, person.firstName, person.lastName, person.email, person.phone),
    env.DB.prepare(`INSERT INTO corporate_profiles(person_id,corporate_customer,billing_account,active) VALUES(?,?,?,1) ON CONFLICT(person_id,corporate_customer) DO UPDATE SET billing_account=excluded.billing_account,active=1,updated_at=CURRENT_TIMESTAMP`)
      .bind(person.personId, data.corporateCustomer || 'MAXIM', data.billingAccount || null),
    data.moveFromRegistrationId ? env.DB.prepare(`UPDATE registrations SET status='superseded',superseded_by=?,updated_at=CURRENT_TIMESTAMP WHERE registration_id=? AND person_id=? AND status='registered'`).bind(registrationId, data.moveFromRegistrationId, person.personId) : env.DB.prepare(`SELECT 1`),
    env.DB.prepare(`INSERT INTO registrations(registration_id,person_id,renewal_id,source_renewal_ref,source_person_ref,corporate_customer,billing_account,course_id,credential_key,class_id,registration_url,starts_at,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?, 'registered')`)
      .bind(registrationId, person.personId, renewalId, sourceRenewalRef, sourcePersonRef, data.corporateCustomer || 'MAXIM', data.billingAccount || null, offer.courseId, offer.credentialKey, data.classId, availabilityRow.registration_url, data.startsAt),
    renewalId ? env.DB.prepare(`UPDATE renewal_cycles SET status='registered',updated_at=CURRENT_TIMESTAMP WHERE renewal_id=?`).bind(renewalId) : env.DB.prepare(`SELECT 1`),
    renewalId ? env.DB.prepare(`UPDATE go_tokens SET state='consumed',consumed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE renewal_id=? AND state='active'`).bind(renewalId) : env.DB.prepare(`SELECT 1`),
    env.DB.prepare(`INSERT INTO portal_events(event_id,person_id,renewal_id,registration_id,event_type,actor_type,payload_json) VALUES(?,?,?,?,?,?,?)`)
      .bind(id('evt'), person.personId, renewalId, registrationId, data.moveFromRegistrationId ? 'registration_moved' : 'registration_created', data.actorType || 'corporate_user', JSON.stringify({ offerKey: data.offerKey, courseId: offer.courseId, startsAt: data.startsAt, classId: data.classId, moveFromRegistrationId: data.moveFromRegistrationId || null }))
  ]);
  return { ok: true, registrationId, personId: person.personId };
}

async function createRegistrationRecord(env, data) {
  const offer = COURSE_MAP[data?.offerKey] || COURSE_ID_TO_OFFER[String(data?.courseId || '')];
  const person = normalizePerson(data?.person || data);
  if (!person || !offer || !data?.startsAt || !data?.classId) return { error: 'person, offer/course, startsAt and classId are required', status: 400 };
  const availabilityRow = await authoritativeAvailabilityRow(data, offer, env);
  if (!availabilityRow) return { error: 'stale_slot_rejected', status: 409 };
  if (env.STORE?.createRegistration) return env.STORE.createRegistration(data, person, offer, availabilityRow);
  return d1CreateRegistration(env, data, person, offer, availabilityRow);
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

async function listRegistrations(env) {
  if (env.STORE?.listRegistrations) return json({ registrations: await env.STORE.listRegistrations() });
  const registrations = await env.DB.prepare(`SELECT r.*, p.first_name, p.last_name, p.email, p.phone FROM registrations r JOIN people p ON p.person_id=r.person_id WHERE r.status='registered' AND r.superseded_by IS NULL ORDER BY r.starts_at ASC`).all();
  return json({ registrations: registrations.results });
}

async function createRegistration(request, env) {
  const data = await body(request);
  const result = await createRegistrationRecord(env, data);
  if (!result.ok) return json({ error: result.error, existingRegistration: result.existingRegistration }, result.status || 500);
  return json(result);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: { 'access-control-allow-origin': env.PUBLIC_ORIGIN, 'access-control-allow-methods': 'GET,POST,OPTIONS', 'access-control-allow-headers': 'content-type,authorization,x-maxim-portal-token' } });
    let response;
    const corporateApi = url.pathname.startsWith('/api/corp/maxim/');
    const authError = corporateApi ? authFailure(request, env) : null;
    if (authError) response = authError;
    else if (request.method === 'POST' && url.pathname === '/api/corp/maxim/go-links') response = await createGoToken(request, env);
    else if (request.method === 'GET' && url.pathname.startsWith('/api/go/')) response = await resolveGoToken(url.pathname.split('/').pop(), env);
    else if (request.method === 'POST' && /^\/api\/corp\/maxim\/renewals\/[^/]+\/skip$/.test(url.pathname)) response = await skipRenewal(request, env, url.pathname.split('/')[5]);
    else if (request.method === 'GET' && /^\/api\/corp\/maxim\/people\/[^/]+\/history$/.test(url.pathname)) response = await history(env, url.pathname.split('/')[5]);
    else if (request.method === 'GET' && url.pathname === '/api/corp/maxim/registrations') response = await listRegistrations(env);
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

export { createRegistrationRecord };
