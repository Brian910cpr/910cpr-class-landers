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
function safeName(name) {
  return String(name || 'document').replace(/[^a-zA-Z0-9._-]+/g, '_').slice(0, 180);
}
async function sha256Hex(file) {
  const hash = await crypto.subtle.digest('SHA-256', await file.arrayBuffer());
  return [...new Uint8Array(hash)].map(b => b.toString(16).padStart(2, '0')).join('');
}
async function secureEqual(a, b) {
  const enc = new TextEncoder();
  const [ha, hb] = await Promise.all([
    crypto.subtle.digest('SHA-256', enc.encode(a || '')),
    crypto.subtle.digest('SHA-256', enc.encode(b || ''))
  ]);
  const aa = new Uint8Array(ha), bb = new Uint8Array(hb);
  let diff = aa.length ^ bb.length;
  for (let i = 0; i < aa.length; i++) diff |= aa[i] ^ bb[i];
  return diff === 0;
}
async function requireAdmin(request, env) {
  if (!env.ADMIN_TOKEN) return json({ error: 'ADMIN_TOKEN secret is not configured' }, 503);
  const auth = request.headers.get('authorization') || '';
  const supplied = auth.startsWith('Bearer ') ? auth.slice(7) : '';
  return (await secureEqual(supplied, env.ADMIN_TOKEN)) ? null : json({ error: 'Unauthorized' }, 401);
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
  return json({ token: code, intentType: row.intent_type, person: { firstName: row.first_name, lastName: row.last_name, email: row.email, phone: row.phone }, corporateCustomer: row.corporate_customer, billingAccount: row.billing_account, credentialKey: row.credential_key, renewalId: row.renewal_id });
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
  if (!data.availabilityProof) return json({ error: 'Authoritative availability proof required; booking not written.' }, 409);
  const registrationId = id('reg');
  await env.DB.batch([
    env.DB.prepare(`INSERT INTO registrations(registration_id,person_id,renewal_id,corporate_customer,billing_account,course_id,credential_key,class_id,starts_at,status) VALUES(?,?,?,?,?,?,?,?,?,'registered')`).bind(registrationId,data.personId,data.renewalId||null,data.corporateCustomer||'MAXIM',data.billingAccount||null,offer.courseId,offer.credentialKey,data.classId||null,data.startsAt),
    data.renewalId ? env.DB.prepare(`UPDATE renewal_cycles SET status='registered',updated_at=CURRENT_TIMESTAMP WHERE renewal_id=?`).bind(data.renewalId) : env.DB.prepare(`SELECT 1`),
    data.renewalId ? env.DB.prepare(`UPDATE go_tokens SET state='consumed',consumed_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE renewal_id=? AND state='active'`).bind(data.renewalId) : env.DB.prepare(`SELECT 1`),
    env.DB.prepare(`INSERT INTO portal_events(event_id,person_id,renewal_id,registration_id,event_type,actor_type,payload_json) VALUES(?,?,?,?,?,?,?)`).bind(id('evt'),data.personId,data.renewalId||null,registrationId,'registration_created',data.actorType||'corporate_user',JSON.stringify({ offerKey:data.offerKey, startsAt:data.startsAt }))
  ]);
  return json({ ok: true, registrationId });
}

async function uploadDocument(request, env) {
  const denied = await requireAdmin(request, env); if (denied) return denied;
  if (!env.DOCUMENTS) return json({ error: 'DOCUMENTS R2 binding is not configured' }, 503);
  const form = await request.formData();
  const file = form.get('file');
  if (!(file instanceof File)) return json({ error: 'file is required' }, 400);
  const max = Number(env.MAX_FILE_BYTES || 26214400);
  if (file.size < 1 || file.size > max) return json({ error: `File must be between 1 byte and ${max} bytes` }, 413);
  const documentId = id('doc');
  const digest = await sha256Hex(file);
  const storageKey = `maxim/${new Date().toISOString().slice(0,10)}/${documentId}-${safeName(file.name)}`;
  await env.DOCUMENTS.put(storageKey, file.stream(), { httpMetadata: { contentType: file.type || 'application/octet-stream' }, customMetadata: { documentId, originalName: file.name, sha256: digest } });
  try {
    await env.DB.prepare(`INSERT INTO documents(document_id,storage_key,original_name,content_type,size_bytes,sha256,document_type,state,corporate_customer,person_id,registration_id,class_id,notes,uploaded_by) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)`)
      .bind(documentId,storageKey,file.name,file.type||null,file.size,digest,String(form.get('documentType')||'unknown'),'unfiled',String(form.get('corporateCustomer')||'MAXIM'),form.get('personId')||null,form.get('registrationId')||null,form.get('classId')||null,form.get('notes')||null,'admin_portal').run();
  } catch (error) {
    await env.DOCUMENTS.delete(storageKey);
    throw error;
  }
  await env.DB.prepare(`INSERT INTO portal_events(event_id,person_id,registration_id,event_type,actor_type,payload_json) VALUES(?,?,?,?,?,?)`).bind(id('evt'),form.get('personId')||null,form.get('registrationId')||null,'document_uploaded','admin_user',JSON.stringify({ documentId, originalName:file.name, storageKey, sha256:digest })).run();
  return json({ ok:true, documentId, state:'unfiled', originalName:file.name }, 201);
}

async function listDocuments(request, env) {
  const denied = await requireAdmin(request, env); if (denied) return denied;
  const url = new URL(request.url);
  const state = url.searchParams.get('state') || 'unfiled';
  const rows = await env.DB.prepare(`SELECT d.*,p.first_name,p.last_name,r.starts_at,r.credential_key FROM documents d LEFT JOIN people p ON p.person_id=d.person_id LEFT JOIN registrations r ON r.registration_id=d.registration_id WHERE d.state=? ORDER BY d.uploaded_at DESC LIMIT 250`).bind(state).all();
  return json({ documents: rows.results });
}

async function recentRegistrations(request, env) {
  const denied = await requireAdmin(request, env); if (denied) return denied;
  const url = new URL(request.url);
  const days = Math.min(365, Math.max(1, Number(url.searchParams.get('days') || 120)));
  const rows = await env.DB.prepare(`SELECT r.registration_id,r.person_id,r.class_id,r.starts_at,r.credential_key,r.status,r.corporate_customer,p.first_name,p.last_name,p.email FROM registrations r JOIN people p ON p.person_id=r.person_id WHERE r.starts_at >= datetime('now', ?) ORDER BY r.starts_at DESC LIMIT 500`).bind(`-${days} days`).all();
  return json({ registrations: rows.results });
}

async function assignDocument(request, env, documentId) {
  const denied = await requireAdmin(request, env); if (denied) return denied;
  const data = await body(request);
  if (!data?.registrationId) return json({ error:'registrationId is required' }, 400);
  const reg = await env.DB.prepare(`SELECT registration_id,person_id,class_id FROM registrations WHERE registration_id=?`).bind(data.registrationId).first();
  if (!reg) return json({ error:'Registration not found' }, 404);
  const doc = await env.DB.prepare(`SELECT document_id,state FROM documents WHERE document_id=?`).bind(documentId).first();
  if (!doc) return json({ error:'Document not found' }, 404);
  await env.DB.batch([
    env.DB.prepare(`UPDATE documents SET registration_id=?,person_id=?,class_id=COALESCE(?,class_id),state='assigned',assigned_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP WHERE document_id=?`).bind(reg.registration_id,reg.person_id,reg.class_id,documentId),
    env.DB.prepare(`INSERT INTO portal_events(event_id,person_id,registration_id,event_type,actor_type,payload_json) VALUES(?,?,?,?,?,?)`).bind(id('evt'),reg.person_id,reg.registration_id,'document_assigned','admin_user',JSON.stringify({ documentId }))
  ]);
  return json({ ok:true, documentId, registrationId:reg.registration_id, personId:reg.person_id, state:'assigned' });
}

export default {
  async fetch(request, env) {
    try {
      const url = new URL(request.url);
      if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: { 'access-control-allow-origin': env.PUBLIC_ORIGIN, 'access-control-allow-methods': 'GET,POST,OPTIONS', 'access-control-allow-headers': 'content-type,authorization' } });
      let response;
      if (request.method === 'POST' && url.pathname === '/api/corp/maxim/go-links') response = await createGoToken(request, env);
      else if (request.method === 'GET' && url.pathname.startsWith('/api/go/')) response = await resolveGoToken(url.pathname.split('/').pop(), env);
      else if (request.method === 'POST' && /^\/api\/corp\/maxim\/renewals\/[^/]+\/skip$/.test(url.pathname)) response = await skipRenewal(request, env, url.pathname.split('/')[5]);
      else if (request.method === 'GET' && /^\/api\/corp\/maxim\/people\/[^/]+\/history$/.test(url.pathname)) response = await history(env, url.pathname.split('/')[5]);
      else if (request.method === 'POST' && url.pathname === '/api/corp/maxim/registrations') response = await createRegistration(request, env);
      else if (request.method === 'POST' && url.pathname === '/api/admin/documents') response = await uploadDocument(request, env);
      else if (request.method === 'GET' && url.pathname === '/api/admin/documents') response = await listDocuments(request, env);
      else if (request.method === 'GET' && url.pathname === '/api/admin/registrations/recent') response = await recentRegistrations(request, env);
      else if (request.method === 'POST' && /^\/api\/admin\/documents\/[^/]+\/assign$/.test(url.pathname)) response = await assignDocument(request, env, url.pathname.split('/')[4]);
      else if (request.method === 'GET' && url.pathname.startsWith('/go/')) return Response.redirect(`${env.PUBLIC_ORIGIN}${env.PORTAL_PATH}?go=${encodeURIComponent(url.pathname.split('/').pop())}`, 302);
      else response = json({ error: 'Not found' }, 404);
      const headers = new Headers(response.headers);
      headers.set('access-control-allow-origin', env.PUBLIC_ORIGIN);
      headers.set('cache-control', 'no-store');
      return new Response(response.body, { status: response.status, headers });
    } catch (error) {
      console.error(JSON.stringify({ event:'worker_error', message:error?.message, stack:error?.stack }));
      return json({ error:'Internal server error' }, 500);
    }
  }
};
