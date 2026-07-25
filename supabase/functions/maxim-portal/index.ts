import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const cors = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "authorization, content-type, x-maxim-session",
  "access-control-allow-methods": "GET,POST,PATCH,DELETE,OPTIONS",
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

const response = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: cors });
const sha256 = async (value: string) =>
  Array.from(new Uint8Array(await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  ))).map((byte) => byte.toString(16).padStart(2, "0")).join("");
const randomToken = () =>
  Array.from(crypto.getRandomValues(new Uint8Array(24)))
    .map((byte) => byte.toString(16).padStart(2, "0")).join("");

function adminConfig() {
  const url = Deno.env.get("SUPABASE_URL")!;
  const secretJson = Deno.env.get("SUPABASE_SECRET_KEYS");
  const secret = secretJson
    ? JSON.parse(secretJson).default
    : Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  return {
    url,
    headers: {
      apikey: secret,
      authorization: `Bearer ${secret}`,
      "content-type": "application/json",
      prefer: "return=representation",
    },
  };
}

async function rest(path: string, init: RequestInit = {}) {
  const config = adminConfig();
  const res = await fetch(`${config.url}/rest/v1/${path}`, {
    ...init,
    headers: { ...config.headers, ...(init.headers || {}) },
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    throw new Error(data?.message || data?.error || `Database request failed (${res.status})`);
  }
  return data;
}

async function authorized(req: Request) {
  const token = req.headers.get("x-maxim-session") ||
    req.headers.get("authorization")?.replace(/^Bearer\s+/i, "") || "";
  if (!token) return false;
  const hash = await sha256(token);
  const rows = await rest(
    `maxim_portal_sessions?token_sha256=eq.${hash}&revoked_at=is.null&expires_at=gt.${
      encodeURIComponent(new Date().toISOString())
    }&select=token_sha256`,
  );
  return rows.length === 1;
}

async function login(req: Request) {
  const body = await req.json().catch(() => ({}));
  const code = String(body.code || "");
  const ip = req.headers.get("cf-connecting-ip") ||
    req.headers.get("x-forwarded-for") || "unknown";
  const ipHash = await sha256(ip);
  const since = new Date(Date.now() - 10 * 60 * 1000).toISOString();
  const failures = await rest(
    `maxim_portal_login_attempts?ip_sha256=eq.${ipHash}&succeeded=eq.false&attempted_at=gt.${
      encodeURIComponent(since)
    }&select=id`,
  );
  if (failures.length >= 5) {
    return response({ error: "Too many attempts. Try again in 10 minutes." }, 429);
  }
  const verifier = await sha256(code);
  const configs = await rest(
    `maxim_portal_access?access_key=eq.maxim-preview&active=eq.true&code_sha256=eq.${verifier}&select=access_key`,
  );
  await rest("maxim_portal_login_attempts", {
    method: "POST",
    body: JSON.stringify({ ip_sha256: ipHash, succeeded: configs.length === 1 }),
  });
  if (configs.length !== 1) return response({ error: "Incorrect access code." }, 401);
  const token = randomToken();
  await rest("maxim_portal_sessions", {
    method: "POST",
    body: JSON.stringify({
      token_sha256: await sha256(token),
      access_key: "maxim-preview",
      expires_at: new Date(Date.now() + 8 * 60 * 60 * 1000).toISOString(),
    }),
  });
  return response({ token, expiresInSeconds: 28800 });
}

function easternMonthBoundary(offset: number) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "numeric",
  }).formatToParts(new Date());
  const year = Number(parts.find((part) => part.type === "year")?.value);
  const month = Number(parts.find((part) => part.type === "month")?.value) - 1;
  const boundary = new Date(Date.UTC(year, month + offset, 1));
  return `${boundary.getUTCFullYear()}-${String(boundary.getUTCMonth() + 1).padStart(2, "0")}-01`;
}

function monthsAgoIso(months: number) {
  const date = new Date();
  date.setUTCMonth(date.getUTCMonth() - months);
  return date.toISOString();
}

function ecardCodeFromStatus(value: unknown) {
  return String(value || "").match(/\beCard\s+([A-Za-z0-9-]+)/i)?.[1] || null;
}

async function listEmployees() {
  const currentMonth = easternMonthBoundary(0);
  const afterNextMonth = easternMonthBoundary(2);
  const invoicedRetentionStart = monthsAgoIso(22);
  const eligibility = `or=(and(workflow_stage.eq.0,expiration_date.gte.${currentMonth},expiration_date.lt.${afterNextMonth}),workflow_stage.in.(1,2,3,4),and(workflow_stage.eq.5,updated_at.gte.${invoicedRetentionStart}))`;
  const rows = await rest(
    `maxim_employee_profiles?active=eq.true&${eligibility}&select=id,source_ref,billing_account,required_training,workflow_stage,status_detail,link_sent_at,prior_class_date,expiration_date,prior_ecard_code,scheduled_class_date,enrollware_class_id,current_external_class_id,current_external_registration_id,updated_at,customers(id,first_name,last_name,email,phone)&order=workflow_stage.asc,expiration_date.asc.nullslast,updated_at.desc`,
  );
  const requests = await rest(
    "maxim_registration_requests?select=id,employee_profile_id,starts_at,registration_url,status,created_at&order=created_at.desc",
  );
  const latestRequest = new Map<string, any>();
  for (const request of requests) {
    if (!latestRequest.has(request.employee_profile_id)) {
      latestRequest.set(request.employee_profile_id, request);
    }
  }
  return response({
    employees: rows.map((row: any) => {
      const registration = latestRequest.get(row.id);
      return ({
      id: row.id,
      sourceRef: row.source_ref,
      firstName: row.customers.first_name,
      lastName: row.customers.last_name,
      email: row.customers.email,
      phone: row.customers.phone,
      billingAccount: row.billing_account,
      requiredTraining: row.required_training,
      workflowStage: row.workflow_stage,
      statusDetail: row.status_detail,
      linkSentDate: row.link_sent_at,
      priorClassDate: row.prior_class_date,
      expirationDate: row.expiration_date,
      eCardCode: row.prior_ecard_code || ecardCodeFromStatus(row.status_detail),
      enrollwareClassId: row.enrollware_class_id,
      externalClassId: row.current_external_class_id,
      externalRegistrationId: row.current_external_registration_id,
      classDate: row.scheduled_class_date || registration?.starts_at || null,
      registrationUrl: registration?.registration_url || null,
      registrationRequestedAt: registration?.created_at || null,
      registrationStatus: registration?.status || null,
      invoiceLabel: row.workflow_stage === 5 ? "INVOICED" : null,
      invoiceDate: row.workflow_stage === 5 ? row.updated_at : null,
    });
    }),
  });
}

async function updateEmployee(req: Request, id: string) {
  const body = await req.json().catch(() => ({}));
  const firstName = String(body.firstName || "").trim();
  const lastName = String(body.lastName || "").trim();
  if (!firstName || !lastName) {
    return response({ error: "First and last name are required." }, 400);
  }
  const profiles = await rest(`maxim_employee_profiles?id=eq.${id}&select=customer_id`);
  if (profiles.length !== 1) return response({ error: "Employee not found." }, 404);
  await rest(`customers?id=eq.${profiles[0].customer_id}`, {
    method: "PATCH",
    body: JSON.stringify({
      first_name: firstName,
      last_name: lastName,
      email: String(body.email || "").trim() || null,
      phone: String(body.phone || "").trim() || null,
      updated_at: new Date().toISOString(),
    }),
  });
  await rest(`maxim_employee_profiles?id=eq.${id}`, {
    method: "PATCH",
    body: JSON.stringify({
      billing_account: body.billingAccount,
      required_training: body.course,
      updated_at: new Date().toISOString(),
    }),
  });
  return response({ ok: true, id });
}

async function deactivateEmployee(id: string) {
  const rows = await rest(`maxim_employee_profiles?id=eq.${id}`, {
    method: "PATCH",
    body: JSON.stringify({ active: false, updated_at: new Date().toISOString() }),
  });
  if (!rows.length) return response({ error: "Employee not found." }, 404);
  return response({ ok: true, id, active: false });
}

async function returnEmployeeToComingDue(id: string) {
  const profiles = await rest(
    `maxim_employee_profiles?id=eq.${id}&active=eq.true&select=id,current_external_registration_id`,
  );
  if (profiles.length !== 1) return response({ error: "Employee not found." }, 404);
  const registrationId = profiles[0].current_external_registration_id;
  if (registrationId) {
    await rest(`maxim_registration_requests?id=eq.${registrationId}&status=eq.requested`, {
      method: "PATCH",
      body: JSON.stringify({ status: "superseded", updated_at: new Date().toISOString() }),
    });
  }
  await rest(`maxim_employee_profiles?id=eq.${id}`, {
    method: "PATCH",
    body: JSON.stringify({
      workflow_stage: 0,
      status_detail: "Returned to Coming Due",
      current_external_class_id: null,
      current_external_registration_id: null,
      updated_at: new Date().toISOString(),
    }),
  });
  return response({ ok: true, id, workflowStage: 0 });
}

async function markScheduleLinkSent(id: string) {
  const sentAt = new Date().toISOString();
  const rows = await rest(`maxim_employee_profiles?id=eq.${id}&active=eq.true`, {
    method: "PATCH",
    body: JSON.stringify({
      workflow_stage: 1,
      status_detail: "Scheduling link sent",
      link_sent_at: sentAt,
      updated_at: sentAt,
    }),
  });
  if (!rows.length) return response({ error: "Employee not found." }, 404);
  return response({ ok: true, id, linkSentDate: sentAt, workflowStage: 1 });
}

const selectorByCourse: Record<string, string> = {
  "209806": "bls",
  "359474": "bls",
  "210549": "bls",
  "209809": "heartsaver",
  "329495": "heartsaver",
};

function canonicalSlotKey(course: any) {
  return [
    course.courseId,
    course.date,
    course.startTime,
    course.appointmentDayId || "",
    course.availabilityBlockId || "",
  ].join("|");
}

function easternTimestamp(date: string, startTime: string) {
  const utcGuess = new Date(`${date}T${startTime}:00Z`);
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(utcGuess).reduce((values: Record<string, string>, part) => {
    values[part.type] = part.value;
    return values;
  }, {});
  const representedAsUtc = Date.UTC(
    Number(parts.year),
    Number(parts.month) - 1,
    Number(parts.day),
    Number(parts.hour === "24" ? "0" : parts.hour),
    Number(parts.minute),
    Number(parts.second),
  );
  const offset = representedAsUtc - utcGuess.getTime();
  return new Date(utcGuess.getTime() - offset).toISOString();
}

async function canonicalCourseSlot(body: any) {
  const courseId = String(body.courseId || "");
  const selector = selectorByCourse[courseId];
  if (!selector) return null;
  const url =
    `https://www.910cpr.com/data/block-selector-availability/${selector}.json?maxim=${
      Date.now()
    }`;
  const payload = await fetch(url, { headers: { "cache-control": "no-cache" } })
    .then((res) => res.ok ? res.json() : null);
  if (
    !payload ||
    payload.schemaVersion !== "selector-resolved-availability.v1" ||
    !Array.isArray(payload.dates)
  ) return null;
  const day = payload.dates.find((item: any) => item.date === String(body.date));
  const slot = day?.startTimes?.find((item: any) =>
    item.startTime === String(body.startTime)
  );
  const course = slot?.courses?.find((item: any) => String(item.courseId) === courseId);
  if (!course || canonicalSlotKey(course) !== String(body.slotKey)) return null;
  return { selector, day, slot, course };
}

async function validateCanonicalSlot(req: Request) {
  const body = await req.json().catch(() => ({}));
  const canonical = await canonicalCourseSlot(body);
  if (!canonical) return response({ error: "stale_slot_rejected" }, 409);
  return response({
    ok: true,
    canonicalSlot: {
      selector: canonical.selector,
      courseId: String(canonical.course.courseId),
      date: canonical.day.date,
      startTime: canonical.slot.startTime,
      slotKey: canonicalSlotKey(canonical.course),
    },
  });
}

async function registerEmployee(req: Request) {
  const body = await req.json().catch(() => ({}));
  const sourceRef = String(body?.person?.personId || body.sourcePersonReference || "");
  const profiles = await rest(
    `maxim_employee_profiles?source_ref=eq.${
      encodeURIComponent(sourceRef)
    }&active=eq.true&select=id`,
  );
  if (profiles.length !== 1) return response({ error: "Employee not found." }, 404);

  const canonical = await canonicalCourseSlot(body);
  if (!canonical) return response({ error: "stale_slot_rejected" }, 409);
  const registrationUrl =
    canonical.course.registrationUrl || canonical.course.appointmentUrl;
  if (!registrationUrl) return response({ error: "canonical_slot_has_no_registration_url" }, 409);

  const existing = await rest(
    `maxim_registration_requests?employee_profile_id=eq.${profiles[0].id}&status=eq.requested&select=id`,
  );
  if (existing.length && !body.moveFromRegistrationId) {
    return response({
      error: "duplicate_active_registration",
      existingRegistration: existing[0],
    }, 409);
  }
  if (body.moveFromRegistrationId) {
    await rest(`maxim_registration_requests?id=eq.${body.moveFromRegistrationId}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "superseded", updated_at: new Date().toISOString() }),
    });
  }

  const externalSessionId =
    `selector:${canonical.selector}:${canonical.day.date}:${canonical.slot.startTime}:${body.courseId}`;
  const startsAt = easternTimestamp(canonical.day.date, canonical.slot.startTime);
  const inserted = await rest("maxim_registration_requests", {
    method: "POST",
    body: JSON.stringify({
      employee_profile_id: profiles[0].id,
      external_session_id: externalSessionId,
      external_course_id: String(body.courseId),
      starts_at: startsAt,
      registration_url: registrationUrl,
      billing_account: body.billingAccount,
      status: "requested",
      supersedes_request_id: body.moveFromRegistrationId || null,
    }),
  });
  await rest(`maxim_employee_profiles?id=eq.${profiles[0].id}`, {
    method: "PATCH",
    body: JSON.stringify({
      workflow_stage: 2,
      status_detail: `Registration requested ${canonical.day.displayDate}`,
      current_external_class_id: externalSessionId,
      current_external_registration_id: inserted[0].id,
      updated_at: new Date().toISOString(),
    }),
  });
  return response({
    ok: true,
    registrationId: inserted[0].id,
    personId: sourceRef,
    canonicalSlot: {
      selector: canonical.selector,
      courseId: String(body.courseId),
      date: canonical.day.date,
      startTime: canonical.slot.startTime,
    },
  });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const url = new URL(req.url);
  const parts = url.pathname.split("/").filter(Boolean);
  const route = parts.slice(parts.indexOf("maxim-portal") + 1);
  try {
    if (req.method === "POST" && route[0] === "login") return await login(req);
    if (!(await authorized(req))) return response({ error: "Unauthorized" }, 401);
    if (req.method === "GET" && route[0] === "employees") return await listEmployees();
    if (req.method === "PATCH" && route[0] === "employees" && route[1]) {
      return await updateEmployee(req, route[1]);
    }
    if (req.method === "DELETE" && route[0] === "employees" && route[1]) {
      return await deactivateEmployee(route[1]);
    }
    if (
      req.method === "POST" && route[0] === "employees" && route[1] &&
      route[2] === "return-to-due"
    ) {
      return await returnEmployeeToComingDue(route[1]);
    }
    if (
      req.method === "POST" && route[0] === "employees" && route[1] &&
      route[2] === "link-sent"
    ) {
      return await markScheduleLinkSent(route[1]);
    }
    if (req.method === "POST" && route[0] === "validate-slot") {
      return await validateCanonicalSlot(req);
    }
    if (req.method === "POST" && route[0] === "registrations") {
      return await registerEmployee(req);
    }
    return response({ error: "Not found" }, 404);
  } catch (error) {
    return response({
      error: error instanceof Error ? error.message : "Unexpected error",
    }, 500);
  }
});
