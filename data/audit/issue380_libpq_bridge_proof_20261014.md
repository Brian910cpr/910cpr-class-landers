# Issue 380 R38 — real local libpq bridge proof

State: PR_OPEN; BUILT system, locally validated transport integration. PR #381 stays draft, SQL outside migrations/unapplied; all six issue acceptance criteria remain open. No production or installed runtime change, merge or deployment. #371/#372 and existing assignments preserved.

## Findings and work

Cleared R37 missing-psql blocker by downloading the Windows 16.15 binary archive linked on https://www.enterprisedb.com/download-postgresql-binaries through https://sbp.enterprisedb.com/getfile.jsp?fileid=1260623. Archive retained outside repository: E:/GitHub/issue380-pg-portable/edb-client-r38.zip. Observed SHA256: 43bb45f173a6f08cf1d29a97a6d8deb119e8e8093a24c00d2d1001a0ccaa8281. Extracted only bin/psql.exe and bin DLLs to client-r38/bin. psql --version: psql (PostgreSQL) 16.15. This is HTTPS vendor provenance plus a reproducibility hash, not independent publisher-checksum/signature verification; executable is unsigned. No machine PATH, service, startup task or production credentials changed.

Initial connection mistakenly used postgres (and diagnostic ten77); neither role exists. Zero fixtures initialized on that attempt. Reused documented dedicated issue380_local administrative fixture identity thereafter. Initial full harness: 48/51 passed, three bridge cases failed canonical_binding_unavailable. Root cause: inherited unsupported-identity regression inserts bigint above JS safe range; publication() derives subsequent issue identities from global maximum. Fixed only bridge_fixture() to allocate a unique small fixture identity independently of deliberately unsupported IDs. No production reader/API/SQL changed.

## Proof and commands

Dedicated retained cluster E:/GitHub/issue380-pg-portable/cluster-r16 started explicitly on 127.0.0.1:55480. Fresh empty databases issue380_test_r38_bridge (failure retained) and issue380_test_r38_fixed (final proof retained). No existing database reused or deleted. Temporary collector login and libpq service file automatically removed by harness.

With E:/GitHub/issue380-pg-portable/client-r38/bin prepended to process PATH:

    $env:ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 dbname=issue380_test_r38_fixed user=issue380_local'
    & E:/GitHub/issue380-pg-env/Scripts/python.exe tests/reconciliation/board_canonical_bridge.py

Exact final output: Ran 51 tests in 12.744s; OK. 20 observed Lock waits. All four real-psql cases passed, including unchanged read-only acquisition, publication version drift, owner resolution before/during acquisition, and missing/unprivileged identity denial. Real Node execFile invokes psql/libpq with explicit temporary service and separately authenticated non-superuser collector identity; only GitHub transport is fixture-controlled. Local trust authentication proves session identity/role privileges and transport, NOT password/TLS or production authentication. Lifecycle acquisition remains unknown/non-executable and never publishes operational evidence.

    node --test tests/github_source_reader.test.mjs tests/canonical_github_source.test.mjs

12 tests, 12 pass, 0 fail, 0 skipped. Python AST and node --check ops/operator/read-canonical-github-source.mjs passed; git diff --check passed. Logs outside repo: r38-bridge-tests.txt (initial role failure), r38-bridge-final.txt (48/51), r38-fixed.txt (51/51), r38-server.log under E:/GitHub/issue380-pg-portable. Cluster stopped after validation.

## Remaining gates and handoff

Next: typed operational attestation and exclusive publisher source enforcement. This test does not establish underlying class/payment/deployment correction, initial mapping authority, production privileges, installed consumer or atomic external side-effect fence. Private evidence, UI/history/counts/reopen/browser proof remain unfinished. Do not merge/deploy #381 or #372. No Brian/account action required.

Production end-to-end last success/cadence/observer/observer health: not established. This is one-time local proof, not an installed monitored process. Recovery: rerun guarded harness with fresh empty disposable DB; engineering owns the remaining gates, Brian is not a routine monitor.

Changed intended files: tests/reconciliation/board_canonical_bridge.py, this report, root Codex_Reply_Issue380_20261014_R38.md. Isolated codex/issue380-r38-20261014; unrelated original checkout unchanged. New worktree's pre-existing Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded. No generator/bulk rebuild. Open CODEX title queue swept; no independent unassigned low-risk change selected from titles. Existing assignments preserved.
