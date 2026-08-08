import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const source = await readFile(new URL("../worker/admin-api.js", import.meta.url), "utf8");
const moduleUrl = `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
const { handleAdminApi, adminApiInternals } = await import(moduleUrl);

const workerSource = await readFile(new URL("../worker/free-time-offer-worker.js", import.meta.url), "utf8");
const workerModuleUrl = `data:text/javascript;base64,${Buffer.from(
  workerSource.replace(
    'import { handleAdminApi } from "./admin-api.js";',
    `import { handleAdminApi } from "${moduleUrl}";`,
  ),
).toString("base64")}`;
const workerModule = await import(workerModuleUrl);
const worker = workerModule.default;

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

test("deployed worker entrypoint routes admin preflight with dashboard CORS", async () => {
  const response = await worker.fetch(request("/admin/hot-sync/hs_test123", {
    method: "OPTIONS",
    headers: {
      "Access-Control-Request-Method": "PUT",
      "Access-Control-Request-Headers": "content-type,x-hot-sync-admin-key",
    },
  }), {}, {});
  assert.equal(response.status, 204);
  assert.equal(response.headers.get("Access-Control-Allow-Origin"), "https://www.910cpr.com");
  assert.match(response.headers.get("Access-Control-Allow-Methods"), /PUT/);
});

for (const [method, path] of [
  ["GET", "/admin/hot-sync"],
  ["POST", "/admin/hot-sync"],
  ["PUT", "/admin/hot-sync/hs_test123"],
  ["DELETE", "/admin/hot-sync/hs_test123"],
]) {
  test(`deployed worker entrypoint routes authenticated HOT_SYNC ${method}`, async () => {
    const hasBody = method === "POST" || method === "PUT";
    const response = await worker.fetch(request(path, {
      method,
      key: "correct",
      body: hasBody ? JSON.stringify({}) : undefined,
      headers: hasBody ? { "Content-Type": "application/json" } : {},
    }), { HOT_SYNC_ADMIN_KEY: "correct" }, {});
    assert.equal(response.status, 503);
    assert.equal(response.headers.get("Access-Control-Allow-Origin"), "https://www.910cpr.com");
    assert.equal((await response.json()).code, "storage_unavailable");
  });
}

test("entrypoint PUT persists a committed hidden class as blocking", async () => {
  const batches = [];
  const existing = {
    id: "hs_test123", source: "hot_sync_manual", status: "tentative", visibility: "hidden",
    course_key: "aha_bls", course_display_name: "AHA BLS", start_time: "2026-08-10T13:00:00.000Z",
    end_time: "2026-08-10T16:00:00.000Z", created_at: "2026-08-01T00:00:00.000Z",
    created_by: "dashboard_admin", needs_class_report_absorption: 1,
  };
  const database = {
    prepare(sql) {
      return {
        bind(...args) {
          return { sql, args, async first() { return sql.startsWith("SELECT") ? existing : null; } };
        },
      };
    },
    async batch(statements) { batches.push(statements); },
  };
  const response = await worker.fetch(request("/admin/hot-sync/hs_test123", {
    method: "PUT",
    key: "correct",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      course_key: "aha_bls",
      course_display_name: "AHA BLS",
      start: "2026-08-10T09:00:00-04:00",
      end: "2026-08-10T12:00:00-04:00",
      client_name: "Private client",
      location_name: "Wilmington",
      status: "committed",
      visibility: "hidden",
    }),
  }), { HOT_SYNC_ADMIN_KEY: "correct", HOT_SYNC_D1: database }, {});
  const payload = await response.json();
  assert.equal(response.status, 200);
  assert.equal(payload.record.visibility, "hidden");
  assert.equal(payload.blocking, true);
  assert.equal(batches.length, 1);
  assert.match(batches[0][0].sql, /^UPDATE hot_sync_sessions/);
  assert.equal(batches[0][0].args[1], "committed");
  assert.equal(batches[0][0].args[2], "hidden");
});

test("click-time recheck rejects an offer overlapping a committed hidden HOT_SYNC class", async () => {
  let queryArgs = [];
  const database = {
    prepare(sql) {
      assert.match(sql, /status = 'committed'/);
      return { bind(...args) { queryArgs = args; return { async first() { return { id: "hs_blocking" }; } }; } };
    },
  };
  const result = await workerModule.offerWorkerInternals.clickTimeRecheck({
    requested_start: "2026-08-26T09:30:00-04:00",
    requested_end: "2026-08-26T11:30:00-04:00",
  }, { HOT_SYNC_D1: database });
  assert.equal(result.available, false);
  assert.match(result.reason, /committed class/);
  assert.deepEqual(queryArgs, ["2026-08-26T15:30:00.000Z", "2026-08-26T13:30:00.000Z"]);
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

test("student normalization preserves source data and validates identity", () => {
  const student = adminApiInternals.normalizeStudent({ first_name: " Jane ", last_name: " Doe ", email: "JANE@EXAMPLE.COM", raw_input: "Jane Doe <JANE@EXAMPLE.COM>" });
  assert.equal(student.first_name, "Jane");
  assert.equal(student.email, "jane@example.com");
  assert.equal(student.raw_input, "Jane Doe <JANE@EXAMPLE.COM>");
  assert.throws(() => adminApiInternals.normalizeStudent({ phone: "910-555-1212" }), /name or email/i);
  assert.throws(() => adminApiInternals.cleanClassRef("../../class"), /invalid/i);
});

test("unauthorized upload is rejected before file processing", async () => {
  const url = new URL("https://schedule.910cpr.com/admin/inbox");
  const response = await handleAdminApi(request("/admin/inbox", { method: "POST", body: new FormData() }), { HOT_SYNC_ADMIN_KEY: "correct" }, url);
  assert.equal(response.status, 401);
});
