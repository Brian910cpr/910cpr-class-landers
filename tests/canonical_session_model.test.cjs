const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const model = require("../docs/admin/canonical-session-model.js");

test("durable canonical Session reports three active registrations from customers", () => {
  const session = { count_available: true, participant_count: 3, participants: [
    { customer_id: "c1", display_name: "A One" },
    { customer_id: "c2", display_name: "B Two" },
    { customer_id: "c3", display_name: "C Three" },
  ] };
  assert.equal(model.participantCount(session), 3);
  assert.equal(model.participantRows(session).length, 3);
  assert.deepEqual(model.participantRows(session).map(row => row.customer_id), ["c1", "c2", "c3"]);
});

test("true canonical zero is zero but external-only evidence is unknown", () => {
  assert.equal(model.participantCount({ count_available: true, participant_count: 0, participants: [] }), 0);
  const unknown = model.asUnknownExternal({ registered_count: 5, students_count_raw: 5 });
  assert.equal(model.participantCount(unknown), null);
  assert.equal(model.countLabel(unknown), "—");
  assert.equal(unknown.registered_count, null);
});

test("canceled and removed registration states are excluded by canonical semantics", () => {
  assert.equal(model.ACTIVE_REGISTRATION_STATUSES.has("registered"), true);
  assert.equal(model.ACTIVE_REGISTRATION_STATUSES.has("confirmed"), true);
  assert.equal(model.ACTIVE_REGISTRATION_STATUSES.has("completed"), true);
  assert.equal(model.ACTIVE_REGISTRATION_STATUSES.has("canceled"), false);
  assert.equal(model.ACTIVE_REGISTRATION_STATUSES.has("removed"), false);
  assert.equal(model.ACTIVE_REGISTRATION_STATUSES.has("rescheduled"), false);
});

test("stale zero or five cannot override canonical three", () => {
  for (const stale of [0, 5]) {
    const [merged] = model.mergeCanonical(
      [{ session_id: "s1", registered_count: stale, students_count_raw: stale }],
      [{ session_id: "s1", count_available: true, participant_count: 3, participants: [{}, {}, {}] }],
    );
    assert.equal(model.participantCount(merged), 3);
  }
});

test("durable Session absent from old snapshot retains its canonical participants", () => {
  const merged = model.mergeCanonical([], [{ session_id: "s-new", count_available: true, participant_count: 1, participants: [{ customer_id: "c1" }] }]);
  assert.equal(merged.length, 1);
  assert.equal(model.participantCount(merged[0]), 1);
});

test("operational projections cannot silently restore legacy participant fallbacks", () => {
  const root = path.resolve(__dirname, "..");
  const publisher = fs.readFileSync(path.join(root, "scripts/publish_admin_schedule.py"), "utf8");
  const builder = fs.readFileSync(path.join(root, "scripts/build_sessions_current.py"), "utf8");
  const dashboard = fs.readFileSync(path.join(root, "docs/admin/dashboard.html"), "utf8");
  assert.doesNotMatch(publisher, /apply_snapshot_to_sessions|STUDENT_SNAPSHOT/);
  assert.doesNotMatch(builder, /apply_snapshot_to_sessions|enrollware_student_snapshot\.json/);
  assert.doesNotMatch(dashboard, /students_count_raw\?\?|capacity\?\.registered_count/);
  assert.match(dashboard, /CanonicalSessionModel\.participantCount/);
  assert.doesNotMatch(dashboard, /person_id\|\|p\.participant_id/);
});
