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
- The 910CPR repository is the durable dispatch/receipt transport for the existing PC-worker handshake.
- Preserve the existing ShiftCommander checkout, worktrees, branches, uncommitted work, operational data, and backups. Do not reset merely to obtain a clean tree.
- Preserve ADR Google Calendar's currently documented published-staffing authority until an explicitly verified cutover.
- Quick Test Mode and Real Mode are separate. Do not infer production authority from a database/deployment name.
- Release claims require evidence beyond a passing build: authentication, authorization, persistence, auditability, scheduling correctness, and end-to-end workflow evidence must be distinguished as local/staging/deployed/unverified.
- Development authentication or misleading save-success behavior remains a release blocker if still present.
- ShiftCommander work must follow the implementation repository's `AGENTS.md`, `docs/PROJECT_BOUNDARIES.md`, `docs/CONFIRMED_SCHEDULING_RULES.md`, `RULES.md`, `DATA_CONTRACT.md`, and current migration/overlay documentation.
- Brian has already approved the initial supervisors (member IDs 159, 186, 188) and the accepted starter roster is sufficient for private-pilot preparation. Missing roster members alone are not a blocker.
- Connected Cloudflare metadata access was established in the R43 evidence. Do not revive the retired blanket metadata-access blocker without new contradictory evidence.

## Current state

**Overall state:** BUILT WITH SYNTHETIC PRIVATE-PILOT PROOF / PRODUCTION BLOCKED

**Last verified checkpoint:** ShiftCommander R81 was reviewed and acknowledged. Draft PR #19 remains open/draft/unmerged at `b9cc8cfeb3412569fc02ebed878e3124a5d19dee`. The R81 implementation fails closed if the private pilot availability file is deleted, initializes a deliberate blank availability record for a new private root, and preserves the reviewed offline recovery path. The reported combined local validation was 96 passing tests with no failures/errors/skips; no CI status checks are attached to PR #19. The transport receipt has already been retired as `Codex_Read_ShiftCommanderAstra_R81.md` on its receipt branch.

**Last known blocker:** 2026-10-11 private-install preflight: E:/ShiftCommander now exists as an empty outside-Git parent, but no operational PrivatePilot root or selected TLS input files exist. No valid localhost/127.0.0.1 certificate with a private key was found in CurrentUser/My (count 0). The existing launcher reports dispatcher worker lock held or inaccessible; no duplicate Astra worker was started and no fresh Astra review is claimed. Reviewed settings provenance and trusted TLS inputs must be selected before check-only can pass; initialization then requires hidden password entry in an interactive local terminal. Production incident/release gates remain unchanged.

**Last attempted action:** 2026-10-11: resumed R81, ran existing Astra launcher CheckOnly, ran initialize_private_pilot.py --check-only, created only the missing outside-Git parent E:/ShiftCommander, and repeated check-only. No private store/accounts or TLS trust were created.

**Observed result:** Initial check-only returned root_requires_existing_absolute_parent. After parent creation, it returned private_setup_failed; presence checks independently confirm selected TLS certificate/key are absent. PrivatePilot remains absent. No real workflow proof. Existing draft PR #19 remains the implementation checkpoint; no source change, merge or deployment.

**Next exact action:**
1. Resume from the current draft stack through PR #19; do not restart the release audit.
2. The 2026-10-11 execution created only the empty outside-Git parent `E:/ShiftCommander`. Keep `E:/ShiftCommander/PrivatePilot` new. Select actual reviewed settings and trusted loopback TLS PEM inputs privately; the checked candidate `E:/ShiftCommander/PrivatePilotInputs/tls.crt` and `tls.key` are absent. The current-user pilot does not require a new Windows service account.
3. Use the reviewed R77/R81 setup path to establish a new private root only if it does not already exist. Supply reviewed settings, trusted loopback TLS certificate/key, and supervisor member IDs 159, 186, 188. Run `scripts/initialize_private_pilot.py` in `--check-only` mode before any initialization. Do not invent or import historical availability consent.
4. If check-only proves the inputs safe, initialize the private root with hidden temporary-password entry, then run `scripts/start_private_pilot.py ... --check-only` before starting the pilot. Do not bypass incomplete/missing/corrupt-state guards.
5. Perform the accepted starter-roster private demonstration and record real evidence: named login, required password change, fresh availability save, restart persistence, legal resolver output, supervisor review, and matching private views. Keep production publication/calendar authority unchanged.
6. Separately coordinate the bridge-credential incident disposition. Inventory actual consumers/maintenance authority without printing credential values, replace/rotate only through an authorized provider path, and prove the superseded credential is rejected. Never paste credentials into GitHub.
7. Update this file with the exact result, blocker, and next action before ending. Create a new unique `Codex_Reply_ShiftCommander...R<n>.md` only for genuinely new work; do not recreate R81.

## Owner/account gates

Keep unresolved human gates visible here until positively verified cleared. An owner gate is not acceptable unless it states the exact physical action Brian must take.

**Current gate status:** As of 2026-10-11, trusted TLS inputs are absent at the checked paths, no matching valid localhost/127.0.0.1 certificate with private key was found in CurrentUser/My, and this execution has noninteractive stdin. Do not initialize real accounts through captured input. The Astra launcher reports its dispatcher lock held or inaccessible; preserve it. No newly verified need for Brian to manipulate GitHub/Cloudflare/Render/Windows settings merely to resume code work. The worker should first execute the reversible private-installation preparation above. If the private installation reaches an interactive hidden-password step, Brian (or the authorized intended Windows user) must enter temporary passwords locally; passwords must not be sent through GitHub/chat or stored in arguments/environment variables. If bridge-token rotation cannot be completed using already-authorized provider access, the worker must name the exact provider/account page and exact credential/permission action Brian must perform. Until that exact provider-side blocker is reproduced, do not ask Brian to guess, retrieve, or paste a key.

Production remains blocked until the credential-incident disposition and superseded-key rejection proof are complete.

## Attempt log

### 2026-09-17 - Durable checkpoint introduced

- Reason: repeated ShiftCommander build/recovery visits were starting with broad re-orientation instead of resuming from prior failure state.
- Action: introduced this canonical resume-first build-state file.
- Result: future workers have a single durable checkpoint for known facts, last blocker, prior attempt, result, next action, and owner gates.
- Required follow-through: every meaningful ShiftCommander attempt must update this file before yielding, failing, or dispatching another round.

### 2026-09-17 - R81 state reconciled into durable checkpoint

- Starting blocker: durable state still said exact blocker/owner gate were unknown even though the reviewed R81 handoff and PR #19 contained later verified evidence.
- Evidence inspected: issue #214 continuation history through R81; acknowledged `Codex_Read_ShiftCommanderAstra_R81.md`; ShiftCommander PR #19 current open/draft state and core patches; R77 private-pilot setup report; current 910CPR Actions status.
- Action attempted: reconciled the canonical state to the already-reviewed R81 checkpoint and converted the vague owner gate into a resume-first operational sequence.
- Result: next worker can proceed directly to private-installation check/setup instead of re-auditing the project or asking Brian to guess at credentials.
- New/unchanged root cause: application preparation is substantially built; real private installation and credential-incident disposition remain the release gates.
- Tests/checks run: connector review only; no local test rerun. PR #19 still has no GitHub CI status checks.
- Commit/PR/branch: PR #19 remains draft at `b9cc8cfeb3412569fc02ebed878e3124a5d19dee`.
- Owner/account gate: only local hidden-password entry if/when initialization reaches that step, plus any exact provider-side credential action that the worker proves it cannot perform itself.
- Next exact action: execute the private-installation check/setup sequence above and record the result here.

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


### 2026-10-11 EDT - Private-install prerequisite execution
- Starting blocker: R81 preparation complete; actual private installation absent.
- Evidence inspected: originating #214 body/history, pinned dispatch, this state, R77/R81 reports, target AGENTS.md and confirmed rules, #116, root handoff/proof protocols, draft #372 hold.
- Action attempted: existing launcher CheckOnly; actual setup --check-only before and after creating E:/ShiftCommander outside Git; certificate metadata/presence checks only. No credential values read.
- Result: parent prepared; selected TLS inputs absent, CurrentUser/My matching valid certificate/private-key count zero, no private root initialized. Setup returns private_setup_failed after the missing-parent gate is resolved.
- New/unchanged root cause: installation inputs and interactive password entry remain required; dispatcher lock prevents a competing Astra launch.
- Tests/checks run: focused existing private setup suite; two Python AST checks; scope/whitespace and remote receipt readback recorded in this round's receipt.
- Commit/PR/branch: existing ShiftCommander draft #19 at b9cc8cfeb3412569fc02ebed878e3124a5d19dee unchanged. Courier codex/issue-214-private-install-preflight-20261011; see Codex_Reply_ShiftCommanderPrivateInstall_20261011_R1.md for state-update commit.
- Owner/account gate: intended Windows user must enter temporary passwords locally only after reviewed settings and trusted TLS pass check-only. No password in chat, GitHub, arguments or environment. Do not claim a provider rotation blocker from this run; no provider write/probe attempted.
- Next exact action: select reviewed settings and trusted loopback TLS PEM pair privately; rerun existing initialize_private_pilot.py --check-only with actual paths. Then intended user runs --initialize with hidden prompts, followed by start_private_pilot.py --check-only and the private workflow demonstration. Preserve PR #372, the existing target draft stack, production/calendar hold and credential incident disposition.
- Queue sweep: current open [CODEX] list reviewed; #373 explicitly follows #371 foundation and must not interrupt it; #215/#219 have existing delivered work with remaining access/role/proof gates. No newly eligible unclaimed narrow backend edit was established; no competing stream or duplicate repair launched.
- Courier integrity: original E:/GitHub/910cpr-class-landers fetch failed on bad object 6e61cabca5981d1389e52c60d95424d9893bb50f and refs/remotes/origin/codex/group-training-experience. No ref deletion/cleanup/reset attempted. Fresh sparse remote checkout used only for the two intended transport files.
