const GENERATED_BY = "910cpr_travel_worker";
const DEFAULT_BASE_ADDRESS = "4018 Shipyard Blvd, Wilmington, NC 28403";
const DEFAULT_FALLBACK_MINUTES = 90;

export async function handleTravelCalendarSync(request, env, dependencies = {}) {
  if (request.method !== "POST") return json({ error: "method_not_allowed" }, 405);
  if (String(env.TRAVEL_EVENT_SYNC_ENABLED || "false") !== "true") {
    return json({ status: "disabled", writesPerformed: false }, 503);
  }
  if (!env.TRAVEL_SYNC_WEBHOOK_SECRET || !await secretsMatch(request.headers.get("x-910cpr-travel-secret"), env.TRAVEL_SYNC_WEBHOOK_SECRET)) {
    return json({ error: "unauthorized" }, 401);
  }

  let change;
  try {
    change = await request.json();
  } catch {
    return json({ error: "invalid_json" }, 400);
  }
  const result = await reconcileTravelEvents(change, env, dependencies);
  return json(result, result.status === "invalid" ? 400 : 200);
}

export async function reconcileTravelEvents(change, env, dependencies = {}) {
  const fetcher = dependencies.fetch || fetch;
  const event = change && change.event;
  const action = String(change && change.action || "upsert").toLowerCase();
  const parentId = String((event && event.id) || change && change.eventId || "").trim();
  if (!parentId) return { status: "invalid", reason: "missing_parent_event_id", writesPerformed: false };
  if (isGeneratedTravelEvent(event)) {
    return { status: "ignored", reason: "generated_travel_event", parentEventId: parentId, writesPerformed: false };
  }

  const inboundId = await travelEventId(parentId, "inbound");
  const outboundId = await travelEventId(parentId, "outbound");
  const accessToken = await googleAccessToken(env, fetcher);
  requireEnv(env, "TRAVEL_CALENDAR_ID");

  if (action === "delete" || event && event.status === "cancelled") {
    const deleted = [];
    for (const id of [inboundId, outboundId]) {
      deleted.push(await deleteCalendarEvent(id, env, accessToken, fetcher));
    }
    return { status: "deleted", parentEventId: parentId, travelEventIds: [inboundId, outboundId], deleted, writesPerformed: true };
  }

  const source = normalizeSourceEvent(event);
  if (!source.ok) {
    return { status: "skipped", reason: source.reason, parentEventId: parentId, writesPerformed: false };
  }
  const baseAddress = String(env.TRAVEL_BASE_ADDRESS || DEFAULT_BASE_ADDRESS).trim();
  const fallbackMinutes = positiveInt(env.TRAVEL_UNKNOWN_OFFSITE_MINUTES, DEFAULT_FALLBACK_MINUTES);
  const marginMinutes = positiveInt(env.TRAVEL_ROUTE_MARGIN_MINUTES, 0);
  const namedMinimum = namedMinimumMinutes(source.location, event.summary, env);

  const inboundRoute = await resolveRoute(baseAddress, source.location, env, fetcher, fallbackMinutes);
  const outboundRoute = await resolveRoute(source.location, baseAddress, env, fetcher, fallbackMinutes);
  const inboundMinutes = effectiveMinutes(inboundRoute.minutes, namedMinimum, marginMinutes);
  const outboundMinutes = effectiveMinutes(outboundRoute.minutes, namedMinimum, marginMinutes);
  const inboundStart = new Date(new Date(source.start).getTime() - inboundMinutes * 60000).toISOString();
  const outboundEnd = new Date(new Date(source.end).getTime() + outboundMinutes * 60000).toISOString();

  const common = {
    parentEventId: parentId,
    parentSummary: String(event.summary || "Calendar event"),
    baseAddress,
    destinationAddress: source.location,
  };
  const inbound = calendarEvent({
    ...common, id: inboundId, direction: "inbound", start: inboundStart, end: source.start,
    origin: baseAddress, destination: source.location, minutes: inboundMinutes, route: inboundRoute,
  });
  const outbound = calendarEvent({
    ...common, id: outboundId, direction: "outbound", start: source.end, end: outboundEnd,
    origin: source.location, destination: baseAddress, minutes: outboundMinutes, route: outboundRoute,
  });
  const upserts = [
    await upsertCalendarEvent(inbound, env, accessToken, fetcher),
    await upsertCalendarEvent(outbound, env, accessToken, fetcher),
  ];
  return {
    status: "upserted", parentEventId: parentId, travelEventIds: [inboundId, outboundId],
    inboundMinutes, outboundMinutes, namedMinimumMinutes: namedMinimum,
    routeSources: [inboundRoute.source, outboundRoute.source], upserts, writesPerformed: true,
  };
}

export function isGeneratedTravelEvent(event) {
  if (!event) return false;
  const marker = event.extendedProperties && event.extendedProperties.private && event.extendedProperties.private.generated_by;
  return marker === GENERATED_BY || /^TRAVEL\s+[—-]/i.test(String(event.summary || ""));
}

export async function travelEventId(parentId, direction) {
  const bytes = new TextEncoder().encode(`${parentId}|${direction}`);
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  const hex = Array.from(digest, value => value.toString(16).padStart(2, "0")).join("");
  return `trvl${hex.slice(0, 40)}${direction === "inbound" ? "a" : "b"}`;
}

function normalizeSourceEvent(event) {
  if (!event || typeof event !== "object") return { ok: false, reason: "missing_event" };
  const location = String(event.location || "").replace(/\\,/g, ",").trim();
  const start = event.start && event.start.dateTime;
  const end = event.end && event.end.dateTime;
  if (!location) return { ok: false, reason: "missing_event_address" };
  if (!start || !end || !Number.isFinite(Date.parse(start)) || !Number.isFinite(Date.parse(end))) {
    return { ok: false, reason: "timed_event_required" };
  }
  if (Date.parse(end) <= Date.parse(start)) return { ok: false, reason: "invalid_event_interval" };
  return { ok: true, location, start: new Date(start).toISOString(), end: new Date(end).toISOString() };
}

function namedMinimumMinutes(location, summary, env) {
  let rules = [];
  try { rules = JSON.parse(env.TRAVEL_NAMED_RULES_JSON || "[]"); } catch { rules = []; }
  const text = `${location || ""} ${summary || ""}`.toLowerCase();
  return rules.reduce((largest, rule) => {
    const matches = Array.isArray(rule.match_any) && rule.match_any.some(value => text.includes(String(value).toLowerCase()));
    return matches ? Math.max(largest, positiveInt(rule.minutes_each_way, 0)) : largest;
  }, 0);
}

async function resolveRoute(origin, destination, env, fetcher, fallbackMinutes) {
  if (!env.GOOGLE_ROUTES_API_KEY) return { source: "fallback", minutes: fallbackMinutes, distanceMeters: null, reason: "routing_key_missing" };
  try {
    const response = await fetcher("https://routes.googleapis.com/directions/v2:computeRoutes", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-goog-api-key": env.GOOGLE_ROUTES_API_KEY,
        "x-goog-fieldmask": "routes.duration,routes.distanceMeters",
      },
      body: JSON.stringify({ origin: { address: origin }, destination: { address: destination }, travelMode: "DRIVE" }),
    });
    if (!response.ok) throw new Error(`routes_http_${response.status}`);
    const payload = await response.json();
    const route = payload && payload.routes && payload.routes[0];
    const seconds = Number(String(route && route.duration || "").replace(/s$/, ""));
    if (!route || !Number.isFinite(seconds) || seconds <= 0) throw new Error("routes_missing_duration");
    return { source: "google_routes", minutes: Math.ceil(seconds / 60), distanceMeters: Number(route.distanceMeters || 0) || null };
  } catch (error) {
    return { source: "fallback", minutes: fallbackMinutes, distanceMeters: null, reason: error.message };
  }
}

function effectiveMinutes(routeMinutes, namedMinimum, marginMinutes) {
  const raw = Math.max(routeMinutes + marginMinutes, namedMinimum);
  return Math.ceil(raw / 5) * 5;
}

function calendarEvent(input) {
  const arrow = input.direction === "inbound" ? `${input.baseAddress} → ${input.destinationAddress}` : `${input.destinationAddress} → ${input.baseAddress}`;
  return {
    id: input.id,
    summary: `TRAVEL — ${arrow}`,
    description: `Generated travel occupancy for ${input.parentSummary}. Parent event: ${input.parentEventId}.`,
    location: input.direction === "inbound" ? input.destinationAddress : input.baseAddress,
    start: { dateTime: input.start },
    end: { dateTime: input.end },
    transparency: "opaque",
    extendedProperties: { private: {
      generated_by: GENERATED_BY, parent_event_id: input.parentEventId, direction: input.direction,
      travel_minutes: String(input.minutes), route_source: input.route.source,
      distance_meters: input.route.distanceMeters == null ? "" : String(input.route.distanceMeters),
    } },
  };
}

async function upsertCalendarEvent(event, env, token, fetcher) {
  const base = calendarEventUrl(env, event.id);
  let response = await fetcher(base, { method: "PATCH", headers: googleHeaders(token), body: JSON.stringify(event) });
  if (response.status === 404) {
    response = await fetcher(calendarCollectionUrl(env), { method: "POST", headers: googleHeaders(token), body: JSON.stringify(event) });
  }
  if (!response.ok) throw new Error(`calendar_upsert_failed_${response.status}`);
  return { id: event.id, operation: response.status === 201 ? "inserted" : "updated" };
}

async function deleteCalendarEvent(id, env, token, fetcher) {
  const response = await fetcher(calendarEventUrl(env, id), { method: "DELETE", headers: { authorization: `Bearer ${token}` } });
  if (response.status === 404 || response.status === 410) return { id, operation: "already_absent" };
  if (!response.ok) throw new Error(`calendar_delete_failed_${response.status}`);
  return { id, operation: "deleted" };
}

async function googleAccessToken(env, fetcher) {
  if (env.GOOGLE_CALENDAR_ACCESS_TOKEN) return env.GOOGLE_CALENDAR_ACCESS_TOKEN;
  if (env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET && env.GOOGLE_REFRESH_TOKEN) {
    const response = await fetcher("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: env.GOOGLE_CLIENT_ID,
        client_secret: env.GOOGLE_CLIENT_SECRET,
        refresh_token: env.GOOGLE_REFRESH_TOKEN,
        grant_type: "refresh_token",
      }).toString(),
    });
    if (!response.ok) throw new Error(`google_token_refresh_failed_${response.status}`);
    const payload = await response.json();
    if (!payload.access_token) throw new Error("google_token_refresh_missing_access_token");
    return payload.access_token;
  }
  throw new Error("Google Calendar OAuth credentials are not configured");
}

function calendarCollectionUrl(env) {
  return `https://www.googleapis.com/calendar/v3/calendars/${encodeURIComponent(env.TRAVEL_CALENDAR_ID)}/events`;
}
function calendarEventUrl(env, id) { return `${calendarCollectionUrl(env)}/${encodeURIComponent(id)}`; }
function googleHeaders(token) { return { authorization: `Bearer ${token}`, "content-type": "application/json" }; }
function requireEnv(env, name) { if (!env[name]) throw new Error(`${name} is not configured`); }
function positiveInt(value, fallback) { const parsed = Number.parseInt(value, 10); return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback; }
function json(payload, status) { return new Response(JSON.stringify(payload), { status, headers: { "content-type": "application/json" } }); }

async function secretsMatch(provided, expected) {
  const encoder = new TextEncoder();
  const [providedHash, expectedHash] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(String(provided || ""))),
    crypto.subtle.digest("SHA-256", encoder.encode(String(expected || ""))),
  ]);
  return crypto.subtle.timingSafeEqual(providedHash, expectedHash);
}
