import { createClient } from "https://esm.sh/@supabase/supabase-js@2.56.0";

const allowedOrigins = new Set([
  "https://www.910cpr.com",
  "https://910cpr.com",
  "https://nhso.910cpr.com",
  "https://nhcso.910cpr.com",
]);
const corsFor = (req: Request) => {
  const origin = req.headers.get("origin") || "";
  return {
    "Access-Control-Allow-Origin": allowedOrigins.has(origin) ? origin : "https://www.910cpr.com",
    "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
  };
};
const admin = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
  { auth: { persistSession: false } },
);
const json = (req: Request, body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { ...corsFor(req), "Content-Type": "application/json", "Cache-Control": "no-store" },
});
const clean = (value: unknown) => String(value ?? "").trim();
const sha256 = async (value: string) =>
  Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value))))
    .map((byte) => byte.toString(16).padStart(2, "0")).join("");
const randomToken = () =>
  Array.from(crypto.getRandomValues(new Uint8Array(32))).map((byte) => byte.toString(16).padStart(2, "0")).join("");
const requestIp = (req: Request) =>
  clean(req.headers.get("cf-connecting-ip") || req.headers.get("x-forwarded-for")?.split(",")[0] || "unknown");
const departmentEmail = (value: unknown) => {
  const email = clean(value).toLowerCase();
  return /^[^@\s]+@(nhcgov\.com|910cpr\.com)$/.test(email) ? email : "";
};
const maskEmail = (email: string) => {
  const [local, domain] = email.split("@");
  const shown = local.length <= 2 ? local.slice(0, 1) : local.slice(0, 2);
  return shown + "•••@" + domain;
};
const otpHash = async (email: string, code: string) =>
  sha256(email + "\n" + code + "\n" + (Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") || ""));
function randomFourDigitCode() {
  const values = new Uint32Array(1);
  do crypto.getRandomValues(values); while (values[0] >= 4294960000);
  return String(values[0] % 10000).padStart(4, "0");
}

async function authorizeWorkspaceRequest(req: Request) {
  const authHeader = req.headers.get("authorization") || "";
  const token = authHeader.replace(/^Bearer\s+/i, "").trim();
  if (!token) return { ok: false, reason: "missing_bearer" };

  if (/^[a-f0-9]{64}$/i.test(token)) {
    const tokenSha = await sha256(token);
    const now = new Date().toISOString();
    const { data: session, error } = await admin.from("nhcso_portal_sessions")
      .select("id,email,expires_at,last_seen_at")
      .eq("token_sha256", tokenSha)
      .is("revoked_at", null)
      .gt("expires_at", now)
      .maybeSingle();
    if (error || !session) return { ok: false, reason: "invalid_portal_session" };
    if (!departmentEmail(session.email)) return { ok: false, reason: "session_email_not_allowed" };
    const lastSeen = Date.parse(session.last_seen_at || "1970-01-01");
    if (Date.now() - lastSeen > 60 * 60 * 1000) {
      await admin.from("nhcso_portal_sessions").update({ last_seen_at: now }).eq("id", session.id);
    }
    return {
      ok: true,
      email: session.email,
      user_id: null,
      session_id: session.id,
      session_expires_at: session.expires_at,
      auth_type: "department_code",
      token_sha256: tokenSha,
    };
  }

  let role = "";
  try {
    const payloadPart = token.split(".")[1] || "";
    const normalized = payloadPart.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(normalized.length + ((4 - normalized.length % 4) % 4), "=");
    const claims = JSON.parse(atob(padded));
    role = clean(claims.role);
  } catch {
    return { ok: false, reason: "invalid_token_shape" };
  }
  if (role !== "authenticated") return { ok: false, reason: "anonymous_not_allowed" };

  const { data, error } = await admin.auth.getUser(token);
  const user = data?.user;
  const email = clean(user?.email).toLowerCase();
  if (error || !user || !user.email_confirmed_at) return { ok: false, reason: "unverified_user" };
  if (!(email.endsWith("@nhcgov.com") || email.endsWith("@910cpr.com"))) {
    return { ok: false, reason: "email_not_allowed" };
  }
  return { ok: true, email, user_id: user.id, auth_type: "supabase_jwt", session_expires_at: null };
}

async function deliverLoginCode(email: string, code: string) {
  const resendKey = Deno.env.get("RESEND_API_KEY") || "";
  const from = Deno.env.get("NHSCO_FROM_EMAIL") || Deno.env.get("REQUIREMENT_FROM_EMAIL") || "910CPR <brian@910cpr.com>";
  if (resendKey) {
    const result = await fetch("https://api.resend.com/emails", {
      method: "POST",
      signal: AbortSignal.timeout(12000),
      headers: {
        authorization: `Bearer ${resendKey}`,
        "content-type": "application/json",
        "Idempotency-Key": `nhcso-login/${email}/${Date.now()}`,
      },
      body: JSON.stringify({
        from,
        to: [email],
        subject: "Your NHCSO training portal code",
        text: `Your 910CPR NHCSO training portal code is ${code}.\n\nIt expires in 15 minutes and can be used only for the NHCSO training workspace. If you did not request this code, you can ignore this message. No new code is sent automatically after a failed login attempt.`,
      }),
    });
    const payload = await result.json().catch(() => ({}));
    if (!result.ok || !payload.id) throw new Error(payload.message || `Resend returned ${result.status}`);
    return String(payload.id);
  }

  const workerUrl = Deno.env.get("TRANSACTIONAL_EMAIL_WORKER_URL") || "";
  const workerSecret = Deno.env.get("TRANSACTIONAL_EMAIL_WORKER_SECRET") || "";
  if (workerUrl && workerSecret) {
    const result = await fetch(workerUrl, {
      method: "POST",
      signal: AbortSignal.timeout(12000),
      headers: { authorization: `Bearer ${workerSecret}`, "content-type": "application/json" },
      body: JSON.stringify({
        to: email,
        notificationType: "nhcso_login_code",
        subject: "Your NHCSO training portal code",
        code,
        expiresInMinutes: 15,
        text: `Your 910CPR NHCSO training portal code is ${code}. It expires in 15 minutes.`,
      }),
    });
    const payload = await result.json().catch(() => ({}));
    if (!result.ok) throw new Error(payload.error || `Email worker returned ${result.status}`);
    return clean(payload.messageId) || "transactional-worker";
  }
  throw new Error("Login email delivery is not configured");
}

async function requestLoginCode(req: Request, body: any) {
  const email = departmentEmail(body.email);
  if (!email) return json(req, { error: "Use your authorized @nhcgov.com or @910cpr.com email address." }, 400);
  const now = new Date();
  const nowIso = now.toISOString();
  const minuteAgo = new Date(now.getTime() - 60 * 1000).toISOString();
  const hourAgo = new Date(now.getTime() - 60 * 60 * 1000).toISOString();
  const ipSha = await sha256(requestIp(req));
  const emailSha = await sha256(email);

  const [{ count: recentEmail }, { count: hourlyEmail }, { count: hourlyIp }, { count: failedEmail }] = await Promise.all([
    admin.from("nhcso_login_codes").select("id", { count: "exact", head: true }).eq("email", email).gt("created_at", minuteAgo),
    admin.from("nhcso_login_codes").select("id", { count: "exact", head: true }).eq("email", email).gt("created_at", hourAgo),
    admin.from("nhcso_login_codes").select("id", { count: "exact", head: true }).eq("request_ip_sha256", ipSha).gt("created_at", hourAgo),
    admin.from("nhcso_login_attempts").select("id", { count: "exact", head: true }).eq("email_sha256", emailSha).eq("succeeded", false).gt("attempted_at", hourAgo),
  ]);
  if ((recentEmail || 0) >= 1) return json(req, { error: "A code was already requested. Please wait 60 seconds before requesting another." }, 429);
  if ((hourlyEmail || 0) >= 5) return json(req, { error: "Too many codes were requested for this address. Try again later." }, 429);
  if ((hourlyIp || 0) >= 20) return json(req, { error: "Too many code requests came from this network. Try again later." }, 429);
  if ((failedEmail || 0) >= 10) return json(req, { error: "Too many unsuccessful attempts. Try again later or contact 910CPR." }, 429);

  await admin.from("nhcso_login_codes").update({ consumed_at: nowIso })
    .eq("email", email).is("consumed_at", null);

  const code = randomFourDigitCode();
  const expiresAt = new Date(now.getTime() + 15 * 60 * 1000).toISOString();
  const { data: created, error: insertError } = await admin.from("nhcso_login_codes").insert({
    email,
    code_sha256: await otpHash(email, code),
    request_ip_sha256: ipSha,
    expires_at: expiresAt,
  }).select("id").single();
  if (insertError || !created) throw insertError || new Error("Could not create login code");

  try {
    const messageId = await deliverLoginCode(email, code);
    await admin.from("nhcso_login_codes").update({ delivery_message_id: messageId }).eq("id", created.id);
    console.info("nhcso_login_code_sent", { email_sha256: emailSha.slice(0, 16), ip_sha256: ipSha.slice(0, 16) });
    return json(req, {
      ok: true,
      email: maskEmail(email),
      expires_in_seconds: 900,
      resend_after_seconds: 60,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    await admin.from("nhcso_login_codes").update({
      consumed_at: new Date().toISOString(),
      delivery_error: message.slice(0, 500),
    }).eq("id", created.id);
    console.error("nhcso_login_code_delivery_failed", { error: message });
    return json(req, { error: "Email delivery is temporarily unavailable. Please try again shortly." }, 503);
  }
}

async function verifyLoginCode(req: Request, body: any) {
  const email = departmentEmail(body.email);
  const code = clean(body.code);
  if (!email || !/^\d{4}$/.test(code)) return json(req, { error: "Enter the four-digit code sent to your department email." }, 400);

  const now = new Date();
  const nowIso = now.toISOString();
  const hourAgo = new Date(now.getTime() - 60 * 60 * 1000).toISOString();
  const ipSha = await sha256(requestIp(req));
  const emailSha = await sha256(email);
  const [{ count: emailFailures }, { count: ipFailures }] = await Promise.all([
    admin.from("nhcso_login_attempts").select("id", { count: "exact", head: true }).eq("email_sha256", emailSha).eq("succeeded", false).gt("attempted_at", hourAgo),
    admin.from("nhcso_login_attempts").select("id", { count: "exact", head: true }).eq("ip_sha256", ipSha).eq("succeeded", false).gt("attempted_at", hourAgo),
  ]);
  if ((emailFailures || 0) >= 10 || (ipFailures || 0) >= 20) {
    return json(req, { error: "Too many unsuccessful attempts. Try again later or request help from 910CPR." }, 429);
  }

  const { data: codeRow, error: lookupError } = await admin.from("nhcso_login_codes")
    .select("id,code_sha256,attempt_count,expires_at")
    .eq("email", email)
    .is("consumed_at", null)
    .gt("expires_at", nowIso)
    .order("created_at", { ascending: false })
    .limit(1)
    .maybeSingle();
  if (lookupError) throw lookupError;
  if (!codeRow) return json(req, { error: "That code is expired or no longer active. Request a new code." }, 400);
  if (Number(codeRow.attempt_count || 0) >= 5) {
    await admin.from("nhcso_login_codes").update({ consumed_at: nowIso }).eq("id", codeRow.id).is("consumed_at", null);
    return json(req, { error: "That code has been locked. Request a new code." }, 429);
  }

  const matches = (await otpHash(email, code)) === codeRow.code_sha256;
  if (!matches) {
    const nextAttempt = Number(codeRow.attempt_count || 0) + 1;
    const update: Record<string, unknown> = { attempt_count: nextAttempt };
    if (nextAttempt >= 5) update.consumed_at = nowIso;
    await admin.from("nhcso_login_codes").update(update)
      .eq("id", codeRow.id).eq("attempt_count", codeRow.attempt_count).is("consumed_at", null);
    await admin.from("nhcso_login_attempts").insert({ email_sha256: emailSha, ip_sha256: ipSha, succeeded: false });
    return json(req, {
      error: nextAttempt >= 5
        ? "That code has been locked after too many attempts. Request a new code."
        : "That code did not match. No new email was sent.",
      attempts_remaining: Math.max(0, 5 - nextAttempt),
    }, 401);
  }

  const { data: consumed } = await admin.from("nhcso_login_codes").update({ consumed_at: nowIso })
    .eq("id", codeRow.id).eq("attempt_count", codeRow.attempt_count).is("consumed_at", null)
    .select("id").maybeSingle();
  if (!consumed) return json(req, { error: "That code was already used. Request a new code." }, 409);

  await admin.from("nhcso_login_attempts").insert({ email_sha256: emailSha, ip_sha256: ipSha, succeeded: true });
  const token = randomToken();
  const expiresAt = new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000).toISOString();
  const userAgent = clean(req.headers.get("user-agent"));
  const { error: sessionError } = await admin.from("nhcso_portal_sessions").insert({
    token_sha256: await sha256(token),
    email,
    expires_at: expiresAt,
    created_ip_sha256: ipSha,
    user_agent_sha256: userAgent ? await sha256(userAgent) : null,
  });
  if (sessionError) throw sessionError;
  console.info("nhcso_login_verified", { email_sha256: emailSha.slice(0, 16), ip_sha256: ipSha.slice(0, 16) });
  return json(req, { ok: true, token, email, expires_at: expiresAt, expires_in_seconds: 2592000 });
}

async function revokeWorkspaceSession(req: Request) {
  const token = (req.headers.get("authorization") || "").replace(/^Bearer\s+/i, "").trim();
  if (!/^[a-f0-9]{64}$/i.test(token)) return;
  await admin.from("nhcso_portal_sessions").update({ revoked_at: new Date().toISOString() })
    .eq("token_sha256", await sha256(token)).is("revoked_at", null);
}

async function studentKey(name: string, email: string) {
  const bytes = new TextEncoder().encode((email || name).trim().toLowerCase());
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest)).map((byte) => byte.toString(16).padStart(2, "0")).join("").slice(0, 24);
}

async function dispatchNotifications(classSessionId: string) {
  const workerUrl = Deno.env.get("TRANSACTIONAL_EMAIL_WORKER_URL") || "";
  const workerSecret = Deno.env.get("TRANSACTIONAL_EMAIL_WORKER_SECRET") || "";
  const { data: pending, error } = await admin.from("transactional_email_outbox").select("*")
    .eq("class_session_id", classSessionId).in("status", ["pending", "failed"]).order("created_at");
  if (error) throw error;
  const results = [];
  for (const item of pending || []) {
    if (!workerUrl || !workerSecret) {
      const message = "Transactional email delivery is not configured";
      await admin.from("transactional_email_outbox").update({
        status: "failed", attempt_count: item.attempt_count + 1, last_error: message, updated_at: new Date().toISOString(),
      }).eq("id", item.id);
      console.error("notification delivery", { id: item.id, error: message });
      results.push({ id: item.id, ok: false, error: message });
      continue;
    }
    try {
      await admin.from("transactional_email_outbox").update({ status: "sending", updated_at: new Date().toISOString() }).eq("id", item.id);
      const mailResponse = await fetch(workerUrl, {
        method: "POST",
        headers: { authorization: `Bearer ${workerSecret}`, "content-type": "application/json" },
        body: JSON.stringify({
          to: item.recipient_email,
          notificationType: item.notification_type,
          subject: item.notification_type === "submitter_confirmation" ? "910CPR received your NHCSO class" : "NHCSO class ready for card review",
          ...item.payload,
        }),
      });
      const mailResult = await mailResponse.json().catch(() => ({}));
      if (!mailResponse.ok) throw new Error(mailResult.error || `Email worker returned ${mailResponse.status}`);
      await admin.from("transactional_email_outbox").update({ status: "sent", attempt_count: item.attempt_count + 1, last_error: null, message_id: mailResult.messageId || null, sent_at: new Date().toISOString(), updated_at: new Date().toISOString() }).eq("id", item.id);
      results.push({ id: item.id, ok: true, message_id: mailResult.messageId || null });
    } catch (dispatchError) {
      const message = dispatchError instanceof Error ? dispatchError.message : String(dispatchError);
      await admin.from("transactional_email_outbox").update({ status: "failed", attempt_count: item.attempt_count + 1, last_error: message, updated_at: new Date().toISOString() }).eq("id", item.id);
      console.error("notification delivery", { id: item.id, error: message });
      results.push({ id: item.id, ok: false, error: message });
    }
  }
  return results;
}


function structuredCardRows(notes: string) {
  const rows: Array<{ card: string; first: string; last: string; email: string }> = [];
  for (const rawLine of String(notes || "").split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) continue;
    const parts = rawLine.split("\t").map((part) => clean(part));
    const card = parts[0] || "";
    const email = parts.find((part) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(part))?.toLowerCase() || "";
    if (!/^\d{10,14}$/.test(card) || !email) continue;
    rows.push({ card, first: parts[2] || "", last: parts[3] || "", email });
  }
  return rows;
}

async function ensureCustomerFact(row: { card: string; first: string; last: string; email: string }, classNumber: string) {
  let { data: customer, error: customerLookupError } = await admin.from("customers")
    .select("id,first_name,last_name,email").ilike("email", row.email).limit(1).maybeSingle();
  if (customerLookupError) throw customerLookupError;
  if (!customer) {
    const { data: created, error: createError } = await admin.from("customers").insert({
      first_name: row.first || row.email.split("@")[0],
      last_name: row.last || "",
      email: row.email,
    }).select("id,first_name,last_name,email").single();
    if (createError) throw createError;
    customer = created;
  }
  const nowIso = new Date().toISOString();
  const { error: factError } = await admin.from("customer_profile_facts").upsert({
    customer_id: customer.id,
    fact_type: "aha_ecard_number",
    fact_value: row.card,
    normalized_value: row.card,
    source_type: "nhcso_class_note",
    source_ref: classNumber,
    confidence: 1,
    observed_at: nowIso,
    updated_at: nowIso,
  }, { onConflict: "customer_id,fact_type,normalized_value" });
  if (factError) throw factError;
  return customer.id;
}

async function processStructuredClassNotes(classNumber: string) {
  const { data: classRow, error: classError } = await admin.from("nhcso_classes")
    .select("class_number,notes,class_session_id").eq("class_number", classNumber).maybeSingle();
  if (classError) throw classError;
  if (!classRow) return { processed: 0, matched: 0, person_facts: 0 };
  const rows = structuredCardRows(clean(classRow.notes));
  if (!rows.length) return { processed: 0, matched: 0, person_facts: 0 };

  let matched = 0;
  let personFacts = 0;
  for (const row of rows) {
    const { data: student, error: studentError } = await admin.from("nhcso_students")
      .select("id,name,email,ecard_number").eq("class_number", classNumber)
      .ilike("email", row.email).limit(1).maybeSingle();
    if (studentError) throw studentError;
    if (!student) continue;

    if (clean(student.ecard_number) !== row.card) {
      const { error: updateError } = await admin.from("nhcso_students")
        .update({ ecard_number: row.card, updated_at: new Date().toISOString() }).eq("id", student.id);
      if (updateError) throw updateError;
    }
    matched++;
    await ensureCustomerFact(row, classNumber);
    personFacts++;
  }
  if (matched) {
    console.info("nhcso_structured_notes_processed", { class_number: classNumber, rows: rows.length, matched, person_facts: personFacts });
  }
  return { processed: rows.length, matched, person_facts: personFacts };
}

function easternDateString() {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit",
  }).formatToParts(new Date());
  const get = (type: string) => parts.find((part) => part.type === type)?.value || "";
  return `${get("year")}-${get("month")}-${get("day")}`;
}

async function settleClassIfComplete(classNumber: string) {
  const { data: classRow, error: classError } = await admin.from("nhcso_classes")
    .select("class_number,class_date,status,class_session_id").eq("class_number", classNumber).maybeSingle();
  if (classError) throw classError;
  if (!classRow || classRow.status === "finalized" || !classRow.class_date || classRow.class_date >= easternDateString()) return classRow;

  const [{ data: activeStudents, error: studentError }, { count: paperworkCount, error: paperworkError }] = await Promise.all([
    admin.from("nhcso_students").select("id,ecard_number").eq("class_number", classNumber).eq("status", "Active"),
    admin.from("nhcso_documents").select("*", { count: "exact", head: true }).eq("class_number", classNumber),
  ]);
  if (studentError) throw studentError;
  if (paperworkError) throw paperworkError;
  const students = activeStudents || [];
  const cardsIssued = students.length > 0 && students.every((student) => !!clean(student.ecard_number));
  if (!cardsIssued || !(paperworkCount || 0)) return classRow;

  const nowIso = new Date().toISOString();
  const { data: finalized, error: updateError } = await admin.from("nhcso_classes")
    .update({ status: "finalized", updated_at: nowIso })
    .eq("class_number", classNumber).neq("status", "finalized")
    .select("class_number,class_date,status,class_session_id").maybeSingle();
  if (updateError) throw updateError;

  const settled = finalized || { ...classRow, status: "finalized" };
  if (settled.class_session_id) {
    await admin.from("class_sessions").update({ status: "completed", updated_at: nowIso })
      .eq("id", settled.class_session_id).in("status", ["scheduled", "active"]);
    await admin.from("class_session_audit").insert({
      class_session_id: settled.class_session_id,
      event_key: `nhcso:auto-finalized:${classNumber}`,
      event_type: "auto_finalized",
      actor_label: "NHCSO workspace",
      occurred_at: nowIso,
      details: {
        reason: "past_class_with_paperwork_and_all_active_cards_issued",
        class_number: classNumber,
      },
    }).catch(() => null);
  }
  return settled;
}

async function settleEligibleClasses() {
  const today = easternDateString();
  const { data: candidates, error } = await admin.from("nhcso_classes")
    .select("class_number").neq("status", "finalized").lt("class_date", today).limit(250);
  if (error) throw error;
  for (const row of candidates || []) await settleClassIfComplete(row.class_number);
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: corsFor(req) });
  if (req.method !== "POST") return json(req, { error: "POST required" }, 405);
  const authContentType = req.headers.get("content-type") || "";
  if (!authContentType.includes("multipart/form-data")) {
    const publicBody = await req.clone().json().catch(() => ({}));
    const publicAction = clean(publicBody.action);
    try {
      if (publicAction === "request_code") return await requestLoginCode(req, publicBody);
      if (publicAction === "verify_code") return await verifyLoginCode(req, publicBody);
    } catch (error) {
      console.error("nhcso_public_auth_error", error);
      return json(req, { error: "The login service is temporarily unavailable." }, 500);
    }
  }
  const access = await authorizeWorkspaceRequest(req);
  if (!access.ok) {
    console.warn("nhcso workspace access denied", { reason: access.reason });
    return json(req, { error: "Authorized agency access is required" }, 403);
  }
  try {
    const contentType = req.headers.get("content-type") || "";
    if (contentType.includes("multipart/form-data")) {
      const form = await req.formData();
      if (clean(form.get("action")) !== "upload_document") return json(req, { error: "Unsupported multipart action" }, 400);
      const classNumber = clean(form.get("class_number"));
      const documentType = clean(form.get("document_type")) || "course_completion";
      const file = form.get("file");
      if (!classNumber || !(file instanceof File) || !file.size) return json(req, { error: "class_number and file are required" }, 400);
      if (file.size > 15 * 1024 * 1024) return json(req, { error: "File exceeds 15 MB limit" }, 400);
      const { data: exists } = await admin.from("nhcso_classes").select("class_number,status").eq("class_number", classNumber).maybeSingle();
      if (!exists) return json(req, { error: "Save the class before uploading paperwork" }, 400);
      if (exists.status === "finalized") return json(req, { error: "Finalized classes are locked; paperwork cannot be changed" }, 409);
      const safe = file.name.replace(/[^a-zA-Z0-9._-]+/g, "_");
      const path = `${classNumber}/${documentType}/${Date.now()}-${safe}`;
      const { error: uploadError } = await admin.storage.from("nhcso-class-docs").upload(path, file, {
        contentType: file.type || "application/octet-stream",
        upsert: false,
      });
      if (uploadError) throw uploadError;
      const { data, error } = await admin.from("nhcso_documents").insert({
        class_number: classNumber,
        document_type: documentType,
        file_name: file.name,
        storage_path: path,
        content_type: file.type || null,
        file_size: file.size,
      }).select().single();
      if (error) throw error;
      return json(req, { ok: true, document: data });
    }

    const body = await req.json();
    const action = clean(body.action);
    if (action === "session_status") {
      return json(req, {
        ok: true,
        email: access.email,
        auth_type: access.auth_type,
        expires_at: access.session_expires_at || null,
      });
    }
    if (action === "logout") {
      await revokeWorkspaceSession(req);
      return json(req, { ok: true });
    }
    if (action === "save_class") {
      const c = body.class || {};
      const course = clean(c.course);
      const classDate = clean(c.class_date || c.date);
      const startTime = clean(c.start_time || c.time);
      const client = clean(body.client || c.client) || "NHCSO";
      if (!course || !classDate || !startTime) return json(req, { error: "course, class_date, and start_time are required" }, 400);
      let classNumber = clean(c.class_number);
      if (!classNumber) classNumber = `NHSO-${classDate.replaceAll("-", "")}-${startTime.replace(":", "")}-${crypto.randomUUID().slice(0, 6).toUpperCase()}`;
      const { data: existingClass } = await admin.from("nhcso_classes").select("status,class_session_id").eq("class_number", classNumber).maybeSingle();
      const finalizedLocalOverride = existingClass?.status === "finalized" &&
        body.finalized_local_override === true && body.finalized_warning_accepted === true;
      if (existingClass?.status === "finalized" && !finalizedLocalOverride) {
        return json(req, { error: "This class is FINALIZED and locked. Official corrections must be directed to the Training Site at Brian@910cpr.com. Use the explicit local-record edit control only for a documented LanderWare correction." }, 409);
      }
      const classRow = {
        class_number: classNumber,
        course,
        class_date: classDate,
        start_time: startTime,
        location: clean(c.location) || null,
        lead_instructor: clean(c.lead_instructor || c.lead) || null,
        assistant_instructors: clean(c.assistant_instructors || c.assistants) || null,
        notes: clean(c.notes) || null,
        status: existingClass?.status === "finalized" ? "finalized" : (clean(c.status) || "scheduled"),
        updated_at: new Date().toISOString(),
      };
      const { error: classError } = await admin.from("nhcso_classes").upsert(classRow, { onConflict: "class_number" });
      if (classError) throw classError;
      const { data: existingStudents, error: existingError } = await admin.from("nhcso_students")
        .select("student_key,name,email").eq("class_number", classNumber);
      if (existingError) throw existingError;
      const existingByIdentity = new Map<string, string>();
      for (const student of existingStudents || []) {
        const email = clean(student.email).toLowerCase();
        const name = clean(student.name).toLowerCase().replace(/\s+/g, " ");
        existingByIdentity.set(email ? `email:${email}` : `name:${name}`, student.student_key);
      }
      const stagedRows = new Map<string, Record<string, unknown>>();
      for (const raw of Array.isArray(body.students) ? body.students : []) {
        const name = clean(raw.name);
        const email = clean(raw.email).toLowerCase();
        if (!name && !email) continue;
        const identity = email ? `email:${email}` : `name:${name.toLowerCase().replace(/\s+/g, " ")}`;
        const canonicalKey = existingByIdentity.get(identity) || clean(raw.student_key) || await studentKey(name, email);
        stagedRows.set(identity, {
          class_number: classNumber,
          student_key: canonicalKey,
          client: clean(raw.client) || client,
          name: name || email,
          email: email || null,
          status: clean(raw.status) || "Active",
          score_or_certificate: clean(raw.score_or_certificate || raw.score || raw.certificate_number) || null,
          ecard_number: clean(raw.ecard_number || raw.card) || null,
          updated_at: new Date().toISOString(),
        });
      }
      const rows = [...stagedRows.values()];
      if (rows.length) {
        const { error } = await admin.from("nhcso_students").upsert(rows, { onConflict: "class_number,student_key" });
        if (error) throw error;
      }
      await processStructuredClassNotes(classNumber);
      const { data: savedStudents, error } = await admin.from("nhcso_students").select("*").eq("class_number", classNumber).order("created_at");
      if (error) throw error;
      if (finalizedLocalOverride && existingClass?.class_session_id) {
        const nowIso = new Date().toISOString();
        await admin.from("class_session_audit").insert({
          class_session_id: existingClass.class_session_id,
          event_key: `nhcso:local-finalized-correction:${classNumber}:${Date.now()}`,
          event_type: "local_finalized_correction",
          actor_label: access.email || "NHCSO workspace user",
          occurred_at: nowIso,
          details: {
            class_number: classNumber,
            warning_acknowledged: true,
            official_record_unchanged: true,
            training_site_contact: "Brian@910cpr.com",
          },
        }).catch(() => null);
      }
      return json(req, {
        ok: true,
        class_number: classNumber,
        student_records: savedStudents || [],
        finalized_local_override: finalizedLocalOverride,
        warning: finalizedLocalOverride
          ? "Local LanderWare record updated. Issued cards and official Training Site records were not changed."
          : null,
      });
    }
    if (action === "correct_finalized_student") {
      const classNumber = clean(body.class_number);
      const studentKeyValue = clean(body.student_key);
      const name = clean(body.name);
      const email = clean(body.email).toLowerCase();
      if (!classNumber || !studentKeyValue || (!name && !email) || body.certifying_body_warning_accepted !== true) return json(req, { error: "Class, participant, corrected identity, and warning acceptance are required" }, 400);
      const { data: classRow } = await admin.from("nhcso_classes").select("status").eq("class_number", classNumber).maybeSingle();
      if (classRow?.status !== "finalized") return json(req, { error: "This correction route is only for finalized classes" }, 409);
      const { data: existingStudent, error: lookupError } = await admin.from("nhcso_students").select("student_key").eq("class_number", classNumber).eq("student_key", studentKeyValue).single();
      if (lookupError || !existingStudent) return json(req, { error: "Participant not found" }, 404);
      const { data: corrected, error: correctionError } = await admin.from("nhcso_students").update({ name: name || email, email: email || null, updated_at: new Date().toISOString() }).eq("class_number", classNumber).eq("student_key", studentKeyValue).select().single();
      if (correctionError) throw correctionError;
      return json(req, { ok: true, student: corrected, warning: "Certifying-body credential records are unchanged" });
    }
    if (action === "finalize_class") {
      const classNumber = clean(body.class_number);
      if (!classNumber || clean(body.confirm_class_number) !== classNumber) return json(req, { error: "Exact class-number confirmation is required" }, 400);
      const { data: classRow, error: classError } = await admin.from("nhcso_classes").select("*").eq("class_number", classNumber).single();
      if (classError || !classRow) return json(req, { error: "Class not found" }, 404);
      const { data: students, error: studentError } = await admin.from("nhcso_students").select("*").eq("class_number", classNumber).order("created_at");
      if (studentError) throw studentError;
      if (!(students || []).some((student) => clean(student.status || "Active") === "Active")) return json(req, { error: "A class cannot be finalized without active students" }, 409);
      const activeStudents = (students || []).filter((student) => clean(student.status || "Active") === "Active");
      if (activeStudents.some((student) => !clean(student.ecard_number))) return json(req, { error: "Record an issued eCard number for every active participant before finalizing" }, 409);
      const { count: paperworkCount, error: paperworkError } = await admin.from("nhcso_documents").select("*", { count: "exact", head: true }).eq("class_number", classNumber);
      if (paperworkError) throw paperworkError;
      if (!(paperworkCount || 0)) return json(req, { error: "Upload class paperwork before finalizing" }, 409);
      if (classRow.status !== "finalized") {
        const { error: updateError } = await admin.from("nhcso_classes").update({ status: "finalized", updated_at: new Date().toISOString() }).eq("class_number", classNumber).neq("status", "finalized");
        if (updateError) throw updateError;
      }
      const { data: finalizedClass, error: reloadError } = await admin.from("nhcso_classes").select("*").eq("class_number", classNumber).single();
      if (reloadError) throw reloadError;
      if (finalizedClass.class_session_id) {
        await admin.from("class_sessions").update({ status: "completed", updated_at: new Date().toISOString() })
          .eq("id", finalizedClass.class_session_id).in("status", ["scheduled", "active"]);
      }
      return json(req, { ok: true, class: finalizedClass, students: students || [] });
    }
    if (action === "get_class") {
      const classNumber = clean(body.class_number);
      await processStructuredClassNotes(classNumber);
      await settleClassIfComplete(classNumber);
      const [{ data: classRow, error: classError }, { data: students, error: studentError }, { data: documents, error: docError }] = await Promise.all([
        admin.from("nhcso_classes").select("*").eq("class_number", classNumber).single(),
        admin.from("nhcso_students").select("*").eq("class_number", classNumber).order("created_at"),
        admin.from("nhcso_documents").select("id,class_number,document_type,file_name,content_type,file_size,created_at").eq("class_number", classNumber).order("created_at", { ascending: false }),
      ]);
      if (classError) throw classError;
      if (studentError) throw studentError;
      if (docError) throw docError;
      let durable = null;
      if (classRow.class_session_id) {
        const [{ data: session }, { data: instructors }, { data: requirements }, { data: cardProcessing }] = await Promise.all([
          admin.from("class_sessions").select("id,status,external_class_id,start_at,end_at,registration_status,public_notes").eq("id", classRow.class_session_id).single(),
          admin.from("class_session_instructors").select("role,source,instructor:people(id,person_key,display_name,email)").eq("class_session_id", classRow.class_session_id),
          admin.from("class_session_requirements").select("requirement_key,status,evidence_document_id,verified_at,notes").eq("class_session_id", classRow.class_session_id).order("requirement_key"),
          admin.from("session_card_processing").select("status,cards_required,cards_issued,missing_requirements,reviewed_at").eq("class_session_id", classRow.class_session_id).maybeSingle(),
        ]);
        durable = { session, instructors: instructors || [], requirements: requirements || [], card_processing: cardProcessing };
      }
      return json(req, { ok: true, class: classRow, students: students || [], documents: documents || [], durable });
    }
    if (action === "list_instructors") {
      const { data, error } = await admin.from("instructor_qualifications")
        .select("status,instructor:people(id,person_key,display_name,email,active)")
        .eq("qualification_key", "NHCSO_CADRE").eq("status", "active");
      if (error) throw error;
      const instructors = (data || []).map((row) => row.instructor).filter((person) => person?.active)
        .sort((a, b) => a.display_name.localeCompare(b.display_name));
      return json(req, { ok: true, instructors });
    }
    if (action === "dispatch_notifications") {
      const classSessionId = clean(body.class_session_id);
      if (!classSessionId) return json(req, { error: "class_session_id is required" }, 400);
      const results = await dispatchNotifications(classSessionId);
      return json(req, { ok: true, committed_class_preserved: true, results });
    }
    if (action === "get_document_link") {
      const documentId = clean(body.document_id);
      const classNumber = clean(body.class_number);
      const { data: document, error } = await admin.from("nhcso_documents").select("id,class_number,file_name,storage_path").eq("id", documentId).eq("class_number", classNumber).single();
      if (error || !document) return json(req, { error: "Document not found" }, 404);
      const { data: signed, error: signedError } = await admin.storage.from("nhcso-class-docs").createSignedUrl(document.storage_path, 300, { download: document.file_name });
      if (signedError) throw signedError;
      return json(req, { ok: true, document_id: document.id, file_name: document.file_name, signed_url: signed.signedUrl, expires_in: 300 });
    }
    if (action === "delete_document") {
      const documentId = clean(body.document_id);
      const classNumber = clean(body.class_number);
      if (!documentId || !classNumber) return json(req, { error: "document_id and class_number are required" }, 400);
      const { data: classRow } = await admin.from("nhcso_classes").select("status").eq("class_number", classNumber).maybeSingle();
      if (classRow?.status === "finalized") return json(req, { error: "Finalized classes are locked; documents cannot be deleted" }, 409);
      const { data: document, error: lookupError } = await admin.from("nhcso_documents")
        .select("id,class_number,file_name,storage_path").eq("id", documentId).eq("class_number", classNumber).single();
      if (lookupError || !document) return json(req, { error: "Document not found" }, 404);
      const { error: storageError } = await admin.storage.from("nhcso-class-docs").remove([document.storage_path]);
      if (storageError) throw storageError;
      const { error: deleteError } = await admin.from("nhcso_documents").delete().eq("id", document.id).eq("class_number", classNumber);
      if (deleteError) throw deleteError;
      return json(req, { ok: true, document_id: document.id, file_name: document.file_name });
    }
    if (action === "list_classes") {
      await settleEligibleClasses();
      const { data, error } = await admin.from("nhcso_classes")
        .select("class_number,course,class_date,start_time,location,lead_instructor,status,updated_at")
        .order("class_date", { ascending: false }).order("start_time", { ascending: false }).limit(250);
      if (error) throw error;
      const classes = data || [];
      const classNumbers = classes.map((row) => clean(row.class_number)).filter(Boolean);
      if (!classNumbers.length) return json(req, { ok: true, classes });

      const [{ data: students, error: studentError }, { data: documents, error: documentError }] = await Promise.all([
        admin.from("nhcso_students").select("class_number,status,ecard_number").in("class_number", classNumbers).limit(10000),
        admin.from("nhcso_documents").select("class_number").in("class_number", classNumbers).limit(10000),
      ]);
      if (studentError) throw studentError;
      if (documentError) throw documentError;

      const summary = new Map<string, { active_count: number; inactive_count: number; ecard_count: number; document_count: number }>();
      for (const classNumber of classNumbers) summary.set(classNumber, { active_count: 0, inactive_count: 0, ecard_count: 0, document_count: 0 });
      for (const student of students || []) {
        const classNumber = clean(student.class_number);
        const bucket = summary.get(classNumber);
        if (!bucket) continue;
        if (clean(student.status || "Active") === "Active") {
          bucket.active_count++;
          if (clean(student.ecard_number)) bucket.ecard_count++;
        } else {
          bucket.inactive_count++;
        }
      }
      for (const document of documents || []) {
        const bucket = summary.get(clean(document.class_number));
        if (bucket) bucket.document_count++;
      }

      return json(req, {
        ok: true,
        classes: classes.map((row) => ({ ...row, ...(summary.get(clean(row.class_number)) || { active_count: 0, inactive_count: 0, ecard_count: 0, document_count: 0 }) })),
      });
    }
    if (action === "delete_class") {
      const classNumber = clean(body.class_number);
      const { data: classRow } = await admin.from("nhcso_classes").select("status").eq("class_number", classNumber).maybeSingle();
      if (classRow?.status === "finalized") return json(req, { error: "Finalized classes cannot be deleted" }, 409);
      const { count, error: countError } = await admin.from("nhcso_students").select("*", { count: "exact", head: true }).eq("class_number", classNumber).eq("status", "Active");
      if (countError) throw countError;
      if ((count || 0) > 0) return json(req, { error: "Clear all active participants before deleting the class" }, 409);
      const { error } = await admin.from("nhcso_classes").delete().eq("class_number", classNumber);
      if (error) throw error;
      return json(req, { ok: true });
    }
    return json(req, { error: "Unsupported action" }, 400);
  } catch (error) {
    console.error(error);
    return json(req, { error: error instanceof Error ? error.message : String(error) }, 500);
  }
});
