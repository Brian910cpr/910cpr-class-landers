import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const ALLOWED_ORIGINS = new Set(["https://www.910cpr.com", "https://910cpr.com"]);

function headers(origin: string) {
  const allowed = ALLOWED_ORIGINS.has(origin) ? origin : "https://www.910cpr.com";
  return {
    "access-control-allow-origin": allowed,
    "access-control-allow-headers": "content-type,idempotency-key",
    "access-control-allow-methods": "GET,POST,OPTIONS",
    "cache-control": "no-store",
    vary: "Origin",
  };
}

function reply(origin: string, body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...headers(origin), "content-type": "application/json; charset=utf-8" },
  });
}

function config() {
  const url = Deno.env.get("SUPABASE_URL");
  const raw = Deno.env.get("SUPABASE_SECRET_KEYS");
  const key = raw ? JSON.parse(raw).default : Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !key) throw new Error("server_configuration");
  return { url, key };
}

async function rpc(name: string, body: Record<string, unknown>) {
  const { url, key } = config();
  const response = await fetch(`${url}/rest/v1/rpc/${name}`, {
    method: "POST",
    headers: { apikey: key, authorization: `Bearer ${key}`, "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload?.message || `database_${response.status}`);
  return Array.isArray(payload) ? payload[0] : payload;
}

async function publicSession(externalClassId: string) {
  if (!/^\d+$/.test(externalClassId)) throw new Error("invalid_session");
  const response = await fetch("https://www.910cpr.com/data/schedule_future.json", {
    headers: { accept: "application/json" },
  });
  if (!response.ok) throw new Error("public_schedule_unavailable");
  const payload = await response.json();
  const rows = Array.isArray(payload) ? payload : Array.isArray(payload.sessions) ? payload.sessions : [];
  const session = rows.find((item: any) =>
    String(item.session_id) === externalClassId &&
    item.public_direct_booking === true &&
    item.registration_status === "open"
  );
  if (!session) throw new Error("session_not_open");
  const checkout = new URL(session.registration_url);
  if (checkout.origin !== "https://coastalcprtraining.enrollware.com" ||
      checkout.pathname !== "/enroll" || checkout.searchParams.get("id") !== externalClassId) {
    throw new Error("invalid_checkout_url");
  }
  return session;
}

Deno.serve(async (request) => {
  const origin = request.headers.get("origin") || "";
  if (origin && !ALLOWED_ORIGINS.has(origin)) return reply(origin, { error: "origin_not_allowed" }, 403);
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: headers(origin) });
  const parts = new URL(request.url).pathname.split("/").filter(Boolean);
  const route = parts.slice(parts.indexOf("public-registration") + 1);
  try {
    if (request.method === "GET" && route[0] === "session" && route[1]) {
      const session = await publicSession(route[1]);
      return reply(origin, { ok: true, session: {
        id: String(session.session_id), course: session.course_name,
        startsAt: session.start_at, endsAt: session.end_at || null,
        location: session.location_display || session.location_name || "",
        price: session.price ?? session.mapped_price ?? null,
      }});
    }
    if (request.method === "POST" && route[0] === "start") {
      const body = await request.json();
      const externalClassId = String(body.sessionId || "").trim();
      const session = await publicSession(externalClassId);
      const firstName = String(body.firstName || "").trim().slice(0, 100);
      const lastName = String(body.lastName || "").trim().slice(0, 100);
      const email = String(body.email || "").trim().toLowerCase().slice(0, 320);
      const phone = String(body.phone || "").trim().slice(0, 50);
      const idempotencyKey = (request.headers.get("idempotency-key") || "").trim().slice(0, 160);
      if (!firstName || !lastName || !email || !phone || !idempotencyKey) throw new Error("required_registration_field_missing");
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) throw new Error("invalid_email");
      if (phone.replace(/\D/g, "").length < 10) throw new Error("invalid_phone");
      const result = await rpc("queue_public_registration_intent", {
        p_external_class_id: externalClassId,
        p_course_name: String(session.course_name || "CPR Class"),
        p_starts_at: session.start_at,
        p_ends_at: session.end_at || null,
        p_location_name: session.location_display || session.location_name || null,
        p_checkout_url: session.registration_url,
        p_first_name: firstName,
        p_last_name: lastName,
        p_email: email,
        p_phone: phone,
        p_idempotency_key: idempotencyKey,
      });
      return reply(origin, { ok: true, firstName, ...result, handoff: { provider: "enrollware", url: result.checkoutUrl } });
    }
    return reply(origin, { error: "not_found" }, 404);
  } catch (error) {
    const message = error instanceof Error ? error.message : "unexpected_error";
    const bad = ["invalid_session", "session_not_open", "invalid_checkout_url", "required_registration_field_missing", "invalid_email", "invalid_phone"].includes(message);
    return reply(origin, { error: message }, bad ? 400 : 500);
  }
});
