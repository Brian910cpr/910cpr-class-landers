import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const root = path.resolve(import.meta.dirname, "..");
const shared = require(path.join(root, "docs", "assets", "resolved-selector-availability.js"));
const timing = require(path.join(root, "docs", "assets", "calendar-time-filters.js"));

function payload(key) {
  return JSON.parse(fs.readFileSync(
    path.join(root, "docs", "data", "block-selector-availability", `${key}.json`),
    "utf8",
  ));
}

function selectableSet(data, courseId, now) {
  const dates = shared.filterDatesByCourse(data.dates, courseId);
  return new Set(dates.flatMap((day) =>
    shared.selectableStartTimes(day, now).map((slot) => `${day.date}|${slot.startTime}`),
  ));
}

test("shared projection returns exactly the canonical artifact slots for each Maxim course", () => {
  const now = { dateKey: "2026-07-23", minutes: 0 };
  for (const [key, courseIds] of Object.entries({
    bls: ["209806", "359474", "210549"],
    heartsaver: ["209809", "329495"],
  })) {
    const data = payload(key);
    for (const courseId of courseIds) {
      const expected = new Set(data.dates.flatMap((day) =>
        day.startTimes
          .filter((slot) => day.date > now.dateKey || shared.startMinutes(slot.startTime) > now.minutes)
          .filter((slot) => slot.courses.some((course) => String(course.courseId) === courseId))
          .map((slot) => `${day.date}|${slot.startTime}`),
      ));
      assert.deepEqual(selectableSet(data, courseId, now), expected, `${key}:${courseId}`);
    }
  }
});

test("past-time suppression is shared and timezone-independent after business-now resolution", () => {
  const data = {
    dates: [{
      date: "2026-07-23",
      startTimes: [
        { startTime: "09:00", courses: [{ courseId: "209806" }] },
        { startTime: "10:00", courses: [{ courseId: "209806" }] },
      ],
    }],
  };
  assert.deepEqual(
    [...selectableSet(data, "209806", { dateKey: "2026-07-23", minutes: 9 * 60 + 30 })],
    ["2026-07-23|10:00"],
  );
});

test("12-hour feed times are converted before the real-time cutoff", () => {
  assert.equal(shared.startMinutes("8:45 AM"), 8 * 60 + 45);
  assert.equal(shared.startMinutes("12:15 PM"), 12 * 60 + 15);
  assert.equal(shared.startMinutes("12:15 AM"), 15);
  assert.equal(
    shared.isPastStart(
      { date: "2026-09-07" },
      { startTime: "8:45 AM" },
      { dateKey: "2026-09-07", minutes: 9 * 60 + 55 },
    ),
    true,
  );
});

test("unparseable feed times fail closed instead of remaining bookable", () => {
  assert.equal(
    shared.isPastStart(
      { date: "2026-09-07" },
      { startTime: "TBD" },
      { dateKey: "2026-09-07", minutes: 0 },
    ),
    true,
  );
});

const referenceDate = "2026-09-29";
const boundaryTimes = ["00:00", "05:59", "06:00", "11:59", "12:00", "16:59", "17:00", "20:59", "21:00", "23:59"];
const boundaryDay = [{ date: referenceDate, startTimes: boundaryTimes.map(startTime => ({ startTime, courses: [{ courseId: "209806" }] })) }];
const starts = dates => dates.flatMap(day => day.startTimes.map(slot => slot.startTime));
const applyTiming = (dates, query = "", buckets = []) => timing.filterDates(dates, timing.compile(buckets, query, referenceDate));

for (const [index, bucket] of timing.BUCKETS.entries()) {
  test(`${bucket.label} has exact half-open boundaries`, () => {
    assert.deepEqual(starts(applyTiming(boundaryDay, "", [bucket.id])), boundaryTimes.slice(index * 2, index * 2 + 2));
  });
}

test("multiple checkbox selections form a union and Smart Filter further narrows it", () => {
  assert.deepEqual(starts(applyTiming(boundaryDay, "", ["early-am", "evening", "late-pm"])), ["00:00", "05:59", "17:00", "20:59", "21:00", "23:59"]);
  assert.deepEqual(starts(applyTiming(boundaryDay, "after 6pm", ["am", "evening"])), ["20:59"]);
  assert.deepEqual(applyTiming(boundaryDay, "before noon", ["evening"]), []);
});

const week = ["2026-09-29", "2026-09-30", "2026-10-03", "2026-10-04", "2026-10-05", "2026-10-06", "2026-10-11", "2026-10-12"]
  .map(date => ({ date, startTimes: ["08:00", "09:59", "10:00", "12:00", "17:00", "18:00", "18:01", "19:00", "19:01", "21:00"].map(startTime => ({ startTime, courses: [{ courseId: "209806" }] })) }));
const phraseCases = [
  ["after 6pm", (date, minute) => minute > 1080],
  ["Tuesday or Wednesday evening", (date, minute, day) => [2, 3].includes(day) && minute >= 1020 && minute < 1260],
  ["before noon", (date, minute) => minute < 720],
  ["Saturday morning", (date, minute, day) => day === 6 && minute >= 360 && minute < 720],
  ["after work next week", (date, minute) => date >= "2026-10-05" && date <= "2026-10-11" && minute > 1020],
  ["anything after 7pm", (date, minute) => minute > 1140],
  ["weekdays before 10am", (date, minute, day) => day >= 1 && day <= 5 && minute < 600],
];
for (const [query, predicate] of phraseCases) {
  test(`Smart Filter: ${query}`, () => {
    const constraints = timing.compile([], query, referenceDate);
    assert.equal(constraints.valid, true);
    assert.ok(constraints.summary);
    const expected = week.flatMap(day => day.startTimes.filter(slot => predicate(day.date, shared.startMinutes(slot.startTime), new Date(`${day.date}T12:00:00Z`).getUTCDay())).map(slot => `${day.date}|${slot.startTime}`));
    const actual = timing.filterDates(week, constraints).flatMap(day => day.startTimes.map(slot => `${day.date}|${slot.startTime}`));
    assert.deepEqual(actual, expected);
  });
}

test("unavailable periods exclude only the requested day/time intersection", () => {
  for (const query of ["can't Tuesday evening", "I cannot Tuesday evening", "avoid Tuesday evening"]) {
    const expected = week.flatMap(day => day.startTimes.filter(slot => !(new Date(`${day.date}T12:00:00Z`).getUTCDay() === 2 && shared.startMinutes(slot.startTime) >= 1020 && shared.startMinutes(slot.startTime) < 1260)).map(slot => `${day.date}|${slot.startTime}`));
    assert.deepEqual(applyTiming(week, query).flatMap(day => day.startTimes.map(slot => `${day.date}|${slot.startTime}`)), expected);
  }
  assert.deepEqual(starts(applyTiming(boundaryDay, "after 6pm except after 9pm")), ["20:59", "21:00"]);
});

test("explicit alternatives and bounded times retain their meaning", () => {
  assert.deepEqual(starts(applyTiming(boundaryDay, "before 6am or after 9pm")), ["00:00", "05:59", "23:59"]);
  assert.deepEqual(starts(applyTiming(boundaryDay, "between 6am and noon")), ["06:00", "11:59"]);
  assert.deepEqual(starts(applyTiming(boundaryDay, "after 6am and before noon")), ["11:59"]);
  assert.deepEqual(starts(applyTiming(boundaryDay, "at or after 9pm")), ["21:00", "23:59"]);
  assert.deepEqual(starts(applyTiming(boundaryDay, "after 9pm and before midnight")), ["23:59"]);
});

test("unsupported or ambiguous language never silently drops part of a preference", () => {
  for (const query of ["after 6", "after 25pm", "before 10:99am", "Tuesday before noon or maybe Friday", "after 6pm near Raleigh", "Tuesday after my shift", "not after work unless Wednesday", "Tuesday; Wednesday", "between 9pm and 6am", "2026-02-30", "except"]) {
    const constraints = timing.compile([], query, referenceDate);
    assert.equal(constraints.valid, false, query);
    assert.ok(constraints.error, query);
    assert.deepEqual(timing.filterDates(week, constraints), [], query);
  }
});

test("relative dates use the supplied business date, including DST and year boundaries", () => {
  for (const [today, min, max] of [["2026-11-01", "2026-11-02", "2026-11-08"], ["2026-12-31", "2027-01-04", "2027-01-10"], ["2026-10-05", "2026-10-12", "2026-10-18"]]) {
    const { include: [rule] } = timing.compile([], "after work next week", today);
    assert.equal(rule.dateMin, min);
    assert.equal(rule.dateMax, max);
  }
  assert.equal(timing.compile([], "tomorrow", "2026-12-31").include[0].dateMin, "2027-01-01");
  const ny = shared.businessNow("America/New_York", new Date("2026-09-30T02:00:00Z"));
  assert.equal(timing.compile([], "today", ny.dateKey).include[0].dateMin, "2026-09-29");
});

test("invalid feed times fail closed while 12-hour and 24-hour starts agree", () => {
  const dates = [{ date: referenceDate, startTimes: ["6:00 PM", "18:00", "12:00 AM", "00:00", "TBD", "24:00", "13:00 PM", "18:75"].map(startTime => ({ startTime })) }];
  assert.deepEqual(starts(applyTiming(dates, "", ["evening"])), ["6:00 PM", "18:00"]);
  assert.deepEqual(starts(applyTiming(dates, "", ["early-am"])), ["12:00 AM", "00:00"]);
});

test("no results stay empty; clear restores the original family projection without mutation", () => {
  const original = JSON.stringify(week);
  assert.deepEqual(applyTiming(week, "after 11pm"), []);
  assert.strictEqual(applyTiming(week), week);
  assert.equal(JSON.stringify(week), original);
});

test("BLS and ACLS real artifacts are only narrowed, preserving course IDs and registration URLs", () => {
  for (const key of ["bls", "acls"]) {
    const source = payload(key);
    const original = JSON.stringify(source);
    const ids = new Set(source.dates.flatMap(day => day.startTimes.flatMap(slot => slot.courses.map(course => String(course.courseId)))));
    assert.ok(ids.size > 0, key);
    for (const id of ids) {
      const family = shared.filterDatesByCourse(source.dates, id);
      for (const query of phraseCases.map(([phrase]) => phrase).concat("can't Tuesday evening", "")) {
        const filtered = applyTiming(family, query);
        for (const day of filtered) {
          const originalDay = family.find(item => item.date === day.date);
          for (const slot of day.startTimes) {
            assert.ok(originalDay.startTimes.includes(slot), `${key}: slot must be an existing object`);
            assert.ok(slot.courses.every(course => String(course.courseId) === id), `${key}: course context preserved`);
          }
        }
      }
      assert.deepEqual(applyTiming(family), family);
    }
    assert.equal(JSON.stringify(source), original);
  }
});
