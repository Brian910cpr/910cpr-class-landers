import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const ALLOWED_ORIGINS = new Set(["https://www.910cpr.com", "https://910cpr.com"]);
const ACTIVE_REGISTRATION_STATUSES = new Set(["registered", "confirmed", "completed"]);
const OPERATIONAL_SESSION_STATUSES = "(scheduled,active,completed)";

function headers(origin: string) {
  const value: Record<string, string> = {
    "access-control-allow-headers": "content-type,x-hot-sync-admin-key",
    "access-control-allow-methods": "GET,OPTIONS",
    "cache-control": "private, no-store",
    "content-type": "application/json; charset=utf-8",
    vary: "Origin",
  };
  if (ALLOWED_ORIGINS.has(origin)) value["access-control-allow-origin"] = origin;
  return value;
}

function reply(origin: string, body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: headers(origin) });
}

function config() {
  const url = Deno.env.get("SUPABASE_URL");
  const keys = Deno.env.get("SUPABASE_SECRET_KEYS");
  const key = keys ? JSON.parse(keys).default : Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) throw new Error("Supabase service configuration is unavailable");
  return { url, key };
}

async function authorized(req: Request) {
  const key = req.headers.get("x-hot-sync-admin-key") || "";
  if (!key) return false;
  const response = await fetch("https://schedule.910cpr.com/admin/hot-sync", {
    headers: { "x-hot-sync-admin-key": key },
  });
  return response.ok;
}

function dateParam(value: string | null, fallback: string) {
  const date = value || fallback;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || Number.isNaN(Date.parse(`${date}T00:00:00Z`))) {
    throw new Error("Dates must use YYYY-MM-DD");
  }
  return date;
}

function displayName(customer: Record<string, unknown>) {
  return [customer.first_name, customer.last_name].filter(Boolean).join(" ").trim();
}

export function summarizeSession(row: any) {
  const registrations = Array.isArray(row.registrations) ? row.registrations : [];
  const active = registrations.filter((registration: any) => ACTIVE_REGISTRATION_STATUSES.has(registration.status));
  const participants = active.map((registration: any) => {
    const customer = registration.customers || {};
    return {
      registration_id: registration.id,
      registration_status: registration.status,
      customer_id: customer.id || registration.customer_id,
      display_name: displayName(customer),
      first_name: customer.first_name || "",
      last_name: customer.last_name || "",
      email: customer.email || null,
    };
  }).sort((a: any, b: any) => a.display_name.localeCompare(b.display_name));
  return {
    session_id: row.id,
    external_class_id: row.external_class_id,
    source: row.source,
    status: row.status,
    start_at: row.start_at,
    end_at: row.end_at,
    course_name: row.courses?.name || "Course unknown",
    course_key: row.courses?.course_key || null,
    location_name: row.locations?.name || "Location unknown",
    organization_name: row.organizations?.name || null,
    participant_count: participants.length,
    registered_count: participants.length,
    count_available: true,
    roster_available: true,
    count_source: "canonical_active_registrations",
    active_registration_statuses: [...ACTIVE_REGISTRATION_STATUSES],
    registration_ids: participants.map((participant: any) => participant.registration_id),
    participants,
  };
}

async function canonicalSessions(from: string, to: string) {
  const { url, key } = config();
  const select = [
    "id", "external_class_id", "source", "status", "start_at", "end_at",
    "courses!class_sessions_course_id_fkey(name,course_key)",
    "locations!class_sessions_location_id_fkey(name)",
    "organizations!class_sessions_organization_id_fkey(name)",
    "registrations!registrations_class_session_id_fkey(id,customer_id,status,customers!registrations_customer_id_fkey(id,first_name,last_name,email))",
  ].join(",");
  const params = new URLSearchParams({ select, record_scope: "eq.operational", status: `in.${OPERATIONAL_SESSION_STATUSES}`, order: "start_at.asc" });
  params.append("start_at", `gte.${from}T00:00:00-04:00`);
  params.append("start_at", `lt.${to}T00:00:00-04:00`);
  const response = await fetch(`${url}/rest/v1/class_sessions?${params}`, {
    headers: { apikey: key, authorization: `Bearer ${key}` },
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body?.message || `Database request failed (${response.status})`);
  return body.map(summarizeSession);
}

Deno.serve(async (req) => {
  const origin = req.headers.get("origin") || "";
  if (origin && !ALLOWED_ORIGINS.has(origin)) return reply(origin, { error: "Origin is not allowed" }, 403);
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: headers(origin) });
  if (req.method !== "GET") return reply(origin, { error: "Method not allowed" }, 405);
  try {
    if (!(await authorized(req))) return reply(origin, { error: "Unauthorized" }, 401);
    const requestUrl = new URL(req.url);
    const today = new Date().toISOString().slice(0, 10);
    const from = dateParam(requestUrl.searchParams.get("from"), today);
    const defaultTo = new Date(`${from}T00:00:00Z`);
    defaultTo.setUTCDate(defaultTo.getUTCDate() + 366);
    const to = dateParam(requestUrl.searchParams.get("to"), defaultTo.toISOString().slice(0, 10));
    const span = (Date.parse(`${to}T00:00:00Z`) - Date.parse(`${from}T00:00:00Z`)) / 86400000;
    if (span <= 0 || span > 366) return reply(origin, { error: "Date range must be 1 through 366 days" }, 400);
    const sessions = await canonicalSessions(from, to);
    return reply(origin, {
      schema_version: "2.0.0",
      generated_at: new Date().toISOString(),
      scope: { from, to, statuses: ["scheduled", "active", "completed"], record_scope: "operational" },
      summary: {
        sessions: sessions.length,
        sessions_with_participants: sessions.filter((row: any) => row.participant_count > 0).length,
        participants: sessions.reduce((sum: number, row: any) => sum + row.participant_count, 0),
        unknown_counts: 0,
      },
      sessions,
    });
  } catch (error) {
    console.error(JSON.stringify({ event: "canonical_session_workspace_error", message: String(error) }));
    return reply(origin, { error: "Canonical Session Workspace is temporarily unavailable" }, 500);
  }
});
