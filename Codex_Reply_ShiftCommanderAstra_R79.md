# ShiftCommander Astra R79 — private availability preservation

- Assignment: [issue #214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214)
- Dispatch ID: `SHIFTCOMMANDER_ASTRA_20260913_R1`
- Timestamp: `2026-09-14T23:36:32Z` (September 14, America/New_York, UTC-04:00)
- Work-item state: **PR_OPEN** for this increment; **BLOCKED** for production release.
- Persistent-system evidence: **BUILT with synthetic local HTTPS proof**. No real
  PROVEN/MONITORED/HEALTHY release claim.
- Target repository: `Brian910cpr/shiftcommander_v2`
- Target worktree: `E:\GitHub\shiftcommander_v2_codex_issue214_r79`
- Target branch: `codex/issue-214-pilot-state-integrity-r79`
- Implementation commit: `6d7016d271c1cd52c31e5e5e0121490f2659c4c3`
- [Draft PR #17](https://github.com/Brian910cpr/shiftcommander_v2/pull/17), stacked
  on draft #16 at `848517905db9fda064da9cad0a90e14cb878bff3`; open, unmerged.
- Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r79`
- Courier branch: `codex/issue-214-shiftcommander-receipt-r79`
- Courier base: `1f8ede6e38d22b66374adb3b567ab16d0b24084c`
- Courier scope: only this unique root receipt. Its commit is the pushed branch
  tip and is returned on #214 and in the Codex response, avoiding a self-reference.

## Outcome and root cause

The R78 pilot excluded competing processes, but its file store still interpreted
unreadable/malformed availability as empty. A later member save could replace
the damaged record. Reproduced before editing with the existing synthetic HTTPS
fixture and named test accounts:

```text
initial_save_http 200
corrupt_read_http 200 entries []
corrupt_save_http 200 damaged_bytes_preserved False
```

Implemented a narrow private-pilot repair. Availability reads and writes now
reject invalid/unreadable JSON and malformed containers; full supervisor
replacement also checks existing storage before writing. Valid additional fields
and intent vocabulary survive unchanged. Errors use fixed code
`private_pilot_availability_unavailable` without paths, record data or OS details.

The API returns 503 for affected reads/edits/clear/resolver operations and the
private health check. Startup/check-only rejects an existing damaged file before
application import. Tests verify unchanged private data, public mirrors and debug
artifacts across failing requests. Hosted/default file behavior, staffing policy,
calendar authority and the existing auth schema retain their prior behavior.

This does not implement missing/deleted-file detection across restart, integrity
checks for every other JSON resource, transactional backups or automatic repair.
R77 intentionally starts without availability; absence still means first use.
The original atomic replacement path and R78 cooperative process lock remain.

## Exact review files and durable report

All five files are in target commit
[`6d7016d271c1cd52c31e5e5e0121490f2659c4c3`](https://github.com/Brian910cpr/shiftcommander_v2/commit/6d7016d271c1cd52c31e5e5e0121490f2659c4c3):

1. `engine/live_state_store.py` — private availability validation and preservation.
2. `server.py` — sanitized 503 response and private health failure signal.
3. `scripts/start_private_pilot.py` — pre-import availability check.
4. `tests/smoke/test_private_pilot_availability.py` — 10 regression tests.
5. [`docs/PRIVATE_PILOT_AVAILABILITY_ISSUE214_R79.md`](https://github.com/Brian910cpr/shiftcommander_v2/blob/6d7016d271c1cd52c31e5e5e0121490f2659c4c3/docs/PRIVATE_PILOT_AVAILABILITY_ISSUE214_R79.md)
   — primary report with reproduction, exact commands, validation, limits,
   recovery procedure and release continuation. Read this report and source,
   not only this receipt, when reviewing data behavior.

The only transport file changed is `Codex_Reply_ShiftCommanderAstra_R79.md`.
No source, operational data or credentials were copied into the courier.

## Validation and evidence limits

- **81 tests passed in 69.028s**, zero failures/errors/skips: private availability,
  process lock, setup, HTTPS pilot, served clients, live-state store and hard filters.
- After adding the private health check and refining the member message,
  **26 tests passed in 29.530s**, zero failures/errors/skips: availability and private
  serving boundary. These overlap the first run and are not 107 unique tests.
- Four final Python AST/compile syntax checks passed in memory; no bytecode added.
- Explicit staged-file and base-to-head `git diff --check` passed.
- New tests cover 18 malformed-record inputs; initial no-file state; preserved
  richer fields; invalid writes; permission/replace failures; nonregular/hardlinked
  paths; unchanged nonpilot behavior; normal/check-only startup; nine real synthetic
  HTTPS endpoint/method combinations; unchanged bytes and recovery to known bytes.
- Existing isolated resolver/audit and legal hard-filter cases passed. No real
  roster availability or staffing decision was changed. No generator ran.
- The first focused run had one erroneous test expectation about deeply nested
  but valid JSON in an unknown extension. Removed that invalid expectation; the
  final selected checks have no unresolved failures.
- Logs are persisted locally and intentionally ignored in the target worktree:
  `debug/issue214_r79/validation.txt` and
  `debug/issue214_r79/final_health_validation.txt`. Exact repeat commands are in
  the committed primary report.
- At `2026-09-14T23:33:45.715256Z`, complete GitHub bytes and Git blob hashes matched
  all five committed target files. PR #17 is draft/open; no CI checks reported.
- Synthetic subprocess fixtures were stopped and cleaned up. No operational URL
  was started. This is local HTTP/JavaScript/backend evidence, not graphical-browser,
  real-member, production publication or complete release proof.

## Exact remaining blockers and usable continuation

### Private demonstration

Owner comment [September 14 inputs](https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-5670369799)
accepts the starter roster and supervisors 159, 186 and 188. Missing starter members
alone are **not** a gate. The same private-pilot implementation workstream continues.

Actual outside-Git storage/current-user identity, reviewed settings, trusted
loopback TLS, private credential handling and backup arrangement have not been
established. Presence-only inspection in this worker returned:

```json
{"SC_AUTH_DB_PATH_configured": false, "SECRET_KEY_configured": false}
```

No real account database or secret was opened or provisioned. These results describe
this worker's configuration, not a claim that no private material exists elsewhere.
No unchanged failing auth/provider route was retried. The user profile is itself
inside a Git checkout; the old LocalAppData suggestion remains unsuitable.

Usable work: the draft stack contains offline named-account setup, isolated
loopback HTTPS startup, pilot-only clients, durable auth/revocation, process
exclusion and this availability safeguard. Use these target files at the commit:

- `docs/PRIVATE_PILOT_SETUP_ISSUE214_R77.md` — exact check/interactive initialization.
- `docs/PRIVATE_PILOT_LOCK_ISSUE214_R78.md` — lifetime lock and safe restart.
- `docs/PRIVATE_PILOT_ISOLATION_ISSUE214_R75.md` — private layout/origin boundaries.
- `docs/PRIVATE_PILOT_AUTH_ISSUE214_R74.md` — credential incident preparation;
  its LocalAppData suggestion is superseded by the later outside-Git check.

After the private installation inputs are established, from the target review
worktree use the R77 setup command, then:

```powershell
python -B scripts/start_private_pilot.py --pilot-root E:/ShiftCommander/PrivatePilot --member-id 159 --member-id 186 --member-id 188 --check-only
python -B scripts/start_private_pilot.py --pilot-root E:/ShiftCommander/PrivatePilot --member-id 159 --member-id 186 --member-id 188
```

That root is an **unprovisioned proposal**. Expected entry after installation is
`https://127.0.0.1:5443/login/supervisor`; stop with Ctrl+C. There is no currently
running operational URL from this work. Initial passwords require hidden operator
entry and subsequent changes; do not paste credentials into issues or receipts.

On `private_pilot_availability_unavailable`, stop the identified pilot and preserve
the full root, damaged availability and any temporary file. Review permissions
and known backup evidence before recovery; keep current auth/revocations. Do not
initialize over data or delete a held lock. This repair does not authorize an
unreviewed overwrite of operational records.

### Production release

The [September 14 supervisor gate](https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-5660603019)
remains applicable with the later owner-intake changes above. Connected R43 metadata
access remains established history; the blanket metadata-access blocker is retired.

Production still requires coordinated **R37/R47/R77 credential-incident disposition**,
consumer inventory, maintenance/edit authority and rejection of superseded keys.
Replacement status remains unknown. No operational credential value was retrieved,
printed, probed or rotated in R79. ADR Calendar remains published-staffing authority.

Then prove real consent/demand/qualification provenance, legal explained staffing,
protected/partial/overnight/DST/OT/swap scenarios, review/publication, cross-view
agreement, backup restoration, communications and independent observation. The
full checklist in `docs/PRIVATE_PILOT_LOCK_ISSUE214_R78.md` remains open. Phone/SMS/
email are retained in scope, with real identity, consent and retry/delivery proof.

## Persistent-system proof and observation

Expected outcome: named availability -> durable revision after restart -> legal
explained staffing -> supervisor review -> authorized publication -> matching
member/supervisor/mobile/wallboard views. **No full real last-success timestamp is
established.** The latest local synthetic proof is recorded in the test logs above.

Wednesday 23:59 remains the weekly publication boundary. Unreadable/lost saves,
stale sources, illegal assignments and disagreeing views are failures. This change
adds an on-demand 503 health signal for unreadable private availability. An
independent observer, observer heartbeat, retention, automatic recovery and
escalation proof remain unestablished; Brian must not be the routine monitor.
BUILT/synthetic evidence does not establish PROVEN, MONITORED or HEALTHY operation.

## Preservation, runtime and independent queue sweep

Original checkouts remain intact:

- `E:\GitHub\910cpr-class-landers`, branch
  `codex/durable-session-participant-linking`: unrelated Earl HTML, tracked Python
  bytecode, untracked heartbeat/cache files and Supabase temp state preserved.
- `E:\GitHub\shiftcommander_v2`, branch `codex/base44-worker-consolidation`:
  dirty calendar mirror, local slot-schedule code/data/test and availability backup
  preserved. Four unpublished commits remain: `3287eb4`, `9a49b9e`, `69bc1fb`, `55d6a05`.
- Original HEAD, branch, full porcelain status and dirty tracked-file SHA-256
  hashes matched captured baselines after target push. No pending merge/rebase/
  cherry-pick marker was found or changed. No cleanup, reset or rebase occurred.
- The implementation worktree is clean. Both review worktrees are intentionally
  retained. Local debug logs are ignored; they were not staged or uploaded.

Matching active local session `turn_context` reports `gpt-6-astra` at
`2026-09-14T23:20:03.150Z`, CLI `0.153.4`. This is sanitized local runtime evidence,
not provider attestation or merely a changed prompt/default. Runtime inspection
was restricted to exact metadata fields; no environment dump was used.

The existing R2 `scripts/Start-AstraReview.ps1 -CheckOnly` at
`2026-09-14T19:23:14.4533145-04:00` reported an occupied dispatcher lock and
`can_launch=false`. Continued this active worker; no second agent, lock/lease,
timer or machine-default change. Issue #116 concurrency remains intact.

Swept open actionable issues and checked current bodies/latest returns for #140,
#215, #219, #223, #227, #229 and #216. No independent unclaimed narrow repair was
established that justified disrupting this primary workstream:

- #140: unchanged credential parity/401 incident; no repeat auth retry.
- #215/#219: delivered owner access/document controls; legacy connections and
  individual instructor identity/assignment scope are distinct remaining work.
- #223: 19 sessions already reconciled; provisional source end and owner proof
  remain distinct. No duplicate import.
- #216: delivered monitor; private finance inputs and observer proof remain.
- #227: supervisor explicitly defers expansion behind backend freshness/#140.
- #229: existing draft #233 still open on `codex/issue-229-monitor-feed-r3`, current
  head `92bf3b065208445e8481b0a2c4422656df3eed38`; dependency/configuration and real
  endpoint/browser proof are outstanding. No duplicate monitor implementation.

These were queue eligibility checks, not secondary implementation assignments;
no other issue or application was changed. No retired mutable mailbox was used,
and no `Codex_Read_*` acknowledgement was created.

## Required next action

ChatGPT: review draft **PR #17** and the exact primary report/source/test files,
then establish the actual private installation inputs and conduct the accepted
starter-roster demonstration. Keep #214 and the draft stack open and unmerged.
Coordinate production credential incident/release work under the existing gates.

User/account action is required for private interactive setup and unresolved
settings/TLS/backup/credential-maintenance authority. Brian need not identify,
understand or paste the exposed key to permit the already completed preparation.

Deployment status: **persisted locally; intended target files committed and pushed;
draft PR open; validated locally; not merged; not deployed; no production write,
calendar cutover, account activation or member communication**. This root receipt
is committed and pushed separately; GitHub byte/blob/tip verification and its
exact courier commit are returned in the issue completion comment.
