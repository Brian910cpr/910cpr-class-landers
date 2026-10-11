# Issue #266: dispatcher rollout gate

Status: BLOCKED for automatic dispatch. Offline preflight is BUILT and locally
validated; this is a partial checkpoint, not the requested persistent dispatcher.
No runtime installation, Startup registration, recurring job, worker reassignment,
Codex Wake change, merge, or deployment occurred.

## Safe backend slice

`dispatcher-preflight.mjs` exports `preflight({workers, queue, now, staleSeconds})`.
It performs no I/O, executes no commands, and invokes no model. Its result always
has `dispatch_enabled: false`. Eligibility is diagnostic, not a reservation.
Inputs are explicit snapshots, not authority inferred from arbitrary comments.

Each worker input contains:

- `identity`: existing enrollment `worker_id`, `worker_name`, `worker_version`,
  `repository`, `capabilities` (existing `job.<type>` capability convention).
- `heartbeat`: matching identity/version, `state` (idle/working/disabled), and
  timezone-qualified `observed_at_utc`.
- `profile`: explicit boolean `disabled`, `active_job_ids` array, optional integer
  `max_concurrency` (defaults to one).

Each queue input contains durable `job_id`, `job_type`, `source: "explicit"`,
and `worker_safe: true`. Only selftest.ping and site.healthcheck are recognized.
Unknown types remain blocked. Unknown sources and duplicate IDs reject the entire
snapshot. Stale (default 180 seconds), future, working, and disabled heartbeats
cannot become eligible. This does not authenticate snapshot provenance; a future
adapter must authenticate sources before invoking it. Caller owns snapshot time.

Run local checks with `node --test tests/dispatcher_preflight.test.mjs`.
Tests use synthetic workers only. They are not real fleet proof or restart proof.

## Exact engineering blockers

Current main's `Start-910CPRWorker.ps1` uses ambient `gh` authentication; enrollment's
`credential.protected` is not bound to claims. Claim comments do not provide atomic
leases. The local inbox renames jobs to `.processing` but does not recover those
files on restart. `disabled.flag` is local suppression, not credential revocation.
An automatic dispatcher would amplify these risks. #254's owner-authored checkpoint
and draft PR #374 also record these prerequisites. Reuse that worker stream for
worker changes; do not copy its changes or open a competing bootstrap implementation.

Next implementation order:

1. #249: credential binding, authenticated receipts, atomic lease ownership and
   restart recovery; address ambiguous execution without blindly retrying it.
2. #250/#252/#254: clean bootstrap, independent identities, remote revocation and
   observed restart proof. Do not reboot Brian's active machine.
3. #266: separate dispatcher identity/state/lock, crash-safe publication outbox,
   durable job IDs and leases, bounded retry/escalation, authenticated claim/result
   observation, fleet artifact, Startup installer and recovery observer.
4. Prove real two-worker claim/result/restart/no-duplicate cycle before enabling
   configured recurring site.healthcheck. Keep Production Board intake disabled
   until explicit worker-safe provenance is enforced.

## Required operational proof contract (not yet installed)

Useful outcome: capable enrolled worker completes a bounded health job once.
Success evidence: authenticated durable claim/result tied to worker and job/lease,
plus dispatcher completion state that survives restart without republishing.
Cadence/window: must be explicit in future recurring config; no default polling
or retry cadence is activated here. Last real dispatcher proof: none.
Failure: missed heartbeat, expired lease, unknown publication outcome, exhausted
retry budget, invalid receipt or revoked credential. Observer: future local
dispatcher plus independent liveness observer; neither is installed or proven.
Observer health must itself have a timestamp and escalation path. Brian must not
be the routine watchdog. Recovery: preserve state/evidence, reconcile durable
receipts, recover only owned leases, escalate once for unresolved ambiguity.
Account-level action: only credential grants/revocation or access restrictions
after engineering prerequisites are ready; no Brian-only action requested now.

## Migration and design decision

Move deterministic site-health polling and worker heartbeat/receipt/no-delta
checks from ChatGPT watches to local code only after end-to-end and observer proof.
Do not remove existing watches yet. Keep judgment, diagnosis, new capabilities,
owner authorization, and implementation dispatch outside the deterministic loop.

The existing Operator Boot Camp is the reference, not ShiftCommander or Codex Wake.
Explicit identities, typed capabilities and durable lifecycle evidence follow the
existing bounded worker model. This is infrastructure, not a replacement training
workflow. It adds no Enrollware dependency; future useful health work supports
native LanderWare operations. The immediate 910CPR advantage is reduced model
polling cost while preserving authority and crash/restart safety.
