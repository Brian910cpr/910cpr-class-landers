const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { freshness, validateUpload, hotSyncSaveRequest, parseStudentText, MAX_FILE_BYTES } = require("../docs/admin/dashboard-ops.js");

const NOW = Date.parse("2026-07-26T20:00:00Z");

test("freshness formats minutes and applies good state", () => {
  assert.deepEqual(freshness("2026-07-26T19:52:00Z", NOW), {
    text: "Published 8 minutes ago",
    detail: new Date("2026-07-26T19:52:00Z").toLocaleString(),
    state: "good",
  });
});

test("freshness formats hours and minutes", () => {
  assert.equal(freshness("2026-07-26T18:48:00Z", NOW).text, "Published 1 hour 12 minutes ago");
});

test("freshness formats days", () => {
  assert.equal(freshness("2026-07-24T20:00:00Z", NOW).text, "Published 2 days ago");
});

test("freshness handles missing and invalid timestamps without fabrication", () => {
  assert.equal(freshness("", NOW).text, "Publish time unavailable");
  assert.equal(freshness("not-a-date", NOW).text, "Publish time unavailable");
});

test("freshness treats small and large future clock skew as just now", () => {
  assert.equal(freshness("2026-07-26T20:03:00Z", NOW).text, "Published just now");
  assert.equal(freshness("2026-07-27T20:00:00Z", NOW).text, "Published just now");
});

test("freshness state thresholds are good, warning, and stale", () => {
  assert.equal(freshness("2026-07-26T19:15:00Z", NOW).state, "good");
  assert.equal(freshness("2026-07-26T19:14:00Z", NOW).state, "warn");
  assert.equal(freshness("2026-07-26T18:00:00Z", NOW).state, "warn");
  assert.equal(freshness("2026-07-26T17:59:00Z", NOW).state, "bad");
});

test("upload validation accepts supported files and rejects unsafe inputs", () => {
  assert.equal(validateUpload({ name: "roster.PDF", size: 20 }), "");
  assert.equal(validateUpload({ name: "../payload.exe", size: 20 }), "Unsupported file type.");
  assert.equal(validateUpload({ name: "roster.pdf", size: MAX_FILE_BYTES + 1 }), "File exceeds the 15 MB limit.");
  assert.equal(validateUpload({ name: "empty.csv", size: 0 }), "The file is empty.");
});

test("local file dashboard loads its live feeds from the public site", () => {
  const html = fs.readFileSync(path.join(__dirname, "../docs/admin/dashboard.html"), "utf8");
  const operations = fs.readFileSync(path.join(__dirname, "../docs/admin/dashboard-ops.js"), "utf8");
  assert.match(html, /location\.protocol==='file:'\?'https:\/\/www\.910cpr\.com':''/);
  assert.match(html, /PUBLIC_SITE_ORIGIN\+'\/data\/admin_schedule\.json'/);
  assert.match(html, /PUBLIC_SITE_ORIGIN\+url/);
  assert.match(operations, /root\.location\?\.protocol === "file:" \? "https:\/\/www\.910cpr\.com" : ""/);
});

test("admin authentication uses an on-page unlock control instead of a password prompt", () => {
  const html = fs.readFileSync(path.join(__dirname, "../docs/admin/dashboard.html"), "utf8");
  const operations = fs.readFileSync(path.join(__dirname, "../docs/admin/dashboard-ops.js"), "utf8");
  assert.match(html, /id="adminKeyInput" type="password"/);
  assert.match(html, /id="adminUnlockBtn"/);
  assert.match(html, /id="adminForgetBtn"/);
  assert.doesNotMatch(html, /prompt\(['"]HOT_SYNC admin key/);
  assert.doesNotMatch(operations, /prompt\(['"]LanderWare admin key/);
  assert.match(operations, /sessionStorage\.setItem\("hotSyncAdminKey", key\)/);
  assert.match(operations, /sessionStorage\.removeItem\("hotSyncAdminKey"\)/);
});

test("new HOT_SYNC records POST even after a client ID is generated", () => {
  const record = { id: "hs-client-generated" };
  assert.deepEqual(hotSyncSaveRequest(record, false), {
    method: "POST",
    endpoint: "https://schedule.910cpr.com/admin/hot-sync",
  });
  assert.deepEqual(hotSyncSaveRequest(record, true), {
    method: "PUT",
    endpoint: "https://schedule.910cpr.com/admin/hot-sync/hs-client-generated",
  });
});

test("student intake parses email paste, line lists, and CSV headers", () => {
  assert.deepEqual(parseStudentText("Jane Doe <jane@example.com>\n- John Smith 910-555-1212"), [
    { first_name: "Jane", last_name: "Doe", email: "jane@example.com", phone: "", employee_id: "", notes: "", raw_input: "Jane Doe <jane@example.com>" },
    { first_name: "John", last_name: "Smith", email: "", phone: "910-555-1212", employee_id: "", notes: "", raw_input: "- John Smith 910-555-1212" },
  ]);
  assert.deepEqual(parseStudentText("First Name,Last Name,Email,Employee ID\nAmy,Jones,amy@example.com,E-42")[0], {
    first_name: "Amy", last_name: "Jones", email: "amy@example.com", phone: "", employee_id: "E-42", notes: "", raw_input: "Amy,Jones,amy@example.com,E-42",
  });
});

test("student intake UI supports paste and private source documents", () => {
  const html = fs.readFileSync(path.join(__dirname, "../docs/admin/dashboard.html"), "utf8");
  assert.match(html, /id="studentPaste"/);
  assert.match(html, /id="studentFileDrop"/);
  assert.match(html, /PDF, Excel, Word, PNG, and JPG are privately attached/);
});

test("planner merges committed HOT_SYNC classes and suppresses overlapping offer starts", () => {
  const html = fs.readFileSync(path.join(__dirname, "../docs/admin/dashboard.html"), "utf8");
  const operations = fs.readFileSync(path.join(__dirname, "../docs/admin/dashboard-ops.js"), "utf8");
  assert.match(html, /function applyHotSyncRecords\(records\)/);
  assert.match(html, /r\.status==='committed'&&r\.needs_class_report_absorption/);
  assert.match(html, /function offerIsHotSyncBlocked\(offer\)/);
  assert.match(operations, /root\.applyHotSyncRecords\(records\)/);
});
