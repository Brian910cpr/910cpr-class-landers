import { ownerAuthorization } from "./owner-session-auth.js";
import { handleFinanceApi } from "./finance-api.js";

const ALLOWED_ORIGINS = new Set(["https://www.910cpr.com", "https://910cpr.com"]);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";
    if (!url.pathname.startsWith("/admin/finance/")) return json({ error: "Not found.", code: "not_found" }, 404, origin);
    if (origin && !ALLOWED_ORIGINS.has(origin)) return json({ error: "Origin is not allowed.", code: "origin_rejected" }, 403, origin);
    if (request.method === "OPTIONS") return corsPreflight(origin);
    const authStatus = await ownerAuthorization(request, env);
    if (authStatus === 503) return json({ error: "Admin service is temporarily unavailable.", code: "service_unavailable" }, 503, origin);
    if (authStatus !== 200) return json({ error: "Authentication failed.", code: "authentication_failed" }, 401, origin);

    const response = await handleFinanceApi(request, env, url, origin, {
      json, safeError, requestJson, cleanText, actor, ValidationError,
    });
    return response || json({ error: "Financial endpoint not found.", code: "not_found" }, 404, origin);
  },
};

async function requestJson(request) {
  if (!(request.headers.get("Content-Type") || "").toLowerCase().startsWith("application/json")) throw new ValidationError("Content-Type must be application/json.");
  try { return await request.json(); } catch (_) { throw new ValidationError("Request body is not valid JSON."); }
}

function cleanText(value, maxLength, required = false) {
  const text = String(value ?? "").replace(/[\u0000-\u001f\u007f]/g, " ").trim();
  if (required && !text) throw new ValidationError("A required field is missing.");
  if (text.length > maxLength) throw new ValidationError(`A field exceeds ${maxLength} characters.`);
  return text;
}

function actor(env) { return cleanText(env.HOT_SYNC_ADMIN_ACTOR || "dashboard_admin", 120); }
function corsPreflight(origin) { return !origin || !ALLOWED_ORIGINS.has(origin) ? json({ error: "Origin is not allowed.", code: "origin_rejected" }, 403, origin) : new Response(null, { status: 204, headers: corsHeaders(origin) }); }
function corsHeaders(origin, additional = {}) { const headers = { "Access-Control-Allow-Methods": "GET,POST,OPTIONS", "Access-Control-Allow-Headers": "Content-Type,X-Hot-Sync-Admin-Key,X-LanderWare-Owner-Session", "Access-Control-Max-Age": "600", "Vary": "Origin", ...additional }; if (ALLOWED_ORIGINS.has(origin)) headers["Access-Control-Allow-Origin"] = origin; return headers; }
function json(payload, status, origin) { return new Response(JSON.stringify(payload), { status, headers: corsHeaders(origin, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "private, no-store" }) }); }
function safeError(error, origin) { if (error instanceof ValidationError) return json({ error: error.message, code: "validation_error" }, 400, origin); console.error(JSON.stringify({ event: "finance_api_error", message: String(error?.message || "unknown") })); return json({ error: "The financial operation failed safely.", code: "operation_failed" }, 500, origin); }
class ValidationError extends Error {}
