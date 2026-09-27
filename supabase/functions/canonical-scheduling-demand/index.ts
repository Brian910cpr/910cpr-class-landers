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
  return new Response(status === 204 ? null : JSON.stringify(body), { status, headers });
}

const TIMEZONE = "America/New_York";

export function localDate(now = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TIMEZONE, year: "numeric", month: "2-digit", day: "2-digit" }).format(now);
}

export function localMidnight(day: string): string {
  const stamp = Date.parse(`${day}T00:00:00Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day) || !Number.isFinite(stamp) || new Date(stamp).toISOString().slice(0, 10) !== day) {
    throw new RangeError("Dates must be real calendar dates in YYYY-MM-DD format");
  }
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone: TIMEZONE, year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
  });
  let instant = stamp;
  // Resolve the zone at the boundary itself, including 23/25-hour DST days.
  for (let attempt = 0; attempt < 3; attempt++) {
    const parts = Object.fromEntries(formatter.formatToParts(new Date(instant)).map(part => [part.type, part.value]));
    const wall = Date.UTC(+parts.year, +parts.month - 1, +parts.day, +parts.hour, +parts.minute, +parts.second);
    const correction = stamp - wall;
    if (correction === 0) return new Date(instant).toISOString();
    instant += correction;
  }
  throw new RangeError("Could not resolve local midnight");
}

export function demandRange(query: URLSearchParams, now = new Date()) {
  const from = query.get("from") || localDate(now);
  const start = localMidnight(from);
  const end = new Date(`${from}T00:00:00Z`);
  end.setUTCDate(end.getUTCDate() + 366);
  const to = query.get("to") || end.toISOString().slice(0, 10);
  const stop = localMidnight(to);
  if (stop <= start || Date.parse(stop) - Date.parse(start) > 367 * 86400000) throw new RangeError("Invalid date range");
  return { from, to, start, stop };
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
    signal: AbortSignal.timeout(10000), redirect: "error",
  });
  return result.ok;
}

export function projectDemand(row: any) {
  // A live DB read does not make an incomplete Enrollware bridge current (#297).
  // No session-level complete-roster reconciliation proof exists for that bridge.
  const countAvailable = Array.isArray(row.registrations) && ["landerware", "manual"].includes(row.registration_backend);
  const registrations = countAvailable ? row.registrations : [];
  return {
    canonical_session_id: row.id,
    external_class_id: row.external_class_id || null,
    external_course_id: row.external_course_id || null,
    course_key: row.courses?.course_key || null,
    start_at: row.start_at,
    end_at: row.end_at,
    location_id: row.location_id,
    location_name: row.locations?.name || null,
    lead_instructor_id: row.lead_instructor_id,
    lead_instructor_name: null,
    source: row.source,
    session_status: row.status,
    active_registration_count: countAvailable ? registrations.filter((item: any) => ACTIVE.has(item.status)).length : null,
    count_available: countAvailable,
    demand_status: countAvailable ? "current" : "external_reconciliation_required",
    demand_basis: countAvailable ? "canonical_active_registrations" : "unknown",
  };
}

export async function loadDemand(start: string, stop: string) {
  const { url, key } = serviceConfig();
  const select = [
    "id", "external_class_id", "external_course_id", "registration_backend", "source", "status", "start_at", "end_at", "location_id", "lead_instructor_id",
    "courses!class_sessions_course_id_fkey(course_key)",
    "locations!class_sessions_location_id_fkey(name)",
    "registrations!registrations_class_session_id_fkey(status)",
  ].join(",");
  const params = new URLSearchParams({
    select, record_scope: "eq.operational", status: "in.(scheduled,active,completed)", order: "start_at.asc,id.asc", limit: "500",
  });
  params.append("start_at", `gte.${start}`);
  params.append("start_at", `lt.${stop}`);
  const sessions = [];
  for (let offset = 0; ; offset += 500) {
    params.set("offset", String(offset));
    const result = await fetch(`${url}/rest/v1/class_sessions?${params}`, {
      headers: { apikey: key, authorization: `Bearer ${key}` }, signal: AbortSignal.timeout(20000),
    });
    const body = await result.json();
    if (!result.ok || !Array.isArray(body)) throw new Error(`Database request failed (${result.status})`);
    sessions.push(...body.map(projectDemand));
    if (body.length < 500) return sessions;
  }
}

export async function handleRequest(req: Request) {
  const origin = req.headers.get("origin") || "";
  if (origin && !ALLOWED_ORIGINS.has(origin)) return response(origin, { error: "Origin is not allowed" }, 403);
  if (req.method === "OPTIONS") return response(origin, null, 204);
  if (req.method !== "GET") return response(origin, { error: "Method not allowed" }, 405);
  try {
    if (!(await authorized(req))) return response(origin, { error: "Unauthorized" }, 401);
    const range = demandRange(new URL(req.url).searchParams);
    return response(origin, {
      schema_version: "910cpr-canonical-scheduling-demand.v1",
      generated_at: new Date().toISOString(),
      active_registration_statuses: [...ACTIVE],
      sessions: await loadDemand(range.start, range.stop),
    });
  } catch (error) {
    if (error instanceof RangeError) return response(origin, { error: error.message }, 400);
    console.error(JSON.stringify({ event: "canonical_scheduling_demand_error", message: String(error) }));
    return response(origin, { error: "Canonical scheduling demand is temporarily unavailable" }, 500);
  }
}

Deno.serve(handleRequest);
