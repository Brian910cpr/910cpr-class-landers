import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {localDate, localMidnight, demandRange} from '../_shared/scheduling-clock.ts';
export {localDate, localMidnight, demandRange} from '../_shared/scheduling-clock.ts';
import {registrationProof} from '../_shared/external-roster-proof.ts';

// Registration lifecycle state active represents a real occupied seat.
const ACTIVE = new Set(["registered", "confirmed", "completed", "active"]);
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

function catalogCourseId(value: unknown): string | null {
  // This is the joined catalog's identifier, not booking or roster evidence.
  if (typeof value === "number") return Number.isSafeInteger(value) && value > 0 ? String(value) : null;
  return typeof value === "string" && /^[1-9][0-9]*$/.test(value) ? value : null;
}

export function projectDemand(row: any) {
  const now = new Date();
  const proof = registrationProof(row, now);
  const countAvailable = proof.count_available;
  const registrations = countAvailable ? row.registrations : [];
  // Internal occupied-time signal only. A numeric legacy external_class_id can
  // coexist with genuine native registrations; without a fresh complete
  // external roster we must NOT infer the total, remaining seats, or public
  // joinability from those rows. Verified local native lifecycle is sufficient
  // to reserve the instructor's time and supply Anchor gravity.
  const nativeCommittedSeat = row.registration_backend === "landerware"
    && row.source === "landerware_public_offer"
    && Array.isArray(row.registrations)
    && row.registrations.some((item: any) => ACTIVE.has(item.status)
      && item.registration_source === "landerware_native_checkout"
      && !item.external_registration_id);
  // A confirmed appointment intake can have a real seated registration even
  // while its legacy numeric class roster remains unproven. Require the original
  // accepted confirmation-message provenance and the matching active lifecycle;
  // do not infer totals or public joinability from this one-seat signal.
  const emailEvidence = row.external_session_evidence || {};
  const confirmedEmailIntakeSeat = row.registration_backend === "landerware"
    && row.source === "confirmed_booking_intake"
    && emailEvidence.kind === "registration_confirmation"
    && /^[0-9a-f]{16}$/i.test(String(emailEvidence.gmail_message_id || ""))
    && Array.isArray(row.registrations)
    && row.registrations.some((item: any) => ACTIVE.has(item.status)
      && item.registration_source === "enrollware_email_confirmation");
  // An expired previously complete external roster is not a current seat
  // count. But an exact, still-active relationship match is conservative
  // evidence of an existing commitment: reserve time, not public capacity.
  // Reuse the shared relationship validator at its original observation
  // epoch; the normal current-time proof and all public gates stay unchanged.
  const priorObserved = Date.parse(row.external_reconciliation?.source_observed_at || "");
  const staleExactCommitment = proof.demand_status === "stale_reconciliation"
    && row.registration_backend === "enrollware"
    && row.source === "enrollware_reconciled"
    && /^\d+$/.test(String(row.external_class_id || ""))
    && Number.isFinite(priorObserved)
    && now.getTime() - priorObserved > 3600000
    && Array.isArray(row.registrations)
    && !row.registrations.some((item: any) => ACTIVE.has(item.status) && item.canceled_at != null)
    && (() => {
      const prior = registrationProof(row, new Date(priorObserved));
      return prior.count_available && typeof prior.active_registration_count === "number"
        && prior.active_registration_count > 0;
    })();
  const operationalHasActiveSeat = ["scheduled", "active"].includes(row.status)
    && ((countAvailable && typeof proof.active_registration_count === "number"
          && proof.active_registration_count > 0) || nativeCommittedSeat || confirmedEmailIntakeSeat
          || staleExactCommitment);
  const workspaces = row.landerware_sessions || [];
  const workspace = workspaces.length === 1 ? workspaces[0] : null;
  const workspaceStatus = !workspaces.length ? "missing" : !workspace
    || Date.parse(workspace.starts_at) !== Date.parse(row.start_at)
    || Date.parse(workspace.ends_at) !== Date.parse(row.end_at) ? "stale" : "current";
  return {
    canonical_session_id: row.id,
    external_class_id: row.external_class_id || null,
    external_course_id: row.external_course_id || null,
    catalog_course_id: catalogCourseId(row.courses?.enrollware_course_id),
    course_key: row.courses?.course_key || null,
    start_at: row.start_at,
    end_at: row.end_at,
    consumption_start_at: row.consumption_start_at,
    consumption_end_at: row.consumption_end_at,
    location_id: row.location_id,
    location_name: row.source_location_label || row.locations?.name || null,
    lead_instructor_id: row.lead_instructor_id,
    lead_instructor_name: row.source_instructor_label || row.people?.display_name || null,
    course_name: row.courses?.name || null,
    visibility: row.visibility,
    registration_backend: row.registration_backend,
    registration_status: row.registration_status,
    workspace_projection_status: workspaceStatus,
    workspace_session_id: workspace?.id || null,
    // Operational demand is not proof of public joinability or total roster size.
    operational_has_active_seat: operationalHasActiveSeat,
    canonical_recorded_registration_count: Array.isArray(row.registrations)
      ? row.registrations.filter((item: any) => ACTIVE.has(item.status)).length : null,
    source: row.source,
    session_status: row.status,
    active_registration_count: countAvailable ? registrations.filter((item: any) => ACTIVE.has(item.status)).length : null,
    count_available: countAvailable,
    ...proof,
    demand_basis: countAvailable ? "canonical_active_registrations" : "unknown",
  };
}

export async function loadDemand(start: string, stop: string) {
  const { url, key } = serviceConfig();
  const select = [
    "id", "external_class_id", "external_course_id", "registration_backend", "external_reconciliation", "external_session_evidence", "source", "status", "start_at", "end_at", "location_id", "lead_instructor_id",
    "consumption_start_at", "consumption_end_at", "source_location_label", "source_instructor_label", "visibility", "registration_status",
    "courses!class_sessions_course_id_fkey(course_key,name,enrollware_course_id)",
    "locations!class_sessions_location_id_fkey(name)",
    "people!class_sessions_lead_instructor_id_fkey(display_name)",
    "landerware_sessions!landerware_sessions_class_session_id_fkey(id,starts_at,ends_at)",
    "registrations!registrations_class_session_id_fkey(status,external_registration_id,registration_source,canceled_at)",
  ].join(",");
  const params = new URLSearchParams({
    select, record_scope: "eq.operational", status: "in.(scheduled,active,completed)", order: "start_at.asc,id.asc", limit: "500",
  });
  // Include carry-in commitments until their consumption end (or instructional end if absent).
  params.set("or", `(start_at.gte.${start},consumption_end_at.gt.${start},and(consumption_end_at.is.null,end_at.gt.${start}))`);
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

export async function loadNonSessionSources(start: string, stop: string) {
  const { url, key } = serviceConfig();
  const result = await fetch(`${url}/rest/v1/rpc/enrollware_reconciliation_health`, {
    method: "POST", headers: { apikey: key, authorization: `Bearer ${key}`, "content-type": "application/json" },
    body: JSON.stringify({ p_from: start, p_to: stop }), signal: AbortSignal.timeout(20000),
  });
  const body = await result.json();
  if (!result.ok || !Array.isArray(body?.sessions)) throw new Error(`Classification request failed (${result.status})`);
  if (body.sessions.some((row: any) => row.status === "non_session_conflicting_canonical_session")) {
    throw new Error("Non-session classification conflicts with a canonical session");
  }
  // The existing health RPC revalidates the owner's decision against the exact
  // latest source identity. Never export private ingest facts or registrations.
  return body.sessions.filter((row: any) => row.status === "classified_non_session").map((row: any) => ({
    external_class_id: row.external_class_id, start_at: row.start_at,
    classification: row.non_session_classification, reason: row.reason,
    source_observed_at: row.source_observed_at,
  }));
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
      non_session_sources: await loadNonSessionSources(range.start, range.stop),
    });
  } catch (error) {
    if (error instanceof RangeError) return response(origin, { error: error.message }, 400);
    console.error(JSON.stringify({ event: "canonical_scheduling_demand_error", message: String(error) }));
    return response(origin, { error: "Canonical scheduling demand is temporarily unavailable" }, 500);
  }
}

Deno.serve(handleRequest);
