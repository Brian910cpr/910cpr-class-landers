import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const cors = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "authorization, content-type, x-maxim-session",
  "access-control-allow-methods": "POST,OPTIONS",
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

function ecardCodeFromStatus(value: unknown) {
  return String(value || "").match(/\beCard\s+([A-Za-z0-9-]+)/i)?.[1] || null;
}

async function sendReminder(employeeId: string) {
  const workerUrl = Deno.env.get("MAXIM_EMAIL_WORKER_URL") || "";
  const workerSecret = Deno.env.get("MAXIM_EMAIL_WORKER_SECRET") || "";
  if (!workerUrl || !workerSecret) {
    return response({ error: "Maxim email delivery is not configured." }, 503);
  }

  const profiles = await rest(
    `maxim_employee_profiles?select=id,current_external_registration_id,workflow_stage,status_detail,required_training,customers(first_name,email)&id=eq.${
      encodeURIComponent(employeeId)
    }&active=eq.true&limit=1`,
  );
  if (profiles.length !== 1) return response({ error: "Employee not found." }, 404);

  const profile = profiles[0];
  if (
    Number(profile.workflow_stage || 0) >= 4 &&
    ecardCodeFromStatus(profile.status_detail)
  ) {
    return response({ error: "Scheduling is closed because this employee has an eCard." }, 409);
  }

  const email = String(profile.customers?.email || "").trim();
  if (!email) return response({ error: "This employee does not have an email address." }, 409);

  const mailResponse = await fetch(workerUrl, {
    method: "POST",
    headers: {
      authorization: `Bearer ${workerSecret}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      to: email,
      firstName: String(profile.customers?.first_name || ""),
      course: String(profile.required_training || ""),
    }),
  });
  const mailResult = await mailResponse.json().catch(() => ({}));
  if (!mailResponse.ok) {
    return response({
      error: mailResult.error || "Could not send the scheduling reminder.",
      deliveryCode: mailResult.code || null,
    }, 502);
  }

  const sentAt = new Date().toISOString();
  const workflowStage = profile.current_external_registration_id ? 2 : 1;
  await rest(`maxim_employee_profiles?id=eq.${encodeURIComponent(employeeId)}&active=eq.true`, {
    method: "PATCH",
    body: JSON.stringify({
      workflow_stage: workflowStage,
      status_detail: workflowStage === 2
        ? "Registered; another scheduling link sent"
        : "Scheduling link sent",
      link_sent_at: sentAt,
      updated_at: sentAt,
    }),
  });

  return response({
    ok: true,
    id: employeeId,
    emailSent: true,
    linkSentDate: sentAt,
    workflowStage,
    messageId: mailResult.messageId || null,
  });
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  if (req.method !== "POST") return response({ error: "Not found" }, 404);
  try {
    if (!(await authorized(req))) return response({ error: "Unauthorized" }, 401);
    const body = await req.json().catch(() => ({}));
    const employeeId = String(body.employeeId || "").trim();
    if (!employeeId) return response({ error: "employeeId is required." }, 400);
    return await sendReminder(employeeId);
  } catch (error) {
    return response({
      error: error instanceof Error ? error.message : "Unexpected error",
    }, 500);
  }
});
