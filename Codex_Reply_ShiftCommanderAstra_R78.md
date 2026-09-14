# ShiftCommander Astra R78 — pilot process exclusion

- Assignment: [Brian910cpr/910cpr-class-landers#214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214)
- Dispatch: `SHIFTCOMMANDER_ASTRA_20260913_R1`, continuation after R77.
- Timestamp: **2026-09-14 23:01:34 UTC / 19:01:34 America/New_York (UTC-04:00)**.
- Work-item state: **PR_OPEN; production release BLOCKED**.
- Persistent-system evidence: **BUILT with synthetic local HTTPS/process proof**.
- Target branch: `codex/issue-214-pilot-recovery-r78`.
- Target commit: [`848517905db9fda064da9cad0a90e14cb878bff3`](https://github.com/Brian910cpr/shiftcommander_v2/commit/848517905db9fda064da9cad0a90e14cb878bff3).
- Target PR: [draft #16](https://github.com/Brian910cpr/shiftcommander_v2/pull/16), stacked on draft #15 at `1436a266ff670ac8f17744e2e63d524a1d4474b3`.
- Target worktree: `E:\GitHub\shiftcommander_v2_codex_issue214_r78`.
- Courier branch: `codex/issue-214-shiftcommander-receipt-r78`.
- Courier base: `1f8ede6e38d22b66374adb3b567ab16d0b24084c`.
- Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r78`.
- Courier scope: this unique root `Codex_Reply_ShiftCommanderAstra_R78.md` only. Both Reply/Read R78 names were absent before creation. No acknowledgement marker was created.

## Result

Reproduced and repaired a concrete pilot persistence hazard rather than repeating
the old unchanged prerequisite assessment. R77 allowed two HTTPS pilot processes
on different ports to share the same private state directory. Before this fix,
both processes remained alive and the second returned `/api/health` HTTP 200.
The file store uses read/modify/replace operations and shared temporary filenames;
concurrent lost updates or file collisions are risks inferred from that code.
No operational data race or loss was induced.

The pilot launcher now holds a nonblocking OS lock for that directory from
preflight through application import, serving and socket shutdown. A second
launcher or existing-lock `--check-only` exits before account reads/application
import. Windows process termination releases the lock automatically; no stale
PID file cleanup is needed. The helper never deletes or truncates the empty
`.pilot-runtime.lock` file and refuses linked/nonregular/hardlinked lock targets.
No paths, credentials or member data are emitted by its error boundary.

`--check-only` creates no lock file. A normal first launch can leave one empty
lock file if later configuration fails. A successful check does not reserve a
future launch or prove release readiness. This is cooperative exclusion for the
new launcher on protected local storage; older launchers, direct imports, copied
roots and arbitrary writers remain outside it. Stop old pilot processes before
adoption, and do not delete a held lock to force access. Windows is locally tested;
the POSIX branch is documentation-reviewed only.

## Exact implementation and review files

All paths below are in **Brian910cpr/shiftcommander_v2** at the target commit:

1. [`engine/pilot_lock.py`](https://github.com/Brian910cpr/shiftcommander_v2/blob/848517905db9fda064da9cad0a90e14cb878bff3/engine/pilot_lock.py) — 65-line cooperative OS-lock helper.
2. [`scripts/start_private_pilot.py`](https://github.com/Brian910cpr/shiftcommander_v2/blob/848517905db9fda064da9cad0a90e14cb878bff3/scripts/start_private_pilot.py) — 14 added lines, lifetime cleanup and fixed lock errors.
3. [`tests/smoke/test_private_pilot_lock.py`](https://github.com/Brian910cpr/shiftcommander_v2/blob/848517905db9fda064da9cad0a90e14cb878bff3/tests/smoke/test_private_pilot_lock.py) — 12 synthetic unit/process cases.
4. [`docs/PRIVATE_PILOT_LOCK_ISSUE214_R78.md`](https://github.com/Brian910cpr/shiftcommander_v2/blob/848517905db9fda064da9cad0a90e14cb878bff3/docs/PRIVATE_PILOT_LOCK_ISSUE214_R78.md) — primary review report, full release checklist, commands, assumptions and recovery limitations.

No new dependency, generator, resolver/staffing rule, account/schema, provider
configuration, public HTML/CSS/JavaScript or operational data change. The courier
has no ShiftCommander application implementation.

## Local validation and remote readback

| Check | Exact result |
| --- | --- |
| Before-fix HTTPS reproduction | Same synthetic root, distinct ports, first alive=true, second alive=true, second health=200; both processes then stopped. |
| Initial new-suite run | 10 passed, 1 harness error: Windows denied reading the deliberately locked file during a byte snapshot. Fixed the snapshot to exclude only the empty lock and separately check its size. |
| Focused lock suite | 12 passed in 9.918s, no failures/errors/skips. |
| Pilot regression suite | 44 passed in 63.030s, no failures/errors/skips: lock, setup, pilot, and client suites. |
| Final test-only cleanup adjustment | Replaced blocking executor cleanup in the simultaneous-acquisition test with bounded queue reads; 12 tests passed again in 10.110s. Application code unchanged after the 44-case run. |
| Final syntax | Three Python files AST-parsed and compiled in memory; no bytecode writes. |
| Diff/scope | Explicit four-file staged diff check passed; 463 inserted lines total including report/tests. |
| Target push | Branch tip on GitHub is `848517905db9fda064da9cad0a90e14cb878bff3`. |
| Target remote contents | At 2026-09-14T23:00:30.955871+00:00 all four complete contents and Git blob hashes matched committed bytes. |
| PR readback | #16 OPEN/draft, base `codex/issue-214-pilot-install-r77`, exact target head; no GitHub CI checks reported. |
| Fixture cleanup | Zero remaining pilot fixture processes. No operational localhost URL remains running. |

Combined tests retained actual HTTPS named login, temporary-password changes,
secure-cookie responses, own availability save/restart/logout revocation, served
HTML/JavaScript API routing, Windows setup ACLs, and the isolated legal draft with
OPEN seats and supervisor audit output. New tests prove duplicate start on a
different port, duplicate preflight, unchanged private data files, exactly one
winner in simultaneous subprocess acquisition, abrupt termination/restart and
continued revoked-session rejection. Failure recovery covers configuration and
socket bind failures. These are synthetic local checks, not a graphical browser,
real-member, staged publication, full disaster-recovery or production proof.

Reproduce with the exact combined command in the primary report. Full retained
local output: `E:\GitHub\shiftcommander_v2_codex_issue214_r78\debug\issue214_r78\validation.txt`.
This ignored log and `debug/issue214_r78/pr_body.md` were intentionally not committed.
R77's broader 207-test result remains historical evidence and was not rerun here.

## Exact remaining blockers and usable continuation

**Private activation:** this worker's current auth preflight reports
`auth_preflight_passed=false`, `signing_secret_configured=false`,
`auth_path_absolute_outside_checkout=false`, and no validated schema-v2 named
account store. The read-only preflight did not provision anything. Select and
establish the actual outside-Git private root/current-user identity, reviewed
settings, trusted loopback TLS, private credential handling and backup arrangement.
The accepted starter roster is sufficient; missing people alone are not a gate.
Preserve richer/disputed records and collect fresh availability in the app.

Usable setup/launch instructions are in target
`docs/PRIVATE_PILOT_SETUP_ISSUE214_R77.md`,
`docs/PRIVATE_PILOT_ISOLATION_ISSUE214_R75.md`, and this round's primary report.
`E:/ShiftCommander/PrivatePilot` remains a proposed, uncreated installation path.
The profile/LocalAppData proposal cannot be used unchanged because the profile
is inside a Git checkout. After approved private setup and stopping older launchers:

```powershell
python -B scripts/start_private_pilot.py --pilot-root E:/ShiftCommander/PrivatePilot --member-id 159 --member-id 186 --member-id 188 --check-only
python -B scripts/start_private_pilot.py --pilot-root E:/ShiftCommander/PrivatePilot --member-id 159 --member-id 186 --member-id 188
```

Intended supervisor entry is `https://127.0.0.1:5443/login/supervisor`; it is not
running from this dispatch. Ctrl+C stops the foreground pilot. Preserve the
same root for restart. Lock errors require stopping the identified existing
pilot or repairing private access, not deleting data/locks. The new lock does
not implement backups, transactional multi-file restoration or corrupt/deleted
JSON detection. Preserve historical audit and current credential revocations
when preparing the real backup/recovery drill.

**Production:** coordinated R37/R47/R77 bridge-credential incident disposition
remains unknown. Use `docs/PRIVATE_PILOT_AUTH_ISSUE214_R74.md` for the reviewed
consumer inventory, maintenance, replacement/recovery and superseded-key rejection
procedure. Complete consumer/edit-scope/maintenance authorization and rejection
proof are still required. No credential value was retrieved, printed, probed,
rotated or put in GitHub in R78. R43 connected metadata access remains established;
do not revive the retired blanket Cloudflare metadata-access blocker. ADR Calendar
remains published-staffing authority. Production release also requires actual
consent/demand/qualification provenance, staffing/client/publication/recovery,
communications and observer proof.

Account/operator action is still required for the real private installation and
coordinated provider incident change. Brian need not locate or understand an
exposed key; ask only for the exact remaining account or business decision.
Keep #214 and the draft stack open and unmerged. No production release, calendar
cutover, real account activation, member communication or paid service action
occurred. This round was locally processed, locally validated and pushed.

## Runtime, dispatch and work preservation

Matching active local session metadata reports `model=gpt-6-astra` at
`2026-09-14T22:47:21.025Z`, cwd `E:\GitHub\910cpr-class-landers`, CLI `0.153.4`.
Only exact metadata fields were inspected. This is local runtime evidence, not
provider attestation. The existing R2 `scripts/Start-AstraReview.ps1 -CheckOnly`
reported `can_launch=false` at `2026-09-14T18:51:56.8257565-04:00`: dispatcher
worker lock held/inaccessible. Continued this worker; no duplicate Codex worker,
dispatcher lock/lease change or unrelated model-default change.

The full issue body, pinned dispatch, 165-comment inventory and governing
owner/supervisor comments (including the new September 14 intake) were reviewed,
along with both AGENTS files, fetched-main CODEX_HANDOFF_PROTOCOL.md and proof
standard, #116, confirmed scheduling rules, project boundaries, RULES,
DATA_CONTRACT, migration/overlay contracts, R74-R77 continuation and PR #15.
The protocol is absent from the original courier branch; fetched main supplied it.
Pickup was acknowledged on [issue #214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-5671886939).

Both original checkouts retained their HEAD, branch, status paths and captured
dirty tracked-file SHA-256 values. No unfinished Git operation was found:

- `E:\GitHub\910cpr-class-landers`: `codex/durable-session-participant-linking`
  at `f2f5dd06e936e9620e0db5edc2331a38a8517e6d`. Existing Earl HTML, two tracked
  bytecode changes, untracked caches, heartbeat and Supabase temp directory remain.
- `E:\GitHub\shiftcommander_v2`: `codex/base44-worker-consolidation`
  at `55d6a05b919c1661845902b35eda14c9d4935f02`. Existing calendar mirror edit,
  untracked seed/availability backup/generator/script/test remain. Four unpublished
  commits (`3287eb4`, `9a49b9e`, `69bc1fb`, `55d6a05`) remain untouched.

The new target worktree is clean. The new sparse courier initially had an empty
index from `--no-checkout`; `git read-tree -mu HEAD` initialized only that new
worktree and confirmed clean status before the receipt. No source files in the
original checkout were deleted/restored. Only explicit intended files were staged.
No retired mutable mailbox or Codex_Read marker was created or consumed.

## Queue sweep and proof contract

Scanned all open issues and refreshed the latest #140, #215, #216, #219, #223,
#227 and #229 status comments. #140 remains the known HOT_SYNC parity/401 incident
at run `34852690014`; no unchanged-auth retry or weakened publisher gate. Other
items have delivered implementations or separate authentication, source, browser,
finance-input or dependency-review gates. #229's monitor is already in draft
#233; #227 customer expansion is explicitly deferred behind backend freshness.
No independent unclaimed narrow repair was identified; no duplicate change or
separate work-item mutation was made. This eligible backend reliability fix
continued the primary workstream despite external release gates.

Expected full outcome: real named availability -> durable revision after restart
-> legal explained staffing -> supervisor review -> authorized publication ->
matching member/supervisor/mobile/wallboard views. No complete real last-success
timestamp is established. Weekly publish remains Wednesday 23:59. Lost saves,
stale sources, illegal staffing and diverging views indicate failure. The lock
refuses competing starts immediately, but is not a whole-workflow observer or
watchdog. Observer heartbeat, independent escalation and full recovery proof
remain outstanding. Brian is not an acceptable substitute for those systems.
Do not label the operational release PROVEN, MONITORED or HEALTHY.

**Next ChatGPT action:** review draft #16's four files and the exact report above;
retain the production hold. Establish the specific private installation inputs
and perform the accepted starter-roster demonstration using the tested setup and
launcher. Coordinate R37/R47/R77 incident disposition with verified consumers and
maintenance authority, then obtain actual workflow/client/recovery/observer proof.
Only ChatGPT may acknowledge this receipt as Codex_Read.
