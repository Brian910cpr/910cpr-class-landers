const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const root = path.join(__dirname, "..");
const sourcePath = path.join(root, "supabase/functions/session-workspace/index.ts");
const sourceBytes = fs.readFileSync(sourcePath);
const source = sourceBytes.toString("utf8");
const manifest = JSON.parse(fs.readFileSync(path.join(root, "supabase/functions/session-workspace/deployment.json"), "utf8"));

test("committed source is byte-exact to the independently exported production baseline", () => {
  const hash = crypto.createHash("sha256").update(sourceBytes).digest("hex");
  assert.equal(hash, "5253d0e8018705635ab9fc670e7d910d77a2bc1ce71b7217af731127277a7796");
  assert.equal(hash, manifest.live_source_sha256);
  assert.equal(manifest.live_version, 2);
  assert.equal(manifest.live_source_match, true);
});

test("deployment metadata preserves anonymous platform access and internal authorization", () => {
  assert.equal(manifest.verify_jwt, false);
  assert.equal(manifest.authorization_boundary, "x-maxim-session");
  assert.match(source, /req\.headers\.get\('x-maxim-session'\)/);
  assert.match(source, /result\.session&&await authorized\(req\)/);
  assert.match(source, /authorized:false/);
});

test("anonymous summaries cannot call participant detail queries", () => {
  const summariesBranch = source.match(/if\(action==='summaries'[\s\S]+?if\(action==='resolve'/)?.[0] || "";
  assert.match(summariesBranch, /await summary\(item\)/);
  assert.doesNotMatch(summariesBranch, /details\(/);
  assert.doesNotMatch(summariesBranch, /landerware_people|current_email|current_phone/);
});

test("unauthorized resolve returns summary without participant details", () => {
  assert.match(source, /if\(result\.session&&await authorized\(req\)\)return json\(req,\{ok:true,\.\.\.result,details:await details\(result\.session\.id\),authorized:true\}\);return json\(req,\{ok:true,\.\.\.result,authorized:false\}\)/);
});

test("unknown imported counts stay null rather than becoming false zeroes", () => {
  assert.match(source, /participant_count:aggregate\?Number\(input\.registeredCount\):null/);
  assert.match(source, /count_available:aggregate/);
  assert.match(source, /count_source:aggregate\?'imported_aggregate':'unavailable'/);
});

test("live baseline explicitly retains its landerware runtime dependencies", () => {
  for (const table of manifest.runtime_tables) assert.match(source, new RegExp(table));
  assert.doesNotMatch(source, /class_sessions\?|registrations\?class_session_id=|customers\?id=in/);
});

test("repository deploy path is check-only by default and pins no-verify-jwt", () => {
  const deploy = fs.readFileSync(path.join(root, "scripts/deploy_session_workspace.ps1"), "utf8");
  assert.match(deploy, /\[switch\]\$Deploy/);
  assert.match(deploy, /if \(-not \$Deploy\)/);
  assert.match(deploy, /live_source_sha256/);
  assert.match(deploy, /--no-verify-jwt/);
});
