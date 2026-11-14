# Issue #371 Path A CORS checkpoint

Timestamp: 2026-10-12 America/New_York
Branch: codex/issue371-cors-20261012
Existing PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/372
Substantive commit: a196c2671d8f68a52a71f03d035d6aef3dcfc70f
State: IN_PROGRESS / PR_OPEN. Evidence: BUILT, validated locally.

## Execution and findings
Read full issue/body/comments, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard. Acknowledged actual execution on originating issue before implementation (issuecomment-6127545158). Owner Path A supersedes local container staging. No third-party comment was used to authorize production action.

Prior audit identified static www CORS while authorization accepts exact www/apex origins. Fixed request-scoped CORS for those same two origins only, with Vary: Origin and no-store. Reject foreign origins before authorization or storage, including OPTIONS. No-Origin requests still require owner authorization. No credential, origin expansion, shared authorization or production change.

## Exact files changed
- supabase/functions/customer-interactions/handler.ts
- tests/customer_interaction_cors.test.mjs
- docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md
- Codex_Reply_Issue371_PathA_CORS_20261012_R1.md

## Commands and results
PGLITE_MODULE=file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js
node --experimental-strip-types --test tests/customer_interaction*.test.mjs tests/customer_interruptions_sql.test.mjs tests/admin_auth.test.mjs
Result: tests 42; pass 42; fail 0; cancelled/skipped/todo 0.
node --check tests/customer_interaction_cors.test.mjs — passed.
npx --yes deno check supabase/functions/customer-interactions/index.ts — passed.
git diff --check and staged diff check — passed.

Covers exact-origin preflight without private access, rejected opaque/lookalike/local/preview origins, auth denial and backend error CORS, plus prior real synthetic Postgres persistence/conflict/privacy tests. Supabase changelog/manual CORS docs fetched read-only. This is not browser/Edge Runtime integration evidence.

## Preservation and deployment
Dirty E: checkout left untouched. Separate named worktree used; Windows case-collision docs/Earl/index.html and docs/Jackson/index.html appear dirty there and were explicitly excluded. Existing assignments, launchers and monitors untouched. No generators, installs, NAS writes, production DB/API writes, deployment, merge or UI exposure. Only four intended files committed; PR372 remains draft. Push uses ordinary fast-forward to existing PR branch and named codex branch, never force.

## Exact remaining gates and next action
Production NO-GO: actual recoverable backup/restore evidence is absent; durable feature-gated Studio UI and real owner-session UI → API → database reload/resume/conflict proof are not established. Existing UI remains tab-local. Continue existing PR372 with durable feature-gated integration/runtime harness and authorized read-only backup evidence. Do not request approval of incomplete safety gates. Separate explicit owner GO is required before migrations/function deployment/UI exposure/merge. No owner action needed for continued safe code/tests; no Docker/WSL/Synology request.

Expected outcome: owner records survive closure and interruption without duplicates/loss; cadence on demand. Last local proof: this 42-test suite, 2026-10-12. End-to-end owner-browser proof remains absent. Failure: missing save receipt/conflict/unavailable storage. Recovery: retain draft/request ID, retry identical request for transient failure, reload/reconcile conflicts. CRM outcome observer and observer-health proof are unimplemented; no MONITORED/HEALTHY claim and Brian is not assigned routine checks.

Queue sweep read open CODEX issue titles; no other assignment modified or displaced. This receipt is a substantive checkpoint, not completion of #371.
