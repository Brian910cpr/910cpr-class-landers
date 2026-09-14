# ShiftCommander Astra R77 receipt

Assignment: [Brian910cpr/910cpr-class-landers#214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214).
Dispatch: `SHIFTCOMMANDER_ASTRA_20260913_R1`, continuing R76 as R77.
Timestamp: 2026-09-14T18:30:53-04:00 (America/New_York).
Work-item state: **PR_OPEN; production release BLOCKED**.
Persistent evidence state: **BUILT with synthetic local setup/HTTPS proof**.
No real-world PROVEN, MONITORED or HEALTHY claim.

## Pushed implementation

- Target repository: `Brian910cpr/shiftcommander_v2`.
- Worktree: `E:\GitHub\shiftcommander_v2_codex_issue214_r77`.
- Branch: `codex/issue-214-pilot-install-r77`.
- Commit: [`1436a266ff670ac8f17744e2e63d524a1d4474b3`](https://github.com/Brian910cpr/shiftcommander_v2/commit/1436a266ff670ac8f17744e2e63d524a1d4474b3).
- Review: [draft PR #15](https://github.com/Brian910cpr/shiftcommander_v2/pull/15),
  stacked on draft PR #14 (`codex/issue-214-pilot-client-r76`) at
  `8231421adec647fafa04d2c8ab5a58a115625854`.
- GitHub readback: OPEN/draft, exact head above; no GitHub CI statuses.
  Reported tests are local evidence.

Exact four-file scope: 725 insertions; no other target files committed.

| File | Purpose | Committed bytes | Git blob |
| --- | --- | ---: | --- |
| `scripts/initialize_private_pilot.py` | Offline named-account setup and protected new storage | 10299 | `9e70013f55561f36513d97e5849d8f0c3d9493d2` |
| `scripts/start_private_pilot.py` | Refuse incomplete setup before auth/application startup | 4272 | `a676080ef4802f41374157535aa9854cd99dc733` |
| `tests/smoke/test_private_pilot_setup.py` | 16 executable synthetic setup/HTTPS checks | 15562 | `93009ba46e16b0994110b7f818c6c5bf97df659d` |
| `docs/PRIVATE_PILOT_SETUP_ISSUE214_R77.md` | Full findings, commands, validation and continuation | 13283 | `3c757f036f402cff8952cdfbf1a7582a5e16ff1c` |

The complete contents of all four files were fetched from GitHub at that
immutable commit and matched `git show` bytes. Remote branch tip also matched.
Primary review report:
[docs/PRIVATE_PILOT_SETUP_ISSUE214_R77.md](https://github.com/Brian910cpr/shiftcommander_v2/blob/1436a266ff670ac8f17744e2e63d524a1d4474b3/docs/PRIVATE_PILOT_SETUP_ISSUE214_R77.md).

## Findings and work performed

R75/R76 had a launcher for pre-provisioned private state but no operator command
to create named accounts and signing material. This dispatch supplies that
missing setup step using the existing schema-v2 auth initializer and runtime
layout. It advances the newly authorized starter-roster work rather than
repeating the former missing-roster assessment.

The command is read-only by default. Explicit initialization requires a new
outside-Git directory, reviewed roster/settings files, matching supplied TLS
material and distinct active roster identities. It preserves full input bytes
and roles, imports no historical availability/schedule, and creates independent
signing material. Hidden temporary-password prompts require a terminal and
confirmation; all named accounts must change their passwords before normal use.
The shared supervisor credential remains unset. No credential is accepted from
an environment setting, source auth file or password argument.

On Windows, only the newly created empty root's access rules change. Its ACL
permits the current user and SYSTEM, checks owner/rules, and passes those rights
to created descendants. The initial `Set-Acl` implementation failed with
`PrivilegeNotHeldException`; an access-only `Directory.SetAccessControl` operation
resolved it without requesting additional privileges or changing ownership.
Independent tests read back the root, data directory and all seven files.
The POSIX mode-0700 branch exists but was not validated by this Windows run.

Failures preserve the partial installation. A `.setup-incomplete` marker is
removed only at completion; the launcher refuses a marked root even when its
other files are usable. Existing directories are never overwritten or cleaned.
An ACL failure leaves an empty directory before any secret is written. The
helper starts no service and installs no TLS trust. This is a local setup
boundary, not an OS sandbox or a backup service.

The application change is exactly two added launcher lines. No application auth
schema, personnel source, staffing rule, public HTML/asset, dependency, provider
binding or production route was changed. No operational generator ran.

## Validation

Final-tree combined run on Windows:

```text
SYNTAX: 3 Python files passed
DISCOVERED: 207
Ran 207 tests in 228.219s
OK
FINAL: tests=207 failures=0 errors=0 skips=0
remaining_fixture_processes=0
```

This is R76's exact 191-case set plus 16 new cases. It covers setup, private
pilot/client boundaries, auth readiness, temporary-password restrictions,
durable auth, audit/recovery, serving/beta guards, live-state storage and resolver
hard filters. Exact reproducible commands are in the primary report.

Focused final run:

```text
python -B -m unittest discover -s tests/smoke -p test_private_pilot_setup.py -v
Ran 16 tests in 33.043s
OK
```

The initial focused run found five Windows ACL setup errors; these were fixed
before both final runs. Expected storage-error messages in the broader suite
come from negative tests. No final test failures or newly identified unrelated
application failure remain in this run.

New end-to-end synthetic evidence: initialize member/supervisor accounts; start
real loopback HTTPS; require/change both temporary passwords; save availability;
stop/start the process; retain/read the same saved state; reject ordinary-member
supervisor access; permit named supervisor entry; deny publication; revoke the
member session at logout. The HTTPS client verifies the fixture certificate.
Other tests exercise no-write defaults, private prompts, bad identity/JSON/TLS,
duplicate passwords, overwrite/path/concurrent-creation refusal, interrupted
setup and credential-canary output. Source files remain unchanged.

These are synthetic Windows checks, not a full graphical-browser demonstration,
real-member consent, trusted operational TLS, hosted recovery, publication or
complete release proof. No real pilot service remains running. The ignored local
log is `E:\GitHub\shiftcommander_v2_codex_issue214_r77\debug\issue214_r77\final_tests.txt`;
the remote-file verification JSON and PR body are in that same ignored folder.

## Exact remaining blocker and next action

The private auth preflight still reports:

```json
{
  "auth_path_present": false,
  "auth_preflight_passed": false,
  "signing_secret_configured": false,
  "auth_path_absolute_outside_checkout": false,
  "named_accounts_provisioned": false,
  "release_ready": false
}
```

`SC_AUTH_DB_PATH` is absent in this worker environment. No real auth database was
inspected or provisioned. Actual installation still needs a selected private
parent/current-user identity, reviewed settings, trusted loopback TLS, private
credential handling and backup arrangement under the existing private-auth gate.
The current-user interactive helper removes the need to handcraft auth files or
introduce a Windows service account. Do not ask Brian to paste credentials.

Next for ChatGPT: review PR #15's four files and retain PR #14's isolation/client
boundary. Establish the concrete installation inputs and run the report's
check-only, interactive initialize, launcher check and foreground start commands
under the intended Windows login. Candidate root `E:/ShiftCommander/PrivatePilot`
was not created or approved by this dispatch; its parent must exist outside Git.
The profile/LocalAppData proposal remains unsuitable because the profile is
inside a Git checkout. Use the richer accepted roster and supervisor IDs 159,
186 and 188; incomplete starter membership alone is not a pilot gate.

Prepared URL after an actual installation starts:
`https://127.0.0.1:5443/login/supervisor`. Stop with Ctrl+C and restart against
the same private root/signing material. It is not currently an operational URL.
Preserve disputed identities/qualifications and collect fresh consent in-app.

Production remains gated by coordinated credential-incident disposition and
superseded-key rejection, then real staffing/demand/calendar provenance,
member/mobile/wallboard agreement, protected/partial/overnight/DST/OT/swap
scenarios, controlled publication, recovery, communication integrations and
observation. ADR Calendar retains published-staffing authority. R43 provider
metadata connectivity is established; do not revive the blanket access blocker.
Keep #214 and the draft stack open. Do not trigger another unchanged blocked
assessment when the useful next step requires installation/incident inputs.

## Credential exposure in this dispatch

An overly broad environment-name filter accidentally emitted the value held in
`SC_D1_BRIDGE_TOKEN_CODEX_SESSION` into the local tool transcript (output chunk
`c60e3d`). Its provider validity was not tested. This is an additional R77
exposure, and prior R37/R47 replacement/disposition remains unknown.

The value was not copied to GitHub, source, this receipt or the report, used for
an auth probe, or rotated. Further inspection used exact session fields or fixed
boolean preflight results. Do not retrieve the value from the transcript.
Include this incident in the existing coordinated consumer inventory,
replacement/recovery and superseded-key rejection procedure in
`docs/PRIVATE_PILOT_AUTH_ISSUE214_R74.md`. Provider edit scope, complete consumer
inventory and maintenance authorization remain required for production changes.
No release or incident-resolution claim is made.

## Persistent proof and recovery contract

Expected outcome: named availability save -> durable revision after restart ->
legal explained staffing -> supervisor review -> authorized publication ->
matching member/supervisor/mobile/wallboard views. This round proves synthetic
parts only; no complete real last-success timestamp is established. Wednesday
23:59 remains the publish boundary. Lost saves, stale state, illegal staffing
and divergent views are failure conditions. The whole-workflow observer and
its heartbeat remain unestablished, so MONITORED/HEALTHY cannot be claimed.

For failed pre-activation setup, retain the directory/marker, correct the cause
and use a different new root. For a used pilot, stop it, preserve state/evidence,
validate the private backup and follow audited recovery without restoring stale
credentials or revoked sessions. Do not remove an incomplete marker to force a
start, fall back to operational files, or restore the exposed bridge token.
Brian must not be the routine monitoring layer. Private identity/TLS/backup and
production-maintenance decisions are current operator/account boundaries;
deterministic local repairs remain independently eligible.

## Runtime, queue, preservation and courier

Matching active local session metadata:

```json
{"session":{"cli_version":"0.153.4","id_matches":true},"turn":{"model":"gpt-6-astra","timestamp":"2026-09-14T22:08:58.746Z"}}
```

This is local runtime evidence, not provider attestation or a model-setting edit.
The existing `scripts/Start-AstraReview.ps1` in the R2 worktree was read and run
with `-RepoPath E:/GitHub/shiftcommander_v2_codex_issue214_r77 -CheckOnly`.
At 18:12:21-04:00 it reported the dispatcher lock held/inaccessible. No duplicate
worker, lock/lease change or machine-default change. The
[official Codex CLI reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
was consulted for the issue's project-specific model-control requirement.

Both original checkouts retained their branch/HEAD/status and matching tracked
dirty-file hashes against saved baselines. The original ShiftCommander branch
remains four commits ahead of its remote, with its dirty calendar mirror and
untracked implementation/data preserved. LanderWare's Earl HTML, caches, heartbeat
and Supabase temporary files were not staged or edited. No reset, cleanup,
rebase, merge, force-push, stash or existing-worktree modification occurred.

Queue sweep: read the open issue list and #215/#219/#216/#223/#227 bodies/latest
comments. Owner access, document controls and reconciliation have delivered
implementations; instructor identities, financial inputs, legacy service/auth
connections and source freshness/stabilization retain separate gates. No newly
established unclaimed narrow backend defect justified a competing change. This
independent setup implementation advanced the active workstream safely.

Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r77`.
Courier branch: `codex/issue-214-shiftcommander-receipt-r77`.
Courier base: `1f8ede6e38d22b66374adb3b567ab16d0b24084c`.
Only this unique root `Codex_Reply_ShiftCommanderAstra_R77.md` is committed in the
courier. Reply/Read collisions were checked in fetched history/root and the new
remote branch name was checked before push. Its containing commit is the receipt
commit; exact tip and byte readback are reported on #214 and in the final reply.
No existing mailbox record was overwritten or acknowledged by Codex.

Persisted locally and pushed: four intended target files plus this separate
receipt. Intentionally ignored local artifacts: target `debug/issue214_r77/`
test/PR/remote verification records and test resolver outputs under `debug/`;
original-repository `.git/codex-evidence/issue214-r77/` contains non-secret
preservation/runtime/pickup records. No private fixture or credential is committed.
No merge, deployment, real account activation, production write, calendar cutover
or member communication occurred. The retired mutable handoff path was not used.
The pushed receipt and issue response are this return handshake; later ChatGPT
acknowledgement is not claimed.
