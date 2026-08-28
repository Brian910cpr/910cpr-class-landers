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

type ActorSource = "maxim_staff" | "brian_admin" | "employee_self_service" |
  "instructor" | "system" | "enrollware_import";

async function activity(eventType: string, actorSource: ActorSource, links: Record<string, unknown>, details: Record<string, unknown> = {}) {
  await rest("landerware_activity_events", { method: "POST", body: JSON.stringify({
    event_type: eventType, actor_source: actorSource,
    actor_display: actorSource === "employee_self_service" ? "Action performed through employee scheduling link" : actorSource,
    person_id: links.personId || null, organization_id: links.organizationId || null,
    requirement_id: links.requirementId || null, registration_id: links.registrationId || null,
    session_id: links.sessionId || null, details,
  }) });
}

async function ensureDurablePerson(profileId: string) {
  const profiles = await rest(`maxim_employee_profiles?id=eq.${profileId}&select=id,source_ref,billing_account,required_training,expiration_date,landerware_person_id,landerware_organization_id,landerware_requirement_id,customers(id,first_name,last_name,email,phone)`);
  if (profiles.length !== 1) throw new Error("Employee not found.");
  const profile = profiles[0];
  let organizationId = profile.landerware_organization_id;
  if (!organizationId) {
    const found = await rest(`landerware_organizations?display_name=eq.Maxim&billing_reference=eq.${encodeURIComponent(profile.billing_account || "")}&select=id&limit=1`);
    const organization = found[0] || (await rest("landerware_organizations", { method: "POST", body: JSON.stringify({ display_name: "Maxim", billing_reference: profile.billing_account }) }))[0];
    organizationId = organization.id;
  }
  let personId = profile.landerware_person_id;
  if (!personId) {
    const personResult = await rest("rpc/landerware_create_or_find_person", {
      method: "POST", body: JSON.stringify({
        p_first_name: profile.customers.first_name, p_last_name: profile.customers.last_name,
        p_email: profile.customers.email, p_phone: profile.customers.phone,
      }),
    });
    const durablePerson = Array.isArray(personResult) ? personResult[0] : personResult;
    personId = durablePerson.personId;
    await rest("landerware_person_organizations", { method: "POST", body: JSON.stringify({
      person_id: personId, organization_id: organizationId, employer_identifier: profile.source_ref,
    }) });
    await activity("person_created", "system", { personId, organizationId }, { source: "maxim_employee_profile", profileId });
  }
  let requirementId = profile.landerware_requirement_id;
  if (!requirementId) {
    const courseId = String(profile.required_training || "").toUpperCase().includes("BLS") ? "359474" : "329495";
    requirementId = (await rest("landerware_certification_requirements", { method: "POST", body: JSON.stringify({
      person_id: personId, organization_id: organizationId, course_id: courseId,
      course_name: profile.required_training, expiration_date: profile.expiration_date,
      source_policy: "Maxim corporate requirement", source_policy_version: "maxim-2026-08-10",
    }) }))[0].id;
  }
  await rest(`maxim_employee_profiles?id=eq.${profileId}`, { method: "PATCH", body: JSON.stringify({
    landerware_person_id: personId, landerware_organization_id: organizationId,
    landerware_requirement_id: requirementId, updated_at: new Date().toISOString(),
  }) });
  return { profile, personId, organizationId, requirementId };
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

function easternDateOnly(value = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(value);
  const part = (type: string) =>
    parts.find((item) => item.type === type)?.value || "";
  return `${part("year")}-${part("month")}-${part("day")}`;
}

function easternDateTimeDisplay(value: unknown) {
  if (!value) return null;
  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) return null;
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    month: "2-digit",
    day: "2-digit",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function statusDetailClassDisplay(value: unknown) {
  const text = String(value || "");
  const registeredMatch = text.match(/\bRegistered\s+(.+)$/i);
  if (registeredMatch) return registeredMatch[1];
  const importedClassMatch = text.match(/\bClass\s+(\d{1,2}\/\d{1,2}\/\d{4}\s+\d{1,2}:\d{2}\s+[AP]M)\b/i);
  return importedClassMatch?.[1] || null;
}

function wallDateTimeDisplay(dateValue: unknown, startTimeValue: unknown) {
  const dateMatch = String(dateValue || "").match(/^(\d{4})-(\d{2})-(\d{2})/);
  const timeMatch = String(startTimeValue || "").match(/^(\d{2}):(\d{2})/);
  if (!dateMatch || !timeMatch) return null;
  const hour = Number(timeMatch[1]);
  const minute = timeMatch[2];
  const suffix = hour >= 12 ? "PM" : "AM";
  const displayHour = hour % 12 || 12;
  return `${dateMatch[2]}/${dateMatch[3]}/${dateMatch[1]}, ${displayHour}:${minute} ${suffix}`;
}

function courseNameForRegistration(course: any, courseId: string) {
  const projectedName = course.courseName || course.course_name || course.title ||
    course.label;
  if (projectedName) return String(projectedName);
  const knownNames: Record<string, string> = {
    "209806": "AHA BLS Provider",
    "359474": "AHA BLS Provider Renewal",
    "210549": "AHA BLS HeartCode",
    "209809": "AHA Heartsaver First Aid CPR AED",
    "329495": "AHA Heartsaver Total",
  };
  return knownNames[courseId] || `Course ${courseId}`;
}

function locationLabelForRegistration(locationKeyValue: string) {
  const labels: Record<string, string> = {
    "wilmington": "Wilmington - Shipyard Blvd",
    "holly-ridge-jacksonville": "Holly Ridge / Jacksonville",
  };
  return labels[locationKeyValue] || locationKeyValue;
}

function buildMaximSimulatedEmails(input: {
  registrationId: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  billingAccount: string;
  courseName: string;
  displayDateTime: string;
  locationLabel: string;
}) {
  const studentName = [input.firstName, input.lastName].filter(Boolean).join(" ")
    .trim() || "Maxim participant";
  const firstName = input.firstName || studentName;
  return [
    {
      template: "maxim_student_registration_confirmation",
      sendMode: "simulated",
      to: input.email ? [input.email] : [],
      cc: [],
      bcc: [],
      subject: `Your ${input.courseName} training with 910CPR`,
      body:
        `Hi ${firstName},\n\nYou are scheduled for ${input.courseName} on ${input.displayDateTime} at ${input.locationLabel}.\n\nYour class is billed to ${input.billingAccount}; no payment or promo code is needed at registration.\n\nIf you need to change this class, contact 910CPR or your Maxim office.\n\nThank you,\n910CPR`,
      registrationId: input.registrationId,
      createdAt: new Date().toISOString(),
    },
    {
      template: "maxim_internal_registration_notice",
      sendMode: "simulated",
      to: [Deno.env.get("MAXIM_INTERNAL_NOTIFY_EMAIL") || "office@910cpr.com"],
      cc: [],
      bcc: [],
      subject: `Maxim scheduled: ${studentName} - ${input.courseName}`,
      body:
        `Maxim participant scheduled in Hot_sync.\n\nName: ${studentName}\nEmail: ${input.email || ""}\nPhone: ${input.phone || ""}\nCourse: ${input.courseName}\nClass: ${input.displayDateTime}\nLocation: ${input.locationLabel}\nBilling: ${input.billingAccount}\nRegistration ID: ${input.registrationId}\nSource: maxim_portal_hot_sync\nEmail mode: simulated`,
      registrationId: input.registrationId,
      createdAt: new Date().toISOString(),
    },
  ];
}

function calendarDayDifference(startDate: string, endDate: string) {
  const start = Date.parse(`${String(startDate).slice(0, 10)}T00:00:00Z`);
  const end = Date.parse(`${String(endDate).slice(0, 10)}T00:00:00Z`);
  return Math.floor((end - start) / (24 * 60 * 60 * 1000));
}

function ecardCodeFromStatus(value: unknown) {
  return String(value || "").match(/\beCard\s+([A-Za-z0-9-]+)/i)?.[1] || null;
}

async function listEmployees() {
  const currentMonth = easternMonthBoundary(0);
  const afterNextMonth = easternMonthBoundary(2);
  const today = easternDateOnly();
  const rows = await rest(
    "maxim_employee_profiles?select=id,source_ref,billing_account,required_training,workflow_stage,status_detail,active,link_sent_at,link_prepared_at,prior_class_date,expiration_date,prior_ecard_code,ecard_detected_at,scheduled_class_date,enrollware_class_id,current_external_class_id,current_external_registration_id,landerware_person_id,landerware_organization_id,landerware_requirement_id,updated_at,customers(id,first_name,last_name,email,phone)&order=updated_at.desc",
  );
  const requests = await rest(
    "maxim_registration_requests?select=id,employee_profile_id,external_course_id,starts_at,registration_url,status,location_key,supersedes_request_id,superseded_at,commitment_released_at,created_at,registration_source,source_booking_url,class_date,start_time,timezone,simulated_email_payloads,simulated_email_created_at&order=created_at.desc",
  );
  const latestRequest = new Map<string, any>();
  const personIds = rows.map((row: any) => row.landerware_person_id).filter(Boolean);
  const events = personIds.length ? await rest(
    `landerware_activity_events?person_id=in.(${personIds.join(",")})&select=id,event_type,actor_source,actor_display,person_id,registration_id,session_id,details,occurred_at&order=occurred_at.desc`,
  ) : [];
  for (const request of requests) {
    if (request.status === "requested" && !latestRequest.has(request.employee_profile_id)) {
      latestRequest.set(request.employee_profile_id, request);
    }
  }
  const mapped = rows.map((row: any) => {
      const registration = latestRequest.get(row.id);
      const workflowStage = Number(row.workflow_stage || 0);
      const importedCompletion = /^Completed\s+\d{1,2}\/\d{1,2}\/\d{4}\b/i.test(
        String(row.status_detail || ""),
      );
      const priorECardCode = row.prior_ecard_code || null;
      const priorWorkflowClassDate = (workflowStage >= 3 || importedCompletion)
        ? row.prior_class_date
        : null;
      const priorWorkflowClassAgeDays = priorWorkflowClassDate
        ? calendarDayDifference(String(priorWorkflowClassDate), today)
        : null;
      const recentPriorWorkflowClassDate = (
          priorWorkflowClassAgeDays !== null &&
          priorWorkflowClassAgeDays >= 0 &&
          priorWorkflowClassAgeDays <= 14
        )
        ? priorWorkflowClassDate
        : null;
      const currentClassDate = registration?.starts_at || row.scheduled_class_date ||
        recentPriorWorkflowClassDate;
      const currentClassDateDisplay = statusDetailClassDisplay(row.status_detail) ||
        wallDateTimeDisplay(registration?.class_date, registration?.start_time) ||
        easternDateTimeDisplay(currentClassDate);
      const currentClassAgeDays = currentClassDate
        ? calendarDayDifference(String(currentClassDate), today)
        : null;
      const eCardCode = workflowStage >= 4 && currentClassDate
        ? ecardCodeFromStatus(row.status_detail) || priorECardCode
        : null;
      const completedAt = (eCardCode || workflowStage === 3 || importedCompletion)
        ? currentClassDate || row.ecard_detected_at || row.updated_at
        : null;
      const expirationDate = row.expiration_date
        ? String(row.expiration_date).slice(0, 10)
        : null;
      const renewalDueNow = Boolean(
        expirationDate &&
        expirationDate >= currentMonth &&
        expirationDate < afterNextMonth,
      );
      const hasCurrentClassActivity = Boolean(
        currentClassDate &&
        currentClassAgeDays !== null &&
        currentClassAgeDays <= 14,
      );
      const bucket = !row.active
        ? "history"
        : hasCurrentClassActivity
        ? "recently_completed"
        : renewalDueNow
        ? "active"
        : "history";
      return {
      id: row.id,
      personId: row.landerware_person_id,
      organizationId: row.landerware_organization_id,
      requirementId: row.landerware_requirement_id,
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
      linkPreparedDate: row.link_prepared_at,
      priorClassDate: row.prior_class_date,
      expirationDate: row.expiration_date,
      priorECardCode,
      eCardCode,
      eCardDetectedAt: completedAt,
      completionDate: completedAt,
      bucket,
      enrollwareClassId: row.enrollware_class_id,
      externalClassId: row.current_external_class_id,
      externalRegistrationId: row.current_external_registration_id,
      classDate: currentClassDate,
      classDateDisplay: currentClassDateDisplay,
      registrationUrl: registration?.registration_url || null,
      registrationSource: registration?.registration_source || null,
      sourceBookingUrl: registration?.source_booking_url || null,
      classDateWall: registration?.class_date || null,
      classStartTime: registration?.start_time || null,
      timezone: registration?.timezone || "America/New_York",
      simulatedEmails: registration?.simulated_email_payloads || [],
      simulatedEmailCreatedAt: registration?.simulated_email_created_at || null,
      registrationRequestedAt: registration?.created_at || null,
      registrationStatus: registration?.status || null,
      locationKey: registration?.location_key || null,
      activity: events.filter((event: any) => event.person_id === row.landerware_person_id),
      invoiceLabel: workflowStage === 5 && currentClassDate ? "INVOICED" : null,
      invoiceDate: workflowStage === 5 && currentClassDate ? row.updated_at : null,
    };
  });
  const recentCompleted = mapped
    .filter((row: any) => row.bucket === "recently_completed")
    .sort((a: any, b: any) =>
      String(b.eCardDetectedAt).localeCompare(String(a.eCardDetectedAt))
    );
  return response({
    employees: [
      ...mapped.filter((row: any) => row.bucket === "active"),
      ...recentCompleted,
    ],
    history: mapped.filter((row: any) => row.bucket === "history"),
    registrationHistory: requests.filter((request: any) =>
      request.status !== "requested"
    ),
  });
}

async function updateEmployee(req: Request, id: string) {
  const body = await req.json().catch(() => ({}));
  const firstName = String(body.firstName || "").trim();
  const lastName = String(body.lastName || "").trim();
  if (!firstName || !lastName) {
    return response({ error: "First and last name are required." }, 400);
  }
  const durable = await ensureDurablePerson(id);
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
  const oldName = `${durable.profile.customers.first_name} ${durable.profile.customers.last_name}`.trim();
  const newName = `${firstName} ${lastName}`.trim();
  const oldContact = { email: durable.profile.customers.email, phone: durable.profile.customers.phone };
  const newContact = { email: String(body.email || "").trim() || null, phone: String(body.phone || "").trim() || null };
  const durablePeople = await rest(`landerware_people?id=eq.${durable.personId}&select=prior_names,prior_contacts`);
  const durablePerson = durablePeople[0] || { prior_names: [], prior_contacts: [] };
  await rest(`landerware_people?id=eq.${durable.personId}`, { method: "PATCH", body: JSON.stringify({
    current_first_name: firstName, current_last_name: lastName,
    current_email: newContact.email, current_phone: newContact.phone,
    searchable_text: `${firstName} ${lastName} ${newContact.email || ""} ${newContact.phone || ""}`.trim().toLowerCase(),
    prior_names: oldName !== newName ? [...(durablePerson.prior_names || []), { value: oldName, changed_at: new Date().toISOString() }] : durablePerson.prior_names,
    prior_contacts: JSON.stringify(oldContact) !== JSON.stringify(newContact) ? [...(durablePerson.prior_contacts || []), { ...oldContact, changed_at: new Date().toISOString() }] : durablePerson.prior_contacts,
    updated_at: new Date().toISOString(),
  }) });
  if (oldName !== newName) await activity("name_corrected", "maxim_staff", durable, { from: oldName, to: newName });
  if (JSON.stringify(oldContact) !== JSON.stringify(newContact)) await activity("contact_corrected", "maxim_staff", durable, { from: oldContact, to: newContact });
  return response({ ok: true, id });
}

async function createEmployee(req: Request) {
  const body = await req.json().catch(() => ({}));
  const firstName = String(body.firstName || "").trim(), lastName = String(body.lastName || "").trim();
  const requiredTraining = String(body.course || "").trim(), expirationDate = String(body.expirationDate || "").slice(0, 10);
  if (!firstName || !lastName || !requiredTraining || !/^\d{4}-\d{2}-\d{2}$/.test(expirationDate)) {
    return response({ error: "Name, required training, and expiration date are required." }, 400);
  }
  const customer = (await rest("customers", { method: "POST", body: JSON.stringify({
    first_name: firstName, last_name: lastName, email: String(body.email || "").trim() || null,
    phone: String(body.phone || "").trim() || null,
  }) }))[0];
  const profile = (await rest("maxim_employee_profiles", { method: "POST", body: JSON.stringify({
    customer_id: customer.id, source_ref: String(body.providerIdentifier || "").trim() || `maxim-${crypto.randomUUID()}`,
    billing_account: String(body.billingAccount || "#031"), required_training: requiredTraining,
    expiration_date: expirationDate, workflow_stage: 0, status_detail: "New provider — scheduling required", active: true,
  }) }))[0];
  const durable = await ensureDurablePerson(profile.id);
  await activity("corporate_requirement_created", "maxim_staff", durable, { expirationDate, requiredTraining });
  return response({ ok: true, employeeId: profile.id, personId: durable.personId, requirementId: durable.requirementId }, 201);
}

function sessionRequirementsManifest(courseId: string, courseName: string, deliveryMethod: string) {
  const policyVersion = "910cpr-session-requirements-2026-08-10";
  const item = (id: string, requirement: string, classification: string, responsibleParty: string, provided = false) => ({
    requirement_id: `req-${id}`, requirement, source_policy: `AHA / Training Site requirements for ${courseName} (${deliveryMethod})`,
    source_policy_version: policyVersion, classification, responsible_party: responsibleParty,
    provided_by_910cpr: provided, downloaded_at: null, viewed_at: null, acknowledged_at: null,
    offered_for_purchase: false, completed_received: false, completed_received_at: null,
    related_document_id: null, notes: "",
  });
  return { schema_version: "landerware.session-requirements.v1", policy_version: policyVersion,
    captured_at: new Date().toISOString(), certifying_program: "AHA", course_id: courseId,
    course_name: courseName, delivery_method: deliveryMethod, document_ids: [], items: [
      item("roster", "Prefilled session roster with walk-in rows", "landerware_may_provide", "910CPR", true),
      item("session_record", "Instructor/session documentation and closeout record", "landerware_may_provide", "Instructor", true),
      item("evaluation", "910CPR course evaluation/review form", "landerware_may_provide", "910CPR", true),
      item("skills", `Current authorized ${courseName} skills checklist or skills sheet`, "external_controlled_material", "Instructor"),
      item("testing", `Current authorized ${courseName} testing and answer documentation`, "external_controlled_material", "Instructor"),
      item("student_material", `Required student course materials for ${courseName}`, "student_must_obtain", "Student"),
      item("training_center", "Current Training Center / Training Site documentation required for this session", "instructor_must_obtain", "Instructor"),
    ] };
}

async function deactivateEmployee(id: string) {
  const durable = await ensureDurablePerson(id);
  const rows = await rest(`maxim_employee_profiles?id=eq.${id}`, {
    method: "PATCH",
    body: JSON.stringify({ active: false, updated_at: new Date().toISOString() }),
  });
  if (!rows.length) return response({ error: "Employee not found." }, 404);
  await rest(`landerware_people?id=eq.${durable.personId}`, { method: "PATCH", body: JSON.stringify({ archived_at: new Date().toISOString(), updated_at: new Date().toISOString() }) });
  await activity("archived", "maxim_staff", durable, { meaning: "Archived from active workflow" });
  return response({ ok: true, id, active: false });
}

async function returnEmployeeToComingDue(id: string) {
  const durable = await ensureDurablePerson(id);
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
  await rest(`landerware_people?id=eq.${durable.personId}`, { method: "PATCH", body: JSON.stringify({ archived_at: null, updated_at: new Date().toISOString() }) });
  await activity("restored", "maxim_staff", durable, { workflow: "coming_due" });
  return response({ ok: true, id, workflowStage: 0 });
}

async function markScheduleLinkSent(id: string) {
  const durable = await ensureDurablePerson(id);
  const sentAt = new Date().toISOString();
  const profiles = await rest(
    `maxim_employee_profiles?select=current_external_registration_id,workflow_stage,status_detail&id=eq.${id}&active=eq.true&limit=1`,
  );
  if (!profiles.length) return response({ error: "Employee not found." }, 404);
  if (
    Number(profiles[0].workflow_stage || 0) >= 4 &&
    ecardCodeFromStatus(profiles[0].status_detail)
  ) {
    return response({ error: "Scheduling is closed because this employee has an eCard." }, 409);
  }
  const workflowStage = profiles[0].current_external_registration_id ? 2 : 1;
  const rows = await rest(`maxim_employee_profiles?id=eq.${id}&active=eq.true`, {
    method: "PATCH",
    body: JSON.stringify({
      workflow_stage: workflowStage,
      status_detail: workflowStage === 2 ? "Registered; another scheduling link prepared" : "Scheduling link prepared; Gmail delivery pending",
      link_prepared_at: sentAt,
      updated_at: sentAt,
    }),
  });
  const token = randomToken();
  const tokenExpiresAt = durable.profile.expiration_date
    ? `${String(durable.profile.expiration_date).slice(0, 10)}T23:59:59-04:00`
    : new Date(Date.now() + 30 * 86400000).toISOString();
  await rest("landerware_self_service_tokens", { method: "POST", body: JSON.stringify({
    token_sha256: await sha256(token), person_id: durable.personId,
    organization_id: durable.organizationId, requirement_id: durable.requirementId,
    expires_at: tokenExpiresAt,
  }) });
  const scheduleUrl = `${Deno.env.get("PUBLIC_SITE_URL") || "https://www.910cpr.com"}/corp/maxim-schedule.html?t=${token}`;
  const firstName = String(durable.profile.customers.first_name || "there");
  const courseName = String(durable.profile.required_training || "required CPR");
  const expiration = String(durable.profile.expiration_date || "your assigned deadline").slice(0, 10);
  const subject = "Maxim CPR Training — Choose Your Class";
  const bodyText = `Hi ${firstName},\n\nMaxim has asked you to schedule your upcoming ${courseName} training with 910CPR.\n\nYour current certification expires ${expiration}.\n\nUse the link below to choose an available class on or before your expiration date:\n\nChoose Your Class\n${scheduleUrl}\n\nYour required training program has already been selected. You may correct your name or email if needed, but the required program cannot be changed.\n\nIf you have trouble finding a suitable date, reply to this email and we’ll help.\n\nThanks,\n\nBrian\n910CPR\n910-395-5193`;
  const message = await rest("landerware_messages", { method: "POST", body: JSON.stringify({
    person_id: durable.personId, template_key: "maxim_choose_class_v1",
    recipient: durable.profile.customers.email, subject, body_text: bodyText,
    delivery_provider: "gmail", delivery_status: "pending",
    idempotency_key: `maxim-link:${durable.personId}:${await sha256(token)}`,
  }) });
  await activity("schedule_link_created", "maxim_staff", durable, { messageId: message[0]?.id, deliveryStatus: "pending" });
  return response({ ok: true, id, linkPreparedDate: sentAt, workflowStage, scheduleUrl,
    messageId: message[0]?.id, deliveryStatus: "pending", deliveryConfigured: false });
}

async function selfServiceRecords(token: string) {
  const tokenHash = await sha256(token);
  const tokens = await rest(`landerware_self_service_tokens?token_sha256=eq.${tokenHash}&revoked_at=is.null&expires_at=gt.${encodeURIComponent(new Date().toISOString())}&select=id,person_id,organization_id,requirement_id,expires_at&limit=1`);
  if (tokens.length !== 1) return null;
  const access = tokens[0];
  const [people, organizations, requirements] = await Promise.all([
    rest(`landerware_people?id=eq.${access.person_id}&archived_at=is.null&select=id,current_first_name,current_last_name,current_email`),
    rest(`landerware_organizations?id=eq.${access.organization_id}&select=id,display_name`),
    rest(`landerware_certification_requirements?id=eq.${access.requirement_id}&person_id=eq.${access.person_id}&organization_id=eq.${access.organization_id}&status=eq.active&select=id,course_id,course_name,expiration_date`),
  ]);
  if (people.length !== 1 || organizations.length !== 1 || requirements.length !== 1) return null;
  return { access, person: people[0], organization: organizations[0], requirement: requirements[0] };
}

async function selfService(req: Request, token: string) {
  const records = await selfServiceRecords(token);
  if (!records) return response({ error: "This scheduling link is invalid or expired." }, 404);
  if (req.method === "GET") {
    await rest(`landerware_self_service_tokens?id=eq.${records.access.id}`, { method: "PATCH", body: JSON.stringify({ last_opened_at: new Date().toISOString() }) });
    await activity("self_service_link_opened", "employee_self_service", { personId: records.person.id, organizationId: records.organization.id, requirementId: records.requirement.id });
    return response({ person: { firstName: records.person.current_first_name, lastName: records.person.current_last_name, email: records.person.current_email },
      organization: { name: records.organization.display_name }, requirement: records.requirement,
      allowedDateRange: { startsOn: easternDateOnly(), endsOn: records.requirement.expiration_date } });
  }
  if (req.method === "PATCH") {
    const body = await req.json().catch(() => ({}));
    if ("courseId" in body || "courseName" in body || "organizationId" in body || "expirationDate" in body) {
      return response({ error: "The employer-controlled requirement cannot be changed." }, 403);
    }
    const before = { firstName: records.person.current_first_name, lastName: records.person.current_last_name, email: records.person.current_email };
    const after = { firstName: String(body.firstName || before.firstName).trim(), lastName: String(body.lastName || before.lastName).trim(), email: String(body.email || before.email || "").trim() || null };
    await rest(`landerware_people?id=eq.${records.person.id}`, { method: "PATCH", body: JSON.stringify({
      current_first_name: after.firstName, current_last_name: after.lastName, current_email: after.email,
      searchable_text: `${after.firstName} ${after.lastName} ${after.email || ""}`.trim().toLowerCase(), updated_at: new Date().toISOString(),
    }) });
    await activity("self_service_contact_corrected", "employee_self_service", { personId: records.person.id, organizationId: records.organization.id, requirementId: records.requirement.id }, { before, after });
    return response({ ok: true, person: after });
  }
  if (req.method === "POST") {
    const body = await req.json().catch(() => ({}));
    if (String(body.courseId) !== String(records.requirement.course_id) || String(body.date) > String(records.requirement.expiration_date) || String(body.date) < easternDateOnly()) {
      return response({ error: "The selected class is outside this scheduling task." }, 403);
    }
    const profiles = await rest(`maxim_employee_profiles?landerware_person_id=eq.${records.person.id}&landerware_requirement_id=eq.${records.requirement.id}&active=eq.true&select=source_ref,current_external_registration_id,billing_account&limit=1`);
    if (profiles.length !== 1) return response({ error: "The corporate workflow record is unavailable." }, 409);
    const registrationRequest = new Request(req.url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({
      ...body, adminOverrideExpiration: false, expirationDate: records.requirement.expiration_date,
      billingAccount: profiles[0].billing_account, moveFromRegistrationId: profiles[0].current_external_registration_id || null,
      person: { personId: profiles[0].source_ref, firstName: records.person.current_first_name,
        lastName: records.person.current_last_name, email: records.person.current_email },
    }) });
    return await registerEmployee(registrationRequest, "employee_self_service");
  }
  return response({ error: "Not found" }, 404);
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

function locationKey(course: any) {
  const value = String(
    course.location || course.location_display || course.location_name ||
      course.public_location || course.sourceAvailabilityBlock?.location || "",
  ).toLowerCase();
  if (value.includes("wilmington") || value.includes("shipyard")) return "wilmington";
  if (
    value.includes("holly ridge") || value.includes("jacksonville") ||
    value.includes("onslow")
  ) return "holly-ridge-jacksonville";
  return "";
}

function approvedLocationKeys() {
  return new Set(
    (Deno.env.get("MAXIM_APPROVED_LOCATIONS") ||
      "wilmington,holly-ridge-jacksonville")
      .split(",")
      .map((value) => value.trim())
      .filter(Boolean),
  );
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
  const canonicalLocationKey = locationKey(course);
  if (
    !canonicalLocationKey ||
    !approvedLocationKeys().has(canonicalLocationKey) ||
    canonicalLocationKey !== String(body.locationKey || "")
  ) return null;
  if (
    !body.adminOverrideExpiration && body.expirationDate &&
    String(day.date) > String(body.expirationDate)
  ) return null;
  return { selector, day, slot, course, locationKey: canonicalLocationKey };
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
      locationKey: canonical.locationKey,
    },
  });
}

async function registerEmployee(req: Request, actorSource: ActorSource = "maxim_staff") {
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
  const sourceBookingUrl =
    canonical.course.registrationUrl || canonical.course.appointmentUrl || null;

  const existing = await rest(
    `maxim_registration_requests?employee_profile_id=eq.${profiles[0].id}&status=eq.requested&select=id`,
  );
  if (existing.length && !body.moveFromRegistrationId) {
    return response({
      error: "duplicate_active_registration",
      existingRegistration: existing[0],
    }, 409);
  }
  const externalSessionId =
    `selector:${canonical.selector}:${canonical.day.date}:${canonical.slot.startTime}:${body.courseId}`;
  const startsAt = easternTimestamp(canonical.day.date, canonical.slot.startTime);
  const courseId = String(body.courseId);
  const inserted = await rest("rpc/maxim_replace_registration", {
    method: "POST",
    body: JSON.stringify({
      p_employee_profile_id: profiles[0].id,
      p_external_session_id: externalSessionId,
      p_external_course_id: courseId,
      p_starts_at: startsAt,
      p_registration_url: null,
      p_billing_account: body.billingAccount,
      p_location_key: canonical.locationKey,
      p_replace_request_id: body.moveFromRegistrationId || null,
    }),
  });
  const registration = Array.isArray(inserted) ? inserted[0] : inserted;
  const durable = await ensureDurablePerson(profiles[0].id);
  const courseName = courseNameForRegistration(canonical.course, courseId);
  const deliveryMethod = String(canonical.course.deliveryMethod || canonical.course.delivery_method || "classroom");
  const durableResult = await rest("rpc/landerware_register", { method: "POST", body: JSON.stringify({
    p_profile_key: `maxim-course-${courseId}`, p_entry_context: actorSource,
    p_fields: { first_name: body?.person?.firstName, last_name: body?.person?.lastName,
      email: body?.person?.email, phone: body?.person?.phone || null },
    p_existing_person_id: durable.personId,
    p_organization_id: durable.organizationId, p_external_session_id: externalSessionId,
    p_starts_at: startsAt,
    p_location_name: locationLabelForRegistration(canonical.locationKey),
    p_provenance: "maxim_portal_hot_sync", p_requirements_manifest: sessionRequirementsManifest(courseId, courseName, deliveryMethod),
    p_idempotency_key: `maxim:${registration.id}`,
  }) });
  const durableRegistration = Array.isArray(durableResult) ? durableResult[0] : durableResult;
  const displayDateTime = easternDateTimeDisplay(startsAt) ||
    `${canonical.day.date} ${canonical.slot.startTime}`;
  const simulatedEmails = buildMaximSimulatedEmails({
    registrationId: String(registration.id),
    firstName: String(body?.person?.firstName || ""),
    lastName: String(body?.person?.lastName || ""),
    email: String(body?.person?.email || ""),
    phone: String(body?.person?.phone || ""),
    billingAccount: String(body.billingAccount || ""),
    courseName,
    displayDateTime,
    locationLabel: locationLabelForRegistration(canonical.locationKey),
  });
  await rest(`maxim_registration_requests?id=eq.${registration.id}`, {
    method: "PATCH",
    body: JSON.stringify({
      registration_source: "maxim_portal_hot_sync",
      source_booking_url: sourceBookingUrl,
      class_date: canonical.day.date,
      start_time: canonical.slot.startTime,
      timezone: "America/New_York",
      simulated_email_payloads: simulatedEmails,
      simulated_email_created_at: new Date().toISOString(),
      landerware_registration_id: durableRegistration.registrationId,
      landerware_session_id: durableRegistration.sessionId,
    }),
  });
  const registrationProfiles = await rest(`landerware_registration_profiles?profile_key=eq.${encodeURIComponent(`maxim-course-${courseId}`)}&select=confirmation_template_key&limit=1`);
  const templateKey = registrationProfiles[0]?.confirmation_template_key;
  const confirmationTemplates = await rest(`landerware_confirmation_templates?template_key=eq.${encodeURIComponent(templateKey)}&active=eq.true&select=*&limit=1`);
  const confirmationTemplate = confirmationTemplates[0];
  if (!confirmationTemplate) throw new Error("confirmation_template_not_found");
  const confirmationValues: Record<string, string> = {
    first_name: String(body?.person?.firstName || "there"), display_name: courseName,
    session_message: `${canonical.day.date} ${canonical.slot.startTime}; ${locationLabelForRegistration(canonical.locationKey)}; ${deliveryMethod}`,
    requirement_message: "Please follow the preparation requirements assigned to this registration.",
    payer_message: "Your registration uses the payer policy assigned by the registration profile.",
  };
  const renderConfirmation = (value: string) => value.replace(/\{\{([a-z_]+)\}\}/g, (_match: string, key: string) => confirmationValues[key] || "");
  const confirmationKey = `registration-confirmation:${durableRegistration.registrationId}`;
  const priorConfirmation = await rest(`landerware_messages?idempotency_key=eq.${encodeURIComponent(confirmationKey)}&select=id&limit=1`);
  const confirmation = priorConfirmation.length ? priorConfirmation : await rest("landerware_messages", { method: "POST", body: JSON.stringify({
    person_id: durable.personId, registration_id: durableRegistration.registrationId,
    template_key: confirmationTemplate.template_key, recipient: body?.person?.email || null,
    subject: renderConfirmation(confirmationTemplate.subject_template), body_text: renderConfirmation(confirmationTemplate.body_template),
    delivery_provider: confirmationTemplate.delivery_provider, delivery_status: "pending", idempotency_key: confirmationKey,
  }) });
  await activity("confirmation_queued", actorSource, { ...durable, registrationId: durableRegistration.registrationId, sessionId: durableRegistration.sessionId }, { messageId: confirmation[0]?.id, deliveryStatus: "pending" });
  return response({
    ok: true,
    registrationId: registration.id,
    personId: sourceRef,
    registrationSource: "maxim_portal_hot_sync",
    durableRegistration,
    confirmationMessage: { id: confirmation[0]?.id, deliveryStatus: "pending", deliveryConfigured: false },
    emailMode: "simulated",
    simulatedEmails,
    canonicalSlot: {
      selector: canonical.selector,
      courseId,
      date: canonical.day.date,
      startTime: canonical.slot.startTime,
      locationKey: canonical.locationKey,
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
    if ((req.method === "GET" || req.method === "PATCH" || req.method === "POST") && route[0] === "self-service" && route[1]) return await selfService(req, route[1]);
    if (!(await authorized(req))) return response({ error: "Unauthorized" }, 401);
    if (req.method === "GET" && route[0] === "employees") return await listEmployees();
    if (req.method === "POST" && route[0] === "employees" && !route[1]) return await createEmployee(req);
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
