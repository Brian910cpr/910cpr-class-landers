# Issue #380 dispatch R34

Timestamp: 2026-10-14T11:26:00Z (UTC).
State: PR_OPEN; BUILT only, partial implementation. All six acceptance criteria remain open.
Local branch: codex/issue380-r34-20261014.
Pushed PR branch: codex/issue380-manual-resolution-20261011.
Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/381
Substantive commit: 71fba05927c075397523326f212096bb67d06567.
Receipt commit: discover from the pushed branch tip; substantive SHA above avoids self-reference.

## Work / findings

Added real bounded read-only authenticated GitHub lifecycle acquisition with canonical binding validation, fixed host/repository, identity checks, asynchronous binding drift rejection and private content/error suppression. It never interprets prose or third-party comments as authority. Closed issue requires review, not presumed operational resolution. All successful results remain source_state=unknown, worker_safe=false, can_execute=false. No writer or runtime consumer added. Caller-supplied binding is not authenticated by this module; the canonical DB reader/source attestation bridge remains unfinished.

Exact changed files:
- ops/operator/read-github-source.mjs
- tests/github_source_reader.test.mjs
- data/audit/issue380_github_source_reader_20261014.md
- Codex_Reply_Issue380_20261014_R34.md

Read the report above for exact source fields, live JSON probe, commands, limitations and remaining gates. Most important review files are the reader, its tests and report. Existing publisher remains data/audit/issue380_collector_gateway_draft.sql (unchanged/unapplied).

## Validation / deployment

Local node syntax checks for both modules and git diff checks passed. Targeted node suite: 38/38 passed, zero failed/skipped (six new source-reader tests). Authenticated read-only live probe 2026-10-14T11:23:14.303Z fetched issue #380 with expected repo/URL/number and stable source IDs; synthetic card UUID/version, NOT live canonical binding. SQL unchanged; PostgreSQL suite not repeated. No unrelated historical failures rerun or claimed repaired.

Persisted locally in isolated E:/GitHub/910cpr-issue380-r34 and committed. Push targets existing #381 branch; GitHub receipt verification is required before final response. Not merged/deployed. #372 untouched/draft; #371 remains primary. No generator, production mutation, migration, installed runtime/state/task/process change or cleanup. Original dirty checkout preserved. Case-collision docs/Earl/index.html and docs/Jackson/index.html intentionally unstaged; no temporary files committed. Queue scanned; existing assignments preserved, no competing deep workstream selected.

## Remaining gates / next action

Authenticated canonical DB card/intake reader and first-publication issue binding; restricted publisher bridge with revalidation; typed lifecycle-vs-operational evidence; actual source attestation; production privileges; installed no-launch consumer/external atomic side-effect fence; private evidence upload/proxy/UI/history/counts/reopen/browser proof. These are unfinished engineering, not an owner credential blocker. Keep #381 draft and SQL outside migrations/unapplied. Next ChatGPT review should inspect the three substantive files, then continue canonical reader/publisher binding without treating GitHub open/closed as operational truth. No Brian/account action required.

Persistent evidence: BUILT overall; source connectivity alone observed, no real card/read/publish/dispatch end-to-end proof. Last successful operational proof: none. Cadence/observer/observer health: unestablished for the unfinished system. Fail closed on unavailable/mismatched/ambiguous/stale evidence. Recovery: fresh authenticated binding and source, locked expected-version recheck; no mutation from cached lifecycle observation. Escalation only for genuine account/business decisions. Brian is not the routine monitoring layer.
