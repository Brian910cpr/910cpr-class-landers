const DEFAULT_CONFIG = {
  creationEnabled: false,
  dryRun: true,
  allowPublicCreation: false,
  backToScheduleUrl: "https://910cpr.com/bls.html",
  lockTtlSeconds: 600,
  visitorCreationWindowSeconds: 3600,
  maxCreationsPerVisitorPerWindow: 1,
  maxChecksPerVisitorPerDay: 3,
  maxWorkerCreatedClassesPerDay: 5,
};

export default {
  async fetch(request, env, ctx) {
    try {
      return await handleRequest(request, env, ctx);
    } catch (error) {
      console.error(JSON.stringify({ event: "worker_error", message: error && error.message }));
      return failurePage("Something went wrong", "We could not verify that time. Please return to the BLS schedule and choose another option.", 500);
    }
  },
};

async function handleRequest(request, env, ctx) {
  const url = new URL(request.url);
  if (request.method === "GET" && url.pathname.startsWith("/o/")) {
    return handleOfferSlug(request, env);
  }
  if (request.method === "GET" && url.pathname === "/check-time") {
    return handleCheckTime(request, env);
  }
  if (request.method === "POST" && url.pathname === "/open-registration") {
    return handleOpenRegistration(request, env, ctx);
  }
  return failurePage("Offer not found", "That requestable time could not be found.", 404);
}

async function handleOfferSlug(request, env) {
  const validation = await validateOfferFromRequest(request, env);
  if (!validation.ok) {
    return failurePage("Offer expired or not found", validation.reason, 404);
  }

  const recheck = await clickTimeRecheck(validation.offer, env);
  if (!recheck.available) {
    return failurePage("Time no longer available", recheck.reason || "That time is no longer available.", 409);
  }

  return htmlPage(
    "This time looks available",
    `<p>This time looks available. Continue to open registration?</p>
     ${offerSummaryHtml(validation.offer)}
     <form method="post" action="/open-registration">
       <input type="hidden" name="offer_slug" value="${escapeHtml(validation.offer.offer_slug)}">
       <button type="submit">Continue to Registration</button>
     </form>`
  );
}

async function handleCheckTime(request, env) {
  const validation = await validateOfferFromRequest(request, env);
  if (!validation.ok) {
    return failurePage("Offer expired or not found", validation.reason, 404);
  }

  const recheck = await clickTimeRecheck(validation.offer, env);
  if (!recheck.available) {
    return failurePage("Time no longer available", recheck.reason || "That time is no longer available.", 409);
  }

  return htmlPage(
    "This time looks available",
    `<p>This time looks available. Continue to open registration?</p>
     ${offerSummaryHtml(validation.offer)}
     <form method="post" action="/open-registration">
       <input type="hidden" name="token" value="${escapeHtml(validation.token)}">
       <button type="submit">Continue to Registration</button>
     </form>`
  );
}

async function handleOpenRegistration(request, env, ctx) {
  const validation = await validateOfferFromRequest(request, env);
  if (!validation.ok) {
    return failurePage("Offer expired or not found", validation.reason, 404);
  }

  const offer = validation.offer;
  const visitorKey = visitorFingerprint(request);
  const checkLimit = await checkVisitorRateLimit(env, visitorKey);
  if (!checkLimit.allowed) {
    return failurePage("Too many checks", "Please wait before checking another requestable time.", 429);
  }

  const lock = await acquireOfferLock(env, offer);
  if (!lock.acquired) {
    return failurePage("Time currently being checked", "Another request is checking this time. Please try again in a few minutes.", 409);
  }

  try {
    const recheck = await clickTimeRecheck(offer, env);
    if (!recheck.available) {
      return failurePage("Time no longer available", recheck.reason || "That time is no longer available.", 409);
    }

    const config = workerConfig(env);
    if (!config.creationEnabled || config.dryRun || !config.allowPublicCreation) {
      await writeAuditLog(env, {
        action: "creation_blocked_dry_run",
        source: "worker_click_time_creation",
        course_key: offer.course_key,
        start: offer.requested_start,
        location_name: offer.location_name,
      });
      return failurePage("Enrollware creation not wired", "This is a dry-run scaffold. No class was created and no Enrollware write occurred.", 501);
    }

    const dailyCap = await checkSystemDailyCreationCap(env);
    if (!dailyCap.allowed) {
      return failurePage("Daily creation cap reached", "Registration cannot be opened automatically right now. Please choose another option.", 429);
    }

    const creation = await createEnrollwareClass(offer, env);
    if (!creation.ok) {
      await writeAuditLog(env, {
        action: "creation_failed",
        source: "worker_click_time_creation",
        course_key: offer.course_key,
        start: offer.requested_start,
        reason: creation.reason,
      });
      if (creation.reason === "not_wired") {
        return failurePage("Enrollware creation not wired", "Enrollware creation is not wired. No class was created and no Enrollware write occurred.", 501);
      }
      return failurePage("Enrollware creation failed", "Registration could not be opened for this time. Please return to the schedule.", 502);
    }

    await writeHotSyncRecord(env, {
      source: "worker_click_time_creation",
      status: "created_pending_enrollment",
      course_key: offer.course_key,
      course_display_name: offer.course_display_name,
      start: offer.requested_start,
      end: offer.requested_end,
      location_name: offer.location_name,
      instructor: offer.instructor || "Brian",
      enrollware_class_id: creation.enrollware_class_id,
      enrollware_enroll_url: creation.enrollware_enroll_url,
      created_at: new Date().toISOString(),
      needs_class_report_absorption: true,
    });

    ctx.waitUntil(writeAuditLog(env, {
      action: "created_pending_enrollment",
      source: "worker_click_time_creation",
      course_key: offer.course_key,
      start: offer.requested_start,
      enrollware_class_id: creation.enrollware_class_id,
    }));

    if (!creation.enrollware_enroll_url) {
      return failurePage("Booking URL created but redirect failed", "The class was created, but the booking URL was not returned. Please contact 910CPR.", 502);
    }
    return Response.redirect(creation.enrollware_enroll_url, 303);
  } finally {
    await releaseOfferLock(env, lock);
  }
}

async function validateOfferFromRequest(request, env) {
  const url = new URL(request.url);
  let offerSlug = "";
  if (url.pathname.startsWith("/o/")) {
    offerSlug = decodeURIComponent(url.pathname.slice(3)).trim();
  }
  let token = url.searchParams.get("token") || "";
  if (request.method === "POST") {
    const formData = await request.formData();
    token = String(formData.get("token") || token);
    offerSlug = String(formData.get("offer_slug") || offerSlug).trim();
  }
  if (offerSlug) {
    const offer = await getOfferBySlug(offerSlug, env);
    if (!offer) {
      return { ok: false, reason: "Offer slug was not found in trusted offer data.", token: "" };
    }
    return { ok: true, offer, token: "" };
  }
  if (!token) {
    return { ok: false, reason: "Missing offer token or offer slug.", token: "" };
  }
  const decoded = await decodeOfferToken(token, env);
  if (!decoded.ok) {
    return { ok: false, reason: decoded.reason, token };
  }
  if (decoded.offer.offer_source !== "customer_facing_offers") {
    return { ok: false, reason: "Offer source is not valid.", token };
  }
  return { ok: true, offer: decoded.offer, token };
}

async function getOfferBySlug(offerSlug, env) {
  if (!/^[a-z0-9][a-z0-9-]{5,120}$/.test(offerSlug)) {
    return null;
  }

  if (env.OFFERS_KV) {
    const stored = await env.OFFERS_KV.get(`offer:${offerSlug}`, "json");
    if (stored) return normalizeTrustedOffer(stored, offerSlug);
  }

  if (env.OFFERS_D1) {
    const row = await env.OFFERS_D1.prepare("select * from customer_facing_offers where offer_slug = ? and session_status = 'proposed'").bind(offerSlug).first();
    if (row) return normalizeTrustedOffer(row, offerSlug);
  }

  if (env.OFFER_DATA_JSON) {
    try {
      const payload = JSON.parse(env.OFFER_DATA_JSON);
      const found = findOfferInPayload(payload, offerSlug);
      if (found) return normalizeTrustedOffer(found, offerSlug);
    } catch {
      return null;
    }
  }

  // Production should read from KV, D1, R2, or the current offer JSON published to
  // trusted Worker storage. The public slug is only a lookup key; it is not trusted
  // as the source of course, time, or location facts.
  return null;
}

function findOfferInPayload(payload, offerSlug) {
  const courses = Array.isArray(payload && payload.courses) ? payload.courses : [];
  for (const course of courses) {
    const options = Array.isArray(course && course.offered_options) ? course.offered_options : [];
    for (const option of options) {
      if (String(option.offer_slug || option.page_slug || "") === offerSlug) {
        return { ...option, course_key: option.course_key || course.course_key, course_display_name: option.course_display_name || course.course_display_name };
      }
    }
  }
  return null;
}

function normalizeTrustedOffer(raw, offerSlug) {
  return {
    offer_id: String(raw.offer_id || raw.page_slug || offerSlug),
    offer_slug: String(raw.offer_slug || offerSlug),
    course_key: String(raw.course_key || ""),
    course_display_name: String(raw.course_display_name || raw.course_title || ""),
    requested_start: String(raw.requested_start || raw.start_time || ""),
    requested_end: String(raw.requested_end || raw.end_time || ""),
    location_name: String(raw.location_name || ""),
    hub_slug: String(raw.hub_slug || raw.source_page || "bls"),
    source_page: String(raw.source_page || raw.hub_slug || "bls"),
    offer_source: "customer_facing_offers",
  };
}

async function decodeOfferToken(token, env) {
  const [body, signature] = token.split(".");
  if (!body) {
    return { ok: false, reason: "Malformed offer token." };
  }

  if (env.OFFER_LINK_SIGNING_SECRET) {
    if (!signature) {
      return { ok: false, reason: "Signed offer token is required." };
    }
    const expected = await hmacSha256Url(env.OFFER_LINK_SIGNING_SECRET, body);
    if (!timingSafeEqual(expected, signature)) {
      return { ok: false, reason: "Offer token signature is invalid." };
    }
  } else if (env.ALLOW_UNSIGNED_OFFER_TOKENS !== "true") {
    return { ok: false, reason: "Offer signing secret is not configured." };
  }

  try {
    const json = atob(padBase64Url(body));
    const payload = JSON.parse(json);
    return {
      ok: true,
      offer: {
        offer_id: String(payload.offer_id || ""),
        offer_slug: String(payload.offer_slug || payload.offer_id || ""),
        course_key: String(payload.course_key || ""),
        course_display_name: String(payload.course_display_name || ""),
        requested_start: String(payload.requested_start || ""),
        requested_end: String(payload.requested_end || ""),
        location_name: String(payload.location_name || ""),
        hub_slug: String(payload.hub_slug || "bls"),
        source_page: String(payload.source_page || "bls"),
        offer_source: String(payload.offer_source || ""),
      },
    };
  } catch {
    return { ok: false, reason: "Offer token payload is invalid." };
  }
}

function padBase64Url(value) {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  return base64 + "=".repeat((4 - (base64.length % 4)) % 4);
}

async function hmacSha256Url(secret, body) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(body));
  return b64url(new Uint8Array(signature));
}

function b64url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let mismatch = 0;
  for (let index = 0; index < a.length; index += 1) {
    mismatch |= a.charCodeAt(index) ^ b.charCodeAt(index);
  }
  return mismatch === 0;
}

async function clickTimeRecheck(offer, env) {
  // Placeholder boundary:
  // 1. Fetch current ADR calendar and DoNotSchedule blocks.
  // 2. Read canonical Class Report / hot-sync state.
  // 3. Re-run the same travel, cleanup, instructor, duplicate, and same-program rules.
  // 4. Return { available: true } only when the exact course/start/location still fits.
  if (env.CLICK_TIME_RECHECK_URL) {
    return { available: false, reason: "Remote click-time recheck is not wired in this Worker scaffold." };
  }
  return { available: true, scaffold_only: true };
}

async function createEnrollwareClass(offer, env) {
  // Stub only. Real implementation must supply:
  // course/program template, date, start time, location, instructor, capacity,
  // registration settings, and must return a public Enrollware enroll URL.
  // It must not run unless creationEnabled, allowPublicCreation, and dryRun=false.
  return { ok: false, reason: "not_wired" };
}

async function writeHotSyncRecord(env, record) {
  if (env.HOT_SYNC_D1) {
    await env.HOT_SYNC_D1.prepare(
      `insert into hot_sync_sessions
       (source, status, course_key, course_display_name, start_time, end_time, location_name,
        instructor, enrollware_class_id, enrollware_enroll_url, created_at, needs_class_report_absorption)
       values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      record.source,
      record.status,
      record.course_key,
      record.course_display_name,
      record.start,
      record.end,
      record.location_name,
      record.instructor,
      record.enrollware_class_id,
      record.enrollware_enroll_url,
      record.created_at,
      record.needs_class_report_absorption ? 1 : 0
    ).run();
    return;
  }
  await writeAuditLog(env, { action: "hot_sync_stub_only", ...record });
}

async function acquireOfferLock(env, offer) {
  const key = `lock:${offer.course_key}:${offer.requested_start}:${offer.location_name}`;
  if (!env.OFFER_LOCKS) {
    return { acquired: true, key, stub: true };
  }
  const existing = await env.OFFER_LOCKS.get(key);
  if (existing) {
    return { acquired: false, key };
  }
  await env.OFFER_LOCKS.put(key, new Date().toISOString(), { expirationTtl: workerConfig(env).lockTtlSeconds });
  return { acquired: true, key };
}

async function releaseOfferLock(env, lock) {
  if (lock && lock.key && env.OFFER_LOCKS) {
    await env.OFFER_LOCKS.delete(lock.key);
  }
}

async function checkVisitorRateLimit(env, visitorKey) {
  if (!env.OFFER_RATE_LIMITS) {
    return { allowed: true, stub: true };
  }
  const dayKey = `checks:${new Date().toISOString().slice(0, 10)}:${visitorKey}`;
  const current = Number(await env.OFFER_RATE_LIMITS.get(dayKey) || "0");
  if (current >= workerConfig(env).maxChecksPerVisitorPerDay) {
    return { allowed: false };
  }
  await env.OFFER_RATE_LIMITS.put(dayKey, String(current + 1), { expirationTtl: 86400 });
  return { allowed: true };
}

async function checkSystemDailyCreationCap(env) {
  if (!env.OFFER_RATE_LIMITS) {
    return { allowed: true, stub: true };
  }
  const key = `system-creations:${new Date().toISOString().slice(0, 10)}`;
  const current = Number(await env.OFFER_RATE_LIMITS.get(key) || "0");
  return { allowed: current < workerConfig(env).maxWorkerCreatedClassesPerDay };
}

async function writeAuditLog(env, event) {
  const record = { ...event, logged_at: new Date().toISOString() };
  console.log(JSON.stringify(record));
  if (env.HOT_SYNC_D1) {
    await env.HOT_SYNC_D1.prepare(
      "insert into offer_worker_audit_log (logged_at, action, source, course_key, start_time, payload_json) values (?, ?, ?, ?, ?, ?)"
    ).bind(record.logged_at, record.action || "", record.source || "", record.course_key || "", record.start || "", JSON.stringify(record)).run();
  }
}

function workerConfig(env) {
  return {
    ...DEFAULT_CONFIG,
    creationEnabled: env.CREATION_ENABLED === "true",
    dryRun: env.DRY_RUN !== "false",
    allowPublicCreation: env.ALLOW_PUBLIC_CREATION === "true",
  };
}

function visitorFingerprint(request) {
  return request.headers.get("CF-Connecting-IP") || request.headers.get("x-forwarded-for") || "unknown";
}

function offerSummaryHtml(offer) {
  return `<dl>
    <dt>Course</dt><dd>${escapeHtml(offer.course_display_name || offer.course_key)}</dd>
    <dt>Start</dt><dd>${escapeHtml(offer.requested_start)}</dd>
    <dt>Location</dt><dd>${escapeHtml(offer.location_name)}</dd>
  </dl>`;
}

function failurePage(title, message, status = 400) {
  return htmlPage(title, `<p>${escapeHtml(message)}</p>`, status);
}

function htmlPage(title, body, status = 200) {
  return new Response(`<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>${escapeHtml(title)} | 910CPR</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, sans-serif; margin: 0; color: #172033; background: #f5f7fb; }
    main { max-width: 680px; margin: 8vh auto; padding: 24px; background: white; border: 1px solid #d9e1ef; border-radius: 8px; }
    h1 { margin-top: 0; font-size: 1.6rem; }
    button, a.button { display: inline-block; margin-top: 16px; padding: 10px 14px; border-radius: 6px; border: 0; background: #234fe5; color: white; text-decoration: none; font-weight: 700; }
    .back { display: inline-block; margin-top: 18px; color: #234fe5; }
    dl { display: grid; grid-template-columns: max-content 1fr; gap: 8px 14px; }
    dt { font-weight: 700; }
  </style>
</head>
<body>
  <main>
    <h1>${escapeHtml(title)}</h1>
    ${body}
    <p><a class="back" href="${DEFAULT_CONFIG.backToScheduleUrl}">Back to BLS schedule</a></p>
  </main>
</body>
</html>`, {
    status,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" },
  });
}

function escapeHtml(value) {
  return String(value || "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[char]);
}
