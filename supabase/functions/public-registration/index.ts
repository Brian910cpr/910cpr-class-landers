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

async function rest(path: string, method = "GET", body?: unknown) {
  const { url, key } = config();
  const response = await fetch(`${url}/rest/v1/${path}`, { method, headers: { apikey: key, authorization: `Bearer ${key}`, "content-type": "application/json", prefer: "return=representation" }, body: body === undefined ? undefined : JSON.stringify(body) });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload?.message || `database_${response.status}`);
  return payload;
}

async function stripe(path: string, body: URLSearchParams, idempotencyKey: string) {
  const key = Deno.env.get("STRIPE_SECRET_KEY");
  if (!key) throw new Error("stripe_unavailable");
  const response = await fetch(`https://api.stripe.com/v1${path}`, { method: "POST", headers: { authorization: `Bearer ${key}`, "content-type": "application/x-www-form-urlencoded", "idempotency-key": idempotencyKey }, body });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload?.error?.message || `stripe_${response.status}`);
  return payload;
}

async function validStripeSignature(payload: string, header: string) {
  const secret = Deno.env.get("STRIPE_WEBHOOK_SECRET"); if (!secret) throw new Error("stripe_webhook_unavailable");
  const parts = header.split(",").map(x => x.split("=", 2)); const timestamp = parts.find(x => x[0] === "t")?.[1], signatures = parts.filter(x => x[0] === "v1").map(x => x[1]);
  if (!timestamp || !signatures.length || Math.abs(Date.now() / 1000 - Number(timestamp)) > 300) return false;
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const digest = Array.from(new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(`${timestamp}.${payload}`)))).map(b => b.toString(16).padStart(2, "0")).join("");
  return signatures.some(signature => { if (digest.length !== signature.length) return false; let mismatch = 0; for (let i = 0; i < digest.length; i++) mismatch |= digest.charCodeAt(i) ^ signature.charCodeAt(i); return mismatch === 0; });
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
      const profiles = await rest(`landerware_registration_profiles?profile_key=eq.retail-${encodeURIComponent(String(session.course_id))}&active=eq.true&listed=eq.true&select=pricing_behavior,addons&limit=1`);
      const profile = profiles[0]; if (!profile) throw new Error("retail_profile_not_found");
      return reply(origin, { ok: true, session: {
        id: String(session.session_id), courseId: String(session.course_id), course: session.course_name,
        startsAt: session.start_at, endsAt: session.end_at || null,
        location: session.location_display || session.location_name || "",
        price: Number(profile.pricing_behavior?.amount_cents) / 100,
        addons: profile.addons || [],
        fallbackRegistrationUrl: session.registration_url,
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
      const selectedOptions = body.selectedOptions && typeof body.selectedOptions === "object" && !Array.isArray(body.selectedOptions) ? body.selectedOptions : {};
      const result = await rpc("begin_retail_checkout", {
        p_external_class_id: externalClassId,
        p_course_id: String(session.course_id),
        p_course_name: String(session.course_name || "CPR Class"),
        p_starts_at: session.start_at,
        p_ends_at: session.end_at || null,
        p_location_name: session.location_display || session.location_name || null,
        p_first_name: firstName,
        p_last_name: lastName,
        p_email: email,
        p_phone: phone,
        p_selected_options: selectedOptions,
        p_idempotency_key: idempotencyKey,
        p_capacity: session.max_students ?? null,
      });
      if (result.checkoutUrl) return reply(origin, { ok: true, firstName, ...result, handoff: { provider: "stripe", url: result.checkoutUrl } });
      const checkout = await stripe("/checkout/sessions", new URLSearchParams({
        mode: "payment", success_url: `https://www.910cpr.com/register/success/?order=${result.orderId}&session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `https://www.910cpr.com/register/?session=${externalClassId}`,
        customer_email: email, "line_items[0][price_data][currency]": "usd",
        "line_items[0][price_data][product_data][name]": String(session.course_name || "CPR Class"),
        "line_items[0][price_data][unit_amount]": String(result.totalAmountCents), "line_items[0][quantity]": "1",
        "metadata[landerware_order_id]": String(result.orderId), "metadata[external_class_id]": externalClassId,
        expires_at: String(Math.floor(new Date(result.holdExpiresAt).getTime() / 1000)),
      }), `retail-checkout-${result.orderId}`);
      await rest(`landerware_retail_orders?id=eq.${result.orderId}`, "PATCH", { status: "checkout_open", stripe_checkout_session_id: checkout.id, checkout_url: checkout.url, updated_at: new Date().toISOString() });
      await rest("landerware_messages", "POST", { person_id: result.personId, registration_id: result.registrationId, template_key: "retail-checkout-recovery-v1", recipient: email, subject: `Finish registering for ${session.course_name}`, body_text: `Hi ${firstName},\n\nYour seat is held for about 30 minutes. Finish secure payment here:\n${checkout.url}\n\n910CPR\n910-395-5193`, delivery_provider: "gmail", delivery_status: "pending", idempotency_key: `retail-checkout-recovery:${result.orderId}` });
      return reply(origin, { ok: true, firstName, ...result, checkoutUrl: checkout.url, handoff: { provider: "stripe", url: checkout.url } });
    }
    if (request.method === "POST" && route[0] === "stripe-webhook") {
      const raw = await request.text(); if (!await validStripeSignature(raw, request.headers.get("stripe-signature") || "")) return reply(origin, { error: "invalid_signature" }, 400);
      const event = JSON.parse(raw), checkout = event?.data?.object;
      if (event.type === "checkout.session.completed" && checkout?.payment_status === "paid" && checkout?.metadata?.landerware_order_id) await rpc("confirm_retail_payment", { p_order_id: checkout.metadata.landerware_order_id, p_checkout_session_id: checkout.id, p_payment_intent_id: checkout.payment_intent || null, p_evidence: { stripeEventId: event.id, paymentStatus: checkout.payment_status } });
      return reply(origin, { received: true });
    }
    return reply(origin, { error: "not_found" }, 404);
  } catch (error) {
    const message = error instanceof Error ? error.message : "unexpected_error";
    const bad = ["invalid_session", "session_not_open", "invalid_checkout_url", "required_registration_field_missing", "invalid_email", "invalid_phone", "retail_profile_not_found", "retail_price_unavailable", "invalid_retail_option", "session_full", "invalid_signature"].includes(message);
    return reply(origin, { error: message }, bad ? 400 : 500);
  }
});
