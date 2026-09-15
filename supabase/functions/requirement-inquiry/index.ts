import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const ALLOWED_ORIGINS = new Set([
  "https://www.910cpr.com",
  "https://910cpr.com",
  "http://localhost:8000",
  "http://127.0.0.1:8000",
]);
const MAX_BODY_BYTES = 16_384;
const MAX_PER_HOUR = 5;

function corsHeaders(origin: string | null) {
  const allowed = origin && ALLOWED_ORIGINS.has(origin) ? origin : "https://www.910cpr.com";
  return {
    "access-control-allow-origin": allowed,
    "access-control-allow-headers": "content-type",
    "access-control-allow-methods": "POST, OPTIONS",
    "vary": "origin",
  };
}

function json(body: unknown, status: number, origin: string | null) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders(origin), "content-type": "application/json; charset=utf-8" },
  });
}

function clean(value: unknown, max: number) {
  return String(value ?? "").trim().slice(0, max);
}

function validEmail(value: string) {
  return !value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function allowedPageUrl(value: string) {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && (url.hostname === "910cpr.com" || url.hostname === "www.910cpr.com");
  } catch {
    return false;
  }
}

function escapeHtml(value: string) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function sha256(value: string) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function supabaseRequest(path: string, init: RequestInit = {}) {
  const url = Deno.env.get("SUPABASE_URL");
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!url || !serviceKey) throw new Error("database_configuration_missing");
  return fetch(`${url}/rest/v1/${path}`, {
    ...init,
    headers: {
      apikey: serviceKey,
      authorization: `Bearer ${serviceKey}`,
      "content-type": "application/json",
      ...(init.headers || {}),
    },
  });
}

Deno.serve(async (request: Request) => {
  const origin = request.headers.get("origin");
  if (request.method === "OPTIONS") return new Response("ok", { headers: corsHeaders(origin) });
  if (request.method !== "POST") return json({ error: "Method not allowed." }, 405, origin);
  if (!origin || !ALLOWED_ORIGINS.has(origin)) return json({ error: "Origin not allowed." }, 403, origin);

  const contentLength = Number(request.headers.get("content-length") || "0");
  if (contentLength > MAX_BODY_BYTES) return json({ error: "Submission is too large." }, 413, origin);

  let body: Record<string, unknown>;
  try {
    const raw = await request.text();
    if (raw.length > MAX_BODY_BYTES) return json({ error: "Submission is too large." }, 413, origin);
    body = JSON.parse(raw);
  } catch {
    return json({ error: "Invalid submission." }, 400, origin);
  }

  if (clean(body.companyWebsite, 200)) return json({ sent: true }, 200, origin);
  const formElapsedMs = Number(body.formElapsedMs || 0);
  if (!Number.isFinite(formElapsedMs) || formElapsedMs < 1500) {
    return json({ error: "Please wait a moment and try again." }, 400, origin);
  }

  const name = clean(body.name, 120);
  const email = clean(body.email, 254).toLowerCase();
  const phone = clean(body.phone, 40);
  const requirement = String(body.requirement ?? "").slice(0, 5000);
  const pageTitle = clean(body.pageTitle, 240);
  const pageUrl = clean(body.pageUrl, 1000);
  const clientInquiryId = clean(body.clientInquiryId, 100);
  const priorInquiryId = clean(body.inquiryId, 100);
  const registrationId = clean(body.registrationId, 100);
  const selectedCourse = body.selectedCourse && typeof body.selectedCourse === "object"
    ? {
      title: clean((body.selectedCourse as Record<string, unknown>).title, 200),
      href: clean((body.selectedCourse as Record<string, unknown>).href, 500),
    }
    : { title: "", href: "" };

  if (requirement.trim().length < 10) return json({ error: "Please enter the exact requirement." }, 400, origin);
  if (!email && !phone) return json({ error: "Please enter an email or phone." }, 400, origin);
  if (!validEmail(email)) return json({ error: "Please enter a valid email address." }, 400, origin);
  if (!email && phone.replace(/\D/g, "").length < 7) {
    return json({ error: "Please enter a valid phone number." }, 400, origin);
  }
  if (!allowedPageUrl(pageUrl)) return json({ error: "Invalid page URL." }, 400, origin);

  const forwardedFor = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() || "";
  const salt = Deno.env.get("INQUIRY_HASH_SALT") || Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || "";
  const ipHash = await sha256(`${salt}:${forwardedFor}`);
  const since = new Date(Date.now() - 60 * 60 * 1000).toISOString();
  const rateResponse = await supabaseRequest(
    `requirement_inquiries?select=id&ip_hash=eq.${encodeURIComponent(ipHash)}&created_at=gte.${encodeURIComponent(since)}&limit=${MAX_PER_HOUR}`
  );
  if (!rateResponse.ok) {
    console.error("requirement_inquiry_rate_lookup_failed", rateResponse.status);
    return json({ error: "The service is temporarily unavailable. Please try again." }, 503, origin);
  }
  const recent = await rateResponse.json();
  if (Array.isArray(recent) && recent.length >= MAX_PER_HOUR) {
    console.warn("requirement_inquiry_rate_limited", ipHash.slice(0, 12));
    return json({ error: "Too many requests. Please wait and try again." }, 429, origin);
  }

  const submittedAt = new Date().toISOString();
  const insertResponse = await supabaseRequest("requirement_inquiries", {
    method: "POST",
    headers: { prefer: "return=representation" },
    body: JSON.stringify({
      name: name || null,
      email: email || null,
      phone: phone || null,
      requirement_text: requirement,
      selected_course: selectedCourse,
      page_title: pageTitle,
      page_url: pageUrl,
      submitted_at: submittedAt,
      client_inquiry_id: clientInquiryId || null,
      prior_inquiry_id: priorInquiryId || null,
      registration_id: registrationId || null,
      ip_hash: ipHash,
      user_agent: clean(request.headers.get("user-agent"), 500),
      delivery_status: "pending",
    }),
  });
  if (!insertResponse.ok) {
    console.error("requirement_inquiry_insert_failed", insertResponse.status);
    return json({ error: "The service is temporarily unavailable. Please try again." }, 503, origin);
  }
  const inserted = await insertResponse.json();
  const inquiryId = String(inserted?.[0]?.id || "");

  const resendKey = Deno.env.get("RESEND_API_KEY");
  const adminEmail = Deno.env.get("ADMIN_NOTIFY_EMAIL");
  const fromEmail = Deno.env.get("REQUIREMENT_FROM_EMAIL");
  if (!resendKey || !adminEmail || !fromEmail) {
    console.error("requirement_inquiry_email_configuration_missing", inquiryId);
    await supabaseRequest(`requirement_inquiries?id=eq.${encodeURIComponent(inquiryId)}`, {
      method: "PATCH",
      body: JSON.stringify({ delivery_status: "configuration_error" }),
    });
    return json({ error: "Email delivery is not configured. Please try again later." }, 503, origin);
  }

  const courseLabel = selectedCourse.title || "Not selected";
  const text = [
    "A customer submitted exact employer or school wording.",
    "",
    `Name: ${name || "Not provided"}`,
    `Email: ${email || "Not provided"}`,
    `Phone: ${phone || "Not provided"}`,
    `Course: ${courseLabel}`,
    `Course link: ${selectedCourse.href || "Not provided"}`,
    `Page: ${pageTitle}`,
    `URL: ${pageUrl}`,
    `Submitted: ${submittedAt}`,
    `Inquiry ID: ${inquiryId}`,
    `Prior inquiry ID: ${priorInquiryId || "None"}`,
    `Registration ID: ${registrationId || "None"}`,
    "",
    "Exact requirement:",
    requirement,
  ].join("\n");
  const html = `<h2>Employer or school requirement</h2>
    <p><strong>Name:</strong> ${escapeHtml(name || "Not provided")}<br>
    <strong>Email:</strong> ${escapeHtml(email || "Not provided")}<br>
    <strong>Phone:</strong> ${escapeHtml(phone || "Not provided")}<br>
    <strong>Course:</strong> ${escapeHtml(courseLabel)}<br>
    <strong>Page:</strong> ${escapeHtml(pageTitle)}<br>
    <strong>URL:</strong> ${escapeHtml(pageUrl)}<br>
    <strong>Submitted:</strong> ${escapeHtml(submittedAt)}<br>
    <strong>Inquiry ID:</strong> ${escapeHtml(inquiryId)}<br>
    <strong>Prior inquiry ID:</strong> ${escapeHtml(priorInquiryId || "None")}<br>
    <strong>Registration ID:</strong> ${escapeHtml(registrationId || "None")}</p>
    <h3>Exact requirement</h3><pre style="white-space:pre-wrap">${escapeHtml(requirement)}</pre>`;

  const emailResponse = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { authorization: `Bearer ${resendKey}`, "content-type": "application/json" },
    body: JSON.stringify({
      from: fromEmail,
      to: [adminEmail],
      reply_to: email || undefined,
      subject: `Course requirement help${name ? ` — ${name}` : ""}`,
      text,
      html,
    }),
  });
  const emailResult = await emailResponse.json().catch(() => ({}));
  if (!emailResponse.ok || !emailResult.id) {
    console.error("requirement_inquiry_email_failed", inquiryId, emailResponse.status);
    await supabaseRequest(`requirement_inquiries?id=eq.${encodeURIComponent(inquiryId)}`, {
      method: "PATCH",
      body: JSON.stringify({ delivery_status: "failed" }),
    });
    return json({ error: "Email delivery failed. Please try again." }, 502, origin);
  }

  await supabaseRequest(`requirement_inquiries?id=eq.${encodeURIComponent(inquiryId)}`, {
    method: "PATCH",
    body: JSON.stringify({
      delivery_status: "sent",
      delivered_at: new Date().toISOString(),
      provider_message_id: String(emailResult.id).slice(0, 200),
    }),
  });
  console.log("requirement_inquiry_sent", inquiryId);
  return json({ sent: true, inquiryId, sentAt: submittedAt }, 200, origin);
});
