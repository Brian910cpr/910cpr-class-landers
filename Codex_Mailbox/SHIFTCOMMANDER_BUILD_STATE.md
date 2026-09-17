# ShiftCommander durable build state

**Purpose:** This is the canonical resume-first checkpoint for ongoing ShiftCommander development and failure recovery. It exists to prevent each ChatGPT/Codex/PC-worker visit from re-orienting from zero and spending credits rediscovering already established facts.

**Transport repository:** `Brian910cpr/910cpr-class-landers`

**Implementation repository:** `Brian910cpr/shiftcommander_v2`

**Expected local checkout:** `E:\GitHub\shiftcommander_v2`

**Current workstream origin:** `Codex_Mailbox/SHIFTCOMMANDER_ASTRA_20260913_R1.md`

## Mandatory resume rule

Before broad repository discovery, release auditing, or repeating prior diagnostics, read this file and the newest ShiftCommander Codex receipt/checkpoint. Treat the most recent verified entries here as established unless current evidence contradicts them.

For an ongoing failure, start with the **Last known blocker**, **Last attempted action**, **Observed result**, and **Next exact action** below. Do not rerun the entire release assessment merely to rediscover the same blocker.

Re-open older requirements or redo broad inventory only when:

1. the current blocker points there;
2. code/configuration changed since the recorded checkpoint;
3. the recorded evidence is stale or contradicted; or
4. a release-gate verification specifically requires it.

Every ShiftCommander work session that makes meaningful progress, encounters a blocker, changes the diagnosis, or attempts a repair must update this file before stopping. Do not erase history: append a dated attempt entry and refresh the current-state fields.

## Stable project facts

- ShiftCommander product code and operational implementation belong in `Brian910cpr/shiftcommander_v2`, not in LanderWare.
- The 910CPR repository is being used as the durable dispatch/receipt transport for the existing PC-worker handshake.
- Preserve the existing ShiftCommander checkout, worktrees, branches, uncommitted work, operational data, and backups. Do not reset merely to obtain a clean tree.
- Preserve ADR Google Calendar's currently documented published-staffing authority until an explicitly verified cutover.
- Quick Test Mode and Real Mode are separate. Do not infer production authority from a database/deployment name.
- Release claims require evidence beyond a passing build: authentication, authorization, persistence, auditability, scheduling correctness, and end-to-end workflow evidence must be distinguished as local/staging/deployed/unverified.
- Development authentication or misleading save-success behavior remains a release blocker if still present.
- ShiftCommander work must follow the implementation repository's `AGENTS.md`, `docs/PROJECT_BOUNDARIES.md`, `docs/CONFIRMED_SCHEDULING_RULES.md`, `RULES.md`, `DATA_CONTRACT.md`, and current migration/overlay documentation.

## Current state

**Overall state:** ACTIVE / NOT YET VERIFIED RELEASE-READY

**Last verified checkpoint:** The current transport handoff requests a fresh ShiftCommander release assessment and Astra-backed review in the implementation repository. A prior release-fixes patch is retained in `Codex_Mailbox/SHIFTCOMMANDER_RELEASE_FIXES_009b089.patch` and must be checked before duplicating those fixes.

**Last known blocker:** Exact live blocker must be taken from the newest ShiftCommander receipt or current implementation-repository evidence. Do not invent or substitute a stale blocker. If no newer receipt exists, begin by verifying whether the previously reported authentication/deployment/persistence gaps still exist, then record the exact failing gate here.

**Last attempted action:** No attempt newer than the current durable transport artifacts is recorded in this checkpoint yet.

**Observed result:** No newer result has been recorded here yet.

**Next exact action:**
1. Read the newest ShiftCommander Codex receipt/checkpoint, if any.
2. Inspect current `git status`, active branch/worktree, and only the files/tests connected to the recorded blocker.
3. Check whether `SHIFTCOMMANDER_RELEASE_FIXES_009b089.patch` or its equivalent changes are already present before re-implementing them.
4. Reproduce the current blocker with the narrowest relevant test or runtime check.
5. Make the next safe reversible repair or report the exact owner/account gate.
6. Update this file with the attempt and next action before ending the session.

## Owner/account gates

Keep unresolved human gates visible here until positively verified cleared. Distinguish **no new owner action** from **existing owner action still required**.

Current gate status: **UNKNOWN / MUST BE REFRESHED FROM LATEST VERIFIED SHIFTCOMMANDER EVIDENCE.** Do not state that Brian has nothing to do unless this section has been explicitly cleared by current evidence.

## Attempt log

### 2026-09-17 - Durable checkpoint introduced

- Reason: repeated ShiftCommander build/recovery visits were starting with broad re-orientation instead of resuming from prior failure state.
- Action: introduced this canonical resume-first build-state file.
- Result: future workers have a single durable checkpoint for known facts, last blocker, prior attempt, result, next action, and owner gates.
- Required follow-through: every meaningful ShiftCommander attempt must update this file before yielding, failing, or dispatching another round.

## Required exit update template

Append one entry using this shape after every meaningful attempt:

```md
### YYYY-MM-DD HH:MM TZ - <short attempt label>
- Starting blocker:
- Evidence inspected:
- Action attempted:
- Result:
- New/unchanged root cause:
- Tests/checks run:
- Commit/PR/branch:
- Owner/account gate:
- Next exact action:
```

Then refresh **Last known blocker**, **Last attempted action**, **Observed result**, **Next exact action**, and **Owner/account gates** above.

## Receipt rule

When a Codex round is required, use a new unique `Codex_Reply_ShiftCommander...R<n>.md` receipt. Never overwrite an earlier receipt. The receipt should summarize that round; this file is the continuing cross-round state. ChatGPT, not Codex, performs any `Codex_Read_*` acknowledgement in the transport repository after genuine review.
