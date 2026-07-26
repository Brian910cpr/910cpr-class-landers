export const TIMEZONE = "America/New_York";
export const DEFAULT_LIMIT = 10;
export const MAX_LIMIT = 25;
export const DEFAULT_SOURCE_BASE_URL = "https://www.910cpr.com/data/block-selector-availability";
export const SOURCE_FILES = ["bls", "acls", "pals", "heartsaver", "arc", "hsi"];
export const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "Authorization, Content-Type",
  "Access-Control-Max-Age": "86400",
};
export const DAYPARTS = {
  morning: { start: "05:00", end: "11:59", timezone: TIMEZONE },
  afternoon: { start: "12:00", end: "16:59", timezone: TIMEZONE },
  evening: { start: "17:00", end: "20:59", timezone: TIMEZONE },
};

const FILTERS = new Set([
  "program",
  "course_type",
  "delivery_method",
  "date",
  "date_from",
  "date_to",
  "daypart",
  "location",
  "limit",
]);

export function handleVoiceSearchOptions() {
  return new Response(null, {
    status: 204,
    headers: CORS_HEADERS,
  });
}

export async function handleVoiceSearchCprClasses(request, env = {}) {
  if (!isAuthorized(request, env)) {
    return jsonResponse({ error: { code: "unauthorized", message: "Missing or invalid bearer token." } }, 401);
  }

  const url = new URL(request.url);
  const validation = validateQuery(url.searchParams);
  if (!validation.ok) {
    return jsonResponse({ error: { code: "invalid_parameters", message: "One or more query parameters are invalid.", details: validation.errors } }, 400);
  }

  let snapshot;
  try {
    snapshot = await loadSnapshot(env);
  } catch (error) {
    return jsonResponse({
      error: {
        code: "source_unavailable",
        message: "Generated class availability is temporarily unavailable.",
      },
    }, 503);
  }

  const matching = filterOffers(snapshot.offers || [], validation.params);
  const limit = validation.params.limit ?? DEFAULT_LIMIT;
  const returnedOffers = matching.slice(0, limit).map(publicOffer);
  return jsonResponse({
    generated_at: snapshot.generated_at,
    timezone: snapshot.timezone || TIMEZONE,
    offers: returnedOffers,
    total_matching: matching.length,
    returned: returnedOffers.length,
    has_more: matching.length > returnedOffers.length,
  }, 200, { "Cache-Control": "no-store" });
}

export async function loadSnapshot(env = {}) {
  if (env.VOICE_CPR_CLASS_OFFERS_JSON) {
    return normalizeSourcePayloads(JSON.parse(env.VOICE_CPR_CLASS_OFFERS_JSON));
  }

  const baseUrl = String(env.VOICE_SEARCH_SOURCE_BASE_URL || DEFAULT_SOURCE_BASE_URL).replace(/\/+$/, "");
  const payloads = await Promise.all(SOURCE_FILES.map(async (pageKey) => {
    const response = await fetch(`${baseUrl}/${pageKey}.json`, {
      headers: { Accept: "application/json" },
      cf: { cacheTtl: 60, cacheEverything: true },
    });
    if (!response.ok) {
      throw new Error(`source_fetch_failed:${pageKey}:${response.status}`);
    }
    return response.json();
  }));
  return normalizeSourcePayloads(payloads);
}

export function normalizeSourcePayloads(payloadOrPayloads) {
  const payloads = Array.isArray(payloadOrPayloads) ? payloadOrPayloads : [payloadOrPayloads];
  const offers = [];
  const generatedAts = [];
  for (const payload of payloads) {
    if (!payload || !Array.isArray(payload.dates)) continue;
    if (payload.generatedAt) generatedAts.push(String(payload.generatedAt));
    for (const day of payload.dates) {
      const startTimes = Array.isArray(day.startTimes) ? day.startTimes : [];
      for (const slot of startTimes) {
        const courses = Array.isArray(slot.courses) ? slot.courses : [];
        for (const course of courses) {
          const normalized = normalizeOffer(course, payload.pageKey || "");
          if (normalized) offers.push(normalized);
        }
      }
    }
  }
  const deduped = dedupeOffers(offers);
  deduped.sort(compareOffer);
  return {
    generated_at: newestGeneratedAt(generatedAts),
    timezone: TIMEZONE,
    offers: deduped,
    source: {
      kind: "generated_block_selector_availability_snapshots",
      files: SOURCE_FILES.map((pageKey) => `${pageKey}.json`),
      generated_at_values: generatedAts.sort(),
    },
  };
}

export function filterOffers(offers, params) {
  return offers
    .filter((offer) => offer && offer.registration_status === "open")
    .filter((offer) => matchesText(offer.program, params.program))
    .filter((offer) => matchesNullableText(offer.course_type, params.course_type))
    .filter((offer) => matchesText(offer.delivery_method, params.delivery_method))
    .filter((offer) => matchesText(offer.location, params.location))
    .filter((offer) => matchesDate(offer.date, params))
    .filter((offer) => matchesDaypart(offer.start_time, params.daypart))
    .sort(compareOffer);
}

export function validateQuery(searchParams) {
  const errors = [];
  const params = {};

  for (const key of searchParams.keys()) {
    if (!FILTERS.has(key)) {
      errors.push({ parameter: key, message: "Unsupported query parameter." });
    }
  }

  for (const key of ["program", "course_type", "location"]) {
    const value = firstParam(searchParams, key);
    if (value !== null && value.trim()) params[key] = value.trim();
  }

  const delivery = firstParam(searchParams, "delivery_method");
  if (delivery !== null && delivery.trim()) {
    const normalized = normalizeDeliveryMethod(delivery);
    if (!normalized) {
      errors.push({ parameter: "delivery_method", message: "Use In Person, HeartCode, or Blended." });
    } else {
      params.delivery_method = normalized;
    }
  }

  for (const key of ["date", "date_from", "date_to"]) {
    const value = firstParam(searchParams, key);
    if (value !== null && value.trim()) {
      if (!isValidDate(value.trim())) {
        errors.push({ parameter: key, message: "Use YYYY-MM-DD." });
      } else {
        params[key] = value.trim();
      }
    }
  }
  if (params.date && (params.date_from || params.date_to)) {
    errors.push({ parameter: "date", message: "Use either date or date_from/date_to, not both." });
  }
  if (params.date_from && params.date_to && params.date_from > params.date_to) {
    errors.push({ parameter: "date_to", message: "date_to must be on or after date_from." });
  }

  const daypart = firstParam(searchParams, "daypart");
  if (daypart !== null && daypart.trim()) {
    const normalized = daypart.trim().toLowerCase();
    if (!Object.prototype.hasOwnProperty.call(DAYPARTS, normalized)) {
      errors.push({ parameter: "daypart", message: `Use one of: ${Object.keys(DAYPARTS).join(", ")}.` });
    } else {
      params.daypart = normalized;
    }
  }

  const limit = firstParam(searchParams, "limit");
  if (limit !== null && limit.trim()) {
    if (!/^\d+$/.test(limit.trim())) {
      errors.push({ parameter: "limit", message: "Limit must be a positive integer." });
    } else {
      const parsed = Number(limit.trim());
      if (parsed < 1) errors.push({ parameter: "limit", message: "Limit must be at least 1." });
      else if (parsed > MAX_LIMIT) errors.push({ parameter: "limit", message: `Limit must be ${MAX_LIMIT} or less.` });
      else params.limit = parsed;
    }
  }

  return errors.length ? { ok: false, errors, params } : { ok: true, errors: [], params };
}

function normalizeOffer(course, pageKey) {
  if (!course || course.publicSelectable !== true) return null;
  const date = clean(course.date);
  const startTime = clean(course.startTime);
  const courseId = clean(course.courseId);
  const courseName = clean(course.courseName);
  const program = clean(course.courseFamily);
  const location = normalizeLocation(course.location);
  if (!isValidDate(date) || !isValidTime(startTime) || !courseId || !courseName || !program || !location) {
    return null;
  }
  if (isAppointmentOffer(course) && !hasCompleteAppointmentTuple(course)) {
    return null;
  }
  const registrationStatus = clean(course.sourceAvailabilityBlock?.registrationStatus || "open").toLowerCase();
  if (registrationStatus && registrationStatus !== "open") return null;
  const type = normalizeCourseType(courseName, program);
  return {
    offer_id: stableOfferId(course, pageKey, program, type, location),
    course_id: Number(courseId),
    appointment_day_id: course.appointmentDayId == null ? null : clean(course.appointmentDayId),
    program,
    course_type: type,
    delivery_method: normalizeDeliveryMode(course.deliveryMode, courseName),
    date,
    start_time: startTime,
    display_time: clean(course.displayStartTime) || displayTime(startTime),
    display_date: clean(course.displayDate) || displayDate(date),
    location,
    seats_available: numericOrNull(course.seatsAvailable ?? course.seats_available ?? course.availableSeats),
    price: numericOrNull(course.price ?? course.cost),
    currency: "USD",
    registration_status: "open",
  };
}

function isAppointmentOffer(course) {
  return clean(course.appointmentUrl).includes("appointmentDayId=") || course.appointmentDayId != null;
}

function hasCompleteAppointmentTuple(course) {
  const url = clean(course.appointmentUrl);
  return course.appointmentDayId != null && url.includes("startTime=") && url.includes("courseId=");
}

function stableOfferId(course, pageKey, program, courseType, location) {
  const source = clean(course.sourceAvailabilityBlock?.sessionId || course.availabilityBlockId || course.appointmentDayId || course.appointmentUrl);
  const date = clean(course.date).replace(/-/g, "");
  const start = clean(course.startTime).replace(":", "");
  return [
    slug(program),
    slug(courseType || clean(course.certifyingBody) || pageKey || "class"),
    date,
    start,
    slug(location).slice(0, 24),
    clean(course.courseId),
    slug(source).slice(-36),
  ].filter(Boolean).join("-");
}

function dedupeOffers(offers) {
  const byId = new Map();
  for (const offer of offers) {
    if (!byId.has(offer.offer_id)) byId.set(offer.offer_id, offer);
  }
  return [...byId.values()];
}

function newestGeneratedAt(values) {
  const sorted = values.filter(Boolean).sort();
  return sorted[sorted.length - 1] || new Date().toISOString();
}

function isAuthorized(request, env) {
  const expected = String(env.VOICE_SEARCH_BEARER_TOKEN || "");
  if (!expected) return false;
  const header = request.headers.get("Authorization") || "";
  const prefix = "Bearer ";
  if (!header.startsWith(prefix)) return false;
  return timingSafeEqual(header.slice(prefix.length), expected);
}

function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let mismatch = 0;
  for (let index = 0; index < a.length; index += 1) {
    mismatch |= a.charCodeAt(index) ^ b.charCodeAt(index);
  }
  return mismatch === 0;
}

function firstParam(searchParams, key) {
  const values = searchParams.getAll(key);
  return values.length ? values[0] : null;
}

function isValidDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value;
}

function isValidTime(value) {
  return /^([01]\d|2[0-3]):[0-5]\d$/.test(value);
}

function normalizeDeliveryMethod(value) {
  const normalized = value.trim().toLowerCase().replace(/[-_]+/g, " ");
  if (["in person", "inperson", "classroom"].includes(normalized)) return "In Person";
  if (["heartcode", "heart code"].includes(normalized)) return "HeartCode";
  if (["blended", "blended learning", "online"].includes(normalized)) return "Blended";
  return null;
}

function normalizeDeliveryMode(value, courseName) {
  const title = clean(courseName).toLowerCase();
  if (title.includes("heartcode")) return "HeartCode";
  const normalized = clean(value).toLowerCase();
  if (["heartcode", "heart code"].includes(normalized)) return "HeartCode";
  if (["blended", "blended learning", "online", "skills-session"].includes(normalized) || title.includes("blended") || title.includes("online")) {
    return "Blended";
  }
  return "In Person";
}

function normalizeCourseType(courseName, program) {
  const title = clean(courseName).toLowerCase();
  if (title.includes("heartcode")) return "HeartCode";
  if (title.includes("renewal")) return "Renewal";
  if (program.toUpperCase() === "BLS" && title.includes("provider")) return "Initial";
  if (["ACLS", "PALS"].includes(program.toUpperCase()) && title.includes("initial")) return "Initial";
  return null;
}

function normalizeLocation(value) {
  const text = clean(value);
  if (text === ":: Wilmington; Shipyard Blvd" || text === ":: Wilmington; Shipyard Blvd - B") {
    return "Wilmington - Shipyard Blvd";
  }
  return text;
}

function matchesText(value, query) {
  if (!query) return true;
  return String(value || "").toLowerCase() === String(query).toLowerCase();
}

function matchesNullableText(value, query) {
  if (!query) return true;
  return String(value || "").toLowerCase() === String(query).toLowerCase();
}

function matchesDate(value, params) {
  if (params.date) return value === params.date;
  if (params.date_from && value < params.date_from) return false;
  if (params.date_to && value > params.date_to) return false;
  return true;
}

function matchesDaypart(startTime, daypart) {
  if (!daypart) return true;
  const bounds = DAYPARTS[daypart];
  return startTime >= bounds.start && startTime <= bounds.end;
}

function compareOffer(a, b) {
  return (
    String(a.date).localeCompare(String(b.date)) ||
    String(a.start_time).localeCompare(String(b.start_time)) ||
    String(a.program).localeCompare(String(b.program)) ||
    String(a.course_type || "").localeCompare(String(b.course_type || "")) ||
    String(a.location).localeCompare(String(b.location)) ||
    String(a.offer_id).localeCompare(String(b.offer_id))
  );
}

function publicOffer(offer) {
  return {
    offer_id: offer.offer_id,
    course_id: offer.course_id,
    appointment_day_id: offer.appointment_day_id,
    program: offer.program,
    course_type: offer.course_type ?? null,
    delivery_method: offer.delivery_method,
    date: offer.date,
    start_time: offer.start_time,
    display_time: offer.display_time,
    display_date: offer.display_date,
    location: offer.location,
    seats_available: offer.seats_available,
    price: offer.price,
    currency: offer.currency || "USD",
    registration_status: offer.registration_status,
  };
}

function numericOrNull(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function displayTime(value) {
  const [hourText, minuteText] = value.split(":");
  const hour = Number(hourText);
  const suffix = hour < 12 ? "AM" : "PM";
  return `${hour % 12 || 12}:${minuteText} ${suffix}`;
}

function displayDate(value) {
  const date = new Date(`${value}T00:00:00Z`);
  return date.toLocaleDateString("en-US", {
    timeZone: "UTC",
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });
}

function clean(value) {
  return String(value ?? "").replace(/\s+/g, " ").trim();
}

function slug(value) {
  return clean(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

function jsonResponse(payload, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(payload, null, 2) + "\n", {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...CORS_HEADERS,
      ...extraHeaders,
    },
  });
}
