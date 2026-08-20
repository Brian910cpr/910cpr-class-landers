const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { scheduleRows, normalizeSessions, monthSummary, reconcileSchedule, instructorName, instructorNames, annotateConflicts, brianExceptionRows } = require("../docs/admin/schedule-model.js");

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

test("instructor tabs are filters over one dataset and retain unassigned sessions", () => {
  const sessions = normalizeSessions(fixture, parseDate, courseName);
  assert.deepEqual(instructorNames(sessions), ["Amy Jones", "Brian Ennis", "Graves", "Unassigned"]);
  assert.equal(sessions.filter((session) => instructorName(session) === "Amy Jones").length, 2);
  assert.equal(sessions.filter((session) => instructorName(session) === "Unassigned").length, 1);
});

test("overlapping classes and same-location conflicts are annotated, never deduplicated", () => {
  const sessions = normalizeSessions(fixture, parseDate, courseName).filter((session) => keyOf(session._start) === "2026-08-19");
  const annotated = annotateConflicts(sessions, (session) => session.location_name || "");
  assert.equal(annotated.length, 4);
  assert.equal(annotated.find((session) => session.session_id === "aug19-amy-1")._locationConflict, true);
  assert.equal(annotated.find((session) => session.session_id === "aug19-amy-2")._locationConflict, true);
  assert.ok(annotated.filter((session) => session._overlapCount > 0).length >= 3);
});

test("Brian exception layer can be hidden without changing scheduled classes", () => {
  const events = [
    { source_type: "inverse_google_calendar", title: "Travel" },
    { source_type: "google_calendar", title: "Available" },
  ];
  assert.deepEqual(brianExceptionRows(events, true).map((event) => event.title), ["Travel"]);
  assert.deepEqual(brianExceptionRows(events, false), []);
  assert.equal(normalizeSessions(fixture, parseDate, courseName).length, 5);
});

test("dashboard startup has no dead legacy month bindings and schedule read remains independent of HOT_SYNC auth", () => {
  const html = fs.readFileSync(path.join(__dirname, "../docs/admin/dashboard.html"), "utf8");
  assert.doesNotMatch(html, /getElementById\(['"]prevMonth['"]\)/);
  assert.doesNotMatch(html, /getElementById\(['"]nextMonth['"]\)/);
  assert.match(html, /clearRecord\(\);load\(\)/);
  assert.match(html, /fetch\(`\$\{SCHEDULE_URL\}\?v=\$\{Date\.now\(\)\}`/);
  assert.match(html, /schedule-model\.js\?v=20260820-1/);
  assert.match(html, /id="scheduleIntegrity"/);
  assert.match(html, /data-class-count=/);
  assert.match(html, /class=\"instructor-tabs\"/);
  assert.match(html, /ScheduleModel\.instructorNames\(sessions\)/);
  assert.match(html, /Same-time location conflict/);
  assert.match(html, /id="brianExceptionsToggle"[^>]*checked/);
  assert.match(html, /ScheduleModel\.brianExceptionRows/);
  assert.doesNotMatch(html, /fetch\(`\$\{SCHEDULE_URL\}[^`]*X-Hot-Sync-Admin-Key/);
});
