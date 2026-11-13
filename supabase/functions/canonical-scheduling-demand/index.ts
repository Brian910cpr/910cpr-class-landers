import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import {localDate, localMidnight, demandRange} from '../_shared/scheduling-clock.ts';
export {localDate, localMidnight, demandRange} from '../_shared/scheduling-clock.ts';
import {registrationProof} from '../_shared/external-roster-proof.ts';

const ACTIVE = new Set(["registered", "confirmed", "completed"]);
const ALLOWED_ORIGINS = new Set(["https://www.910cpr.com", "https://910cpr.com"]);
const RELEASE_PROOF_SCHEMA = "910cpr-native-release-proof.v1";
const RELEASE_BATCH_SIZE = 64;
const NATIVE_ID = /^lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/;

function response(origin: string, body: unknown, status = 200) {
  const headers: Record<string, string> = {
    "access-control-allow-headers": "content-type,x-hot-sync-admin-key",
    "access-control-allow-methods": "GET,POST,OPTIONS",
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

// Only service-read authority events opt into the native count contract.
// The dedicated STABLE RPC reads exact identity, registrations, holds and
// inherited reserve from one database statement snapshot.
function hasNativeAuthority(row: any) {
  return Array.isArray(row.landerware_session_authority_events)
    && row.landerware_session_authority_events.some((event: any) => event.enabled === true);
}

// Lifecycle witnesses are service-only. Materialized provenance without a
// witness must also take the native path and fail closed, never lose its holds.
function hasGeneratedMaterialization(row: any) {
  const witness = row.native_checkout_generated_sessions;
  return (Array.isArray(witness) ? witness.length > 0 : witness != null)
    || ["skills_session_native", "native_full_course"].includes(row.external_session_evidence?.materializedBy);
}

function capturedGeneratedIdentity(row: any): string {
  const relationship = row.native_checkout_generated_sessions;
  const witness = Array.isArray(relationship) ? relationship.length === 1 ? relationship[0] : null : relationship;
  if (row.registration_backend !== "landerware" || row.source !== "landerware_event"
      || row.record_scope !== "operational" || witness?.state !== "holding"
      || !/^[0-9a-f]{32}$/.test(witness?.identity_hash || "")
      || !/^lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(row.external_class_id || "")
      || !["skills_session_native", "native_full_course"].includes(row.external_session_evidence?.materializedBy)) {
    throw new Error("Native generated authority is unavailable");
  }
  return witness.identity_hash;
}

// Compare PostgreSQL timestamptz values by instant, retaining microseconds.
// Date.parse alone would hide identity changes smaller than one millisecond.
function timestampIdentity(value: any): bigint | null {
  if (typeof value !== "string") return null;
  const match = value.match(/^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,6}))?(Z|[+-]\d{2}:\d{2})$/);
  if (!match) return null;
  const milliseconds = Date.parse(match[1] + match[3]);
  if (!Number.isFinite(milliseconds)) return null;
  return BigInt(milliseconds) * 1000n + BigInt((match[2] || "").padEnd(6, "0"));
}

function matchesSessionIdentity(row: any, captured: any): boolean {
  const identity = [row.course_id, row.start_at, row.end_at, row.consumption_start_at,
    row.consumption_end_at, row.lead_instructor_id, row.location_id, row.resource_id,
    row.organization_id, row.external_class_id, row.record_scope];
  return Array.isArray(captured) && captured.length === identity.length
    && identity.every((value: any, index: number) => {
      if (value === undefined || captured[index] === undefined) return false;
      if (value === null || captured[index] === null) return value === captured[index];
      if (index >= 1 && index <= 4) {
        const instant = timestampIdentity(value);
        return instant !== null && instant === timestampIdentity(captured[index]);
      }
      return value === captured[index];
    });
}

function capturedAuthorityRevision(row: any): number {
  const events = row.landerware_session_authority_events;
  const revisions = events.map((event: any) => event.revision);
  if (revisions.some((revision: any) => !Number.isSafeInteger(revision) || revision < 1)
      || new Set(revisions).size !== revisions.length) throw new Error("Invalid native authority history");
  const latest = events.reduce((a: any, b: any) => a.revision > b.revision ? a : b);
  if (row.registration_backend !== "landerware" || latest.enabled !== true
      || !matchesSessionIdentity(row, latest.session_identity)) throw new Error("Native scheduling identity changed");
  return latest.revision;
}

export function projectDemand(row: any, seats: any = null) {
  const adopted = hasNativeAuthority(row);
  const native = adopted || hasGeneratedMaterialization(row);
  const capturedRevision = adopted ? capturedAuthorityRevision(row) : null;
  const generatedIdentity = native && !adopted ? capturedGeneratedIdentity(row) : null;
  if (native && (seats?.registrationAuthority !== (adopted ? "landerware-session-authority.v1" : "landerware-generated-session.v1")
      || seats.authorityRevision !== capturedRevision
      || seats.generatedIdentity !== generatedIdentity
      || !matchesSessionIdentity(row, seats.sessionIdentity)
      || typeof row.status !== "string" || seats.sessionStatus !== row.status
      || typeof row.registration_status !== "string" || seats.registrationStatus !== row.registration_status
      || typeof row.visibility !== "string" || seats.visibility !== row.visibility
      || [seats.registered, seats.holds, seats.unreconciledReserved, seats.capacity]
        .some((value: any) => !Number.isSafeInteger(value) || value < 0)
      || seats.capacity < 1
      || seats.registered + seats.holds + seats.unreconciledReserved > seats.capacity)) {
    throw new Error("Native scheduling occupancy is unavailable");
  }
  const booking = native ? seats.publicBooking : null;
  if (booking != null && (booking.schemaVersion !== "native-session-booking.v1"
      || !["209806", "359474"].includes(booking.publicCourseId)
      || booking.publicCourseId !== row.external_course_id
      || !Number.isSafeInteger(booking.profileVersion) || booking.profileVersion < 1
      || booking.capacity !== seats.capacity
      || booking.remaining !== seats.capacity - seats.registered - seats.holds - seats.unreconciledReserved
      || booking.remaining < 1 || row.visibility !== "public" || row.registration_status !== "open"
      || !["scheduled", "active"].includes(row.status))) throw new Error("Native booking admission is unavailable");
  const skills = native ? seats.skillsBooking : null;
  if (skills != null && (skills.schemaVersion !== "native-skills-session-booking.v1"
      || skills.publicCourseId !== "509474" || row.external_course_id !== "509474"
      || skills.profileKey !== "native_skills_shared" || !Number.isSafeInteger(skills.profileVersion) || skills.profileVersion < 1
      || skills.sourceSessionId !== row.external_class_id || !/^[a-f0-9]{32}$/.test(skills.identityWitness || "")
      || skills.capacity !== 2 || seats.capacity !== 2 || skills.remaining !== seats.capacity - seats.registered - seats.holds - seats.unreconciledReserved
      || !Number.isSafeInteger(skills.remaining) || skills.remaining < 1
      || skills.qualificationPolicy !== "skills-session-policy.v1" || !Array.isArray(skills.skillsContexts) || !skills.skillsContexts.length
      || new Set(skills.skillsContexts).size !== skills.skillsContexts.length
      || skills.skillsContexts.some((c: string) => !["cpr-aed","first-aid-cpr-aed","arc-blended","hsi-blended","bls-skills"].includes(c))
      || row.visibility !== "public" || row.registration_status !== "open" || !["scheduled","active"].includes(row.status)))
    throw new Error("Native skills admission is unavailable");
  const heartsaver = native ? seats.heartsaverBooking : null;
  if (heartsaver != null) {
    const course = heartsaver.publicCourseId;
    const canonical = course === "209809" ? "23dfcfa7-4224-46ed-8d45-64d43d5425db" : course === "344085" ? "306bc81a-0e09-49e1-8910-e05501222eb4" : null;
    const fields = ["schemaVersion","publicCourseId","canonicalCourseId","coursePolicyKey","profileKey","profileVersion","sourceSessionId","identityWitness","capacity","remaining","instructionMinutes","cleanupMinutes"];
    if (Object.keys(heartsaver).length !== fields.length || fields.some(key => !Object.hasOwn(heartsaver,key))
        || heartsaver.schemaVersion !== "native-heartsaver-session-booking.v1" || canonical === null
        || heartsaver.canonicalCourseId !== canonical || row.course_id !== canonical || row.external_course_id !== course
        || heartsaver.coursePolicyKey !== `heartsaver-full:${course}.v1` || heartsaver.profileKey !== `native_heartsaver_${course}_draft`
        || !Number.isSafeInteger(heartsaver.profileVersion) || heartsaver.profileVersion < 1
        || heartsaver.sourceSessionId !== row.external_class_id || !/^(?:[0-9]+|lw-[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})$/.test(heartsaver.sourceSessionId || "")
        || !/^[a-f0-9]{32}$/.test(heartsaver.identityWitness || "") || (!adopted && heartsaver.identityWitness !== generatedIdentity)
        || heartsaver.capacity !== seats.capacity || heartsaver.remaining !== seats.capacity - seats.registered - seats.holds - seats.unreconciledReserved
        || !Number.isSafeInteger(heartsaver.remaining) || heartsaver.remaining < 1
        || heartsaver.instructionMinutes !== (course === "209809" ? 120 : 90) || heartsaver.cleanupMinutes !== (course === "209809" ? 30 : 15)
        || timestampIdentity(row.end_at)!==timestampIdentity(row.start_at)! + BigInt(heartsaver.instructionMinutes)*60000000n
        || timestampIdentity(row.consumption_start_at)!==timestampIdentity(row.start_at)
        || timestampIdentity(row.consumption_end_at)!==timestampIdentity(row.end_at)! + BigInt(heartsaver.cleanupMinutes)*60000000n
        || row.resource_id !== null || row.visibility !== "public" || row.registration_status !== "open" || !["scheduled","active"].includes(row.status))
      throw new Error("Native Heartsaver admission is unavailable");
  }
  const proof = native ? {
    count_available: true, demand_status: "current", source_observed_at: null,
    reconciled_at: null, source_sha256: null, freshness_minutes: null,
    active_registration_count: seats.registered + seats.holds + seats.unreconciledReserved,
    registration_authority: seats.registrationAuthority,
    native_booking_admission: booking == null ? null : {
      schemaVersion: booking.schemaVersion, publicCourseId: booking.publicCourseId,
      profileVersion: booking.profileVersion, capacity: booking.capacity, remaining: booking.remaining,
    },
    native_skills_booking_admission: skills == null ? null : {
      schemaVersion: skills.schemaVersion, publicCourseId: skills.publicCourseId, profileKey: skills.profileKey,
      profileVersion: skills.profileVersion, sourceSessionId: skills.sourceSessionId, identityWitness: skills.identityWitness,
      capacity: skills.capacity, remaining: skills.remaining, skillsContexts: skills.skillsContexts,
      qualificationPolicy: skills.qualificationPolicy,
    },
    native_heartsaver_booking_admission: heartsaver == null ? null : {...heartsaver},
    authority_revision: seats.authorityRevision,
    canonical_registered_count: seats.registered,
    held_seat_count: seats.holds,
    unreconciled_reserved_count: seats.unreconciledReserved,
  } : registrationProof(row);
  const countAvailable = proof.count_available;
  const registrations = countAvailable && Array.isArray(row.registrations) ? row.registrations : [];
  const workspaces = row.landerware_sessions || [];
  const workspace = workspaces.length === 1 ? workspaces[0] : null;
  const workspaceStatus = !workspaces.length ? "missing" : !workspace
    || Date.parse(workspace.starts_at) !== Date.parse(row.start_at)
    || Date.parse(workspace.ends_at) !== Date.parse(row.end_at) ? "stale" : "current";
  return {
    canonical_session_id: row.id,
    external_class_id: row.external_class_id || null,
    external_course_id: row.external_course_id || null,
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
    canonical_recorded_registration_count: native ? seats.registered : Array.isArray(row.registrations)
      ? row.registrations.filter((item: any) => ACTIVE.has(item.status)).length : null,
    source: row.source,
    session_status: row.status,
    active_registration_count: countAvailable ? registrations.filter((item: any) => ACTIVE.has(item.status)).length : null,
    count_available: countAvailable,
    ...proof,
    demand_basis: native ? "native_authoritative_occupied_seats" : countAvailable ? "canonical_active_registrations" : "unknown",
  };
}

export async function loadDemand(start: string, stop: string) {
  const { url, key } = serviceConfig();
  const select = [
    "id", "course_id", "resource_id", "organization_id", "record_scope", "external_class_id", "external_course_id", "registration_backend", "external_reconciliation", "external_session_evidence", "source", "status", "start_at", "end_at", "location_id", "lead_instructor_id",
    "consumption_start_at", "consumption_end_at", "source_location_label", "source_instructor_label", "visibility", "registration_status",
    "courses!class_sessions_course_id_fkey(course_key,name)",
    "locations!class_sessions_location_id_fkey(name)",
    "people!class_sessions_lead_instructor_id_fkey(display_name)",
    "landerware_sessions!landerware_sessions_class_session_id_fkey(id,starts_at,ends_at)",
    "registrations!registrations_class_session_id_fkey(status,external_registration_id,registration_source)",
    "landerware_session_authority_events!landerware_session_authority_events_class_session_id_fkey(enabled,revision,session_identity)",
    "native_checkout_generated_sessions!native_checkout_generated_sessions_class_session_id_fkey(identity_hash,state)",
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
    // Bound parallel RPCs; never convert a failed native authority read to zero
    // or silently fall back to historical external evidence.
    for (let index = 0; index < body.length; index += 10) {
      sessions.push(...await Promise.all(body.slice(index, index + 10).map(async (row: any) => {
        if (!hasNativeAuthority(row) && !hasGeneratedMaterialization(row)) return projectDemand(row);
        const result = await fetch(`${url}/rest/v1/rpc/native_scheduling_seat_snapshot`, {
          method: "POST", headers: { apikey: key, authorization: `Bearer ${key}`, "content-type": "application/json" },
          body: JSON.stringify({ p_session_id: row.id }), signal: AbortSignal.timeout(20000),
        });
        if (!result.ok) throw new Error(`Native occupancy request failed (${result.status})`);
        return projectDemand(row, await result.json());
      })));
    }
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

async function nativeMaintenance() {
  const {url,key} = serviceConfig();
  const result = await fetch(`${url}/rest/v1/rpc/native_publication_release_expired`, {
    method: "POST", headers: {apikey:key,authorization:`Bearer ${key}`,"content-type":"application/json"},
    body: "{}", signal: AbortSignal.timeout(20000), redirect: "error",
  });
  const body = await result.json();
  if (!result.ok || body?.schemaVersion !== "native-publication-maintenance.v1"
      || !Number.isSafeInteger(body.released) || body.released < 0 || body.released > 32
      || !Number.isSafeInteger(body.examined) || body.examined < 0 || body.examined > 32)
    throw new Error("Native maintenance unavailable");
  return {schemaVersion:body.schemaVersion,released:body.released,examined:body.examined,batchLimit:32,observedAt:body.observedAt};
}

async function releasedSessions(ids: string[]) {
  const {url,key} = serviceConfig();
  const result = await fetch(`${url}/rest/v1/rpc/native_released_scheduling_sessions`, {
    method: "POST", headers: {apikey:key,authorization:`Bearer ${key}`,"content-type":"application/json"},
    body: JSON.stringify({p_external_class_ids:ids}), signal: AbortSignal.timeout(20000), redirect: "error",
  });
  const proof = await result.json();
  const rows = proof?.released_native_sessions;
  if (!result.ok || proof?.schema_version !== RELEASE_PROOF_SCHEMA || proof.complete !== true
      || timestampIdentity(proof.generated_at) === null
      || !Array.isArray(proof.requested_external_class_ids)
      || JSON.stringify(proof.requested_external_class_ids) !== JSON.stringify(ids)
      || !Array.isArray(rows) || rows.length > ids.length
      || new Set(rows.map((row: any) => row?.external_class_id)).size !== rows.length
      || rows.some((row: any) => !ids.includes(row?.external_class_id)))
    throw new Error("Native release projection unavailable");
  return proof;
}

async function heartsaverPolicyProof() {
  const {url,key} = serviceConfig();
  const result = await fetch(`${url}/rest/v1/rpc/native_heartsaver_publication_policy`, {
    method:"POST", headers:{apikey:key,authorization:`Bearer ${key}`,"content-type":"application/json"},
    body:"{}", signal:AbortSignal.timeout(20000), redirect:"error",
  });
  const proof = await result.json();
  const observed = timestampIdentity(proof?.observedAt), until = timestampIdentity(proof?.validUntil);
  if (!result.ok || proof?.schemaVersion !== "native-heartsaver-publication-policy.v1"
      || observed === null || until === null || until-observed !== 900000000n
      || !proof.courses || Object.keys(proof.courses).sort().join(",") !== "209809,344085")
    throw new Error("Native Heartsaver policy proof unavailable");
  for (const course of ["209809","344085"]) {
    const p = proof.courses[course];
    if (!p || typeof p.materializationEnabled !== "boolean" || typeof p.nativePublicationEnabled !== "boolean"
        || p.nativeScopeId !== "brian-shipyard-b.v1" || p.pageKey !== "heartsaver"
        || p.coursePolicyKey !== `heartsaver-full:${course}.v1`
        || p.canonicalCourseId !== (course === "209809" ? "23dfcfa7-4224-46ed-8d45-64d43d5425db" : "306bc81a-0e09-49e1-8910-e05501222eb4")
        || p.instructionMinutes !== (course === "209809" ? 120 : 90) || p.cleanupMinutes !== (course === "209809" ? 30 : 15)
        || (p.maxStudents !== null && (!Number.isSafeInteger(p.maxStudents) || p.maxStudents < 1 || p.maxStudents > 100))
        || (p.nativePublicationEnabled && (!p.materializationEnabled || p.maxStudents === null
          || timestampIdentity(p.qualificationValidThrough) === null || timestampIdentity(p.qualificationValidThrough)! < observed)))
      throw new Error("Native Heartsaver policy proof unavailable");
  }
  return proof;
}

async function blsSkillsPolicyProof() {
  const {url,key} = serviceConfig();
  const result = await fetch(`${url}/rest/v1/rpc/native_bls_skills_publication_policy`, {
    method:"POST", headers:{apikey:key,authorization:`Bearer ${key}`,"content-type":"application/json"},
    body:"{}", signal:AbortSignal.timeout(20000), redirect:"error",
  });
  const p = await result.json(), observed = timestampIdentity(p?.observedAt), until = timestampIdentity(p?.validUntil);
  const fields = ["schemaVersion","observedAt","validUntil","nativeScopeId","physicalCourseId","context","profileKey","profileVersion",
    "skillsEnabled","bundleEnabled","qualificationValidThrough","instructionMinutes","cleanupMinutes","capacity","skillsCents","bundleCents"];
  if (!result.ok || !p || Object.keys(p).length !== fields.length || fields.some(key => !Object.hasOwn(p,key))
      || p.schemaVersion !== "native-bls-skills-publication-policy.v1" || observed === null || until === null || until-observed !== 900000000n
      || p.nativeScopeId !== "brian-shipyard-b.v1" || p.physicalCourseId !== "509474" || p.context !== "bls-skills" || p.profileKey !== "native_skills_shared"
      || typeof p.skillsEnabled !== "boolean" || typeof p.bundleEnabled !== "boolean" || (p.bundleEnabled && !p.skillsEnabled)
      || p.instructionMinutes !== 45 || p.cleanupMinutes !== 15 || p.capacity !== 2 || p.skillsCents !== 5500 || p.bundleCents !== 9500
      || (p.skillsEnabled ? (!Number.isSafeInteger(p.profileVersion) || p.profileVersion < 1
          || timestampIdentity(p.qualificationValidThrough) === null || timestampIdentity(p.qualificationValidThrough)! < observed)
        : p.profileVersion !== null || p.qualificationValidThrough !== null))
    throw new Error("Native BLS skills policy proof unavailable");
  return p;
}

async function advancedRpc(name:string,body:unknown){
 const {url,key}=serviceConfig();const r=await fetch(`${url}/rest/v1/rpc/${name}`,{method:"POST",headers:{apikey:key,authorization:`Bearer ${key}`,"content-type":"application/json"},body:JSON.stringify(body),redirect:"error",signal:AbortSignal.timeout(20000)});
 if(!r.ok)throw Error("Native advanced policy service unavailable");return r.json();
}
async function advancedPolicyProof(){
 if(Deno.env.get("NATIVE_ADVANCED_PUBLICATION_ENABLED")!=="true")throw Error("Native advanced publication disabled");
 const p=await advancedRpc("native_advanced_publication_policy",{});
 if(p?.schemaVersion!=="native-advanced-publication-policy.v1"||Object.keys(p.courses||{}).sort().join(',')!=="209805,209818,241108,251496"||timestampIdentity(p.validUntil)===null||timestampIdentity(p.observedAt)===null||timestampIdentity(p.validUntil)!-timestampIdentity(p.observedAt)!!==900000000n)throw Error("Native advanced policy proof unavailable");return p;
}

export async function handleRequest(req: Request) {
  const origin = req.headers.get("origin") || "";
  if (origin && !ALLOWED_ORIGINS.has(origin)) return response(origin, { error: "Origin is not allowed" }, 403);
  if (req.method === "OPTIONS") return response(origin, null, 204);
  if (!["GET", "POST"].includes(req.method)) return response(origin, { error: "Method not allowed" }, 405);
  try {
    if (!(await authorized(req))) return response(origin, { error: "Unauthorized" }, 401);
    const params=new URL(req.url).searchParams;
    if (req.method === "POST") {
      const advanced=params.get("advanced_publish")==="1";
      if(params.has("advanced_publish")&&(params.getAll("advanced_publish").length!==1||!advanced||[...params.keys()].some(k=>k!=="advanced_publish")))return response(origin,{error:"Invalid advanced publication request"},400);
      const limit=advanced?262144:128;
      // An explicit, authenticated mutation. GET/preview reads never clean up.
      if (req.headers.get("content-type") !== "application/json" || Number(req.headers.get("content-length") || 0) > limit)
        return response(origin, {error:"Invalid maintenance request"},400);
      const reader = req.body?.getReader();
      if (!reader) return response(origin,{error:"Invalid maintenance request"},400);
      let raw = "", bytes = 0;
      try {
        while (true) {
          const chunk = await reader.read(); if (chunk.done) break;
          bytes += chunk.value.length;
          if (bytes > limit) {await reader.cancel();return response(origin,{error:"Invalid maintenance request"},400);}
          raw += new TextDecoder().decode(chunk.value);
        }
      } finally {reader.releaseLock();}
      let input;try {input=JSON.parse(raw);} catch {return response(origin,{error:"Invalid maintenance request"},400);}
      if(advanced){
       if(Deno.env.get("NATIVE_ADVANCED_PUBLICATION_ENABLED")!=="true"||input?.action!=="publish_advanced_offers"||Object.keys(input).length!==2||!Array.isArray(input.offers)||input.offers.length<1||input.offers.length>128)return response(origin,{error:"Invalid advanced publication request"},400);
       const accepted=await advancedRpc("native_publish_advanced_offers",{p_offers:input.offers});
       if(accepted!==input.offers.length)throw Error("Incomplete advanced publication admission");return response(origin,{ok:true,accepted},200);
      }
      if (input?.action !== "release_expired_native_holds" || Object.keys(input).length !== 1)
        return response(origin,{error:"Invalid maintenance request"},400);
      return response(origin, await nativeMaintenance(), 200);
    }
    if (params.has("release_ids") || params.has("projection")) {
      const ids = (params.get("release_ids") || "").split(",");
      if (params.get("projection") !== "native-release-proof"
          || [...params.keys()].some(key => !["projection", "release_ids"].includes(key))
          || params.getAll("projection").length !== 1 || params.getAll("release_ids").length !== 1
          || ids.length > RELEASE_BATCH_SIZE || ids.some(id => !NATIVE_ID.test(id))
          || new Set(ids).size !== ids.length)
        return response(origin, {error:"Invalid native release proof request"}, 400);
      // Authenticated and read-only; never run maintenance from GET/preview.
      return response(origin, await releasedSessions(ids));
    }
    if(params.has("native_advanced")&&(params.getAll("native_advanced").length!==1||params.get("native_advanced")!=="1"))return response(origin,{error:"Invalid advanced policy request"},400);
    if (params.has("native_heartsaver") && (params.getAll("native_heartsaver").length !== 1 || params.get("native_heartsaver") !== "1"))
      return response(origin,{error:"Invalid Heartsaver policy request"},400);
    if (params.has("native_bls_skills") && (params.getAll("native_bls_skills").length !== 1 || params.get("native_bls_skills") !== "1"))
      return response(origin,{error:"Invalid BLS skills policy request"},400);
    const range = demandRange(params);
    return response(origin, {
      schema_version: "910cpr-canonical-scheduling-demand.v1",
      generated_at: new Date().toISOString(),
      active_registration_statuses: [...ACTIVE],
      native_active_registration_statuses: [...ACTIVE, "active"],
      sessions: await loadDemand(range.start, range.stop),
      non_session_sources: await loadNonSessionSources(range.start, range.stop),
      // History is not publication input. The client asks only for IDs still
      // present in its retained schedule, in bounded explicit proof requests.
      released_native_sessions: [],
      ...(params.get("native_advanced")==="1"?{native_advanced_policy_proof:await advancedPolicyProof()}:{}),
      ...(params.get("native_heartsaver") === "1" ? {native_heartsaver_policy_proof:await heartsaverPolicyProof()} : {}),
      ...(params.get("native_bls_skills") === "1" ? {native_bls_skills_policy_proof:await blsSkillsPolicyProof()} : {}),
    });
  } catch (error) {
    if (error instanceof RangeError) return response(origin, { error: error.message }, 400);
    console.error(JSON.stringify({ event: "canonical_scheduling_demand_error", message: String(error) }));
    return response(origin, { error: "Canonical scheduling demand is temporarily unavailable" }, 500);
  }
}

Deno.serve(handleRequest);
