# Issue #380 R3 — dispatcher reconciliation contract

Timestamp: 2026-10-12T03:44Z
Branch: codex/issue380-dispatch-contract-r3
PR branch destination: codex/issue380-manual-resolution-20261011
Substantive commit: a4780c01402f8baeeb7e6d9231ffc87bb1e87a64
State: PR_OPEN; partial BUILT, integration gated; all six acceptance criteria open.

Execution acknowledged on originating issue before implementation. Reused draft
PR #381. No merge/deploy; #371 remains primary and #372 untouched. Original dirty
checkout preserved. Separate named worktree used; Windows case-collision dirt in
docs/Earl/index.html and docs/Jackson/index.html excluded from staging.

Findings: issue updatedAt is not blocker reconciliation. Tracked Codex Wake selector
exists, correcting earlier audit; installed version differs and includes important
receipt/manual-hold/retry safeguards. Exact hashes, paths and selection findings
are preserved in data/audit/issue380_resolution_preflight_20261011.md R3 section.
No runtime file, state, process, scheduled task or launcher changed.

Files changed:
- supabase/functions/production-board/dispatch-reconciliation.mjs
- tests/dispatch_reconciliation.test.mjs
- data/audit/issue380_resolution_preflight_20261011.md
- Codex_Reply_Issue380_20261012_R3.md

Pure typed contract skips blocked/resolved items, rejects ambiguous/stale input,
requires explicit worker-safe opt-in and source check, proposes verification of
external fixes, and ranks P0 before owner priority. All results can_execute=false.
Regression covers #297 blocked suppression/#371 priority, new P0 and resolution
after selection. No caller imports it yet; no atomicity or production enforcement
claim. New source signatures alone cannot clear a blocker.

Validation commands:
node --experimental-strip-types --test tests/dispatch_reconciliation.test.mjs tests/production_execution_check.test.mjs tests/owner_access.test.mjs
Result: tests 37, pass 37, fail 0; pure/mocked local tests only.
node --check supabase/functions/production-board/dispatch-reconciliation.mjs
Result: exit 0.
git diff --check and git diff --cached --check: exit 0.
Known unrelated failures: earlier audit records 3 obsolete Maxim auth assertions;
that unrelated Python suite was not rerun. No generators or production writes.

Exact integration gate: installed/tracked launcher drift needs preservation and
review; authenticated structured canonical intake/versioned claim and atomic
pre-side-effect adapter do not exist in this increment. Selector location is now
known, so do not repeat the old unidentified-launcher blocker. Transactional
resolution/version/audit/evidence/UI remains unfinished, not credential-blocked.
No isolated SQL/concurrency/upload/browser or actual worker-skip proof obtained.

Persistent evidence: BUILT only. Last successful real resolution/evidence/worker
skip cycle: none. Expected cadence: every selection and side effect. Failure:
blocked/resolved selection, stale execution or P0 priority bypass. Observer and
observer health: not integrated/proven. Recovery: preserve audit/runtime state,
use approved hold controls then reconcile canonical truth before resuming.
Brian must not be the routine monitoring layer; that requirement remains open.

Recommended next engineering step: review R3 module/tests/audit in #381; preserve
installed safeguards in a reconciled source baseline, supply authenticated typed
intake and transactional claim/skip audit, and exercise isolated no-launch and
pre-mutation stop tests before separate rollout review. No Brian action required
for this review increment. No new competing deep stream started; eligible backend
contract work advanced while runtime integration remains gated.

Persisted locally and committed; receipt pushed with this PR branch checkpoint.
Final chat and originating issue report exact pushed tip after GitHub verification.
