import { createClient } from "https://esm.sh/@supabase/supabase-js@2.56.0";

const enc = new TextEncoder();

function hex(bytes: ArrayBuffer) {
  return Array.from(new Uint8Array(bytes)).map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function safeEqual(a: string, b: string) {
  if (a.length !== b.length) return false;
  let difference = 0;
  for (let index = 0; index < a.length; index += 1) difference |= a.charCodeAt(index) ^ b.charCodeAt(index);
  return difference === 0;
}

async function verify(raw: string, header: string | null, secret: string | null) {
  if (!secret || !header) return false;
  const pieces = Object.fromEntries(header.split(",").map((piece) => piece.split("=", 2) as [string, string]));
  if (!pieces.t || !pieces.v1) return false;
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const signature = hex(await crypto.subtle.sign("HMAC", key, enc.encode(`${pieces.t}.${raw}`)));
  return safeEqual(signature, pieces.v1);
}

const reply = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { "content-type": "application/json", "cache-control": "no-store" },
});

Deno.serve(async (request) => {
  if (request.method !== "POST") return reply({ ok: false }, 405);
  const raw = await request.text();
  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
  const { data: secretRow } = await db.from("landerware_integration_secrets").select("secret_value").eq("secret_key", "stripe_registration_webhook").maybeSingle();
  const webhookSecret = secretRow?.secret_value || Deno.env.get("STRIPE_WEBHOOK_SECRET") || null;
  if (!(await verify(raw, request.headers.get("stripe-signature"), webhookSecret))) return reply({ ok: false, error: "Invalid signature" }, 400);

  let event: any;
  try { event = JSON.parse(raw); } catch { return reply({ ok: false, error: "Invalid JSON" }, 400); }

  const session = event?.data?.object || {};
  const retailOrderId = String(session?.metadata?.landerware_order_id || "").trim();
  const paid = event.type === "checkout.session.completed"
    ? session.payment_status === "paid"
    : event.type === "checkout.session.async_payment_succeeded";

  if (retailOrderId) {
    if (!paid) return reply({ ok: true, ignored: "Retail checkout not paid" });
    const { data, error } = await db.rpc("confirm_retail_payment", {
      p_order_id: retailOrderId,
      p_checkout_session_id: session.id || null,
      p_payment_intent_id: session.payment_intent || null,
      p_evidence: { stripeEventId: event.id, paymentStatus: session.payment_status },
    });
    if (error) return reply({ ok: false, error: "Retail payment reconciliation failed" }, 500);
    return reply({ ok: true, orderId: retailOrderId, status: "paid", result: data });
  }

  const registrationId = String(session.client_reference_id || "").trim();
  if (!registrationId) return reply({ ok: true, ignored: "No registration reference" });
  if (event.type === "checkout.session.async_payment_failed") {
    await db.from("registration_orders").update({ status: "payment_failed", stripe_checkout_session_id: session.id || null, stripe_payment_intent_id: session.payment_intent || null, updated_at: new Date().toISOString() }).eq("registration_id", registrationId);
    return reply({ ok: true, status: "payment_failed" });
  }
  if (!paid) return reply({ ok: true, ignored: "Checkout not paid" });

  const now = new Date().toISOString();
  const { data: order, error: orderError } = await db.from("registration_orders").update({ status: "paid", stripe_checkout_session_id: session.id || null, stripe_payment_intent_id: session.payment_intent || null, paid_at: now, updated_at: now }).eq("registration_id", registrationId).select("id").maybeSingle();
  if (orderError || !order) return reply({ ok: false, error: "Order not found" }, 500);
  await db.from("registrations").update({ status: "registered", updated_at: now }).eq("id", registrationId);
  await db.from("registration_order_items").update({ fulfillment_status: "awaiting_attention", updated_at: now }).eq("order_id", order.id).eq("fulfillment_status", "awaiting_payment");
  return reply({ ok: true, registrationId, orderId: order.id, status: "paid" });
});
