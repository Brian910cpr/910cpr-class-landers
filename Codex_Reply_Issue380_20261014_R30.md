# Issue 380 R30 dispatch receipt

Timestamp: 2026-10-14T05:33Z (UTC).
Assignment: Brian910cpr/910cpr-class-landers #380.
Branch: codex/issue380-r30-20261014; pushed into existing PR #381 head codex/issue380-manual-resolution-20261011.
Substantive commit: 9800afe5286b4ad4d82a9af834a9085c2bf70ffc (report shutdown wording corrected with this receipt).
State: PR_OPEN / IN_PROGRESS. Persistent evidence: BUILT only. All six issue acceptance criteria remain open.

## Work performed / findings

Read full issue/history and repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design/proof gates; acknowledged actual execution on #380 before changes. Added isolated restricted collector capability draft with explicit RLS, limited card-column access, automatic per-transition audit using authenticated session_user, version/snapshot continuity and audit-failure rollback. Tested independent collector and routine login denial boundaries. Original checkout and existing assignments preserved; #371 primary, #372 untouched/draft. Reuses #381; no new PR.

Exact files:
- data/audit/issue380_collector_capability_draft.sql
- tests/reconciliation/board_collector_capability.py
- data/audit/issue380_collector_capability_20261014.md (primary review report; complete test output, limits and next gates)
- Codex_Reply_Issue380_20261014_R30.md

## Validation

33/33 real local PostgreSQL tests passed, including 11 observed Lock waits. PostgreSQL 16.4 / psycopg 3.2.10 / libpq 160009. AST and diff checks passed. Final guarded empty database issue380_test_r30_proof on 127.0.0.1:55480; temporary authenticated probe logins removed and test server stopped. No Node/API change. Initial setup/test corrections are recorded in primary report; no failed run counted as proof. Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html intentionally excluded. Original unrelated dirty files untouched. Local test logs/fixtures retained outside repo, not committed.

## Status, risks and next action

Persisted locally, changed in isolated repo, validated locally, committed and pushed for review only. SQL outside migrations and unapplied to production. No installed runtime/state changes, production writes, merge or deployment. No public-site completion claim.

This draft is a capability/audit foundation, NOT the complete authenticated collector or versioned publisher. Collector trust can still fabricate source assertions or extra self-attributed events; administrative owner exemption remains trusted. Production effective privileges/memberships and API/function reachability are unproven. Raw capability DML lacks expected-version/idempotency/first-publication lock protocol and MUST NOT be installed as the publisher. No new credential blocker is asserted; remaining work is engineering, not Brian action.

Next ChatGPT review: inspect all three substantive files above, especially capability prerequisites, RLS/column grants, trigger ordering and limitations. Keep #381 draft/unmerged/undeployed. Implement versioned/idempotent collector publication with established advisory/intake/card lock ordering, commit acknowledgement and collector-vs-owner/dispatcher contention tests; then bind a narrow authoritative reader. Installed no-launch consumer/external fence and private evidence/UI/history/counts/reopen remain unfinished. No owner/account action required now. Queue titles scanned; no unrelated safe quick win selected from titles alone.

Operational proof: expected outcome skip resolved/blocked/already-corrected work before launch/mutation; last production end-to-end proof none. Cadence/window and installed observer/observer-health/recovery/escalation not established. Stale/missing evidence, version mismatch or uncertain commit must fail closed. Brian is not assigned routine monitoring. Do not call this operationally healthy.
