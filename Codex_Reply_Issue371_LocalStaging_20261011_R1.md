# Issue 371 local staging checkpoint

Timestamp: 2026-10-11 America/New_York (UTC-04:00).
Branch: codex/issue371-local-preflight-20261011; continues existing draft PR372 / feat/customer-learning-studio-20261010.
Substantive commit: 36170d7a3b32f938f3af36b0ecad8a537ab33914.
State: IN_PROGRESS / PR_OPEN; full local Supabase integration BLOCKED. Evidence: BUILT, with local disk-reopen behavioral validation only.

## Execution and findings

Read full originating issue including latest owner local-staging directive, AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard. Actual pickup acknowledged before implementation at https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6105930229 . Queue titles scanned; existing assignments preserved, no additional deep stream opened.

E:/GitHub/910cpr-class-landers contains unrelated dirty work and broken object reference refs/remotes/origin/codex/group-training-experience; fetch failed. No refs deleted or checkout cleanup attempted. Isolated shallow checkout E:/GitHub/910cpr-issue371-staging-20261011 used. Original full clone attempt E:/GitHub/910cpr-issue371-local-20261011 was not usable at checkpoint; it is not authoritative work. Fresh Windows checkout reports case-colliding Earl/Jackson pages; excluded from staging.

CyberPC: WSL status says not installed (exit 1); no Docker executable on PATH or standard installation path, no Docker/Podman found in inspected common install roots. Disk sufficient (C ~1.57 TB / E ~1.20 TB free). Get-SmbMapping returned no mappings; no approved Synology UNC destination known. Runtime and NAS security/access are unproven. No privileged install, NAS writes, production secrets or private customer data used.

## Intended files changed

- tests/customer_interaction_restart.test.mjs
- docs/CUSTOMER_INTERACTION_LOCAL_STAGING.md
- Codex_Reply_Issue371_LocalStaging_20261011_R1.md (this receipt)

No source/config/schema/UI changed. New synthetic disk-backed test executes existing three additive migrations, preserves raw notes/selection/interruption audit across close/reopen, retries original request, rejects stale save, resumes and reopens again, checks authenticated-role denial. Cleanup is limited to its uniquely created synthetic temp database.

## Exact validation

PGLITE_MODULE=file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js (existing scratch installation).

node --check tests/customer_interaction_restart.test.mjs
node --experimental-strip-types --test tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs tests/customer_interruptions_sql.test.mjs tests/customer_interaction_pagination.test.mjs tests/customer_interaction_restart.test.mjs tests/admin_auth.test.mjs

Result: tests 36; pass 36; fail 0; skipped 0. git diff --check passed. No type-check needed for unchanged function source. No generators run.

## Proof boundary and blockers

Last successful proof: local synthetic SQL suite this dispatch, October 11, 2026. Not a real owner-session -> browser -> Edge API proof; not power-loss durability or concurrent-process proof. Expected outcome remains durable customer capture/reload/resume on demand. Failure is denied/failed save, missing receipt or stale versions. Automated CRM observer and its health remain unestablished; do not call this MONITORED/HEALTHY. Existing launcher/supervisor arrangement was not changed or revalidated.

Exact owner-only action: approve prerequisite privileged Docker/WSL2 installation and required Windows feature/reboot after platform checks, as mandated by latest issue safety gate. Identify authorized Synology UNC backup folder/security requirements; no secrets in issue. Earlier paid-cloud-preview gate is superseded by local staging authorization, not still awaiting a cloud project. Next Codex action: establish approved container environment, localhost-only isolated Supabase config and synthetic owner fixture, then prove UI/API/storage path. Do not redirect production to local endpoints or widen production origins.

Deployment: locally persisted and validated; intended files committed; receipt and changes to be pushed on named branch and existing PR372 branch. No merge, deployment, production migration or auth change. PR372 remains draft. No Codex_Read file or retired ops/handoff/next_task.md used. Unrelated files intentionally uncommitted/excluded.

ChatGPT next action: review the two exact files above and secure installation approval / backup-path decision on #371. Keep original complete customer workflow scope and all existing assignments. Resume smallest isolated integration slice after prerequisites; do not mistake SQL tests for connected browser service.
