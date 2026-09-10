import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import { hmacSha256, normalizePayload, signatureBase, verifyRequest } from "../supabase/functions/_shared/rachel-phone-intake-core.mjs";

const fixtureUrl = new URL("./fixtures/marblism_rachel_test_call.json", import.meta.url);
const migrationUrl = new URL("../supabase/migrations/20260909120000_receptionist_phone_intakes.sql", import.meta.url);
const functionUrl = new URL("../supabase/functions/rachel-phone-intake/index.ts", import.meta.url);
const fixture = JSON.parse(await readFile(fixtureUrl, "utf8"));
const migration = await readFile(migrationUrl, "utf8");
const edge = await readFile(functionUrl, "utf8");

test("normalizes the representative Marblism test-call fixture", () => {
  const normalized = normalizePayload(fixture);
  assert.equal(normalized.source, "marblism_rachel");
  assert.equal(normalized.test_call, true);
  assert.equal(normalized.call.duration_seconds, 169);
  assert.equal(normalized.caller.phone, "+19105550193");
  assert.equal(normalized.flags.human_review_required, true);
});

test("requires a real external id and caller phone", () => {
  assert.throws(() => normalizePayload({ ...fixture, external_call_id: "" }), /external_call_id_required/);
  assert.throws(() => normalizePayload({ ...fixture, caller: { ...fixture.caller, phone: "unknown" } }), /caller_phone_required/);
});

test("verifies HMAC with timestamp and nonce and rejects replay-window expiry", async () => {
  const rawBody = JSON.stringify(fixture);
  const secret = "local-test-secret";
  const timestamp = "1788800000";
  const nonce = "nonce-1234567890abcdef";
  const signature = await hmacSha256(secret, signatureBase(timestamp, nonce, rawBody));
  assert.equal(await verifyRequest({ rawBody, timestamp, nonce, signature, secret, nowMs: 1788800000 * 1000 }), true);
  assert.equal(await verifyRequest({ rawBody, timestamp, nonce, signature, secret, nowMs: (1788800000 + 301) * 1000 }), false);
});

test("database contract retains tests without creating operational work", () => {
  assert.match(migration, /if v_call\.test_call then[\s\S]*'operationalWorkCreated',false/);
  assert.match(migration, /unique \(source, external_call_id\)/);
  assert.match(migration, /primary key \(key_id, nonce\)/);
  assert.match(migration, /title text not null default 'NEW PHONE INTAKE'/);
  assert.match(migration, /insert into public\.landerware_activity_events/);
  assert.doesNotMatch(migration, /insert into public\.landerware_(registrations|sessions)/);
});

test("endpoint is server-to-server, signed, size-limited, and service-role only", () => {
  assert.match(edge, /x-landerware-signature/);
  assert.match(edge, /MAX_BODY_BYTES/);
  assert.match(edge, /landerware_ingest_phone_intake/);
  assert.doesNotMatch(edge, /access-control-allow-origin/i);
  assert.match(migration, /revoke execute on function public\.landerware_ingest_phone_intake\(jsonb,text,text,text\) from public, anon, authenticated/);
});
