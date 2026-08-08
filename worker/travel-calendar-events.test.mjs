import test from "node:test";
import assert from "node:assert/strict";
import { handleTravelCalendarSync, isGeneratedTravelEvent, reconcileTravelEvents, travelEventId, validateTravelConfiguration } from "./travel-calendar-events.js";

const sourceEvent = {
  id: "parent-123",
  summary: "CFA Pickup",
  location: "Cape Fear Academy, 3900 College Rd, Wilmington, NC 28412",
  start: { dateTime: "2026-08-20T15:00:00-04:00" },
  end: { dateTime: "2026-08-20T17:30:00-04:00" },
};

function env(overrides = {}) {
  return {
    TRAVEL_EVENT_SYNC_ENABLED: "true",
    TRAVEL_SYNC_WEBHOOK_SECRET: "test-secret",
    TRAVEL_CALENDAR_ID: "travel@example.com",
    GOOGLE_CALENDAR_ACCESS_TOKEN: "calendar-token",
    GOOGLE_ROUTES_API_KEY: "routes-key",
    TRAVEL_ROUTE_MARGIN_MINUTES: "5",
    ...overrides,
  };
}

function response(status, payload = {}) {
  return new Response(JSON.stringify(payload), { status, headers: { "content-type": "application/json" } });
}

test("upserts deterministic visible inbound and outbound events with calculated routes", async () => {
  const calls = [];
  const fetch = async (url, options) => {
    calls.push({ url, options, body: options.body && JSON.parse(options.body) });
    if (url.includes("routes.googleapis.com")) return response(200, { routes: [{ duration: "901s", distanceMeters: 12345 }] });
    if (options.method === "PATCH") return response(404);
    return response(201, { id: "created" });
  };
  const result = await reconcileTravelEvents({ action: "upsert", event: sourceEvent }, env(), { fetch });
  assert.equal(result.status, "upserted");
  assert.equal(result.inboundMinutes, 25);
  assert.equal(result.outboundMinutes, 25);
  assert.deepEqual(result.routeSources, ["google_routes", "google_routes"]);
  const inserted = calls.filter(call => call.options.method === "POST" && call.url.includes("calendar/v3"));
  assert.equal(inserted.length, 2);
  assert.equal(inserted[0].body.summary.startsWith("TRAVEL —"), true);
  assert.equal(inserted[0].body.end.dateTime, "2026-08-20T19:00:00.000Z");
  assert.equal(inserted[0].body.start.dateTime, "2026-08-20T18:35:00.000Z");
  assert.equal(inserted[0].body.extendedProperties.private.generated_by, "910cpr_travel_worker");
  assert.equal(inserted[1].body.start.dateTime, "2026-08-20T21:30:00.000Z");
  assert.equal(inserted[1].body.end.dateTime, "2026-08-20T21:55:00.000Z");
});

test("same parent event produces the same travel IDs after a move", async () => {
  const first = await travelEventId(sourceEvent.id, "inbound");
  const moved = await travelEventId(sourceEvent.id, "inbound");
  assert.equal(first, moved);
});

test("delete removes both deterministic travel events and tolerates absence", async () => {
  const methods = [];
  const fetch = async (_url, options) => { methods.push(options.method); return new Response(null, { status: 404 }); };
  const result = await reconcileTravelEvents({ action: "delete", eventId: sourceEvent.id }, env(), { fetch });
  assert.equal(result.status, "deleted");
  assert.deepEqual(methods, ["DELETE", "DELETE"]);
  assert.deepEqual(result.deleted.map(item => item.operation), ["already_absent", "already_absent"]);
});

test("generated travel events are ignored to prevent recursion", async () => {
  const event = { ...sourceEvent, summary: "TRAVEL — Shipyard → CFA" };
  assert.equal(isGeneratedTravelEvent(event), true);
  const result = await reconcileTravelEvents({ action: "upsert", event }, env(), { fetch: async () => { throw new Error("must not fetch"); } });
  assert.equal(result.status, "ignored");
  assert.equal(result.writesPerformed, false);
});

test("missing address is skipped without routing or calendar writes", async () => {
  const event = { ...sourceEvent, location: "" };
  let calls = 0;
  const result = await reconcileTravelEvents({ action: "upsert", event }, env(), { fetch: async () => { calls += 1; } });
  assert.equal(result.status, "skipped");
  assert.equal(result.reason, "missing_event_address");
  assert.equal(calls, 0);
});

test("endpoint remains disabled and performs no writes by default", async () => {
  const request = new Request("https://schedule.910cpr.com/internal/travel-events/sync", {
    method: "POST", body: JSON.stringify({ action: "upsert", event: sourceEvent }),
  });
  const result = await handleTravelCalendarSync(request, { TRAVEL_EVENT_SYNC_ENABLED: "false" });
  assert.equal(result.status, 503);
  assert.equal((await result.json()).writesPerformed, false);
});

test("refreshes an OAuth access token before calendar writes", async () => {
  const calls = [];
  const fetch = async (url, options) => {
    calls.push({ url, options });
    if (url.includes("oauth2.googleapis.com")) return response(200, { access_token: "refreshed-token" });
    if (url.includes("routes.googleapis.com")) return response(200, { routes: [{ duration: "600s", distanceMeters: 8000 }] });
    if (options.method === "PATCH") return response(200, {});
    throw new Error(`unexpected request ${url}`);
  };
  const oauthEnv = env({
    GOOGLE_CALENDAR_ACCESS_TOKEN: "",
    GOOGLE_CLIENT_ID: "client",
    GOOGLE_CLIENT_SECRET: "secret",
    GOOGLE_REFRESH_TOKEN: "refresh",
  });
  const result = await reconcileTravelEvents({ action: "upsert", event: sourceEvent }, oauthEnv, { fetch });
  assert.equal(result.status, "upserted");
  assert.equal(calls[0].url, "https://oauth2.googleapis.com/token");
  const calendarCalls = calls.filter(call => call.url.includes("calendar/v3"));
  assert.equal(calendarCalls.length, 2);
  assert.equal(calendarCalls[0].options.headers.authorization, "Bearer refreshed-token");
});

test("validation checks calendar and both routes without writes", async () => {
  const methods = [];
  const fetch = async (url, options = {}) => {
    methods.push(options.method || "GET");
    if (url.includes("calendar/v3")) return response(200, { items: [] });
    if (url.includes("routes.googleapis.com")) return response(200, { routes: [{ duration: "720s", distanceMeters: 9000 }] });
    throw new Error(`unexpected request ${url}`);
  };
  const result = await validateTravelConfiguration({ action: "validate", event: sourceEvent }, env(), { fetch });
  assert.equal(result.status, "validated");
  assert.equal(result.writesPerformed, false);
  assert.equal(result.calendarReachable, true);
  assert.deepEqual(result.routes.map(route => route.source), ["google_routes", "google_routes"]);
  assert.deepEqual(methods, ["GET", "POST", "POST"]);
});
