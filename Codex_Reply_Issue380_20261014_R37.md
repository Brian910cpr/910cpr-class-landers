# Codex reply — Issue 380 R37

Timestamp: 2026-10-14 UTC (see commit timestamp).
Branch: codex/issue380-r37-20261014, pushed to existing PR #381 head codex/issue380-manual-resolution-20261011.
Substantive commit: 4019f8dfc69ef71afdd2d817e934fc7291d2e811.
State: BLOCKED for new real-transport proof; PR_OPEN / BUILT overall. All six acceptance criteria remain open.

Work: added guarded actual-psql/libpq bridge harness with four deterministic GitHub-boundary tests. No application/SQL/runtime behavior changed. Exact files: tests/reconciliation/board_canonical_bridge.py; data/audit/issue380_libpq_bridge_harness_20261014.md; Codex_Reply_Issue380_20261014_R37.md.

Exact blocker: no psql executable on PATH or in retained portable server/bin package; common PostgreSQL installation checks found none. Server/libpq availability is insufficient. Final preflight exits explicitly before SQL fixture creation (Ran 0 tests; FAILED(errors=1), BLOCKED: psql executable required on PATH; libpq/server alone is insufficient). Four new integration cases remain unproven. Initial inherited fixture name/identity collisions corrected; failed attempts and exact retained logs described in primary report. This is not authenticated integration or production privilege proof; local cluster uses loopback trust.

Continued independent backend validation: 47/47 existing real PostgreSQL canonical-reader/security/contention tests pass, 20 Lock waits; 44/44 targeted Node tests pass; AST/diff pass. No historical unrelated failure claimed fixed. Test server stop requested; shutdown result recorded in issue follow-up. Original dirty checkout and isolated Windows case-collision HTML excluded from commits. #371/#372 and all assignments preserved. No generators, production writes, migrations, installs, merge or deployment.

Next ChatGPT action: review exact test/report; provision verified local psql, then run harness against a fresh empty guarded loopback DB and record actual results. Continue typed operational attestation/source enforcement, production privileges, installed consumer/external atomic side-effect fence, private evidence/UI/history/count/reopen tests on same draft. No Brian/account action required. Do not merge/deploy #381 or #372.

Persistent proof: BUILT only; no real operational end-to-end success, cadence, observer or observer health established. Missing transport/access/drift must fail closed; recover by engineering local client/transport validation, not owner monitoring. No execution authority granted. This receipt is committed/pushed; full pushed tip and GitHub existence proof appear in originating issue/final response to avoid self-referential SHA.
