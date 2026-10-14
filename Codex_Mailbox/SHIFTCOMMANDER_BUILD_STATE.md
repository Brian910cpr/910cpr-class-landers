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

## Current owner gate override — 2026-10-14

This section supersedes the older September setup directions below. Issue #214 owner acknowledgment at 2026-10-14T11:54:56Z (https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-6167750287) requires suppression of setup/auth/preflight/launcher retries until approved outside-Git private settings and trusted-loopback TLS inputs change. No such input-change evidence was established during this dispatch. Do not treat the historical setup sequence below as permission to retry an unchanged path.

- Last known blocker: approved private settings and trusted-loopback TLS certificate/key paths remain gated; bridge-credential disposition and real operational proof also remain outstanding.
- Last attempted action: bounded read-only issue/dependency review; no installation, auth, preflight or launcher attempt.
- Observed result: existing ShiftCommander draft #19 remains at b9cc8cfeb3412569fc02ebed878e3124a5d19dee; no merge/deploy or fresh Astra runtime proof. Existing backend assignments preserved.
- Next exact action: wait for evidence that approved private inputs changed, then resume existing reviewed check-only member flow for IDs 159/186/188. Require controlled workflow, restart, recovery and observer proof before release claims. Keep #214 open and #372 unmerged/undeployed.
- Owner/account gate: deliver reviewed settings/TLS paths through the approved private local path; never put passwords, signing material or private settings in GitHub/chat. No duplicate owner alert or unchanged retry.

## Current state

**Overall state:** BUILT WITH SYNTHETIC PRIVATE-PILOT PROOF / PRODUCTION BLOCKED

**Last verified checkpoint:** ShiftCommander R81 was reviewed and acknowledged. Draft PR #19 remains open/draft/unmerged at `b9cc8cfeb3412569fc02ebed878e3124a5d19dee`. The R81 implementation fails closed if the private pilot availability file is deleted, initializes a deliberate blank availability record for a new private root, and preserves the reviewed offline recovery path. The reported combined local validation was 96 passing tests with no failures/errors/skips; no CI status checks are attached to PR #19. The transport receipt has already been retired as `Codex_Read_ShiftCommanderAstra_R81.md` on its receipt branch.

**Last known blocker:** The code-preparation stack has reached the point where the next useful step is an actual private installation, not another broad code audit. No real private store has been established in the verified R81 evidence: `SC_AUTH_DB_PATH`/signing configuration were absent in that worker and the candidate `E:/ShiftCommander/PrivatePilot` did not exist. Production also remains gated on coordinated disposition of the R37/R47/R77/R81 bridge-credential exposures and proof that superseded credentials are rejected, followed by real staffing/client/publication/recovery/observer proof.

**Last attempted action:** R81 reproduced deletion of saved private availability being silently treated as empty state after restart and repaired it so missing state now blocks reads/writes/resolver/health and startup until reviewed recovery.

**Observed result:** Draft PR #19 is still open and unmerged. The narrow fail-closed change is consistent with the private-pilot integrity contract and the receipt was already acknowledged. No production deployment, account activation, real recovery, calendar cutover, or member communication is proven by this checkpoint.

**Next exact action:**
1. Resume from the current draft stack through PR #19; do not restart the release audit.
2. On CYBERPC, first determine whether a safe outside-Git parent already exists. The documented candidate is `E:/ShiftCommander/PrivatePilot`; the R77 report says its parent must be outside Git and the current-user interactive pilot does not require a new Windows service account.
3. Use the reviewed R77/R81 setup path to establish a new private root only if it does not already exist. Supply reviewed settings, trusted loopback TLS certificate/key, and supervisor member IDs 159, 186, 188. Run `scripts/initialize_private_pilot.py` in `--check-only` mode before any initialization. Do not invent or import historical availability consent.
4. If check-only proves the inputs safe, initialize the private root with hidden temporary-password entry, then run `scripts/start_private_pilot.py ... --check-only` before starting the pilot. Do not bypass incomplete/missing/corrupt-state guards.
5. Perform the accepted starter-roster private demonstration and record real evidence: named login, required password change, fresh availability save, restart persistence, legal resolver output, supervisor review, and matching private views. Keep production publication/calendar authority unchanged.
6. Separately coordinate the bridge-credential incident disposition. Inventory actual consumers/maintenance authority without printing credential values, replace/rotate only through an authorized provider path, and prove the superseded credential is rejected. Never paste credentials into GitHub.
7. Update this file with the exact result, blocker, and next action before ending. Create a new unique `Codex_Reply_ShiftCommander...R<n>.md` only for genuinely new work; do not recreate R81.

## Owner/account gates

Keep unresolved human gates visible here until positively verified cleared. An owner gate is not acceptable unless it states the exact physical action Brian must take.

**Current gate status:** No newly verified need for Brian to manipulate GitHub/Cloudflare/Render/Windows settings merely to resume code work. The worker should first execute the reversible private-installation preparation above. If the private installation reaches an interactive hidden-password step, Brian (or the authorized intended Windows user) must enter temporary passwords locally; passwords must not be sent through GitHub/chat or stored in arguments/environment variables. If bridge-token rotation cannot be completed using already-authorized provider access, the worker must name the exact provider/account page and exact credential/permission action Brian must perform. Until that exact provider-side blocker is reproduced, do not ask Brian to guess, retrieve, or paste a key.

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

### 2026-10-14 14:34 UTC - Owner-gate continuation
- Starting blocker: approved private settings/trusted-loopback TLS inputs remain gated by the latest owner acknowledgment; no evidence of approved input change.
- Evidence inspected: issue #214 body/current owner instructions, full dispatch artifact, durable checkpoint and previous receipt; both repository AGENTS.md; handoff/proof protocols; current draft #19/#372 metadata and backend queue/PRs.
- Action attempted: read-only dependency/eligibility assessment; actual execution acknowledged before changes. No setup/auth/preflight/launcher retry or secret access.
- Result: BLOCKED. Target draft #19 remains b9cc8cfeb3412569fc02ebed878e3124a5d19dee; courier #372 remains draft/open and untouched. No independently verified Astra runtime.
- New/unchanged root cause: approved private input gate unchanged; credential-incident disposition and real operational proof remain outstanding.
- Tests/checks run: documentation scope/whitespace checks; no source changes, tests, build or generator. Backend #389/#388/#381 already have partial repair PRs; #373 depends on Studio foundation; #392 requires coordinated deep work. No safe unassigned narrow repair established.
- Commit/PR/branch: codex/issue-214-gate-20261014T143431Z; existing ShiftCommander PR #19 reused as target, no new application PR.
- Owner/account gate: privately reviewed settings/TLS paths must change through approved local channel; intended user supplies passwords only through later hidden local prompts. No duplicate owner alert.
- Next exact action: suppress unchanged retries; after approved inputs change resume reviewed check-only IDs 159/186/188, then controlled workflow/restart/recovery/observer proof. Preserve all assignments and held #372. Evidence remains BUILT/prior synthetic only.

### 2026-10-14 15:54 UTC - Bounded dispatch owner-gate review
- Starting blocker: approved private-settings/trusted-loopback TLS gate unchanged in latest owner acknowledgement.
- Evidence inspected: originating issue, dispatch/checkpoint, repository instructions/protocols, current #19/#372 metadata, open backend issue/PR queue.
- Action attempted: execution acknowledged, read-only gate/dependency eligibility review; no setup/auth/preflight/launcher retry.
- Result: BLOCKED; #19 unchanged at b9cc8cfeb3412569fc02ebed878e3124a5d19dee; held #372 untouched. No fresh Astra claim.
- Tests/checks run: documentation scope/whitespace checks; no source/build/test changes. Existing #389/#388/#381 assignments and #373/#392 dependencies retained; no safe independent narrow backend repair established.
- Commit/PR/branch: codex/issue-214-gate-20261014-dispatch-receipt; unique receipt Codex_Reply_Issue214_OwnerGate_20261014T155452Z.md.
- Owner/account gate: approved private input change required; no duplicate alert, secret access or competing launch.
- Next exact action: after private inputs change, reviewed check-only IDs 159/186/188 and controlled workflow/restart/recovery/observer proof. BUILT/prior synthetic evidence only; no merge/deploy.

### 2026-10-14 16:34 UTC - Dispatch gate and backend eligibility review
- Starting blocker: owner acknowledgement at 16:00 UTC requires no retry or redispatch until approved private settings/trusted loopback TLS inputs materially change.
- Evidence inspected: issue #214 body/comment history, linked dispatch, canonical checkpoint, repository AGENTS.md and handoff/proof standards; current target #19 and held courier #372; open backend issues and PRs.
- Action attempted: acknowledged actual execution on #214; read-only dependency review. No setup/auth/preflight/launcher retry or private credential access.
- Result: BLOCKED. Target draft #19 remains b9cc8cfeb3412569fc02ebed878e3124a5d19dee; #372 remains open/draft at 34bb5282cb17258c5680c263942fa11164f597f1. No approved input change evidenced.
- Tests/checks run: documentation whitespace and explicit staging checks. No application code, generators or operational tests run.
- Backend eligibility: existing #389/#388/#381/#393 repair streams preserved; #373 explicitly follows Studio foundation and must not interrupt #371/#372; #392 requires coordinated deep archive work with #141/#327/#297/#209/#150. No safe independent narrow repair established by this bounded review.
- Commit/PR/branch: codex/issue-214-gate-20261014-dispatch-final; existing application PR #19 retained. Unique receipt follows this checkpoint commit.
- Owner/account gate: reviewed settings and trusted TLS pair must arrive through approved private local path; no duplicate owner alert or request to paste secrets.
- Next exact action: suppress unchanged retries. After approved input change, resume existing reviewed check-only flow with supervisor IDs 159/186/188, then controlled real workflow, restart, recovery and observer proof. Credential incident disposition remains a separate release gate.
- Evidence: BUILT with prior synthetic proof only; no fresh Astra runtime, real end-to-end proof or observer health established. No merge or deployment.
