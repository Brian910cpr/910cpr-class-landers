export type RecheckSeedRequest = {
  seed_id: string;
  source_offer_id: string;
  date: string;
  start_time: string;
  course_id: string;
  instructor_person_id: string;
  location: string;
  appointment_url_preview: string;
};

export type RecheckSeedResponse =
  | {
      valid: true;
      redirect_url: string;
      reasons: string[];
    }
  | {
      valid: false;
      message: string;
      reasons: string[];
    };

export type RecheckSeedEnv = {
  RECHECK_SEED_ENABLED?: string;
  GOOGLE_SERVICE_ACCOUNT_JSON?: string;
  ALLOWED_ORIGINS?: string;
  APPOINTMENT_CONTAINER_CONFIG_JSON?: string;
  CALENDAR_SOURCE_CONFIG_JSON?: string;
};

const REQUIRED_FIELDS: Array<keyof RecheckSeedRequest> = [
  "seed_id",
  "source_offer_id",
  "date",
  "start_time",
  "course_id",
  "instructor_person_id",
  "location",
  "appointment_url_preview",
];

export async function handleRecheckSeed(request: Request, env: RecheckSeedEnv): Promise<Response> {
  if (request.method !== "POST") {
    return jsonResponse({ valid: false, message: "Method not allowed.", reasons: ["method_not_allowed"] }, 405);
  }

  const parsed = await parseSeedRequest(request);
  if (!parsed.ok) {
    return jsonResponse({ valid: false, message: "Invalid seed payload.", reasons: parsed.reasons }, 400);
  }

  if (env.RECHECK_SEED_ENABLED !== "true") {
    return jsonResponse({
      valid: false,
      message: "Live seed recheck is not enabled.",
      reasons: [
        "endpoint_disabled",
        "google_calendar_recheck_not_wired",
        "appointment_url_rebuild_not_wired",
      ],
    }, 503);
  }

  const calendarCheck = await recheckGoogleCalendarAvailability(parsed.seed, env);
  const blockingCheck = await recheckBlockingCalendars(parsed.seed, env);
  const occupancyCheck = await recheckOccupancySnapshot(parsed.seed, env);
  const urlBuild = rebuildDeterministicAppointmentUrl(parsed.seed, env);

  const reasons = [
    ...calendarCheck.reasons,
    ...blockingCheck.reasons,
    ...occupancyCheck.reasons,
    ...urlBuild.reasons,
  ];

  if (!calendarCheck.valid || !blockingCheck.valid || !occupancyCheck.valid || !urlBuild.valid) {
    return jsonResponse({
      valid: false,
      message: "That time is no longer available.",
      reasons,
    }, 409);
  }

  return jsonResponse({
    valid: true,
    redirect_url: urlBuild.redirect_url,
    reasons,
  }, 200);
}

export async function parseSeedRequest(request: Request): Promise<{ ok: true; seed: RecheckSeedRequest } | { ok: false; reasons: string[] }> {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return { ok: false, reasons: ["invalid_json"] };
  }

  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return { ok: false, reasons: ["body_must_be_object"] };
  }

  const candidate = body as Partial<Record<keyof RecheckSeedRequest, unknown>>;
  const missing = REQUIRED_FIELDS.filter((field) => typeof candidate[field] !== "string" || String(candidate[field]).trim() === "");
  if (missing.length > 0) {
    return { ok: false, reasons: missing.map((field) => `missing_${field}`) };
  }

  const seed = Object.fromEntries(
    REQUIRED_FIELDS.map((field) => [field, String(candidate[field]).trim()])
  ) as RecheckSeedRequest;

  const formatReasons = validateSeedFormats(seed);
  if (formatReasons.length > 0) {
    return { ok: false, reasons: formatReasons };
  }

  return { ok: true, seed };
}

function validateSeedFormats(seed: RecheckSeedRequest): string[] {
  const reasons: string[] = [];
  if (!/^\d{4}-\d{2}-\d{2}$/.test(seed.date)) {
    reasons.push("invalid_date");
  }
  if (!/^\d{2}:\d{2}$/.test(seed.start_time)) {
    reasons.push("invalid_start_time");
  }
  if (!/^[a-zA-Z0-9_.:-]{1,128}$/.test(seed.seed_id)) {
    reasons.push("invalid_seed_id");
  }
  if (!/^[a-zA-Z0-9_.:-]{1,128}$/.test(seed.source_offer_id)) {
    reasons.push("invalid_source_offer_id");
  }
  if (!/^[a-zA-Z0-9_.:-]{1,128}$/.test(seed.course_id)) {
    reasons.push("invalid_course_id");
  }
  if (!/^[a-zA-Z0-9_.:-]{1,128}$/.test(seed.instructor_person_id)) {
    reasons.push("invalid_instructor_person_id");
  }
  return reasons;
}

async function recheckGoogleCalendarAvailability(
  _seed: RecheckSeedRequest,
  _env: RecheckSeedEnv,
): Promise<{ valid: boolean; reasons: string[] }> {
  // TODO: Use GOOGLE_SERVICE_ACCOUNT_JSON or equivalent auth to query the instructor availability calendar.
  return { valid: false, reasons: ["google_calendar_api_stub"] };
}

async function recheckBlockingCalendars(
  _seed: RecheckSeedRequest,
  _env: RecheckSeedEnv,
): Promise<{ valid: boolean; reasons: string[] }> {
  // TODO: Query DNS / Do Not Schedule, ADR/employment, and personal blocking calendars.
  return { valid: false, reasons: ["blocking_calendar_api_stub"] };
}

async function recheckOccupancySnapshot(
  _seed: RecheckSeedRequest,
  _env: RecheckSeedEnv,
): Promise<{ valid: boolean; reasons: string[] }> {
  // TODO: Check trusted occupancy snapshot freshness and overlap for instructor/location/course.
  return { valid: false, reasons: ["occupancy_recheck_stub"] };
}

function rebuildDeterministicAppointmentUrl(
  _seed: RecheckSeedRequest,
  _env: RecheckSeedEnv,
): { valid: false; reasons: string[] } | { valid: true; redirect_url: string; reasons: string[] } {
  // TODO: Rebuild deterministic URL server-side from appointment container config.
  // Never trust appointment_url_preview from the browser as the redirect URL.
  return { valid: false, reasons: ["appointment_url_rebuild_stub"] };
}

function jsonResponse(payload: RecheckSeedResponse, status: number): Response {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

