# Issue 380 dispatch R39

Timestamp: 2026-10-14T16:17:02.0411616Z
Branch: codex/issue380-r39-20261014; pushed to existing PR #381 head codex/issue380-manual-resolution-20261011.
Substantive commit: 58549aa5769b36dd5ffe5e0a5ecf48a96834bd33
State: PR_OPEN; BUILT only, validated locally. Not complete or deployed.

The full primary report follows. No user/account action required. Review draft source gate and test; continue attestation engineering. No merge/deploy authorization requested or inferred.
# Issue 380 R39 — publisher source identity gate

State: PR_OPEN / BUILT only. Existing PR #381 remains draft/unmerged/unapplied. All six acceptance criteria remain open. No production, installed runtime, migration, merge or deployment change; #371/#372 preserved.

## Finding and change
The restricted publisher previously accepted arbitrary source_ref strings and could bootstrap a card/issue mapping. The canonical reader derives a fixed repository URL, but that did not constrain publication. New review-only SQL adds checks inside the existing transaction after card/intake locking, version/resolution/immutable-issue checks and before observation mutation: require an existing intake mapping, a JS-safe issue identity and the exact fixed-repository URL derived from that mapping. Rejected requests cannot change version, event or receipt. Historical same-request replay remains historical and non-executable; conflicting replay still rejects.

This is identity enforcement, NOT typed operational attestation. It does not prove the underlying class/payment/deployment correction or that the collector actually acquired that state. Initial owner mapping authority and truthful source-state/worker-safe enforcement remain open. Do not install or promote this SQL in isolation. No new Enrollware dependency: existing canonical card/intake owns identity; immutable lifecycle/audit semantics are preserved rather than copied into page state.

## Exact files
- data/audit/issue380_publisher_source_binding_draft.sql (new optional draft after gateway/reader; outside migrations)
- tests/reconciliation/board_source_binding_reader.py (new real PostgreSQL regression; applies gate only around the new test and restores baseline afterward)
- data/audit/issue380_publisher_source_binding_20261014.md (this report)
- Codex_Reply_Issue380_20261014_R39.md (receipt)

The full harness still tests the earlier foundation without this optional gate; the new test alone proves gated behavior. It is not combined operational rollout proof. Under the gate, collector first-publication bootstrap is intentionally rejected; existing owner-published mapping required.

## Validation and exact useful outputs
Dedicated loopback cluster: E:/GitHub/issue380-pg-portable/cluster-r16, 127.0.0.1:55480. Fresh empty databases retained: issue380_test_r39_binding, issue380_test_r39_fixed, issue380_test_r39_final. No existing database reused/deleted. Process PATH uses retained client-r38/bin; Python uses E:/GitHub/issue380-pg-env/Scripts/python.exe.

Command with explicit ISSUE380_TEST_DSN='host=127.0.0.1 port=55480 dbname=issue380_test_r39_final user=issue380_local':

    python tests/reconciliation/board_canonical_bridge.py

Final: Ran 52 tests in 13.792s; OK. 20 observed Lock waits. Includes four real psql bridge cases plus new source-binding rejection/rollback/valid publication/replay test. GitHub transport is fixture controlled; local trust authentication is not production/password/TLS proof.

    node --test tests/github_source_reader.test.mjs tests/canonical_github_source.test.mjs

12 tests, 12 pass, 0 fail. Python AST parse: AST OK. git diff --check: pass. SQL syntax/behavior exercised by real PostgreSQL.

Initial run: 50/52, collisions with inherited issue 380 and oversized identity. Second: 51/52, another oversized identity collision. Fixed new fixture to allocate unused small and global-max identities; no production logic altered to accommodate tests. Logs: E:/GitHub/issue380-pg-portable/r39-tests.txt, r39-fixed.txt, r39-final.txt, r39-server.log. Cluster stopped after final validation.

## Remaining gates / proof contract
Next: typed operational attestation and source-state/worker-safe enforcement through the exclusive publisher; bind bridge output without mistaking GitHub lifecycle for underlying state proof. Then independent production privileges, installed consumer/atomic external side-effect fence, private evidence and coordinated UI/history/counts/reopen/browser proof. Keep #381 draft and SQL unapplied; no Brian/account action required.

Production useful end-to-end proof, cadence, last success, observer and observer health: not established. This is one-time local validation, not a monitored persistent process. Failure evidence is retained test output; recovery is rerun guarded harness against a fresh empty disposable DB. Engineering owns remaining gates; Brian is not a routine monitoring layer.

Dirty original checkout preserved. Isolated branch codex/issue380-r39-20261014; Windows case-collision dirt docs/Earl/index.html and docs/Jackson/index.html excluded. No generators. Open CODEX title queue scanned; existing assignments preserved, no independent safe unassigned quick win selected.

