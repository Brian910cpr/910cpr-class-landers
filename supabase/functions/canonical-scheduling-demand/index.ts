import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const ACTIVE = new Set(["registered", "confirmed", "completed"]);
const ALLOWED_ORIGINS = new Set(["https://www.910cpr.com", "https://910cpr.com"]);

function response(origin: string, body: unknown, status = 200) {
  const headers: Record<string, string> = {
    "access-control-allow-headers": "content-type,x-hot-sync-admin-key",
    "access-control-allow-methods": "GET,OPTIONS",
    "cache-control": "private, no-store",
    "content-type": "application/json; charset=utf-8",
    vary: "Origin",
  };
  if (ALLOWED_ORIGINS.has(origin)) headers["access-control-allow-origin"] = origin;
  return new Response(JSON.stringify(body), { status, headers });
}

function serviceConfig() {
  const url = Deno.env.get("SUPABASE_URL");
  const keys = Deno.env.get("SUPABASE_SECRET_KEYS");
  const key = keys ? JSON.parse(keys).default : Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) throw new Error("Supabase service configuration is unavailable");
  return { url, key };
}

async function authorized(req: Request) {
  const key = req.headers.get("x-hot-sync-admin-key") || "";
  if (!key) return false;
  const result = await fetch("https://schedule.910cpr.com/admin/hot-sync", {
    headers: { "x-hot-sync-admin-key": key },
  });
  return result.ok;
}

export function projectDemand(row: any) {
  const registrations = Array.isArray(row.registrations) ? row.registrations : [];
  return {
    canonical_session_id: row.id,
    external_class_id: row.external_class_id || null,
    external_course_id: null,
    course_key: row.courses?.course_key || null,
    start_at: row.start_at,
    end_at: row.end_at,
    location_id: row.location_id,
    location_name: row.locations?.name || null,
    lead_instructor_id: row.lead_instructor_id,
    lead_instructor_name: null,
    source: row.source,
    session_status: row.status,
    active_registration_count: registrations.filter((item: any) => ACTIVE.has(item.status)).length,
    demand_basis: "canonical_active_registrations",
  };
}

async function loadDemand(from: string, to: string) {
  const { url, key } = serviceConfig();
  const select = [
    "id", "external_class_id", "source", "status", "start_at", "end_at", "location_id", "lead_instructor_id",
    "courses!class_sessions_course_id_fkey(course_key)",
    "locations!class_sessions_location_id_fkey(name)",
    "registrations!registrations_class_session_id_fkey(status)",
  ].join(",");
  const params = new URLSearchParams({
    select, record_scope: "eq.operational", status: "in.(scheduled,active,completed)", order: "start_at.asc",
  });
  params.append("start_at", `gte.${from}T00:00:00-04:00`);
  params.append("start_at", `lt.${to}T00:00:00-04:00`);
  const result = await fetch(`${url}/rest/v1/class_sessions?${params}`, {
    headers: { apikey: key, authorization: `Bearer ${key}` },
  });
  const body = await result.json();
  if (!result.ok) throw new Error(body?.message || `Database request failed (${result.status})`);
  return body.map(projectDemand);
}

Deno.serve(async (req) => {
  const origin = req.headers.get("origin") || "";
  if (origin && !ALLOWED_ORIGINS.has(origin)) return response(origin, { error: "Origin is not allowed" }, 403);
  if (req.method === "OPTIONS") return new Response(null, { status: 204 });
  if (req.method !== "GET") return response(origin, { error: "Method not allowed" }, 405);
  try {
    if (!(await authorized(req))) return response(origin, { error: "Unauthorized" }, 401);
    const query = new URL(req.url).searchParams;
    const from = query.get("from") || new Date().toISOString().slice(0, 10);
    const end = new Date(`${from}T00:00:00Z`);
    end.setUTCDate(end.getUTCDate() + 366);
    const to = query.get("to") || end.toISOString().slice(0, 10);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(from) || !/^\d{4}-\d{2}-\d{2}$/.test(to)) {
      return response(origin, { error: "Dates must use YYYY-MM-DD" }, 400);
    }
    return response(origin, {
      schema_version: "910cpr-canonical-scheduling-demand.v1",
      generated_at: new Date().toISOString(),
      active_registration_statuses: [...ACTIVE],
      sessions: await loadDemand(from, to),
    });
  } catch (error) {
    console.error(JSON.stringify({ event: "canonical_scheduling_demand_error", message: String(error) }));
    return response(origin, { error: "Canonical scheduling demand is temporarily unavailable" }, 500);
  }
});
