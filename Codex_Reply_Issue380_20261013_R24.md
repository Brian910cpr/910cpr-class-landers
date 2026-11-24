# Issue 380 R24 receipt
Timestamp: 2026-10-13T20:04:22.3371722Z
Branch: codex/issue380-r24-20261013; pushed to existing PR #381 head codex/issue380-manual-resolution-20261011.
Substantive commit: ef4a0daab6364b75985324a0663d7e40dbd0b2d2
Work state: PR_OPEN / IN_PROGRESS. Persistent evidence: BUILT only.

Finding: owner assertions could produce reservations without canonical source-observation provenance. Added fail-closed provenance default/gate and owner republication downgrade; privileged synthetic fixtures remain explicit. No execution permission granted.

Exact changed files:
- data/audit/issue380_dispatch_transaction_draft.sql
- data/audit/issue380_intake_publication_draft.sql
- tests/reconciliation/board_dispatch_transaction.py
- tests/reconciliation/board_intake_publication.py
- tests/production_intake_publication.test.mjs
- data/audit/issue380_assertion_provenance_20261013.md
- Codex_Reply_Issue380_20261013_R24.md

Validation: 25/25 real local PostgreSQL tests, 11 Lock waits; 83/83 backend/auth tests; Python AST and diff checks pass. Full exact PostgreSQL output, commands, security limitations and proof contract are in the primary report above. Initial fixture quoting error corrected before final tests. Dedicated disposable server stopped.

Persisted locally, committed and pushed for review only. SQL outside migrations, unapplied. No production/installed runtime/state changes, merge or deployment. #371/#372, existing assignments and original dirty work preserved. Windows case-collision docs/Earl/index.html and docs/Jackson/index.html dirt excluded. Existing corrupt origin/codex/group-training-experience ref blocked fetching from previous checkout; fresh shallow checkout resolved work access without cleanup. No intentionally added untracked files.

All six acceptance criteria open. Direct service_role DML can forge provenance and bypass publisher audit: field is not an attestation. Collector/privilege restriction, installed consumer and atomic external pre-side-effect fence/race proof, private evidence and resolution UI remain unfinished engineering gates. No deployed end-to-end success or observer-health evidence exists. Current cadence/failure/recovery contract is in report; no Brian routine monitoring/account action required.

Next ChatGPT action: review provenance SQL/tests and trusted-role limitation; keep #381 draft/unmerged/undeployed, then continue authoritative collector and restricted write protocol before runtime integration. No account-level action required.
