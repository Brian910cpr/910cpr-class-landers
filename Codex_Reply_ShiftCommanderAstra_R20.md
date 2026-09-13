# ShiftCommander Astra R20: release dependency assessment

- Assignment: `Brian910cpr/910cpr-class-landers#214`; dispatch `SHIFTCOMMANDER_ASTRA_20260913_R1`, continuing after R19.
- Timestamp: 2026-09-13T16:42:00-04:00 (America/New_York).
- Work-item state: **BLOCKED** for release; this dependency assessment is complete.
- Persistent-system evidence: **BUILT**, with retained local synthetic verification. Complete operational PROVEN, MONITORED and HEALTHY states remain unestablished.
- Courier branch: `codex/issue-214-shiftcommander-receipt-r20`.
- Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r20`.
- Courier base commit: `612030fbdc3b8654bf509bd4ec73a5f7af3308b1`.
- Target assessment: `E:\GitHub\shiftcommander_v2_codex_issue214_r9`, branch `codex/issue-214-release-gate-verification-r9`, commit `16d0ace259b485a7585decbef24c74e94bd69f5c`, reused read-only.
- Application commit: `ba0365a250d18297a262b96ab7f15cf3fe6f1780`; [OPEN draft ShiftCommander PR #10](https://github.com/Brian910cpr/shiftcommander_v2/pull/10).
- Exact file changed: `Codex_Reply_ShiftCommanderAstra_R20.md` only. The communication-only commit SHA is discoverable at the pushed branch tip and will be returned on #214 after remote verification; it cannot be embedded in its own commit.

## Findings and work performed

Read the full #214 issue and all 44 pre-pickup comments, pinned dispatch, original/current courier AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_PROOF_AND_HEALTH_STANDARD.md, docs/CODEX_INSTRUCTIONS.md, #116, and target AGENTS/project boundaries/confirmed scheduling rules/RULES/DATA_CONTRACT. The protocol is absent on the original dirty courier branch; fetched origin/main supplied it before edits. Reviewed the existing migration/overlay documents and R8/R9 evidence, distinguishing historical migration claims from current serving proof.

Fresh target fetch and GitHub readback confirm main `67a3f88f1b54fa2ffbd285df7df969cea7837616`. PR #10 remains OPEN/draft with `statusCheckRollup=[]` and exactly three original files: `server.py`, `tests/smoke/test_private_serving_boundary.py`, `docs/RELEASE_CHECKLIST_ISSUE214_R8.md`. Serving PRs #5-#10 remain draft/open; migration PRs #3/#4 remain open. R9 differs from R8 only by its 119-line verification report; no application/data differences exist. These are repository observations, not fresh hosting-health evidence.

No new provider permission evidence, approved private configuration, approved current staffing snapshot or reproducible independent defect clears the reviewed R8/R9 gate. Execution stops before coordinated staging activation. Candidate code, draft PRs, prior local tests and release reports remain usable. No speculative patch or unchanged application-suite rerun was warranted.

## Exact blockers and next actions

| Gate | Evidence and required action |
|---|---|
| Cloudflare serving metadata | R2 recorded authenticated Pages metadata HTTP 401 at 2026-09-13T12:19:20.656580+00:00. Minimum Pages project/deployment, Worker routing and D1-binding metadata remain unverified. Restore those account reads or provide an approved sanitized export, then verify actual serving paths. No unchanged failing account-auth request was retried. |
| Persistent real authentication | Approved persistent filesystem and exact `SC_AUTH_DB_PATH`, schema v2 readiness, real member/named supervisor accounts, signing configuration and deployed/inherited settings remain unverified. Owner/operator must establish approved private configuration for the verified serving lane. No credentials, account values, database or paid storage were invented or provisioned. |
| Current ADR staffing truth | Current roster/certifications, unit-specific qualOp, explicit availability consent, demand and calendar provenance/effective period require approval and reconciliation. R2's last successful schedule observation had 170 shifts ending August 10, 2026; this is historical evidence. Preserve ADR Google Calendar published-staffing authority, Blank = no automatic assignment, hard constraints and visibly OPEN required seats. |
| Coordinated release proof | After those prerequisites, prove scoped Flask/Pages/Worker/React auth, availability -> legal resolver -> supervisor review -> publication, agreement across member/supervisor/mobile/wallboard, hosted recovery and observer health. Secure Windows startup and phone/SMS/email intake remain in scope. |

Exact evidence: `286876e7d506bd127e14c2852f65c827815a8fa7:docs/RELEASE_EVIDENCE_ISSUE214_R2.json` (`read_only_checks`, `pages_error_status`, schedule dates); `5e81303e8f2cc306251ae61bd8566c3763548b83:docs/RELEASE_CHECKLIST_ISSUE214_R6.md` (schema/recovery); [R8 checklist](https://github.com/Brian910cpr/shiftcommander_v2/blob/ba0365a250d18297a262b96ab7f15cf3fe6f1780/docs/RELEASE_CHECKLIST_ISSUE214_R8.md); [R9 report and reproduction command](https://github.com/Brian910cpr/shiftcommander_v2/blob/16d0ace259b485a7585decbef24c74e94bd69f5c/docs/RELEASE_VERIFICATION_ISSUE214_R9.md).

Recovery boundary: do not activate schema v2 code against v1 storage, restore revoked sessions from a stale backup, or assume removing SC_AUTH_DB_PATH is a safe rollback. Preserve failed evidence; recover approved credentials into a distinct store without old sessions, reconcile credential/audit history, and prove staging behavior before switching configuration.

## Runtime and proportionate validation

This active thread's local `turn_context.model` is `gpt-6-astra` at `2026-09-13T20:37:17.92Z`; the session metadata matches the current thread and CLI `0.153.4`. Fresh `codex --version` returns `codex-cli 0.153.4`. These are sanitized local runtime fields, not provider-side attestation. Raw session contents remain private. [Official CLI documentation](https://learn.chatgpt.com/docs/developer-commands?surface=cli) was fetched for the requested model-control check; documentation/configuration alone is not runtime proof.

Existing project entry point: `& E:\GitHub\shiftcommander_v2_codex_issue214_r2\scripts\Start-AstraReview.ps1 -RepoPath E:\GitHub\shiftcommander_v2_codex_issue214_r9 -CheckOnly`. At `2026-09-13T16:41:03.1953386-04:00`, it reported dispatcher lock held/inaccessible, `can_launch=false`, `runtime_model_verified=false`. This current worker continued; no duplicate launch, lock/lease, timer or machine-default change occurred. This is a development-worker launcher, not an operational application launcher.

Fresh local output:

```text
SYNTAX: 3 Python files passed; no bytecode written
SYNTAX: Astra launcher passed
```

Python AST/in-memory compile checked `server.py`, `engine/auth_store.py`, `engine/live_state_store.py`; the PowerShell parser checked the existing launcher. R9 worktree is clean. Retained `E:\GitHub\shiftcommander_v2_codex_issue214_r9\debug\verification_r9\combined_final.log` readback:

```text
Ran 160 tests in 189.801s
OK
FINAL: tests=160 failures=0 errors=0 skips=0
```

Those tests were **not rerun in R20**. They cover synthetic auth, Windows process restart, credential-only recovery and resolver checks, not CI/browser/staging/production proof. No new application-test failure occurred. Initial missing-path reads were resolved using the current GitHub protocol and receipt API; they required no source fix. Receipt checks cover unused Reply/Read identifiers, required fields, Markdown fences, whitespace and explicit one-file staged/base-to-head scope. Push and full remote content/blob readback follow before exit.

## Preservation and independent backend eligibility

Original courier remains dirty on `codex/durable-session-participant-linking`: Earl HTML, tracked/untracked bytecode, existing heartbeat and Supabase temporary files are preserved. Original ShiftCommander remains dirty on `codex/base44-worker-consolidation`: calendar mirror, availability backup, slot generator/data/tests are preserved. Its four unpublished commits remain ahead 4/behind 0; all earlier worktrees and PRs remain intact. No unfinished Git operation was found in either original checkout or R9. The new root-only sparse courier was clean before this receipt. No cleanup, reset, rebase, merge or generator ran. No retired mailbox or ChatGPT acknowledgement marker was written.

Swept all open issues and assessed the current CODEX backend queue:

- **#223 changed since R19:** the reconciliation author returned authenticated evidence at 2026-09-13T20:38:54Z. Read the full new `Codex_Reply_Issue223.md` on `codex/issue223-enrollware-roster-reconciliation`, remote blob `abb6b5d08cd7e0bb774140e5db495b30c3ceb21d`. It reports 19 live admin roster reads, 19 unique canonical classes, 13 real registration IDs and repeat-import no-change proof. R19's separate read-only verification is already pushed at `7653a4971a236f2e848cc4d08769c80790330325`. Do not duplicate the import or verification. The source end for class 51431 remains invalid (18:00 before 18:30 start; 19:30 canonical end explicitly provisional), and authenticated LanderWare owner/API/UI proof remains blocked. Correction requires authoritative scheduling evidence and accepted owner access, not another inferred database write. This is a review of returned evidence, not a fresh database verification by R20.
- **#215:** shared admin-auth migration is published. Latest failed Class History sign-in does not prove the submitted key was wrong; accepted-key navigation and Cloudflare/GitHub/Finance secret parity remain unproven. #140 still explicitly blocks repository-only auth workarounds after both publishers returned HTTP 401 with the updated Actions key. Preserve fail-closed gates; no unchanged auth retry.
- **#216:** dashboard is published; accepted-key end-to-end proof and private current balances/complete upcoming bills remain missing. Do not invent financial inputs or duplicate the dashboard.
- **#219:** owner document controls are published; individual instructor identity/assignment authorization and authenticated click-through remain outstanding. This is a substantive integration requirement, not an independent narrow backend fix. Do not give instructors the owner key.

No independent narrow backend implementation was established outside those account/private-input/integration gates. No secondary issue was modified or implementation duplicated; no additional secondary-work receipt is claimed.

## Proof contract and return action

Expected outcome: authenticated current availability survives restart and produces explainable legal publication consistently across every view. Success evidence must join save/readback, resolver explanations, supervisor publication and rendered views to one revision. Last successful complete real-world cycle: **unknown**. Expected cadence includes Wednesday 23:59 publication. Failure conditions include lost saves, invalid auth storage, stale staffing, unauthorized changes, illegal assignments, inconsistent views and missed publication. Whole-system observer, its heartbeat and escalation delivery remain unproven; Brian must not be the routine detector.

Deployment status: assessed and syntax-validated locally; GitHub reads/comments and this receipt push are remote. No application merge, deployment, activation, real database upgrade, staffing-authority cutover or member communication occurred. No verified operational Windows URL is claimed. #214 and the draft stack remain open.

Exact next action for ChatGPT: review this receipt with R9; resolve minimum provider metadata reads, approved private persistent-auth configuration and current ADR source/provenance through #214, then dispatch coordinated staging. **Account-level access and owner/operator configuration/input approval are required.** This mandatory blocked receipt does not request another speculative implementation loop; unchanged redispatches cannot clear these external gates.
