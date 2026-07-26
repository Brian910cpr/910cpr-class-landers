import assert from "node:assert/strict";
import test from "node:test";

import { DAYPARTS, handleVoiceSearchCprClasses, normalizeSourcePayloads } from "../src/voiceSearchCprClasses.js";

const TOKEN = "unit-test-token";

const FIXTURE_PAYLOADS = [
  payload("bls", [
    course({
      date: "2026-08-04",
      displayDate: "Tuesday, August 4, 2026",
      startTime: "09:15",
      displayStartTime: "9:15 AM",
      courseId: "359474",
      courseName: "AHA BLS Provider Renewal",
      courseFamily: "BLS",
      deliveryMode: "classroom",
      appointmentDayId: 260713,
      appointmentUrl: "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260713&startTime=9%3A15%20AM&courseId=359474",
      availabilityBlockId: "brian_do_not_schedule:inverse_gap:10",
    }),
    course({
      date: "2026-08-03",
      displayDate: "Monday, August 3, 2026",
      startTime: "09:15",
      displayStartTime: "9:15 AM",
      courseId: "209806",
      courseName: "AHA BLS Provider",
      courseFamily: "BLS",
      deliveryMode: "classroom",
      appointmentDayId: 260714,
      appointmentUrl: "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260714&startTime=9%3A15%20AM&courseId=209806",
      availabilityBlockId: "brian_do_not_schedule:inverse_gap:11",
    }),
    course({
      date: "2026-08-05",
      displayDate: "Wednesday, August 5, 2026",
      startTime: "18:15",
      displayStartTime: "6:15 PM",
      courseId: "210549",
      courseName: "AHA HeartCode BLS",
      courseFamily: "BLS",
      deliveryMode: "skills-session",
      appointmentDayId: 260715,
      appointmentUrl: "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260715&startTime=6%3A15%20PM&courseId=210549",
      availabilityBlockId: "brian_do_not_schedule:inverse_gap:12",
    }),
    course({
      date: "2026-08-06",
      startTime: "09:15",
      courseId: "209806",
      courseName: "AHA BLS Provider",
      courseFamily: "BLS",
      location: "Private Residence",
      appointmentDayId: 260716,
      appointmentUrl: "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260716&startTime=9%3A15%20AM&courseId=209806",
      publicSelectable: false,
    }),
    course({
      date: "2026-08-07",
      startTime: "09:15",
      courseId: "209806",
      courseName: "AHA BLS Provider",
      courseFamily: "BLS",
      appointmentDayId: 260717,
      appointmentUrl: "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260717",
    }),
  ]),
  payload("heartsaver", [
    course({
      date: "2026-08-03",
      displayDate: "Monday, August 3, 2026",
      startTime: "12:30",
      displayStartTime: "12:30 PM",
      courseId: "209809",
      courseName: "AHA Heartsaver First Aid CPR AED",
      courseFamily: "Heartsaver",
      deliveryMode: "classroom",
      appointmentDayId: 260718,
      appointmentUrl: "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260718&startTime=12%3A30%20PM&courseId=209809",
      availabilityBlockId: "brian_do_not_schedule:inverse_gap:13",
    }),
  ]),
  payload("acls", [
    course({
      date: "2026-08-08",
      displayDate: "Saturday, August 8, 2026",
      startTime: "14:00",
      displayStartTime: "2:00 PM",
      courseId: "241108",
      courseName: "AHA ACLS Provider (Initial)",
      courseFamily: "ACLS",
      deliveryMode: "classroom",
      appointmentDayId: null,
      appointmentUrl: "https://coastalcprtraining.enrollware.com/enroll?id=13673164",
      registrationUrl: "https://coastalcprtraining.enrollware.com/enroll?id=13673164",
      availabilityBlockId: "seated:13673164",
      availabilityWindow: "seated-class",
      offerType: "seated_class",
      sourceAvailabilityBlock: {
        source: "docs/data/schedule_future.json",
        sessionId: "13673164",
        registrationStatus: "open",
        publicDirectBooking: true,
      },
    }),
  ]),
];

function payload(pageKey, courses) {
  const dates = new Map();
  for (const item of courses) {
    if (!dates.has(item.date)) dates.set(item.date, new Map());
    const startMap = dates.get(item.date);
    if (!startMap.has(item.startTime)) startMap.set(item.startTime, []);
    startMap.get(item.startTime).push(item);
  }
  return {
    schemaVersion: "selector-resolved-availability.v1",
    generatedAt: "2026-07-25T16:00:00-04:00",
    pageKey,
    counts: { publicSelectableOfferCount: courses.filter((item) => item.publicSelectable).length },
    dates: [...dates].map(([date, starts]) => ({
      date,
      displayDate: courses.find((item) => item.date === date)?.displayDate,
      startTimes: [...starts].map(([startTime, items]) => ({
        startTime,
        displayStartTime: items[0].displayStartTime,
        courses: items,
      })),
    })),
  };
}

function course(overrides) {
  return {
    date: "2026-08-01",
    displayDate: "Saturday, August 1, 2026",
    startTime: "09:15",
    displayStartTime: "9:15 AM",
    courseId: "209806",
    courseName: "AHA BLS Provider",
    courseFamily: "BLS",
    certifyingBody: "AHA",
    deliveryMode: "classroom",
    durationMinutes: 120,
    appointmentDayId: 260700,
    appointmentUrl: "https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260700&startTime=9%3A15%20AM&courseId=209806",
    availabilityBlockId: "block-1",
    sourceAvailabilityBlock: {
      sourceAvailabilityBlockId: "block-1",
      sourceType: "inverse_google_calendar",
      approvedInverseGenerated: true,
    },
    location: ":: Wilmington; Shipyard Blvd",
    publicSelectable: true,
    ...overrides,
  };
}

async function request(path, token = TOKEN) {
  const headers = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await handleVoiceSearchCprClasses(
    new Request(`https://schedule.910cpr.com${path}`, { headers }),
    {
      VOICE_SEARCH_BEARER_TOKEN: TOKEN,
      VOICE_CPR_CLASS_OFFERS_JSON: JSON.stringify(FIXTURE_PAYLOADS),
    },
  );
  const body = await response.json();
  return { response, body };
}

test("requires bearer authentication", async () => {
  assert.equal((await request("/voice/search-cpr-classes", null)).response.status, 401);
  assert.equal((await request("/voice/search-cpr-classes", "wrong")).response.status, 401);
  assert.equal((await request("/voice/search-cpr-classes")).response.status, 200);
});

test("validates dates, daypart, delivery method, and limit", async () => {
  for (const path of [
    "/voice/search-cpr-classes?date=08-04-2026",
    "/voice/search-cpr-classes?date_from=2026-08-05&date_to=2026-08-04",
    "/voice/search-cpr-classes?daypart=brunch",
    "/voice/search-cpr-classes?delivery_method=remote",
    "/voice/search-cpr-classes?limit=26",
  ]) {
    const { response, body } = await request(path);
    assert.equal(response.status, 400);
    assert.equal(body.error.code, "invalid_parameters");
  }
});

test("filters by every supported filter", async () => {
  assert.deepEqual((await request("/voice/search-cpr-classes?program=Heartsaver")).body.offers.map((row) => row.program), ["Heartsaver"]);
  assert.deepEqual((await request("/voice/search-cpr-classes?course_type=Renewal")).body.offers.map((row) => row.course_type), ["Renewal"]);
  assert.deepEqual((await request("/voice/search-cpr-classes?delivery_method=HeartCode")).body.offers.map((row) => row.delivery_method), ["HeartCode"]);
  assert.deepEqual((await request("/voice/search-cpr-classes?date=2026-08-04")).body.offers.map((row) => row.date), ["2026-08-04"]);
  assert.deepEqual((await request("/voice/search-cpr-classes?date_from=2026-08-04&date_to=2026-08-05")).body.offers.map((row) => row.date), ["2026-08-04", "2026-08-05"]);
  assert.deepEqual((await request("/voice/search-cpr-classes?daypart=afternoon")).body.offers.map((row) => row.start_time), ["12:30", "14:00"]);
  assert.deepEqual((await request("/voice/search-cpr-classes?location=Wilmington%20-%20Shipyard%20Blvd")).body.offers.length, 5);
});

test("returns zero results and limit metadata correctly", async () => {
  const zero = await request("/voice/search-cpr-classes?program=PALS");
  assert.equal(zero.body.total_matching, 0);
  assert.equal(zero.body.returned, 0);
  assert.equal(zero.body.has_more, false);

  const limited = await request("/voice/search-cpr-classes?limit=1");
  assert.equal(limited.body.total_matching, 5);
  assert.equal(limited.body.returned, 1);
  assert.equal(limited.body.has_more, true);
});

test("keeps offer IDs unique and omits registration URLs", async () => {
  const { body } = await request("/voice/search-cpr-classes");
  const ids = body.offers.map((row) => row.offer_id);
  assert.equal(new Set(ids).size, ids.length);
  for (const row of body.offers) {
    assert.ok(!Object.hasOwn(row, "registration_url"));
    assert.notEqual(String(row.offer_id), String(row.course_id));
  }
});

test("excludes hidden private and incomplete appointment inventory", async () => {
  const { body } = await request("/voice/search-cpr-classes");
  assert.equal(body.offers.some((row) => row.location === "Private Residence"), false);
  assert.equal(body.offers.some((row) => row.date === "2026-08-07"), false);
});

test("sorts deterministically by date, start time, and stable tie-breakers", async () => {
  const first = (await request("/voice/search-cpr-classes")).body.offers;
  const second = (await request("/voice/search-cpr-classes")).body.offers;
  assert.deepEqual(first.map((row) => row.offer_id), second.map((row) => row.offer_id));
  assert.deepEqual(first.map((row) => `${row.date} ${row.start_time}`), [
    "2026-08-03 09:15",
    "2026-08-03 12:30",
    "2026-08-04 09:15",
    "2026-08-05 18:15",
    "2026-08-08 14:00",
  ]);
});

test("normalizes real-class and appointment-backed field gaps without fabricating price or seats", async () => {
  const snapshot = normalizeSourcePayloads(FIXTURE_PAYLOADS);
  const seated = snapshot.offers.find((row) => row.offer_id.includes("13673164"));
  assert.equal(seated.appointment_day_id, null);
  assert.equal(seated.price, null);
  assert.equal(seated.seats_available, null);
});

test("documents daypart boundaries in Eastern Time", () => {
  assert.deepEqual(DAYPARTS, {
    morning: { start: "05:00", end: "11:59", timezone: "America/New_York" },
    afternoon: { start: "12:00", end: "16:59", timezone: "America/New_York" },
    evening: { start: "17:00", end: "20:59", timezone: "America/New_York" },
  });
});
