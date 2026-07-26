import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const source = await readFile(new URL("../worker/admin-api.js", import.meta.url), "utf8");
const moduleUrl = `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
const { handleAdminApi, adminApiInternals } = await import(moduleUrl);

function request(path, { method = "GET", key = "", origin = "https://www.910cpr.com", body, headers = {} } = {}) {
  return new Request(`https://schedule.910cpr.com${path}`, {
    method,
    headers: { Origin: origin, "X-Hot-Sync-Admin-Key": key, ...headers },
    body,
  });
}

test("unauthorized HOT_SYNC read and write are rejected", async () => {
  const env = { HOT_SYNC_ADMIN_KEY: "correct" };
  const read = await handleAdminApi(request("/admin/hot-sync"), env, new URL("https://schedule.910cpr.com/admin/hot-sync"));
  const write = await handleAdminApi(request("/admin/hot-sync", { method: "POST", key: "wrong", body: "{}", headers: { "Content-Type": "application/json" } }), env, new URL("https://schedule.910cpr.com/admin/hot-sync"));
  assert.equal(read.status, 401);
  assert.equal(write.status, 401);
});

test("unconfigured service and missing persistence report unavailable", async () => {
  const url = new URL("https://schedule.910cpr.com/admin/hot-sync");
  assert.equal((await handleAdminApi(request("/admin/hot-sync"), {}, url)).status, 503);
  assert.equal((await handleAdminApi(request("/admin/hot-sync", { key: "correct" }), { HOT_SYNC_ADMIN_KEY: "correct" }, url)).status, 503);
});

test("origin restriction rejects public cross-origin writes", async () => {
  const url = new URL("https://schedule.910cpr.com/admin/hot-sync");
  const response = await handleAdminApi(request("/admin/hot-sync", { method: "POST", key: "correct", origin: "https://attacker.example", body: "{}" }), { HOT_SYNC_ADMIN_KEY: "correct" }, url);
  assert.equal(response.status, 403);
});

test("class normalization validates required fields and server-controlled values", () => {
  assert.throws(() => adminApiInternals.normalizeClass({}, "hs_valid123"), /required|Start/i);
  const record = adminApiInternals.normalizeClass({
    source: "untrusted",
    course_display_name: "AHA BLS",
    start: "2026-07-27T13:00:00-04:00",
    end: "2026-07-27T16:00:00-04:00",
    client_name: "Test Client",
    location_name: "Wilmington",
    instructor: "Brian",
    status: "committed",
    visibility: "hidden",
  }, "hs_valid123");
  assert.equal(record.source, "hot_sync_manual");
  assert.equal(record.needs_class_report_absorption, true);
  assert.equal(adminApiInternals.blocksAvailability(record), true);
});

test("cancelled and tentative classes do not block availability", () => {
  assert.equal(adminApiInternals.blocksAvailability({ status: "cancelled", needs_class_report_absorption: true }), false);
  assert.equal(adminApiInternals.blocksAvailability({ status: "tentative", needs_class_report_absorption: true }), false);
});

test("IDs reject path traversal", () => {
  assert.throws(() => adminApiInternals.cleanId("../../secret"), /invalid/i);
  assert.equal(adminApiInternals.cleanId("inbox_safe_123"), "inbox_safe_123");
});

test("unauthorized upload is rejected before file processing", async () => {
  const url = new URL("https://schedule.910cpr.com/admin/inbox");
  const response = await handleAdminApi(request("/admin/inbox", { method: "POST", body: new FormData() }), { HOT_SYNC_ADMIN_KEY: "correct" }, url);
  assert.equal(response.status, 401);
});
