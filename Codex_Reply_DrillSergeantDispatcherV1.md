# Issue #266 — offline preflight checkpoint

- Timestamp: 2026-10-10T20:20:00-04:00 (America/New_York).
- Branch: `codex/issue266-dispatch-preflight-20261010`.
- Substantive commit: `7ab9b3ea641717261be7d020ae2793f431a4f3b3`.
- Work-item state: BLOCKED for persistent automatic dispatch; partial backend
  slice locally validated. Evidence level: BUILT only. Not CONNECTED, PROVEN,
  MONITORED or HEALTHY as a dispatcher.
- Execution acknowledged before implementation on originating issue:
  https://github.com/Brian910cpr/910cpr-class-landers/issues/266#issuecomment-6103675855

## Findings and exact blocker

Read full #266 (no preceding comments), repository AGENTS.md,
CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_DESIGN_ETHOS.md and
LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Reused #254's current owner-authored
checkpoint and inspected current main worker installer/runtime and draft PR #374.
No third-party comment was treated as owner authorization.

Current main worker uses ambient gh credentials rather than enrollment's
credential.protected; comment-based claims are not atomic leases; interrupted
local .processing jobs lack restart recovery; disabled.flag does not remotely
revoke credentials. Those prerequisites block safe automatic assignment, bounded
retry, exactly-once/restart proof and independent revocation. See exact source
paths `ops/operator/Start-910CPRWorker.ps1` and
`ops/operator/Install-910CPRWorker.ps1`; rollout evidence also exists in #254 and
PR #374. A new dispatcher must not amplify these gaps.

## Work performed and changed files

Safe independent backend progress while preserving the primary #371/PR #372 stream:

- `ops/operator/dispatcher-preflight.mjs`: pure offline snapshot validation,
  capability eligibility, stale/disabled/busy isolation, concurrency default one,
  explicit worker-safe source gate, unsupported-type blocker. Always returns
  dispatch_enabled=false; no I/O, worker execution, model call or reservation.
- `tests/dispatcher_preflight.test.mjs`: eight synthetic regression cases.
- `ops/operator/DISPATCHER_ROLLOUT.md`: snapshot contract, exact blockers,
  dependency order, future proof/observer requirements and watch migration gate.
- `Codex_Reply_DrillSergeantDispatcherV1.md`: this immutable root receipt.

No actual fleet state is asserted by these synthetic tests. No recurring config,
dispatcher installer, persistence loop, lease/publication implementation or real
worker round-trip was added; the full issue request remains outstanding.

## Validation and exact meaningful outputs

All processed locally in isolated worktree:
`E:\GitHub\910cpr-issue266-dispatch-preflight`.

```text
node --check ops/operator/dispatcher-preflight.mjs  [exit 0]
node --check tests/dispatcher_preflight.test.mjs   [exit 0]
node --test tests/dispatcher_preflight.test.mjs
# tests 8
# suites 0
# pass 8
# fail 0
# cancelled 0
# skipped 0
# todo 0
git diff --cached --check                       [exit 0]
```

Tests cover distinct identities/capability matching, unsupported job blocking,
default/explicit concurrency, disable isolation, stale/future timestamps,
identity/repository mismatch, unapproved source and duplicate job ID rejection,
invalid profile rejection, deterministic/no-input-mutation idle invocation.
They do not prove leases, durable completion, real worker execution or restart.

## Persistence, deployment and preserved work

Files persisted locally and committed; this receipt will be pushed before exit.
No merge, install, deployment or public rebuild. Draft PR #372 untouched.
No ops/handoff/next_task.md use. No credentials or worker state changed.
Original E: dirty checkout preserved. Its git fetch stalled; fresh sibling was
used instead, without cleanup/reset. New worktree has pre-existing Windows
case-collision modifications in docs/Earl/index.html and docs/Jackson/index.html;
both intentionally remain unstaged/uncommitted. All intended files staged by
explicit path; no cache/runtime artifacts included. No new untracked artifacts
intentionally left in this worktree.

## Proof, recovery and next action

Last successful real dispatcher end-to-end proof: none. No observer installed;
observer health unproven. Future success must be authenticated durable claim and
result reconciled to dispatcher completion after restart with no duplicate.
Cadence must be explicit before activation. Fail/stale conditions include missing
heartbeats, expired leases, invalid receipts and ambiguous publication/execution.
Future observer must have an independently observed heartbeat and deduplicated
escalation; Brian cannot be the routine watchdog. Detailed recovery/observer
contract is in `ops/operator/DISPATCHER_ROLLOUT.md`.

Recommended next action: review this bounded slice; reuse existing #249/#250/#252/
#254 and PR #374 worker stream for credential binding, atomic leases, stranded-job
recovery and revocation proof before enabling #266 dispatch. Preserve #371 as
the one deep implementation stream. Then implement dispatcher persistence/outbox/
receipt reconciliation and prove all #266 a–g acceptance steps on real workers.
Do not disable ChatGPT watches yet. No Brian-only or account-level action is
requested before backend prerequisites are ready. No claim that #266 is complete.
