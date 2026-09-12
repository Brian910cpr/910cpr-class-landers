const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.join(__dirname, "..");
const source = fs.readFileSync(path.join(root, "supabase/functions/session-workspace/index.ts"), "utf8");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "supabase/functions/session-workspace/deployment.json"), "utf8"));
const schema = JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures/production_session_workspace_schema.json"), "utf8"));

test("deployment contract keeps anonymous platform access and internal detail authorization", () => {
  assert.equal(manifest.verify_jwt, false);
  assert.equal(manifest.authorization_boundary, "x-maxim-session");
  assert.match(source, /req\.headers\.get\(['"]x-maxim-session['"]\)/);
  assert.match(source, /result\.session\s*&&\s*await authorized\(req\)/);
  assert.match(source, /authorized:\s*false/);
  assert.match(source, /if \(result\.session\s*&&\s*await authorized\(req\)\)[\s\S]+?details:\s*await details/);
});

test("anonymous summary exposes counts, never participant detail", () => {
  const summariesBranch = source.match(/if \(action === "summaries"[\s\S]+?if \(action === "resolve"/)?.[0] || "";
  assert.match(summariesBranch, /await summary\(item\)/);
  assert.doesNotMatch(summariesBranch, /details\(/);
  assert.doesNotMatch(summariesBranch, /customers|first_name|email|phone/);
});

test("unknown imported counts remain null instead of becoming false zeroes", () => {
  assert.match(source, /participant_count:\s*aggregate\s*\?\s*Number\(input\.registeredCount\)\s*:\s*null/);
  assert.match(source, /count_available:\s*aggregate/);
  assert.match(source, /count_source:\s*aggregate\s*\?\s*"imported_aggregate"\s*:\s*"unavailable"/);
});

test("runtime uses current-main canonical participant/session objects, not stale landerware tables", () => {
  assert.match(source, /class_sessions\?/);
  assert.match(source, /registrations\?class_session_id=/);
  assert.match(source, /customers\?id=in/);
  assert.doesNotMatch(source, /landerware_(sessions|registrations|people|registration_requirements|credentials|activity_events)/);
});

test("literal REST selects are covered by the captured production schema", () => {
  const objects = [...source.matchAll(/rest\(`([a-z][a-z0-9_]*)\?/g)].map((match) => match[1]);
  assert.ok(objects.length > 0);
  assert.deepEqual([...new Set(objects)].filter((name) => !schema.objects[name]), []);
  const sessionFields = source.match(/const SESSION_SELECT = "([^"]+)"/)[1].split(",");
  for (const field of sessionFields) assert.ok(schema.objects.class_sessions.includes(field), `class_sessions.${field} absent from contract`);
});

test("repository deployment path is pinned to no-verify-jwt and parity gate", () => {
  const deploy = fs.readFileSync(path.join(root, "scripts/deploy_session_workspace.ps1"), "utf8");
  assert.match(deploy, /--no-verify-jwt/);
  assert.match(deploy, /ExpectedLiveSourceSha256/);
  assert.match(deploy, /Source hash does not match independently established live hash/);
});
