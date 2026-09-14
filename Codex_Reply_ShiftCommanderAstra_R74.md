# Issue 214 R74: owner inputs incorporated; private-auth preparation pushed

- Dispatch: `SHIFTCOMMANDER_ASTRA_20260913_R1`, continuing R73 as R74.
- Timestamp: September 14, 2026, 16:41 EDT (UTC-04:00).
- Work-item state: **PR_OPEN**; overall release **BLOCKED**.
- Persistent application evidence: **BUILT**, locally tested, with previously established partial provider connectivity. No complete operational PROVEN/MONITORED/HEALTHY claim.
- Courier branch: `codex/issue-214-shiftcommander-receipt-r74`.
- Courier base: `1f8ede6e38d22b66374adb3b567ab16d0b24084c`.
- Courier checkout: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r74`.
- Substantive target commit: **`d6b94876686f6839dc30eb2ed01dacc0ea05bfbd`**. This receipt references that already pushed commit; its own courier commit is supplied in the final issue/UI return after push.

## Changed evidence and work performed

Read the complete issue body and all 156 comments available at initial fetch, original pinned dispatch, original/current courier AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, proof standard, #116 and target governing documents. Later read the new owner-input comment recorded at 20:29:32Z. Preserve one active worker and the no-production-cutover gate.

**The owner supplied new inputs; this is not another unchanged blocked assessment.** Found and read `Codex_Reply_ShiftCommanderOwnerInputs_20260914_R1.md` on `codex/issue-214-owner-input-receipt-20260914`, then verified [target PR #11](https://github.com/Brian910cpr/shiftcommander_v2/pull/11) at `4005dc60f4d89eaded4509ccd7e1b6d4cd216814`. Initial supervisors and the starter roster are accepted for a private demonstration. Missing people alone must not block that demonstration. Preserve all 41 richer application records, disputed identities/qualifications and unknown availability. Historical availability is not current consent; 0600/1800 and ADR Calendar publication authority remain intact. The Drive continuity folder is not an approved live SQLite mount.

Created an isolated target worktree based on PR #11. Added a read-only private-auth preflight and concrete pilot/bridge-replacement runbook. The preflight checks four allowlisted environment settings, existing schema-v2 SQLite structure, named-account hash format and shared-supervisor exclusion. It reuses `AuthStore.read_users`, never imports Flask, never creates/migrates a database, never contacts a service, and emits fixed booleans rather than values. A passing check explicitly does not claim release readiness, successful login, disk durability or supervisor-role verification.

The runbook gives the proposed private storage/TLS/environment boundaries, named login approach, next isolated launcher/provisioning step, verified serving-path references, one-token Worker/Render replacement sequence, write-pause requirements, old-token rejection evidence and recovery without restoring an exposed key. It identifies the real bridge contract as POST `/api/live-state/availability/read`, not anonymous health or stub session status. The deployed handler must be verified before using that source-derived probe plan.

## Target branch, PR and exact review files

- Repository: `Brian910cpr/shiftcommander_v2`.
- Branch: `codex/issue-214-auth-readiness-r74`.
- Checkout: `E:\GitHub\shiftcommander_v2_codex_issue214_r74`.
- Commit: `d6b94876686f6839dc30eb2ed01dacc0ea05bfbd`.
- [Draft PR #12](https://github.com/Brian910cpr/shiftcommander_v2/pull/12), stacked on PR #11; OPEN/draft, exact three-file scope, no GitHub check results at verification.
- [scripts/check_auth_readiness.py](https://github.com/Brian910cpr/shiftcommander_v2/blob/d6b94876686f6839dc30eb2ed01dacc0ea05bfbd/scripts/check_auth_readiness.py): new read-only command.
- [tests/smoke/test_auth_readiness.py](https://github.com/Brian910cpr/shiftcommander_v2/blob/d6b94876686f6839dc30eb2ed01dacc0ea05bfbd/tests/smoke/test_auth_readiness.py): 15 synthetic regression cases.
- [docs/PRIVATE_PILOT_AUTH_ISSUE214_R74.md](https://github.com/Brian910cpr/shiftcommander_v2/blob/d6b94876686f6839dc30eb2ed01dacc0ea05bfbd/docs/PRIVATE_PILOT_AUTH_ISSUE214_R74.md): full preparation report, configuration table, credential-replacement/recovery runbook and proof contract.

All three complete remote contents and Git blob IDs matched local committed bytes: script 5,355 bytes / `8c4cd664c3dc4959cd790f5829d5dcdda4259e2d`; tests 7,348 bytes / `e01dd42c7b5ca4b66e9df5ad43a7cbdfa23558e0`; runbook 12,696 bytes / `28992083f8c66de828bcb5eb70f62315924f5b0a`.

Only this root receipt changes the courier. No runtime, dependency, roster, schema, HTML, CSS/JS asset or operational-data change in R74. No generator ran. PR #11's intake remains separate, unchanged and draft; R8 PR #10 remains OPEN/draft at `ba0365a250d18297a262b96ab7f15cf3fe6f1780`.

## Exact local validation and limitations

```text
python -B -m unittest discover -s tests/smoke -p test_auth_readiness.py -v
Ran 15 tests in 1.385s
OK
SYNTAX: 2 files passed; no bytecode generated
git diff --cached --check: passed
git diff 4005dc60f4d89eaded4509ccd7e1b6d4cd216814..HEAD --check: passed
```

The tests include actual CLI exit 0/2, missing-store noncreation, corrupt-store preservation, v1 non-upgrade, missing audit schema, malformed private documents/hashes, shared-account rejection, bypass/signing checks, output secret canaries and file preservation. Test accounts are synthetic. No test failure, error or skip occurred. A connection-cleanup correction was made during authoring before the first test run; no runtime source changed.

Ran the command against this worker's current process configuration with required IDs 159/186/188. It correctly returned Python exit 2 and `auth_preflight_passed=false`: `SC_AUTH_DB_PATH` is absent and the signing-secret check fails. No real store could be inspected. Downstream schema/account checks are unverified consequences of that missing path, not evidence that every real account is absent. Development-auth-disabled check passes in this local environment; that says nothing about deployed Render configuration. PowerShell's external-command wrapper initially reported exit 1; direct subprocess readback confirmed the script's exit code is 2.

Prior `docs/RELEASE_VERIFICATION_ISSUE214_R9.md` records 160 passing synthetic runtime/auth/restart/resolver tests; those unchanged suites were not rerun. No visual browser, real login, OS restart of an operational pilot, hosted recovery, deployment dry run or end-to-end release test was performed here. The runbook is source/documentation reviewed, not executed. Initial file-discovery probes used two absent paths on the migration lineage; corrected to the actual JS/serving-lineage documents without changing files.

## Exact remaining blocker and next action

Execution stopped before real private-account provisioning/activation and production credential replacement. The candidate and preflight are usable; no ordinary operational localhost URL is claimed.

1. **Private pilot configuration/execution:** this process has no `SC_AUTH_DB_PATH` and no passing signing-secret setting. The proposed `%LOCALAPPDATA%/ShiftCommander/PrivatePilot` location, service-user ACLs/backup and trusted private TLS must be selected/configured. Prepare the isolated provisioning/launcher command with allowlisted environment and all repository-relative mutable inputs/outputs isolated; `SC_STATE_DIR` alone is insufficient. Use the accepted starter roster and named accounts, then collect fresh availability and show save/readback/restart plus a legal explained pass. Do not require a complete replacement roster first.
2. **Bridge incidents:** R37/R47 replacement status remains unknown. No value was retrieved from prior logs, repeated, used for authentication, or rotated here. Follow the prepared consumer inventory, deployed-handler verification, coordinated maintenance/replacement and superseded-token rejection sequence. Actual provider edit scope and maintenance/cutover authorization remain unverified. Surface an exact denied account action if encountered, not a generic request that Brian understand the credential.
3. **Release:** approved current consent/qualification/demand for the actual scenario, client/auth agreement, staged publication/recovery and observer proof remain. The private starter approval does not authorize guessed availability, qualification changes or production/calendar cutover.

Cloudflare metadata access remains established by R43, target commit `0420626ad718898061332e4ff1e7f073f92dd37e`: `docs/RELEASE_METADATA_ISSUE214_R43.md`, `docs/PROVIDER_METADATA_ISSUE214_R43.json`, `docs/PUBLIC_SERVING_ISSUE214_R43.json`. Do not reinstate the retired blanket access blocker or blindly repoint the failed tunnel. No new provider probe was necessary for this local preparation. Current official Cloudflare secret and Render environment/disk documentation is linked in the target runbook.

**Next ChatGPT action:** review PR #12's three files with the new owner-input receipt/PR #11, preserve the draft stack, and continue the prepared isolated private-pilot setup. Obtain only the precise private storage/TLS or maintenance/account decisions actually needed. Keep #214 open; a preflight/PR is not the completed release.

## Preservation, queue and runtime

Original `E:\GitHub\910cpr-class-landers` status remains on `codex/durable-session-participant-linking`, behind 2, with its Earl HTML, tracked bytecode, untracked bytecode/heartbeat and Supabase temporary directory preserved. Nothing was staged there. Original `E:\GitHub\shiftcommander_v2` remains on `codex/base44-worker-consolidation`, ahead four unpublished commits, with its changed calendar mirror and untracked slot-generator/availability/data/tests preserved. Owner-intake and R9 worktrees remain clean. New target and courier changes were explicitly staged. Courier root-only sparse initialization populated an initially empty, `.git`-only worktree; no existing worktree files were reset, restored, cleaned, merged or rebased.

Swept open issues and checked #229/#227's latest dependencies. No newly dispatched unclaimed narrow independent repair was established: #229's #230-#233 stack retains source/access/runtime/job-to-page proof gates; #227 retains its freshness/stabilization direction; #140 retains its fail-closed credential-parity boundary. Preserve delivered owner-access/reconciliation and completed #226/#228 work. Advanced the newly eligible ShiftCommander auth preparation above instead of duplicating those systems. No additional issue implementation or member communication occurred.

Matching active-session local `turn_context`: `model=gpt-6-astra`, timestamp `2026-09-14T20:26:34.748Z`, CLI `0.153.4`; local runtime fields, not provider attestation. Existing `E:\GitHub\shiftcommander_v2_codex_issue214_r2\scripts\Start-AstraReview.ps1 -RepoPath E:\GitHub\shiftcommander_v2_codex_issue214_owner_intake -CheckOnly` at 16:29:48-04:00 returned `can_launch=false`, dispatcher lock held/inaccessible. No second worker, lock/lease/default or timer change. No retired mutable mailbox or Codex_Read marker was used or created.

## Deployment and persistent proof

Persisted locally, committed, pushed and remotely byte-verified target work; PR_OPEN. Courier receipt is committed/pushed separately. Nothing merged, deployed, activated or cut over. No paid service or account configuration changed.

Expected real success remains named availability save -> durable revision after restart -> legal explained resolution -> reviewed publication -> matching member/mobile/wallboard views. Complete real last-success timestamp is unestablished. Confirmed publication boundary: Wednesday 23:59. Lost saves, stale revisions, illegal assignments and divergent views are failures. Whole-workflow observer, observer heartbeat and escalation/recovery delivery remain unproven; Brian must not be their routine detector. The preflight is on-demand validation, not a monitor. Recovery must preserve current state/evidence, avoid resurrecting revoked sessions or accepting an exposed bridge key, and prove a separate replacement before resuming service.
