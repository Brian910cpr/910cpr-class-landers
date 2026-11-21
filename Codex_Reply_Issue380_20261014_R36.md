# Codex Reply — Issue 380 R36

Timestamp: 2026-10-14 UTC (dispatch date; exact commit time in git).
Assignment: Brian910cpr/910cpr-class-landers#380.
Branch: codex/issue380-r36-20261014, pushed to existing PR #381 head codex/issue380-manual-resolution-20261011.
Substantive commit: b75386397118ce18468fd11a22c788567316226d.
State: PR_OPEN / IN_PROGRESS. Evidence: BUILT only.

Work: read repository/issue gates, acknowledged execution on originating issue, added bounded read-only psql canonical-binding -> authenticated GitHub lifecycle -> canonical-recheck transport. Explicit libpq service required. No publication or execution permission; resolved cards skip and drift suppresses observations. Findings/limitations and proof contract in data/audit/issue380_canonical_github_bridge_20261014.md.

Exact changes:
- ops/operator/read-canonical-github-source.mjs
- tests/canonical_github_source.test.mjs
- data/audit/issue380_canonical_github_bridge_20261014.md
- Codex_Reply_Issue380_20261014_R36.md

Validated locally: both node syntax checks PASS; 44/44 targeted Node tests PASS, zero failed/skipped; git diff --check PASS. Initial fixture assertion failure corrected as documented in report. SQL unchanged; existing PostgreSQL tests not repeated. Known unrelated historical failures not rerun/claimed fixed.

Persistence/deployment: intended files committed and pushed to existing draft PR #381; verify pushed receipt via GitHub Contents API before exit. No merge, deploy, production migration/write, installed runtime/state/task changes or generators. Original dirty checkout and case-collision HTML dirt preserved/excluded; #371 primary, #372 draft/unmerged/undeployed; assignments preserved. Queue titles swept, no safely independent unassigned backend fix established.

Exact unfinished gate: no authenticated DB/libpq-to-GitHub end-to-end transport proof or typed operational attestation/publisher enforcement. Lifecycle metadata is not underlying business-state proof. No service provisioning attempted; this is unfinished engineering, not a credential request. All six acceptance criteria remain open. First-binding authority, production privileges, installed consumer/atomic external fence and private evidence/UI/history/counts/reopen remain unfinished.

Last successful production end-to-end proof: none. Operational cadence/observer/observer-health not established. Invalid/missing/stale binding, access failure, resolution or ambiguous source must fail closed. Recovery: reacquire authenticated binding/operational state and use reviewed locked publisher; never mutate based on cached lifecycle output. Brian is not the routine monitor.

Next for ChatGPT: review the exact new source/test/report above; keep #381 draft and SQL unapplied; continue disposable authenticated libpq bridge proof and typed operational attestation enforcement before production integration. No Brian/account action required now.
