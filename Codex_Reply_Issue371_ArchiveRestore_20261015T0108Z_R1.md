# Issue 371 — archive restore / observer checkpoint

- Timestamp: 2026-10-15T01:08:00Z (UTC).
- Assignment: #371; existing draft PR https://github.com/Brian910cpr/910cpr-class-landers/pull/372 .
- Branch: codex/issue371-proof-gates-20261015.
- Substantive commit: 8b4b4032472d93b4b4661f0c5e0a35d59cbb4c16. Receipt commit: discoverable as pushed branch tip.
- State: IN_PROGRESS / PR_OPEN; operational proof gates BLOCKED. Evidence: BUILT, locally validated synthetic only.

## Work and exact review paths

Read full issue body/comments and repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md, LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Acknowledged actual execution on issue before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/371#issuecomment-6181995658 .

Changed only:
1. tests/customer_interaction_restart.test.mjs — new synthetic archive restore regression.
2. docs/CUSTOMER_INTERACTION_PATH_A_SAFETY.md — final section contains complete findings, test boundary, observer evidence and remaining gates.
3. This unique repository-root receipt.

Archive is written to a temporary file, source database closed, and bytes restored into a fresh directory. Checks retain original request receipts, raw notes, pending task/provenance and audit counts; resolution with pending obligation and actor-mismatched retry fail; service-role audit deletion and anon/authenticated access remain denied. Synthetic archive/databases removed after test. No new production restore mechanism or dependency.

## Exact validation

Existing cached module:
PGLITE_MODULE=file:///C:/Users/ten77/AppData/Local/Temp/landerware-interruption-tests/node_modules/@electric-sql/pglite/dist/index.js

Commands:
- node --check tests/customer_interaction_restart.test.mjs
- node --experimental-strip-types --test tests/customer_interaction_restart.test.mjs tests/customer_interaction_next.test.mjs tests/customer_interruptions_sql.test.mjs
- git diff --check

Result: syntax/diff pass; TAP tests 19, pass 19, fail 0, cancelled 0, skipped 0, duration_ms 24009.675. This is local synthetic validation, not genuine owner-session, independent-session locks, production backup restore or abrupt-crash evidence. No public output changed, generator run, installation or browser test required for this test-only increment.

## Observer incident / exact blocker

Latest owner incident requested inspection of existing Delta Watch task 6aa07a7161408191b146dc743eeab786. Callable tools expose no existing-task execution-management API. Computer-use inventory returned apps=[] and browsers=[]; opening https://chatgpt.com/scheduled failed `Browser is not available: iab`. Latest execution trace and reason for the earlier stale receipt cannot be inspected here. No task settings changed, manual receipt refresh, duplicate monitor or dispatcher.

Read-only recheck at 2026-10-15T01:06:50 UTC found an independently published scheduled receipt:
https://github.com/Brian910cpr/910cpr-class-landers/pull/372#issuecomment-6102801791
- updated_at: 2026-10-15T01:02:22Z
- checked_at: 2026-10-15T01:02:22.288Z
- invocation_kind: scheduled
- signal_published_at: 2026-10-15T01:01:15.7092900+00:00
- status: FRESH
- last_session_id: 01a13d00-bcd9-7e51-b3f4-d3dd2d106a50

Observation resumed without this dispatch changing the task/publication path. Prior gap remains unexplained; do not claim repair or sustained HEALTHY. Existing hourly observer stale threshold is 90 minutes; Deep Stability Review watches the canonical receipt. If it becomes stale again and trace remains inaccessible, ask Brian only to open the existing Delta Watch task and show latest run status/error. No immediate owner action required after fresh independent evidence.

## Persistence / deployment / preservation

Persisted locally in isolated worktree E:/GitHub/910cpr-issue371-proof-gates. Only explicit intended paths staged. Shared E: dirty work/receipts/runtime artifacts and broken remote ref preserved; fetch failed `fatal: bad object refs/remotes/origin/codex/group-training-experience`, so worktree uses existing verified e653af2ed8f57c6f66b3fe39c8871eeb97478586 object matching PR head from git ls-remote. Windows case-collision modifications docs/Earl/index.html and docs/Jackson/index.html in new worktree intentionally left unstaged. No cleanup, assignment or existing monitor changes. Open CODEX issue queue scanned; no competing deep workstream or independent speculative change started.

Push intended commits to named branch and existing PR372 branch; no duplicate PR. Gate OFF, PR draft, unmerged and undeployed. No production database/API write, customer data, external customer action, origin expansion or production exposure.

## Remaining gates and next action

Independent-session READ COMMITTED concurrency proof requires the existing guarded runner and authorized empty loopback PostgreSQL/psycopg runtime (previous preflight absent). Genuine owner-session UI/API/database recovery/conflict and usable production backup/restore evidence remain absent; synthetic archive test does not clear them. Then prepare exact minimal rollout and obtain separate explicit GO. Do not merge/deploy #372. Existing source, UI and test foundation remain available for review. Broader email/learning/discovery/reminder milestones remain open.

ChatGPT: review substantive commit and above exact files; retain gate OFF; use resumed independent receipt as fresh point-in-time observation, not explanation of gap. Continue genuine integration/concurrency/backup evidence in same stream. No Docker/WSL/Synology prerequisite request. On-demand test runner is regression observer only; no deployed CRM outcome monitor or genuine end-to-end success timestamp exists. Owner must not become routine monitoring layer.
