const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { scheduleRows, normalizeSessions, monthSummary, reconcileSchedule } = require("../docs/admin/schedule-model.js");

const fixture = JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures/admin_schedule_multiple_sessions.json"), "utf8"));
const parseDate = (value) => { const date = new Date(value); return Number.isNaN(date.getTime()) ? null : date; };
const courseName = (record) => record.course_name || "Class";
const keyOf = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;

test("production-schema sessions normalize without collapsing overlaps or instructors", () => {
  const sessions = normalizeSessions(fixture, parseDate, courseName);
  assert.equal(scheduleRows(fixture).length, 5);
  assert.equal(sessions.length, 5);
  const august19 = sessions.filter((session) => keyOf(session._start) === "2026-08-19");
  assert.equal(august19.length, 4);
  assert.equal(new Set(august19.map((session) => session.session_id)).size, 4);
  assert.deepEqual(new Set(august19.map((session) => session.lead_instructor_name)), new Set(["Brian Ennis", "Amy Jones", "Graves"]));
  assert.equal(august19.filter((session) => session._start.getHours() === 9).length, 3);
});

test("month reconciliation counts every session and every marked date", () => {
  const sessions = normalizeSessions(fixture, parseDate, courseName);
  const summary = monthSummary(sessions, 2026, 7, keyOf);
  assert.deepEqual(summary, { sessionCount: 5, dateCount: 2 });
  assert.deepEqual(reconcileSchedule({
    loadedCount: 5, normalizedCount: 5,
    monthSessionCount: 5, monthDateCount: 2,
    renderedSessionCount: 5, renderedDateCount: 2,
  }), { ok: true, errors: [] });
});

test("reconciliation fails loudly for a 23-loaded-to-1-rendered calendar", () => {
  const result = reconcileSchedule({
    loadedCount: 23, normalizedCount: 23,
    monthSessionCount: 23, monthDateCount: 8,
    renderedSessionCount: 1, renderedDateCount: 1,
  });
  assert.equal(result.ok, false);
  assert.match(result.errors.join(" "), /23 sessions belong to this month but only 1/);
  assert.match(result.errors.join(" "), /8 dates should contain classes but only 1/);
});

test("dashboard startup has no dead legacy month bindings and schedule read remains independent of HOT_SYNC auth", () => {
  const html = fs.readFileSync(path.join(__dirname, "../docs/admin/dashboard.html"), "utf8");
  assert.doesNotMatch(html, /getElementById\(['"]prevMonth['"]\)/);
  assert.doesNotMatch(html, /getElementById\(['"]nextMonth['"]\)/);
  assert.match(html, /clearRecord\(\);load\(\)/);
  assert.match(html, /fetch\(`\$\{SCHEDULE_URL\}\?v=\$\{Date\.now\(\)\}`/);
  assert.match(html, /id="scheduleIntegrity"/);
  assert.match(html, /data-class-count=/);
  assert.doesNotMatch(html, /fetch\(`\$\{SCHEDULE_URL\}[^`]*X-Hot-Sync-Admin-Key/);
});
