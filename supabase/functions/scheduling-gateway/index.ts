import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const ORIGIN = "https://www.910cpr.com";
const ALLOWED_ORIGINS = new Set([ORIGIN, "https://910cpr.com"]);
const TOKEN_PATTERN = /^[A-Za-z0-9_-]{43,128}$/;
const PURPOSES = new Set([
  "initial_scheduling", "direct_registration", "reschedule", "no_show_recovery",
  "renewal_22_month", "renewal_23_month", "instructor_invitation",
]);
const PAYMENT_POLICIES = new Set(["inherit", "prepaid", "organization_billed", "no_charge", "self_pay"]);

const purposeLabels: Record<string, string> = {
  initial_scheduling: "Choose your class",
  direct_registration: "Complete your registration",
  reschedule: "Choose a new class date",
  no_show_recovery: "Choose a replacement class",
  renewal_22_month: "Plan your certification renewal",
  renewal_23_month: "Renew your certification",
  instructor_invitation: "Choose your class",
};

function cors(origin: string) {
  return {
    "access-control-allow-origin": ALLOWED_ORIGINS.has(origin) ? origin : ORIGIN,
    "access-control-allow-headers": "content-type,idempotency-key,x-hot-sync-admin-key",
    "access-control-allow-methods": "GET,POST,OPTIONS",
    "cache-control": "no-store",
    vary: "Origin",
  };
}

function json(origin: string, body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...cors(origin), "content-type": "application/json; charset=utf-8" },
  });
}

function config() {
  const url = Deno.env.get("SUPABASE_URL");
  const raw = Deno.env.get("SUPABASE_SECRET_KEYS");
  const key = raw ? JSON.parse(raw).default : Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) throw new Error("server_configuration");
  return { url, key };
}

async function db(path: string, init: RequestInit = {}) {
  const { url, key } = config();
  const response = await fetch(`${url}/rest/v1/${path}`, {
    ...init,
    headers: {
      apikey: key,
      authorization: `Bearer ${key}`,
      "content-type": "application/json",
      prefer: "return=representation",
      ...(init.headers || {}),
    },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload?.message || `database_${response.status}`);
  return payload;
}

async function rpc(name: string, body: unknown) {
  const payload = await db(`rpc/${name}`, { method: "POST", body: JSON.stringify(body) });
  return Array.isArray(payload) ? payload[0] : payload;
}

async function sha256(value: string) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function randomToken() {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return btoa(String.fromCharCode(...bytes)).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
}

function route(request: Request) {
  const parts = new URL(request.url).pathname.split("/").filter(Boolean);
  return parts.slice(parts.indexOf("scheduling-gateway") + 1);
}

function clean(value: unknown, max = 320) {
  return String(value ?? "").trim().slice(0, max);
}

function stringArray(value: unknown) {
  return Array.isArray(value) ? [...new Set(value.map((item) => clean(item, 120)).filter(Boolean))] : [];
}

async function tokenRecord(rawToken: string) {
  if (!TOKEN_PATTERN.test(rawToken)) throw new Error("invalid_scheduling_token");
  const rows = await db(
    `landerware_scheduling_tokens?token_sha256=eq.${await sha256(rawToken)}&select=*&limit=1`,
  );
  const token = rows[0];
  if (!token) throw new Error("invalid_scheduling_token");
  if (token.revoked_at) throw new Error("scheduling_token_revoked");
  if (new Date(token.expires_at) <= new Date()) throw new Error("scheduling_token_expired");
  if (Number(token.completed_action_count) >= Number(token.max_completed_actions)) {
    throw new Error("scheduling_token_completed");
  }
  return token;
}

async function currentPaymentPolicy(token: any) {
  let policy = token.payment_policy;
  if (token.registration_id) {
    const rows = await db(
      `landerware_registrations?id=eq.${encodeURIComponent(token.registration_id)}` +
      "&select=id,person_id,organization_id,payer_mode,payment_state,billing_state,status&limit=1",
    );
    const registration = rows[0];
    if (!registration || (token.person_id && registration.person_id !== token.person_id)) {
      throw new Error("scheduling_registration_mismatch");
    }
    if (registration.status === "cancelled") throw new Error("registration_cancelled");
    if (registration.payment_state === "paid" || registration.payer_mode === "prepaid") policy = "prepaid";
    else if (["corporate_client_pays", "invoice_later"].includes(registration.payer_mode)) policy = "organization_billed";
    else if (registration.payer_mode === "free") policy = "no_charge";
    else if (registration.payment_state === "pending" || registration.payer_mode === "customer_pays") policy = "self_pay";
  } else if (policy === "inherit") {
    policy = token.organization_id ? "organization_billed" : "self_pay";
  }
  if (policy !== token.payment_policy) {
    await db(`landerware_scheduling_tokens?id=eq.${token.id}`, {
      method: "PATCH",
      body: JSON.stringify({ payment_policy: policy, updated_at: new Date().toISOString() }),
    });
    token.payment_policy = policy;
  }
  return policy;
}

function paymentMessage(policy: string, organizationName: string | null) {
  if (policy === "prepaid") return "Your course has already been paid. You will not be asked to pay again.";
  if (policy === "organization_billed") return `${organizationName || "Your organization"} is handling payment.`;
  if (policy === "no_charge") return "No payment is required for this registration.";
  return "The current class price and secure payment step will be shown after you choose a date.";
}

async function liveSessions(token: any) {
  const response = await fetch(`${ORIGIN}/data/schedule_future.json`, {
    headers: { accept: "application/json" },
    cache: "no-store",
  });
  if (!response.ok) throw new Error("public_schedule_unavailable");
  const payload = await response.json();
  const rows = Array.isArray(payload) ? payload : payload.sessions || [];
  const compatible = new Set(token.compatible_course_ids || []);
  const modes = new Set(token.allowed_delivery_modes || []);
  const now = Date.now();
  const seen = new Set<string>();
  return rows.filter((session: any) => {
    const id = clean(session.session_id, 80);
    const courseId = clean(session.course_id || session.course_number, 120);
    const mode = clean(session.delivery_mode, 40);
    if (!id || seen.has(id) || !compatible.has(courseId)) return false;
    if (modes.size && !modes.has(mode)) return false;
    if (session.public_direct_booking !== true || session.registration_status !== "open") return false;
    if (!session.start_at || new Date(session.start_at).getTime() <= now) return false;
    seen.add(id);
    return true;
  }).map((session: any) => ({
    id: clean(session.session_id, 80),
    courseId: clean(session.course_id || session.course_number, 120),
    course: clean(session.course_name, 240),
    startsAt: session.start_at,
    endsAt: session.end_at || null,
    location: clean(session.location_display || session.location_name, 320),
    deliveryMode: clean(session.delivery_mode, 40),
    seatsRemaining: Number.isFinite(Number(session.seats_remaining)) ? Number(session.seats_remaining) : null,
  }));
}

async function context(rawToken: string, origin: string) {
  const token = await tokenRecord(rawToken);
  const paymentPolicy = await currentPaymentPolicy(token);
  const sessions = await liveSessions(token);
  await db(`landerware_scheduling_tokens?id=eq.${token.id}`, {
    method: "PATCH",
    body: JSON.stringify({ last_opened_at: new Date().toISOString(), updated_at: new Date().toISOString() }),
  });
  return json(origin, {
    ok: true,
    purpose: token.purpose,
    heading: purposeLabels[token.purpose] || "Choose your class",
    course: token.course_display_name,
    organization: token.organization_display_name || null,
    explanation: token.public_explanation || null,
    payment: { policy: paymentPolicy, message: paymentMessage(paymentPolicy, token.organization_display_name) },
    sessions,
    expiresAt: token.expires_at,
  });
}

async function selectSession(request: Request, rawToken: string, origin: string) {
  const token = await tokenRecord(rawToken);
  const paymentPolicy = await currentPaymentPolicy(token);
  const body = await request.json();
  const selectedId = clean(body.sessionId, 80);
  const idempotencyKey = clean(request.headers.get("idempotency-key"), 180);
  if (!selectedId || !idempotencyKey) throw new Error("invalid_scheduling_selection");
  const sessions = await liveSessions(token);
  const session = sessions.find((item: any) => item.id === selectedId);
  if (!session) throw new Error("session_not_available");
  const result = await rpc("landerware_apply_scheduling_selection", {
    p_token_id: token.id,
    p_idempotency_key: `scheduling-gateway:${token.id}:${idempotencyKey}`,
    p_external_session_id: session.id,
    p_course_id: session.courseId,
    p_course_name: session.course,
    p_starts_at: session.startsAt,
    p_ends_at: session.endsAt,
    p_location_name: session.location,
    p_delivery_mode: session.deliveryMode,
  });
  const checkoutUrl = paymentPolicy === "self_pay" ? `${ORIGIN}/register/?session=${encodeURIComponent(session.id)}` : null;
  return json(origin, {
    ok: true,
    status: result.status,
    checkoutUrl,
    confirmation: checkoutUrl
      ? "Your date is selected. Continue to the secure payment step to confirm the seat."
      : "Your class is confirmed. A confirmation email will follow.",
  });
}

function requireAdmin(request: Request) {
  const expected = Deno.env.get("HOT_SYNC_ADMIN_KEY");
  const supplied = request.headers.get("x-hot-sync-admin-key") || "";
  if (!expected || supplied.length !== expected.length) throw new Error("admin_unauthorized");
  let mismatch = 0;
  for (let index = 0; index < expected.length; index += 1) mismatch |= expected.charCodeAt(index) ^ supplied.charCodeAt(index);
  if (mismatch !== 0) throw new Error("admin_unauthorized");
}

async function issueToken(request: Request, origin: string) {
  requireAdmin(request);
  const body = await request.json();
  const purpose = clean(body.purpose, 80);
  const paymentPolicy = clean(body.paymentPolicy, 80) || "inherit";
  let personId = clean(body.personId, 80) || null;
  let organizationId = clean(body.organizationId, 80) || null;
  const registrationId = clean(body.registrationId, 80) || null;
  let profileKey = clean(body.registrationProfileKey, 160) || null;
  let courseId = clean(body.courseId, 120);
  let courseDisplayName = clean(body.courseDisplayName, 240);
  let organizationDisplayName: string | null = null;
  if (!PURPOSES.has(purpose) || !PAYMENT_POLICIES.has(paymentPolicy)) {
    throw new Error("invalid_token_request");
  }

  if (registrationId) {
    const registrations = await db(
      `landerware_registrations?id=eq.${encodeURIComponent(registrationId)}` +
      "&select=id,person_id,organization_id,course_id,registration_profile_key,status&limit=1",
    );
    const registration = registrations[0];
    if (!registration || registration.status === "cancelled") throw new Error("invalid_token_request");
    if (personId && personId !== registration.person_id) throw new Error("invalid_token_request");
    if (organizationId && registration.organization_id && organizationId !== registration.organization_id) {
      throw new Error("invalid_token_request");
    }
    personId = registration.person_id;
    organizationId = registration.organization_id || organizationId;
    profileKey = registration.registration_profile_key || profileKey;
    courseId = registration.course_id || courseId;
  }

  if (personId) {
    const people = await db(`landerware_people?id=eq.${encodeURIComponent(personId)}&select=id&limit=1`);
    if (!people[0]) throw new Error("invalid_token_request");
  } else if (paymentPolicy !== "self_pay") {
    throw new Error("invalid_token_request");
  }

  if (profileKey) {
    const profiles = await db(
      `landerware_registration_profiles?profile_key=eq.${encodeURIComponent(profileKey)}` +
      "&active=eq.true&select=profile_key,course_id,display_name&limit=1",
    );
    const profile = profiles[0];
    if (!profile) throw new Error("invalid_token_request");
    courseId = courseId || profile.course_id;
    courseDisplayName = courseDisplayName || profile.display_name;
  }

  if (organizationId) {
    const organizations = await db(
      `landerware_organizations?id=eq.${encodeURIComponent(organizationId)}` +
      "&archived_at=is.null&select=id,display_name&limit=1",
    );
    if (!organizations[0]) throw new Error("invalid_token_request");
    organizationDisplayName = organizations[0].display_name;
  }

  if (courseId && !courseDisplayName) {
    const courses = await db(
      `landerware_courses?id=eq.${encodeURIComponent(courseId)}&active=eq.true&select=id,display_name&limit=1`,
    );
    courseDisplayName = courses[0]?.display_name || "910CPR certification course";
  }
  if (!courseId || !courseDisplayName) throw new Error("invalid_token_request");

  const compatibleCourseIds = stringArray(body.compatibleCourseIds);
  if (!compatibleCourseIds.length) compatibleCourseIds.push(courseId);
  if (!compatibleCourseIds.includes(courseId)) throw new Error("invalid_token_request");
  const expiresInDays = Math.min(Math.max(Number(body.expiresInDays || 30), 1), 400);
  const rawToken = randomToken();
  const rows = await db("landerware_scheduling_tokens", {
    method: "POST",
    body: JSON.stringify({
      token_sha256: await sha256(rawToken),
      purpose,
      person_id: personId,
      organization_id: organizationId,
      registration_id: registrationId,
      registration_profile_key: profileKey,
      course_id: courseId,
      course_display_name: courseDisplayName,
      compatible_course_ids: compatibleCourseIds,
      allowed_delivery_modes: stringArray(body.allowedDeliveryModes),
      allowed_actions: ["select_session"],
      payment_policy: paymentPolicy,
      organization_display_name: organizationDisplayName,
      public_explanation: clean(body.publicExplanation, 800) || null,
      entry_context: clean(body.entryContext, 80) || "secure_known_person",
      expires_at: new Date(Date.now() + expiresInDays * 86400000).toISOString(),
      max_completed_actions: Math.min(Math.max(Number(body.maxCompletedActions || 1), 1), 20),
      created_by: clean(body.createdBy, 160) || "brian_admin",
    }),
  });
  return json(origin, {
    ok: true,
    tokenId: rows[0].id,
    url: `${ORIGIN}/schedule/${rawToken}`,
    expiresAt: rows[0].expires_at,
  }, 201);
}

Deno.serve(async (request) => {
  const origin = request.headers.get("origin") || "";
  if (origin && !ALLOWED_ORIGINS.has(origin)) return json(origin, { error: "origin_not_allowed" }, 403);
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(origin) });
  const parts = route(request);
  try {
    if (request.method === "GET" && parts[0] === "context" && parts[1]) return await context(parts[1], origin);
    if (request.method === "POST" && parts[0] === "select" && parts[1]) return await selectSession(request, parts[1], origin);
    if (request.method === "POST" && parts[0] === "admin" && parts[1] === "issue") return await issueToken(request, origin);
    return json(origin, { error: "not_found" }, 404);
  } catch (error) {
    const message = error instanceof Error ? error.message : "unexpected_error";
    const gone = ["invalid_scheduling_token", "scheduling_token_revoked", "scheduling_token_expired", "scheduling_token_completed"].includes(message);
    const unauthorized = message === "admin_unauthorized";
    const conflict = ["session_not_available", "registration_cancelled"].includes(message);
    const bad = ["invalid_scheduling_selection", "invalid_token_request", "incompatible_course", "incompatible_delivery_mode"].includes(message);
    return json(origin, { error: message }, gone ? 410 : unauthorized ? 401 : conflict ? 409 : bad ? 400 : 500);
  }
});
