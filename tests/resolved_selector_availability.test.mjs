import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const root = path.resolve(import.meta.dirname, "..");
const shared = require(path.join(root, "docs", "assets", "resolved-selector-availability.js"));

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
