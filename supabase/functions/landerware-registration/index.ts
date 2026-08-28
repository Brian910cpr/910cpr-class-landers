import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const COURSE_ID = "aha-heartsaver-skills-session";
const COURSE_NAME = "AHA Heartsaver Skills Session";
const REQUIREMENT_TYPE = "AHA_ONLINE_COMPLETION_CERTIFICATE";
const BUCKET = "landerware-requirement-documents";
const MAX_BYTES = 10 * 1024 * 1024;
const ALLOWED = new Map([
  ["application/pdf", "pdf"], ["image/jpeg", "jpg"], ["image/png", "png"], ["image/webp", "webp"],
]);
const cors = {
  "access-control-allow-origin": "https://www.910cpr.com",
  "access-control-allow-headers": "content-type, idempotency-key",
  "access-control-allow-methods": "GET,POST,OPTIONS",
  "cache-control": "no-store",
};
const json = (data: unknown, status = 200) => new Response(JSON.stringify(data), {
  status, headers: { ...cors, "content-type": "application/json; charset=utf-8" },
});
const sha256 = async (value: string) => Array.from(new Uint8Array(await crypto.subtle.digest(
  "SHA-256", new TextEncoder().encode(value),
))).map((byte) => byte.toString(16).padStart(2, "0")).join("");
const randomToken = () => Array.from(crypto.getRandomValues(new Uint8Array(32)))
  .map((byte) => byte.toString(16).padStart(2, "0")).join("");

function config() {
  const url = Deno.env.get("SUPABASE_URL")!;
  const secretJson = Deno.env.get("SUPABASE_SECRET_KEYS");
  const secret = secretJson ? JSON.parse(secretJson).default : Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  return { url, headers: { apikey: secret, authorization: `Bearer ${secret}` } };
}
async function rest(path: string, init: RequestInit = {}) {
  const c = config();
  const res = await fetch(`${c.url}/rest/v1/${path}`, { ...init, headers: {
    ...c.headers, "content-type": "application/json", prefer: "return=representation", ...(init.headers || {}),
  } });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) throw new Error(data?.message || `Database request failed (${res.status})`);
  return data;
}
function route(req: Request) {
  const parts = new URL(req.url).pathname.split("/").filter(Boolean);
  return parts.slice(parts.indexOf("landerware-registration") + 1);
}
function clean(value: FormDataEntryValue | null, max = 320) {
  return String(value || "").trim().slice(0, max);
}
async function tokenRecord(raw: string) {
  if (!/^[a-f0-9]{64}$/.test(raw)) return null;
  const rows = await rest(`landerware_document_submission_tokens?token_sha256=eq.${await sha256(raw)}&revoked_at=is.null&select=id,person_id,registration_id,requirement_id,expires_at,submission_count&limit=1`);
  const row = rows[0];
  if (!row || new Date(row.expires_at).getTime() <= Date.now()) return null;
  return row;
}
async function attachDocument(file: File, token: any) {
  if (!file.name || file.size === 0) throw new Error("missing_file");
  if (file.size > MAX_BYTES) throw new Error("file_too_large");
  const extension = ALLOWED.get(file.type);
  if (!extension) throw new Error("unsupported_file_type");
  const bytes = new Uint8Array(await file.arrayBuffer());
  const checksum = await crypto.subtle.digest("SHA-256", bytes);
  const checksumHex = Array.from(new Uint8Array(checksum)).map((b) => b.toString(16).padStart(2, "0")).join("");
  const duplicate = await rest(`landerware_documents?checksum_sha256=eq.${checksumHex}&related_record_ids->>registrationId=eq.${token.registration_id}&select=id&limit=1`);
  if (duplicate.length) return { documentId: duplicate[0].id, duplicate: true };
  const storageKey = `${token.person_id}/${token.registration_id}/${crypto.randomUUID()}.${extension}`;
  const c = config();
  const upload = await fetch(`${c.url}/storage/v1/object/${BUCKET}/${storageKey}`, {
    method: "POST", headers: { ...c.headers, "content-type": file.type, "x-upsert": "false" }, body: bytes,
  });
  if (!upload.ok) throw new Error(`storage_upload_failed_${upload.status}`);
  const inserted = await rest("landerware_documents", { method: "POST", body: JSON.stringify({
    document_type: REQUIREMENT_TYPE, source: "customer_upload", received_at: new Date().toISOString(),
    related_record_ids: { personId: token.person_id, registrationId: token.registration_id, requirementId: token.requirement_id },
    original_filename: file.name.slice(0, 240), checksum_sha256: checksumHex,
    storage_provider: "supabase_storage", storage_reference: `${BUCKET}/${storageKey}`,
  }) });
  const documentId = inserted[0].id;
  const requirements = await rest(`landerware_certification_requirements?id=eq.${token.requirement_id}&select=document_ids`);
  await rest(`landerware_certification_requirements?id=eq.${token.requirement_id}`, { method: "PATCH", body: JSON.stringify({
    document_ids: [...new Set([...(requirements[0]?.document_ids || []), documentId])], satisfied_at: new Date().toISOString(), status: "satisfied", updated_at: new Date().toISOString(),
  }) });
  const registrations = await rest(`landerware_registrations?id=eq.${token.registration_id}&select=document_ids`);
  await rest(`landerware_registrations?id=eq.${token.registration_id}`, { method: "PATCH", body: JSON.stringify({
    document_ids: [...new Set([...(registrations[0]?.document_ids || []), documentId])], updated_at: new Date().toISOString(),
  }) });
  await rest(`landerware_document_submission_tokens?id=eq.${token.id}`, { method: "PATCH", body: JSON.stringify({ submission_count: token.submission_count + 1, last_opened_at: new Date().toISOString() }) });
  await rest("landerware_activity_events", { method: "POST", body: JSON.stringify({
    event_type: "requirement_document_received", actor_source: "system", person_id: token.person_id,
    registration_id: token.registration_id, requirement_id: token.requirement_id, details: { documentId, requirementType: REQUIREMENT_TYPE },
  }) });
  return { documentId, duplicate: false };
}
async function register(req: Request) {
  const form = await req.formData();
  const firstName = clean(form.get("firstName"), 100), lastName = clean(form.get("lastName"), 100);
  const email = clean(form.get("email")).toLowerCase(), phone = clean(form.get("phone"), 50);
  const completed = clean(form.get("onlineCompleted")) === "true";
  if (!firstName || !lastName || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || !completed) {
    return json({ error: "valid_name_email_and_online_completion_required" }, 400);
  }
  const idempotency = req.headers.get("idempotency-key") || clean(form.get("idempotencyKey"), 160);
  if (!idempotency) return json({ error: "idempotency_key_required" }, 400);
  const resultRows = await rest("rpc/landerware_register", { method: "POST", body: JSON.stringify({
    p_first_name: firstName, p_last_name: lastName, p_email: email, p_phone: phone || null,
    p_course_id: COURSE_ID, p_course_name: COURSE_NAME, p_source: "public_heartsaver_skills",
    p_idempotency_key: `heartsaver:${idempotency}`, p_requirement_type: REQUIREMENT_TYPE,
  }) });
  const result = Array.isArray(resultRows) ? resultRows[0] : resultRows;
  let tokenRows = await rest(`landerware_document_submission_tokens?registration_id=eq.${result.registrationId}&select=id&limit=1`);
  let rawToken = "";
  if (!tokenRows.length) {
    rawToken = randomToken();
    tokenRows = await rest("landerware_document_submission_tokens", { method: "POST", body: JSON.stringify({
      token_sha256: await sha256(rawToken), person_id: result.personId, registration_id: result.registrationId,
      requirement_id: result.requirementId, expires_at: new Date(Date.now() + 180 * 86400000).toISOString(),
    }) });
  }
  const file = form.get("certificate");
  let upload = null;
  if (file instanceof File && file.size) upload = await attachDocument(file, { ...tokenRows[0], person_id: result.personId, registration_id: result.registrationId, requirement_id: result.requirementId, submission_count: 0 });
  const submitUrl = rawToken ? `https://www.910cpr.com/certificate-submit/?token=${rawToken}` : null;
  const hasCertificate = Boolean(upload);
  const bodyText = hasCertificate
    ? `Hi ${firstName},\n\nYour Heartsaver Skills Session registration is confirmed. We received your AHA online-course completion certificate.\n\n910CPR\n910-395-5193`
    : `Hi ${firstName},\n\nYour Heartsaver Skills Session registration is confirmed.\n\nIf you have not already uploaded your AHA online-course completion certificate, please submit it before your skills session:\n\nSubmit Completion Certificate: ${submitUrl}\n\nYou may also bring the certificate with you to class.\n\n910CPR\n910-395-5193`;
  await rest("landerware_messages", { method: "POST", body: JSON.stringify({
    person_id: result.personId, registration_id: result.registrationId, template_key: "heartsaver_skills_confirmation_v1",
    recipient: email, subject: "Heartsaver Skills Session registration confirmed", body_text: bodyText,
    delivery_provider: "gmail", delivery_status: "pending", idempotency_key: `heartsaver-confirmation:${result.registrationId}`,
  }) });
  return json({ ok: true, personId: result.personId, registrationId: result.registrationId,
    requirementId: result.requirementId, certificateReceived: hasCertificate, certificateSubmitUrl: submitUrl,
    idempotentReplay: result.idempotentReplay });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const parts = route(req);
  try {
    if (req.method === "POST" && parts[0] === "register") return await register(req);
    if (parts[0] === "certificate" && parts[1]) {
      const record = await tokenRecord(parts[1]);
      if (!record) return json({ error: "invalid_or_expired_token" }, 410);
      if (req.method === "GET") {
        await rest(`landerware_document_submission_tokens?id=eq.${record.id}`, { method: "PATCH", body: JSON.stringify({ last_opened_at: new Date().toISOString() }) });
        return json({ ok: true, registrationId: record.registration_id, requirementType: REQUIREMENT_TYPE, submissionCount: record.submission_count });
      }
      if (req.method === "POST") {
        const form = await req.formData();
        const file = form.get("certificate");
        if (!(file instanceof File)) return json({ error: "missing_file" }, 400);
        return json({ ok: true, ...(await attachDocument(file, record)) });
      }
    }
    return json({ error: "not_found" }, 404);
  } catch (error) {
    const message = error instanceof Error ? error.message : "unexpected_error";
    const status = message === "missing_file" || message === "unsupported_file_type" || message === "file_too_large" ? 400 : 500;
    return json({ error: message }, status);
  }
});
