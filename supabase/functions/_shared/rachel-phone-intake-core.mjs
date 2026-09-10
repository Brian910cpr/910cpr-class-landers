const encoder = new TextEncoder();

export const MAX_BODY_BYTES = 1024 * 1024;
export const MAX_CLOCK_SKEW_SECONDS = 300;

export function clean(value, max = 500) {
  return String(value ?? "").trim().slice(0, max);
}

export function normalizePhone(value) {
  const digits = clean(value, 50).replace(/\D/g, "");
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length >= 11 && digits.length <= 15) return `+${digits}`;
  return "";
}

export function normalizePayload(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) throw new Error("invalid_json_object");
  const caller = input.caller && typeof input.caller === "object" ? input.caller : {};
  const request = input.request && typeof input.request === "object" ? input.request : {};
  const call = input.call && typeof input.call === "object" ? input.call : {};
  const flags = input.flags && typeof input.flags === "object" ? input.flags : {};
  const windows = value => Array.isArray(value) ? value.map(item => clean(item, 160)).filter(Boolean).slice(0, 20) : [];
  const initialOrRenewal = clean(request.initial_or_renewal, 20).toLowerCase();
  const serviceType = clean(request.service_type, 40).toLowerCase();
  const payload = {
    schema_version: clean(input.schema_version || "1.0", 20),
    source: clean(input.source, 80),
    external_call_id: clean(input.external_call_id, 200),
    external_call_id_kind: clean(input.external_call_id_kind || "provider", 60),
    test_call: input.test_call === true,
    received_at: clean(input.received_at, 40),
    caller: {
      name: clean(caller.name, 200), phone: normalizePhone(caller.phone),
      email: clean(caller.email, 320).toLowerCase(), organization: clean(caller.organization, 200),
    },
    request: {
      credential_text: clean(request.credential_text, 500), course: clean(request.course, 200),
      certifying_body: clean(request.certifying_body, 120),
      initial_or_renewal: ["initial", "renewal", "unknown"].includes(initialOrRenewal) ? initialOrRenewal : "unknown",
      required_by: clean(request.required_by, 160),
      service_type: ["public_class", "skills_session", "private_group", "onsite_group", "unknown"].includes(serviceType) ? serviceType : "unknown",
      group_size: Number.isInteger(request.group_size) && request.group_size > 0 ? request.group_size : null,
      preferred_location: clean(request.preferred_location, 300),
      preferred_windows: windows(request.preferred_windows), alternate_windows: windows(request.alternate_windows),
      flexibility: clean(request.flexibility, 500), unresolved_questions: windows(request.unresolved_questions),
    },
    call: {
      started_at: clean(call.started_at, 40), ended_at: clean(call.ended_at, 40),
      duration_seconds: Number.isInteger(call.duration_seconds) && call.duration_seconds >= 0 ? call.duration_seconds : null,
      summary: clean(call.summary, 10000), transcript: clean(call.transcript, 200000),
      recording_url: clean(call.recording_url, 2000), outcome: clean(call.outcome || "unknown", 80),
      transfer_status: clean(call.transfer_status || "unknown", 80),
      booking_status: clean(call.booking_status || "unknown", 80),
    },
    flags: {
      urgent: flags.urgent === true, same_day_problem: flags.same_day_problem === true,
      contradiction_detected: flags.contradiction_detected === true, human_review_required: true,
    },
  };
  if (payload.source !== "marblism_rachel") throw new Error("invalid_source");
  if (!payload.external_call_id) throw new Error("external_call_id_required");
  if (!payload.caller.phone) throw new Error("caller_phone_required");
  if (!payload.received_at || Number.isNaN(Date.parse(payload.received_at))) throw new Error("received_at_invalid");
  for (const key of ["started_at", "ended_at"]) {
    if (payload.call[key] && Number.isNaN(Date.parse(payload.call[key]))) throw new Error(`${key}_invalid`);
  }
  if (payload.call.recording_url) {
    let url;
    try { url = new URL(payload.call.recording_url); } catch { throw new Error("recording_url_invalid"); }
    if (url.protocol !== "https:") throw new Error("recording_url_invalid");
  }
  return payload;
}

function hex(bytes) {
  return [...new Uint8Array(bytes)].map(value => value.toString(16).padStart(2, "0")).join("");
}

export async function sha256(value) {
  return hex(await crypto.subtle.digest("SHA-256", encoder.encode(value)));
}

export async function hmacSha256(secret, value) {
  const key = await crypto.subtle.importKey("raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", key, encoder.encode(value)));
}

export function signatureBase(timestamp, nonce, rawBody) {
  return `${timestamp}.${nonce}.${rawBody}`;
}

export function timingSafeHexEqual(left, right) {
  if (!/^[0-9a-f]+$/i.test(left) || !/^[0-9a-f]+$/i.test(right) || left.length !== right.length) return false;
  let mismatch = 0;
  for (let i = 0; i < left.length; i += 1) mismatch |= left.charCodeAt(i) ^ right.charCodeAt(i);
  return mismatch === 0;
}

export async function verifyRequest({ rawBody, timestamp, nonce, signature, secret, nowMs = Date.now() }) {
  if (!timestamp || !nonce || !signature || !secret) return false;
  if (!/^[A-Za-z0-9._:-]{16,160}$/.test(nonce)) return false;
  const seconds = Number(timestamp);
  if (!Number.isInteger(seconds) || Math.abs(Math.floor(nowMs / 1000) - seconds) > MAX_CLOCK_SKEW_SECONDS) return false;
  const expected = await hmacSha256(secret, signatureBase(timestamp, nonce, rawBody));
  return timingSafeHexEqual(expected, signature.toLowerCase());
}
