import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { MAX_BODY_BYTES, normalizePayload, sha256, verifyRequest } from "../_shared/rachel-phone-intake-core.mjs";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });
}

function config() {
  const url = Deno.env.get("SUPABASE_URL") || "";
  const raw = Deno.env.get("SUPABASE_SECRET_KEYS");
  const serviceKey = raw ? JSON.parse(raw).default : Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const intakeKeys = JSON.parse(Deno.env.get("RACHEL_INTAKE_KEYS") || "{}");
  if (!url || !serviceKey) throw new Error("server_configuration");
  return { url, serviceKey, intakeKeys };
}

async function ingest(url: string, serviceKey: string, payload: unknown, requestHash: string, keyId: string, nonce: string) {
  const response = await fetch(`${url}/rest/v1/rpc/landerware_ingest_phone_intake`, {
    method: "POST",
    headers: { apikey: serviceKey, authorization: `Bearer ${serviceKey}`, "content-type": "application/json" },
    body: JSON.stringify({ p_payload: payload, p_request_hash: requestHash, p_key_id: keyId, p_nonce: nonce }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body?.message || `database_${response.status}`);
  return Array.isArray(body) ? body[0] : body;
}

Deno.serve(async request => {
  if (request.method !== "POST") return json({ error: "method_not_allowed" }, 405);
  if (!(request.headers.get("content-type") || "").toLowerCase().startsWith("application/json")) return json({ error: "content_type_required" }, 415);
  const length = Number(request.headers.get("content-length") || "0");
  if (length > MAX_BODY_BYTES) return json({ error: "payload_too_large" }, 413);
  try {
    const rawBody = await request.text();
    if (new TextEncoder().encode(rawBody).byteLength > MAX_BODY_BYTES) return json({ error: "payload_too_large" }, 413);
    const { url, serviceKey, intakeKeys } = config();
    const keyId = request.headers.get("x-landerware-key-id") || "";
    const secret = typeof intakeKeys[keyId] === "string" ? intakeKeys[keyId] : "";
    const timestamp = request.headers.get("x-landerware-timestamp") || "";
    const nonce = request.headers.get("x-landerware-nonce") || "";
    const signature = request.headers.get("x-landerware-signature") || "";
    if (!await verifyRequest({ rawBody, timestamp, nonce, signature, secret })) return json({ error: "unauthorized" }, 401);
    const payload = normalizePayload(JSON.parse(rawBody));
    const result = await ingest(url, serviceKey, payload, await sha256(rawBody), keyId, nonce);
    return json({ ok: true, ...result }, result?.idempotentReplay ? 200 : 201);
  } catch (error) {
    const message = error instanceof Error ? error.message : "unexpected_error";
    const bad = ["invalid_json_object", "invalid_source", "external_call_id_required", "caller_phone_required", "received_at_invalid", "started_at_invalid", "ended_at_invalid", "recording_url_invalid"].includes(message) || message.startsWith("Unexpected token");
    const conflict = message.includes("intake_nonce_replay");
    return json({ error: bad ? "invalid_payload" : conflict ? "replay_rejected" : "intake_unavailable" }, bad ? 400 : conflict ? 409 : 500);
  }
});
