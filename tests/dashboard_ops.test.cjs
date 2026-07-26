const test = require("node:test");
const assert = require("node:assert/strict");
const { freshness, validateUpload, MAX_FILE_BYTES } = require("../docs/admin/dashboard-ops.js");

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
