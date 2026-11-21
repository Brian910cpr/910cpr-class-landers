# Issue 380 — R35 canonical binding reader

Timestamp: 2026-10-14T13:00:00Z (UTC).
State: PR_OPEN; persistent evidence level BUILT only, validated locally.
Local branch: codex/issue380-r35-20261014.
Pushed destination: codex/issue380-manual-resolution-20261011, existing draft https://github.com/Brian910cpr/910cpr-class-landers/pull/381 .
Substantive commit: 163bb42db000aba6bf6470e9ba652aa0c534aac3. Receipt committed separately; pushed tip reported on originating issue and final response.

Execution acknowledged on originating issue before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/380#issuecomment-6168838761 . Full issue/history, repository AGENTS.md, handoff/design/proof gates read.

Finding: R34 GitHub acquisition accepts a caller-provided card/issue/version binding and is not a canonical database reader. Added private SECURITY INVOKER collector-only reader for existing canonical intake/card identity/version; source URL constructed from immutable issue identity in fixed repository, no arbitrary ref/private card text returned. Missing/invisible/unsupported binding requires review; resolved cards skip. No bootstrap, source attestation, publication or execution permission. Read is not a lease; publisher revalidates version.

Exact changed files:
- data/audit/issue380_source_binding_reader_draft.sql
- tests/reconciliation/board_source_binding_reader.py
- data/audit/issue380_source_binding_reader_20261014.md (primary report, full final test output)
- Codex_Reply_Issue380_20261014_R35.md (this receipt)

Validation: 47/47 real disposable PostgreSQL tests pass, 20 observed Lock waits; four new reader tests plus 43 inherited gateway tests. PostgreSQL 16.4/psycopg 3.2.10/libpq 160009 on guarded 127.0.0.1:55480 database issue380_test_r35_final. AST PASS; git diff --check PASS. Initial infrastructure assumptions and one fixture failure corrected; final fresh database passed. Exact commands/output in primary report. Dedicated test server stopped; no operational database accessed. No HTTP behavior change, no generator or broad rebuild. Existing unrelated historical failures not rerun or claimed fixed.

Persisted locally and changed in repo; committed and pushed for draft review. No merge/deploy, production migration/write, installed runtime/state/task change or #372 change. SQL outside migrations and unapplied. Original dirty checkout preserved. Isolated worktree Windows case-collision docs/Earl/index.html and docs/Jackson/index.html intentionally unstaged; cache artifacts excluded. No unrelated files committed, no cleanup. #371 primary and all existing assignments preserved. Queue titles swept; no unassigned safe independent backend item selected.

All six acceptance criteria OPEN. Exact remaining rollout gates: authenticated DB-to-GitHub bridge and lifecycle/operational typed attestation, trusted initial mapping and publisher source enforcement, production effective privilege proof, installed no-launch consumer and external atomic side-effect fence, private owner evidence upload/retrieval/UI/history/counts/reopen/browser proof. These are unfinished engineering, not missing Brian credentials. No user/account action required. Next ChatGPT action: review the three substantive files/47-test proof on #381, preserve draft/unapplied state, then continue authenticated reader/publisher binding without treating lifecycle state as operational truth.

Expected outcome: prevent duplicate launch/mutation of resolved/blocked/already-corrected cards. Last production end-to-end proof: NONE. No cadence/observer/observer-health established here. Failure/staleness: missing/stale/unsupported binding or ambiguous source state must fail closed. Recovery: reacquire authenticated binding and underlying evidence, revalidate through versioned committed publisher; never execute from cached lifecycle evidence. Escalate only real account/business decisions. Brian is not assigned routine monitoring. This increment is BUILT, not CONNECTED/PROVEN/MONITORED/HEALTHY.
