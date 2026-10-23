# Operator Boot Camp: six-worker rollout and graduation gates

Issue #254; inspected baseline 2393ff85ac6e14e5dfb876b8b14ab65f68c800bb on 2026-10-10.
Status: BLOCKED for clean-room graduation. This is a rollout plan, not proof that the fleet has graduated.

Read-only readiness check (no enrollment, process launch, credential reads, or network calls):

```powershell
powershell -NoProfile -File .\ops\operator\Test-910CPRBootCamp.ps1
```

It emits JSON prerequisite results and the four reviewed graduation blockers, then exits 1 while those gates remain closed. CLI presence does not establish authentication. Startup folder presence does not prove startup registration or logon survival. A passing host prerequisite list must never be interpreted as graduation. The implementation gates are deliberately fixed until replacement code and durable proof are reviewed.

## Existing evidence to reuse

| Worker | Identity | Evidence |
| --- | --- | --- |
| CYBERPC-01 | 4f966f81-b645-467c-a0e0-7073cfb28b86 | #259 selftest PASS 2026-09-18T10:34:58.7303045Z; #261 fixed-endpoint PASS 2026-09-20T12:04:05.7347642Z |
| 4018-TOUCHSCREEN | d8527052-cad2-46f2-ae79-78fc26451429 | #256 selftest PASS 2026-09-18T10:26:56.1955989Z; #262 outbound selftest PASS 2026-09-18T11:18:02.5988775Z |

The #256 transcript records missing Git, then direct downloads/reinstallation. This is useful operational evidence but does not satisfy the no-hand-patching clean bootstrap requirement. Preserve this worker's existing name/ID. Do not reinstall it merely to manufacture a new name.

## Safety blockers before another enrollment

1. **#249 credential binding:** Install-910CPRWorker.ps1 generates a unique DPAPI-protected credential.protected, but Start-910CPRWorker.ps1 never reads it. GitHub requests use ambient gh authentication. A distinct local seed is not a distinct revocable control-plane identity. Implement per-worker server-enforced credentials with least privilege; never copy the CyberPC account token to another environment. Prefer the existing LanderWare control plane as directed by #248. No service-role credential belongs on a worker.
2. **#249 claim/recovery:** GitHub comment creation is not an atomic claim/lease. The file lock is per state directory, not fleet-wide. Duplicate suppression works after a result exists, not across the execute/write crash window. Local *.processing files stranded by process death are not recovered. Implement atomic claims, attempt IDs, lease expiry, result idempotency and explicit ambiguous-outcome reconciliation before claiming exactly-once safety. Do not blindly replay jobs whose effects are unknown.
3. **#250 clean environment/bootstrap:** WindowsSandbox.exe is absent here and Get-VM is unavailable in this session. No second remotely controllable clean Windows environment was exposed. A second folder on Brian's active Windows account inherits authentication and Startup, so it is not a clean second environment. Add prerequisite checks for PowerShell/Git/CLI, credential enrollment, clean install failure handling and graduation before using a disposable VM or second machine. Never reboot the active physical CyberPC for this proof.
4. **#252 revocation/health:** disabled.flag only suspends one local directory at loop boundaries. It does not revoke a credential or cancel a claim already in flight. Remote heartbeat registry, credential revocation isolation, and a monitored observer are still required.

These are engineering/environment prerequisites, not a request for Brian to repeat Worker #1 installation. No new fleet credential was created or copied in this dispatch.

## Bounded v1 authority policy

Worker v0.2.4 accepts typed GitHub jobs only when the issue author login equals the configured repository owner's login (Brian910cpr here). Third-party comments and collaborator association do not grant permission. Only that owner's result comments suppress execution in this v1 queue. Deleted/null authors fail closed. A future dispatcher/bot needs an explicitly approved identity binding before its issues or receipts are trusted; do not broaden this to all collaborators. This is a narrow defense, not a replacement for atomic leases or per-worker credentials.

## Versioned installation entry point

From a reviewed release checkout, the existing exact command is:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\operator\Install-910CPRWorker.ps1 -WorkerName "CYBERPC-02"
```

This command currently installs a local runtime; **it is not a graduating clean-install/enroll command**. Do not execute it on Brian's active host to stand in for a clean environment. A valid one-command install/enroll process remains an acceptance gap under #250. Release packaging must pin installer/runtime hashes and version together and run the same prerequisites and graduation flow on every clean environment. Fix package defects and rerun from clean state; do not patch installed copies.

## Placement and capabilities

| Slot | Name | Proposed role | Initial capability gates |
| --- | --- | --- | --- |
| 1 | CYBERPC-01 (preserve ID) | Local engineering host | Existing selftest.ping/site.healthcheck; only one Codex stream project-wide |
| 2 | 4018-TOUCHSCREEN (preserve ID) | Existing second worker; clean reproof needed | Same bounded jobs; hardware profile remains unmeasured |
| 3 | CYBERPC-03 | Public endpoint/propagation checks | Fixed targets, status-only, no mutation |
| 4 | CYBERPC-04 | Artifact validation | Designated paths/hash comparison only, after #251 implementation |
| 5 | CYBERPC-05 | Reconciliation checks | Fixed input contracts, no writes to production, after #251 implementation |
| 6 | CYBERPC-06 | Acceptance evidence/reserve | Explicit deterministic criteria, after #253 implementation |

CYBERPC-02 is reserved for a genuinely new second clean environment if 4018-TOUCHSCREEN cannot be reset/reproved safely. Do not run two names for one installed identity. Placement is proposed, not a claim of available machines. Collect WORKER_PROFILE_TEMPLATE.md data before assigning heavy workloads. Start with one deterministic job per worker. No secret-management, arbitrary shell/filesystem, customer communication, money movement, or production deletion capabilities.

## Enrollment, update, recovery and retirement

- Enrollment: provision a unique server identity and narrowly scoped revocable credential; approve only supported typed capabilities. Store protected credential outside Git, logs, job/results and transcripts. Check independent remote heartbeat before assigning a harmless graduation job.
- Updates: canary Worker #2 first, verify version/hash and full graduation evidence, then roll one worker at a time. Preserve identity and completed-result ledger. Never use ForceReenroll for a version update. Keep previous reviewed package for rollback; pause claims while updating and reconcile the existing attempt first.
- Recovery: inspect heartbeat, diagnostic.json, worker.log and outstanding attempt before restarting only that worker. Preserve stranded processing files/results as evidence. Reconcile ambiguous jobs at the control plane before replay. Do not delete ledgers to clear an error.
- Re-enrollment/replacement: revoke the old server credential first; preserve old identity, results and audit links; create a new ID/credential on the replacement with explicit supersedes relationship. ForceReenroll alone is not sufficient while server revocation is absent.
- Retirement: disable claims remotely, finish/reconcile the current attempt, revoke that worker's credential, remove only its explicit Startup launcher, stop only its process, and retain non-secret audit/results. Prove another worker can still claim; never revoke a shared account to simulate isolated retirement.

## Graduation evidence and monitoring contract

For each clean installation, retain package commit/hash, exact command, machine/environment ID, distinct worker ID/name, credential identifier (never value), capabilities, Startup launcher, both heartbeat timestamps, job/attempt ID, structured result and durable reference. Inject one unapproved type and expect REJECTED with no effects. Stop the worker during a leased harmless attempt, restart, reconcile expiry and prove one execution/attempt outcome. Disable/revoke only Worker #2, prove no new claims, then prove Worker #1 still claims successfully. Run concurrent distinct harmless jobs to establish independence. An isolated VM may reboot/log on; otherwise verify registration and cold process start, recording physical reboot as pending. Missing credential/lease proof means reboot cannot be the only pending item.

Expected outcome: approved deterministic job -> unique lease -> bounded execution -> durable result retrieved by orchestrator. Proposed cadence: 60-second idle heartbeat, stale after 180 seconds; lease/job deadlines must include maximum execution and receipt latency (current five-target healthcheck may take about 100 seconds). Last useful Worker #1 proof is #261 above; fresh idle heartbeat is not fresh end-to-end job evidence. Current code has no remote monitored fleet observer. #252/#266 should observe worker staleness and lease deadlines; a separate supervisor must observe that observer's heartbeat and deduplicate escalation. Until that chain is proved, monitoring depends on manual inspection and the fleet is not MONITORED/HEALTHY. Recovery is component restart/reconciliation; escalation is limited to unavailable clean Windows environment or credential provisioning authority after backend work is ready.

This worker infrastructure does not alter Enrollware course truth, scheduling, public pages, or registrations. It supports deterministic native LanderWare operations without adding an Enrollware dependency.
