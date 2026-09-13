# ShiftCommander Astra R28: release dependency assessment

- Assignment: `Brian910cpr/910cpr-class-landers#214`, dispatch `SHIFTCOMMANDER_ASTRA_20260913_R1`, continuing after R27.
- Timestamp: 2026-09-13T19:42:24-04:00 (America/New_York).
- Work-item state: **BLOCKED** for release. Existing application is **PR_OPEN**, draft/unmerged. This round completed dependency assessment; no application change was justified.
- Persistent-system evidence: **BUILT**, with retained local synthetic validation. Complete operational PROVEN, MONITORED and HEALTHY states remain unestablished.
- Courier branch: `codex/issue-214-shiftcommander-receipt-r28`; worktree `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r28`; base commit `612030fbdc3b8654bf509bd4ec73a5f7af3308b1`.
- Target assessment: `E:\GitHub\shiftcommander_v2_codex_issue214_r9`, reused read-only; branch `codex/issue-214-release-gate-verification-r9`, commit `16d0ace259b485a7585decbef24c74e94bd69f5c`.
- Application commit: `ba0365a250d18297a262b96ab7f15cf3fe6f1780`, branch `codex/issue-214-private-boundary-r8`, [ShiftCommander draft PR #10](https://github.com/Brian910cpr/shiftcommander_v2/pull/10).
- Exact file changed: `Codex_Reply_ShiftCommanderAstra_R28.md` only. Its communication-only commit SHA and verified remote readback are returned on #214 and in the final response after push; no self-referential SHA is invented.
- [Pickup acknowledgement](https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-5657107777).

## Findings and work performed

Read the full issue body and all 60 pre-pickup comments, pinned `ccc2a6c8ca626e6e650836a3014ac26cdac82496:Codex_Mailbox/SHIFTCOMMANDER_ASTRA_20260913_R1.md`, original/current courier AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_PROOF_AND_HEALTH_STANDARD.md, docs/CODEX_INSTRUCTIONS.md and #116. The original courier branch lacks CODEX_HANDOFF_PROTOCOL.md; the current GitHub default-branch version was read before changes. Read target AGENTS.md, docs/PROJECT_BOUNDARIES.md, docs/CONFIRMED_SCHEDULING_RULES.md, RULES.md, DATA_CONTRACT.md, migration/overlay records and R8/R9 release evidence. Historical migration assertions are not current deployment proof.

Fetched both repositories. Target main remains `67a3f88f1b54fa2ffbd285df7df969cea7837616`. GitHub confirms PR #10 OPEN/draft, `statusCheckRollup=[]`, and exactly `server.py`, `tests/smoke/test_private_serving_boundary.py`, `docs/RELEASE_CHECKLIST_ISSUE214_R8.md`. PRs #5-#10 remain open/draft; #3/#4 remain open. R9 differs from R8 only by its 119-line verification report; the application/data tree is unchanged. Read the newly fetched R25 acknowledgement at `ed523bf22829dc0eb159ae2089bae0d69eec5f07`; it retains the same gates and authorizes no speculative repair, merge or deployment.

No changed account access, approved private authentication configuration, current ADR source approval or new reproducible independent defect appeared. Execution stops before coordinated staging activation. The reviewed no-speculative-implementation/no-merge/no-deploy instruction remains in force. No unchanged failing provider-auth request was repeated. Repository refs do not prove current hosting health.

## Exact blockers and required next action

| Gate | Evidence and concrete action |
|---|---|
| Cloudflare serving metadata | R2's authenticated Pages metadata request returned HTTP 401. Restore minimum Pages project/deployment, Worker routing and D1-binding metadata reads, or supply an approved sanitized export. Verify actual serving paths/bindings before cutover. No new access evidence clears this gate. |
| Persistent real authentication | Approved persistent filesystem and exact `SC_AUTH_DB_PATH`, schema v2 readiness, real private member/named supervisor accounts, signing material and deployed/inherited configuration remain unverified. Establish the approved private configuration for the verified serving lane. No accounts, credentials, database or paid service were invented/provisioned. |
| Current ADR staffing inputs | Approved current roster/certifications, unit-specific `qualOp`, explicit availability consent, demand and calendar provenance/effective period remain unreconciled. R2's 170 shifts ending August 10, 2026 are historical. Identify/approve current sources while preserving ADR Google Calendar published-staffing authority, Blank exclusion, locks/protected assignments and visibly OPEN unmet seats. |
| Complete release proof | After those prerequisites, coordinate scoped Pages/Worker/React/Flask clients; prove availability -> legal resolver -> supervisor review -> publication and member/supervisor/mobile/wallboard agreement. Include partial/overnight/DST, ALS/driver shortages, locks, OT, swaps, duplicate submissions, hosted recovery and observer heartbeat. Secure Windows usability and phone/SMS/email intake remain in scope. |

**Account/operator action is required** for provider access and approved persistent authentication; owner/source authority is required for current ADR inputs. Next ChatGPT action: read this receipt with R9, keep #214 and the draft stack open, and return those three prerequisites through #214. Resume coordinated staging after they clear, or a safe independent backend repair when a reproducible eligible defect exists. Unchanged redispatches cannot resolve these external gates; this mandatory receipt does not request another speculative implementation loop.

Existing usable work and exact review references:

- [docs/RELEASE_VERIFICATION_ISSUE214_R9.md](https://github.com/Brian910cpr/shiftcommander_v2/blob/16d0ace259b485a7585decbef24c74e94bd69f5c/docs/RELEASE_VERIFICATION_ISSUE214_R9.md): eight-suite reproducer, retained tests and restart/recovery limits.
- [docs/RELEASE_CHECKLIST_ISSUE214_R8.md](https://github.com/Brian910cpr/shiftcommander_v2/blob/ba0365a250d18297a262b96ab7f15cf3fe6f1780/docs/RELEASE_CHECKLIST_ISSUE214_R8.md): candidate boundary, full checklist and client compatibility gaps.
- `286876e7d506bd127e14c2852f65c827815a8fa7:docs/RELEASE_EVIDENCE_ISSUE214_R2.json`, `read_only_checks`: historical provider/auth/schedule observations, not fresh R28 production verification.
- `5e81303e8f2cc306251ae61bd8566c3763548b83:docs/RELEASE_CHECKLIST_ISSUE214_R6.md`: current-state schema v2 copy-upgrade versus credential-only recovery. Preserve failed storage; do not restore revoked sessions from a stale backup, activate against v1, or assume removing SC_AUTH_DB_PATH is a safe rollback.

## Validation, runtime and limitations

Fresh AST parse/in-memory compile passed for `server.py`, `engine/auth_store.py`, `engine/live_state_store.py`; no bytecode written. PowerShell parser validation passed for the existing R2 `scripts/Start-AstraReview.ps1`. Candidate/PR/ref scope checks passed. No unfinished merge/cherry-pick/revert/rebase/sequencer operation was found in either original checkout or R9.

```text
SYNTAX: 3 Python source files passed; no bytecode written
SYNTAX: existing Astra launcher passed
RETAINED R9: Ran 160 tests in 189.801s
RETAINED R9: OK
RETAINED R9: FINAL: tests=160 failures=0 errors=0 skips=0
```

The test lines were read from `E:\GitHub\shiftcommander_v2_codex_issue214_r9\debug\verification_r9\combined_final.log`; the suite was **not rerun in R28**. Unchanged code and no new failure did not justify repeated testing. This is retained synthetic local evidence, not CI/browser/staging/production proof. Receipt required fields, Markdown fences/whitespace and explicit one-file staged/base-to-head scope are checked before push; remote tip/content/blob verification follows push and is returned on #214.

Actual active-thread local `turn_context` reports `model=gpt-6-astra` at `2026-09-13T23:37:52.232Z`; `codex-cli 0.153.4`. Only these sanitized fields were extracted. This is local runtime evidence, not provider-side attestation or a configuration-only claim. Official [model selection](https://learn.chatgpt.com/docs/models) and [Astra model documentation](https://developers.openai.com/api/docs/models/gpt-6-astra) were fetched; documentation is not runtime proof.

Existing `E:\GitHub\shiftcommander_v2_codex_issue214_r2\scripts\Start-AstraReview.ps1 -RepoPath E:\GitHub\shiftcommander_v2_codex_issue214_r9 -CheckOnly` returned `can_launch=false` at `2026-09-13T19:40:08.2322556-04:00`, dispatcher lock held/inaccessible. The current worker continued; no duplicate worker or lock/lease/default/timer change occurred. After the legitimate lease releases, this existing launcher selects Astra for development review. It is not an application launcher; no secure normal operational URL/start-stop workflow is newly verified.

No new application test failure was established. Large read outputs were reread in bounded portions. The first pickup command produced no captured completion and no matching GitHub comment/process; readback preceded one successful retry. No credentials or account-auth path were retried.

## Persistence, deployment and proof contract

**Persisted locally / changed in repo:** this receipt only, in a clean isolated root-only sparse courier worktree (55,002 index entries). Local work: repository assessment and syntax checks. Remote work: GitHub reads, issue comments, receipt push/readback and official documentation retrieval. **Deployment:** no application merge/deploy/activation, real database change, calendar cutover, production write or member communication. No generator ran and no application PR was created.

Expected success is real authenticated availability saved durably across restart and producing legal reviewed publication at the same revision across all rendered views. No complete operational cycle or last-success timestamp is established. Wednesday 23:59 publication and source freshness need approved-input proof. Missing/schema-invalid credentials, stale sources, lost availability, illegal/unauthorized changes and inconsistent publication are failure conditions. Component storage checks exist; complete observer health, heartbeat and escalation delivery remain unproven. Brian must not be the routine detector. Follow the existing R6/R9 recovery instructions and preserve failed evidence before changing approved configuration.

Original dirty work remains preserved: courier `codex/durable-session-participant-linking` has Earl HTML, bytecode, heartbeat and Supabase temporary work; target `codex/base44-worker-consolidation` has its calendar mirror, availability backup, slot generator/data/tests and four unpublished commits `3287eb4`, `9a49b9e`, `69bc1fb`, `55d6a05`. No cleanup/reset/rebase/merge occurred. All prior worktrees and Reply/Read history remain intact. Existing ignored R9 logs stay local; comment-body scratch files are in the new worktree's Git metadata. No new working-tree artifact is intentionally left untracked. The retired mutable mailbox was not used.

## Independent backend eligibility

Swept all open issues and read every other open CODEX dispatch body/latest comments plus #140. No clearing update since R27:

| Issue | Latest update (UTC), remaining work and eligibility |
|---|---|
| #215 | 2026-09-13T19:54:57Z. Shared helper/migration is published. Accepted-key owner proof and Cloudflare/GitHub/Finance Worker credential parity remain unresolved. Generic login failure does not prove a wrong submitted key. No duplicate migration or repeated failed login. |
| #216 | 2026-09-13T17:02:55Z. Monitor is published; accepted owner access and private current balances/complete bills remain required. No invented finance values. |
| #219 | 2026-09-13T18:05:27Z. Owner View/Remove controls are deployed; individual instructor identity/assignment authorization and authenticated click-through remain. This requires substantive auth integration, not an independent narrow repair; never share the owner key with instructors. |
| #223 | 2026-09-13T20:38:54Z. Existing 19-class/13-participant reconciliation and roster evidence must not be duplicated. Class 51431 has source end before start; provisional 19:30 awaits authoritative correction. Owner UI proof remains auth-blocked. |

#140's latest 2026-09-13T17:25:22Z post-owner-update evidence still reports both publishers failing HTTP 401 and prohibits repository-only workarounds. No newly eligible independent narrow backend implementation was established. Completed work was not duplicated, and no secondary issue implementation or mutation occurred. Continue those items when account/source evidence or an independently reproducible defect makes work actionable, with separate receipts for work advanced.
