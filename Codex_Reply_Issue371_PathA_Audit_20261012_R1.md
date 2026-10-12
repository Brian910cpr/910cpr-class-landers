# Codex reply — Issue371 PathA Audit 20261012 R1

Timestamp: 2026-10-12T09:47:00-04:00 (America/New_York).
Assignment: #371, existing draft PR https://github.com/Brian910cpr/910cpr-class-landers/pull/372 .
Review branch: codex/issue371-patha-20261012. Delivery branch: feat/customer-learning-studio-20261010.
Substantive commit: a2798d1873f9537d81246ad5572ec135a81adb65.
State: IN_PROGRESS / PR_OPEN; production rollout BLOCKED on remaining safety gates. Evidence: BUILT / validated locally. No merge or deployment.

## Execution and findings

Actual execution acknowledged before implementation on originating issue: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6125469045 . Full issue/body/comments and repository AGENTS, handoff, ethos and proof rules read. Latest owner Path A supersedes Docker/WSL/Synology staging for this milestone. No third-party instruction used as owner authorization.

Read-only live Supabase catalog audit found new-object defaults granting service_role ALL table privileges. Original pending CRM migrations only added SELECT/INSERT and therefore left audit UPDATE/DELETE/TRUNCATE inherited. Local regression reproduced the failure, then passed after explicit service_role revocation before allowlisted grants. Six CRM tables and three RPCs are absent live; customer-interactions function is undeployed. Existing owner-access v5 and owner-session source reviewed read-only. No customer row or secret collected.

## Exact changed files / review targets

- supabase/migrations/20261010210607_customer_interaction_storage.sql
- supabase/migrations/20261010211804_customer_interaction_interruptions.sql
- supabase/migrations/20261010212019_customer_follow_up_task_mutations.sql
- tests/customer_interaction_grants.test.mjs
- data/audit/issue371_patha_metadata_20261012.json
- docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md
- Codex_Reply_Issue371_PathA_Audit_20261012_R1.md (this receipt)

The full primary report is docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md, committed with code on the named review branch and existing PR. JSON metadata[0].default_acl shows the exact live ACLs; metadata[0].tables shows only existing owner auth objects among the queried six CRM/auth names; metadata[0].functions is null; edge_functions contains deployed slugs/versions/JWT settings. `query` retains exact read-only SQL. Key source review: supabase/functions/customer-interactions/index.ts and handler.ts, supabase/functions/_shared/owner-auth.ts and owner-session.ts, docs/admin/admin-auth.js and customer-learning.html. These source files were reviewed, not changed in this increment.

## Exact validation results

Before correction, `node --test tests/customer_interaction_grants.test.mjs` failed:
```
service_role UPDATE customer_interaction_events
true !== false
# tests 1
# pass 0
# fail 1
```

After correction:
```
node --experimental-strip-types --test tests/customer_interactions.test.mjs tests/customer_interactions_sql.test.mjs tests/customer_interruptions_sql.test.mjs tests/customer_interaction_pagination.test.mjs tests/customer_interaction_restart.test.mjs tests/customer_interaction_grants.test.mjs tests/admin_auth.test.mjs
# tests 38
# suites 0
# pass 38
# fail 0
# cancelled 0
# skipped 0
# todo 0
```
Scratch PGLITE_MODULE reused at file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js (0.3.14). No new dependency. `node --check tests/customer_interaction_grants.test.mjs`, `npx --yes deno check supabase/functions/customer-interactions/index.ts` and `git diff --check` passed. Real SQL migrations/RPCs/default ACLs executed locally with synthetic data; no real owner browser/API proof or restore drill.

## Blockers and exact next action

Production gate is NOT passed. Actual recoverable backup/export, restore capability and secure destination have not been verified. Studio is still tab-local; feature-gated durable UI integration and real owner-session UI/API/database reload/resume/conflict/failure proof remain unfinished. CORS permits apex authorization but responds www-only; use canonical www or restrict reflection to current two origins with tests. Client endpoint allowlist must be updated only with tested UI connection. No broad origin expansion is authorized.

Next Codex step: continue existing PR372 with feature-gated UI/runtime test work and read-only backup/recovery verification. Do not request installation approval. Exact future production GO scope and staged reversal/recovery plan are in the full report; do not ask Brian to approve incomplete safety evidence. Once gates pass, request explicit GO for the reviewed commit's three additive migrations and customer-interactions only, UI flag OFF, PR draft; production UI exposure/merge needs separate express approval. No current owner action needed for eligible code/test continuation; backup access may require a precise account-level action if an authorized read-only route is unavailable. Never post secrets.

Persistent proof contract: expected outcome is saved owner interaction/follow-up surviving browser close and interruption/resume; on-demand cadence. Last proof: synthetic SQL suite on 2026-10-12, not end-to-end browser/API proof. Failure: missing receipt, failed write/version conflict or unrecoverable draft; recover via identical retry or explicit reload/reconcile, never blind overwrite. CRM outcome observer/observer health not established; not MONITORED/HEALTHY. Existing launcher heartbeat at 13:42:02Z showed task371 working; launcher, assignments and monitors unchanged.

## Preservation / deployment boundary

E:/GitHub/910cpr-class-landers fetch failed with bad object 6e61cabca5981d1389e52c60d95424d9893bb50f and broken origin/codex/group-training-experience. No cleanup or repeated repair attempted. Used healthy D: repository to create isolated E:/GitHub/910cpr-issue371-patha-20261012 from PR tip f304aeff00395bc33732d1879dc8a5f2fd77649a. Original dirty files, receipt backlog and runtime artifacts preserved. Windows case-collision docs/Earl/index.html and docs/Jackson/index.html also appear dirty in the new worktree; excluded explicitly, no reset/restore. No unrelated files staged. Queue titles scanned; no additional assignment displaced or touched.

Locally persisted and committed; receipt and intended files to be pushed on review branch and existing PR branch, with GitHub existence verified before final response. No production migrations/API writes/function deployment, UI exposure, lander rebuild, merge, privileged install, reboot, NAS write, new launcher or duplicate PR. No Codex_Read file or ops/handoff/next_task.md created.
