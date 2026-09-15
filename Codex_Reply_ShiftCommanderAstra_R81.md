# ShiftCommander Astra R81 — private availability deletion guard

- Assignment: [issue #214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214).
- Dispatch: `SHIFTCOMMANDER_ASTRA_20260913_R1`, continuing R80 as R81.
- Timestamp: `2026-09-14T20:37:28-04:00` (America/New_York).
- Work-item state: **PR_OPEN; production release BLOCKED**.
- Persistent-system evidence: **BUILT with synthetic local HTTPS proof**.
- Target repository: `Brian910cpr/shiftcommander_v2`.
- Target worktree: `E:/GitHub/shiftcommander_v2_codex_issue214_r81`.
- Target branch: `codex/issue-214-pilot-missing-availability-r81`.
- Implementation commit: [`b9cc8cfeb3412569fc02ebed878e3124a5d19dee`](https://github.com/Brian910cpr/shiftcommander_v2/commit/b9cc8cfeb3412569fc02ebed878e3124a5d19dee).
- [Draft target PR #19](https://github.com/Brian910cpr/shiftcommander_v2/pull/19), stacked on draft #18 at `ad1703c154c1ef291f33aec37b62220fce0974f8`.
- Courier worktree: `E:/GitHub/910cpr-class-landers_codex_issue214_receipt_r81`.
- Courier branch: `codex/issue-214-shiftcommander-receipt-r81`.
- Courier base: `1f8ede6e38d22b66374adb3b567ab16d0b24084c`.
- Courier change: only this unique repository-root receipt. Its commit is the
  branch tip after push, reported in the return issue comment/UI to avoid a
  self-referential commit hash.

## Findings and work performed

R79 preserved malformed availability and R80 added reviewed recovery, but missing
availability still became an empty state. I reproduced the loss through the real
synthetic HTTPS launcher before editing: save Preferred -> stop -> delete fixture
availability -> restart -> empty entries and healthy HTTP 200.

```json
{"baseline_save_status":200,"after_delete_restart_read_status":200,"after_delete_restart_entries":[],"after_delete_restart_health_status":200}
```

New private setup now exclusively writes an explicit empty availability record
inside its protected new root. No historical availability or consent is imported.
Missing availability now raises the existing sanitized storage error: reads,
saves, supervisor replacement/clear, resolver and health return 503; normal and
check-only startup refuse the root. The existing offline recovery command can
restore a reviewed same-installation snapshot with current state explicitly
recorded as `missing`, while retaining credential revocations.

**Compatibility:** existing readable roots continue normally. Older private roots
with no availability file now intentionally refuse startup, including a claimed
unused root. Preserve them; use reviewed recovery for a used installation. Without
a trustworthy saved record, recovery is blocked on authoritative availability
evidence. Do not invent empty consent or overwrite the installation. A confirmed
unused legacy root may be preserved and replaced by an approved new installation.
Nonpilot file-backend behavior and production/calendar authority are unchanged.

## Exact review files

All six files are at the implementation commit above:

1. `engine/live_state_store.py` — missing private availability refuses reads/saves.
2. `scripts/initialize_private_pilot.py` — explicit blank initial record.
3. `tests/smoke/test_private_pilot.py` — updated synthetic initial state.
4. `tests/smoke/test_private_pilot_setup.py` — no historical consent import, source preservation and Windows ACL checks.
5. `tests/smoke/test_private_pilot_availability.py` — missing-file and HTTPS/recovery/regression evidence.
6. [`docs/PRIVATE_PILOT_MISSING_AVAILABILITY_ISSUE214_R81.md`](https://github.com/Brian910cpr/shiftcommander_v2/blob/b9cc8cfeb3412569fc02ebed878e3124a5d19dee/docs/PRIVATE_PILOT_MISSING_AVAILABILITY_ISSUE214_R81.md) — full report, commands, compatibility, recovery and release gates.

Existing operational continuation remains in:

- `docs/PRIVATE_PILOT_SETUP_ISSUE214_R77.md` (use the R81 explicit-blank-file correction).
- `docs/PRIVATE_PILOT_RECOVERY_ISSUE214_R80.md`.
- `docs/PRIVATE_PILOT_AUTH_ISSUE214_R74.md` (coordinated bridge replacement).
- `docs/CONFIRMED_SCHEDULING_RULES.md`, `docs/PROJECT_BOUNDARIES.md`, `DATA_CONTRACT.md`.

## Validation and remote evidence

Focused suite: `python -B -m unittest discover -s tests/smoke -p test_private_pilot_availability.py -v`
equivalent loader execution: **12 passed in 12.210s**.

The full exact combined command is in the R81 report. Suites: private recovery,
availability, lock, setup, paths/HTTPS process, clients, live-state store and
resolver hard filters. Local ignored full log:
`E:/GitHub/shiftcommander_v2_codex_issue214_r81/debug/issue214_r81/validation.txt`.

```text
Ran 96 tests in 93.226s
OK
FINAL: tests=96 failures=0 errors=0 skips=0
Syntax: 5 Python files passed; no bytecode writes.
```

Counts overlap; do not add 12 and 96. No known unrelated failure occurred in
these suites. The entire repository test suite was not run.

Actual HTTPS tests cover deletion while running; nine protected/read/write/
health/resolver combinations returning 503; data, public mirror and audit bytes
preserved; both startup modes refusing missing state; read-only recovery;
explicit CLI restore; restart; restored preference; and rejection of the token
logged out after snapshot. Every other private-root file is byte-identical
across recovery, including credentials/revocations. Existing setup, temporary
password lifecycle, Windows ACL, client routing, lock/crash, corruption recovery
and 15 resolver hard-filter tests pass. No graphical-browser or real-member
proof is claimed.

Explicit staged/base diff and whitespace checks passed. No generator ran.
GitHub readback matched all six complete committed file contents and blob hashes.
Remote branch tip and PR #19 head equal `b9cc8cfeb3412569fc02ebed878e3124a5d19dee`.
PR #19 is OPEN/draft with no CI results reported at readback. No merge or deployment.

## Astra runtime and single-worker evidence

Matching current-session allowlisted local fields:

```json
{"cli_version":"0.153.4","originator":"Codex Desktop","turn_context_timestamp":"2026-09-15T00:26:37.475Z","model":"gpt-6-astra"}
```

This is local runtime evidence, not provider-side model attestation. Existing
`E:/GitHub/shiftcommander_v2_codex_issue214_r2/scripts/Start-AstraReview.ps1`
with `-RepoPath E:/GitHub/shiftcommander_v2_codex_issue214_r81 -CheckOnly` reported
`can_launch=false` at `2026-09-14T20:30:01-04:00`: dispatcher lock held/inaccessible.
No competing Codex worker was launched; no lease, lock, permission or machine
model default changed. Zero private-pilot launcher processes remain after tests.

## Exact blockers and required next action

1. **Private installation is not established.** Presence-only checks found no
   `SC_AUTH_DB_PATH` or `SECRET_KEY` in this worker; candidate
   `E:/ShiftCommander/PrivatePilot` does not exist. No real account store was opened.
   Select the actual outside-Git directory/current-user installation, reviewed
   settings, trusted loopback TLS, hidden named-account setup and backup arrangement.
   Then perform the accepted starter-roster demonstration with fresh availability.
   The accepted roster and supervisors 159/186/188 are sufficient for preparation;
   roster incompleteness is not a gate. These process-local checks do not establish
   inherited hosting configuration.
2. **Credential incident disposition remains unverified.** This R81 dispatch
   accidentally included a credential-valued environment variable in its tool
   transcript during an overly broad environment-name inspection. The variable
   was `SC_D1_BRIDGE_TOKEN_CODEX_SESSION`; its value is not in GitHub, this receipt
   or the report. It was not probed, rotated or used. Add R81 to the existing
   R37/R47/R77 coordinated containment/replacement requirement, verified consumer
   inventory/maintenance authority and superseded-key rejection proof. Current
   validity/replacement status is unknown. Subsequent runtime inspection used
   exact session fields only. No one needs to paste a credential into this issue.
3. **Complete release proof is outstanding.** Real staffing consent, current
   qualifications/unit-specific driving permission, demand/calendar provenance,
   protected/partial/overnight/DST/OT/swap scenarios, publication, client agreement,
   recovery, phone/SMS/email integration and independent observation remain open.
   R43 connected Cloudflare metadata evidence remains established; no obsolete
   blanket metadata-access blocker or unchanged denied credential retry was added.

Next ChatGPT action: review PR #19 with #18 and the dependent draft stack, including
the intentional missing-file compatibility behavior. Establish the exact private
installation inputs and privately coordinate credential-incident disposition.
Keep #214 and the draft stack open. No release, production auth/routing activation,
real recovery, calendar cutover, account activation or member communication is
authorized by this checkpoint. The expected private URL after actual installation
remains `https://127.0.0.1:5443/login/supervisor`; it is not running now. The R81
report supplies exact check/start/stop and recovery commands.

User/account action is needed for the remaining private installation and
credential-maintenance decisions; reversible local code preparation was completed
without another permission prompt.

## Persistent-system proof and recovery limits

Expected outcome: named availability -> durable revision after restart -> legal
explained staffing -> supervisor review -> authorized publication -> matching
member/supervisor/mobile/wallboard views. No complete real end-to-end last-success
timestamp exists in this return. Wednesday 23:59 remains the weekly publication
boundary. Missing/corrupt/stale inputs, lost saves, illegal assignments and view
disagreement are failures. Startup and on-demand health detect the repaired
missing-file failure. Independent observer/heartbeat, whole-system/off-device
backup and real recovery remain unproven. Use the reviewed offline recovery path;
escalate absent trustworthy saved state rather than inventing consent. This
checkpoint is BUILT with synthetic proof, not real PROVEN/MONITORED/HEALTHY.

## Preservation and independent queue sweep

Both original checkout HEAD/branch/status/dirty tracked-file hashes and the R80
worktree matched the captured baseline after validation. Four unpublished commits
on `codex/base44-worker-consolidation` remain preserved. Original LanderWare dirty
work includes `docs/Earl/index.html`, tracked Python caches, the existing heartbeat,
untracked caches and `supabase/.temp/`; none was staged. Original ShiftCommander
dirty work includes `data/google_calendar_june_2026_mirror.json`, the seed/backup
JSON files, `engine/slot_schedule_generator.py`, `scripts/run_slot_schedule_mvp.py`
and `tests/resolver/test_slot_schedule_generator.py`; none was staged. No cleanup,
reset, restore, merge, rebase or forced update touched an existing worktree.

This target worktree is clean after its six-file commit. The sole local validation
log is intentionally ignored/uncommitted, not public. The new root-only courier
was initialized from pinned main with no application files edited. Reply/read
collision checks found no prior R81 receipt before creation. Prior receipt/read
history remains intact; Codex created no acknowledgement marker.

Swept the open issue queue and reviewed current #215/#219/#227, #229 and #140
directions/returns. Owner entry and document controls are already delivered;
remaining instructor identity, finance/legacy connections and authenticated proof
need their distinct inputs. #229's existing #230-#233 stack retains feed/runtime/
source/access and workflow proof gates. #140 remains the credential-parity/401
incident; do not bypass it or repeat unchanged authentication. #227 directs
stabilization before more customer-facing expansion. No new independent unclaimed
narrow repair was established; no duplicate work or timer was launched. Safe
backend progress in this dispatch is the concrete ShiftCommander defect above.

Full issue body/pinned dispatch and all 171 prior comments were fetched; governing
supervisor/owner instructions and current returns were reviewed. Repository
AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, proof standard and #116 were read. Pickup is
recorded at issue comment `5672823304` (2026-09-15T00:30:30Z). The return comment
will supply this receipt's immutable commit URL after push and byte verification.
