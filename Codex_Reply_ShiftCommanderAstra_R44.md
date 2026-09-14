# ShiftCommander Astra R44 — remaining release prerequisites

- Assignment: [Brian910cpr/910cpr-class-landers#214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214).
- Dispatch: `SHIFTCOMMANDER_ASTRA_20260913_R1`, continuing R43.
- Timestamp: `2026-09-14T03:27:47-04:00` (America/New_York).
- Work-item state: **BLOCKED** for release. Assessment and required courier delivery completed; #214 remains open.
- Evidence state: **BUILT**, with retained synthetic local tests and partial live connectivity. No complete operational PROVEN, MONITORED or HEALTHY claim.
- Courier branch: `codex/issue-214-shiftcommander-receipt-r44`.
- Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r44`.
- Courier base commit: `387be9c0c16a6d6b8184fed30b59a17a5eec5bbf`. This communication-only commit has no self-referential SHA; its pushed tip is returned on #214 and in the Codex response.
- Target application commit: `ba0365a250d18297a262b96ab7f15cf3fe6f1780`, [OPEN draft PR #10](https://github.com/Brian910cpr/shiftcommander_v2/pull/10), branch `codex/issue-214-private-boundary-r8`.
- Read-only target assessment: `E:\GitHub\shiftcommander_v2_codex_issue214_r9`, `codex/issue-214-release-gate-verification-r9` at `16d0ace259b485a7585decbef24c74e94bd69f5c`.
- Latest provider evidence: target branch `codex/issue-214-provider-metadata-r43`, commit `0420626ad718898061332e4ff1e7f073f92dd37e`.

## Findings and work performed

Read the complete issue body and all 91 pre-pickup comments, pinned original dispatch, original/fetched courier AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_PROOF_AND_HEALTH_STANDARD.md, #116, target AGENTS.md/project boundaries/confirmed scheduling rules/RULES/DATA_CONTRACT, consolidation migration/overlay documents and R8/R9/R43 release evidence. The historical migration documents are not current deployment proof. Pickup is [issue comment 5660504478](https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-5660504478).

**The blanket Cloudflare metadata-access blocker is retired for the connected API route.** R44 independently verified the complete committed bytes and GitHub blobs of all three R43 evidence files, and validated their JSON relationships locally. It did not repeat provider calls, operational reads or failed credential requests. These are R43 observations from approximately 06:54–06:59 UTC, not fresh R44 service-health measurements:

| Evidence at target commit `0420626ad718898061332e4ff1e7f073f92dd37e` | Exact relevant facts |
|---|---|
| [docs/RELEASE_METADATA_ISSUE214_R43.md](https://github.com/Brian910cpr/shiftcommander_v2/blob/0420626ad718898061332e4ff1e7f073f92dd37e/docs/RELEASE_METADATA_ISSUE214_R43.md) | Full serving-lane report; blob `1c451b449d07cae4e63f76d4bac57479771d9f9d`. |
| [docs/PROVIDER_METADATA_ISSUE214_R43.json](https://github.com/Brian910cpr/shiftcommander_v2/blob/0420626ad718898061332e4ff1e7f073f92dd37e/docs/PROVIDER_METADATA_ISSUE214_R43.json) | `observations` contains 13 successful HTTP 200 metadata records. `worker_settings` and `worker_version` DB bindings equal `d1_database.data.uuid`, resolving to `adr_fr_scheduler`. `sc_api_tunnel.data.status=down`, `connection_count=0`. Blob `2a46ba64eaf91bad353f6189b32ef3bb9f4074ab`. |
| [docs/PUBLIC_SERVING_ISSUE214_R43.json](https://github.com/Brian910cpr/shiftcommander_v2/blob/0420626ad718898061332e4ff1e7f073f92dd37e/docs/PUBLIC_SERVING_ISSUE214_R43.json) | Nine anonymous HTTP records: eight 200, one 530. Pages JS `api_hosts` points to Render. Render health has `quick_test_mode=true`, `demo_supervisor_bypass=true`; Worker session has `authenticated=true`, `role=admin`, `local_worker_session=true`. Blob `e9e954bc2d5d36e60fa9a8c5f0c2807208acf632`. |

Pages serves the June 3 consolidation deployment, while the tested authentication candidate is an opt-in Flask branch. The failed `sc-api.adr-fr.org` tunnel is not the Worker's custom domain. Repointing it would neither establish client compatibility nor repair the observed authentication blockers. No routing, authentication, calendar authority or staffing policy was changed.

Fresh GitHub readback confirms PR #10 is OPEN/draft at the same application commit, with the original three changed files and an empty `statusCheckRollup`. Target `origin/main` remains `67a3f88f1b54fa2ffbd285df7df969cea7837616`. R43's remote branch tip matches its evidence commit. No new approval or independently reproduced defect appears in #214 that clears the reviewed implementation/release gate.

## Exact blockers and next action

1. **Persistent real authentication:** no approved persistent filesystem/exact `SC_AUTH_DB_PATH`, schema-v2 readiness, real named member/supervisor provisioning, signing configuration or verified inherited hosting configuration has been supplied. Obtain that private configuration through the existing owner/account channel. Do not publish secret values. The candidate remains opt-in; do not activate against schema v1 or remove its setting as an assumed safe rollback.
2. **Current ADR staffing authority:** current approved roster/certifications, unit-specific `qualOp`, availability consent, demand and calendar provenance remain unestablished. Obtain the approved source references and effective dates, reconcile them read-only, and preserve ADR Google Calendar's published-staffing authority. Old schedule/seed data is not current consent; Blank remains ineligible for automatic assignment.
3. **R37 credential incident:** the previously reported bridge-credential exposure still requires private operator disposition, coordinated rotation/containment where necessary and old-credential rejection evidence. R44 did not retrieve, repeat, use or change that credential.
4. **Coordinated release proof:** after those prerequisites, prepare a reviewed serving/client configuration and prove real scoped authentication, availability save/readback/restart, legal explained resolver output, supervisor review/publication and matching member/mobile/wallboard revisions. Include hosted recovery and observer heartbeat. Keep Windows start/stop usability, partial/overnight/DST cases, locks, ALS/driver shortages, OT, swaps, duplicate/unauthorized writes and phone/SMS/email integrations in the release scope.

**Recommended next ChatGPT action:** review the R43 files linked above with this receipt; retain the successful metadata-access finding; obtain the exact private-auth/current-input approvals and incident disposition on #214, then dispatch coordinated staging against those verified serving paths. Keep PR #10 and the serving draft stack open/unmerged. An unchanged access-restoration request or another speculative application round cannot clear these remaining gates. User/account-level action is required for the configuration/input approvals and incident disposition; no new model or GitHub access action is required.

## Independent backend queue

Swept all open issues and read the bodies/latest relevant updates of every other open `[CODEX]` item. No new unconflicted narrow backend implementation was established, so no secondary assignment or duplicate worker was started:

- #226 explicitly has active `codex/class-record-details-intake` work. Preserve it and its canonical data model.
- #227's latest stabilization review accepts its Sites preview but defers customer feature/SEO expansion pending backend freshness/auth/reconciliation. It is not scheduler/private-data integration proof.
- #215 reports private owner access delivered by merged PR #225. Preserve that delivery; remaining Financial/legacy Hot Sync connections, individual instructor identity, static-data privacy and monitoring are separate work. Do not reintroduce withdrawn public access or the old universal-key assumption.
- #216 still needs current private balances/upcoming bills and full monitor proof. Do not fabricate cash prompts; its older auth wording predates #215's owner-session delivery.
- #219 has delivered owner document controls; individual instructor identity/assignment scope and authenticated click-through remain substantive work overlapping current access/document work.
- #223's 19-class/13-participant reconciliation is already delivered. Its source end-time correction and owner-view proof remain; do not duplicate imports or treat #215 delivery alone as proof of that view.
- #140's latest recurrence still records run `34796567750` failing occupancy reconciliation with HTTP 401 after a successful build. Preserve its fail-closed publication gate; no unchanged-auth retry or repository workaround was attempted. Other paused/blocked work retains its dependencies.

## Validation and evidence limits

Fresh local checks: AST parse and in-memory compilation of `server.py`, `engine/auth_store.py`, `engine/live_state_store.py` passed; PowerShell parser validation of the existing R2 `scripts/Start-AstraReview.ps1` passed. No bytecode was generated. Application diff between R8 and the R9 assessment is empty for `server.py`, `engine/` and `tests/`. R9 and R43 worktrees are clean.

R43 GitHub Contents API bytes match `git show <commit>:<path>` for all three files above. JSON parsing/count/status/binding/tunnel relationships passed. These checks validate the retained artifact, not current remote uptime or operational correctness.

Read the retained `E:\GitHub\shiftcommander_v2_codex_issue214_r9\debug\verification_r9\combined_final.log`:

```text
Ran 160 tests in 189.801s
OK
FINAL: tests=160 failures=0 errors=0 skips=0
```

Those unchanged synthetic behavioral tests were **not rerun** in R44. Exact suites and reproduction command remain in [docs/RELEASE_VERIFICATION_ISSUE214_R9.md](https://github.com/Brian910cpr/shiftcommander_v2/blob/16d0ace259b485a7585decbef24c74e94bd69f5c/docs/RELEASE_VERIFICATION_ISSUE214_R9.md). They cover local auth/audit/restart/credential-only recovery/resolver behavior; they are not browser, CI, hosted recovery or complete publication proof. No generator, frontend rebuild or new behavioral test was warranted for this receipt-only assessment.

Known local assessment correction: reading the consolidation-only migration document from R9 returned file-not-found; it was then read from the original consolidation checkout. New courier sparse initialization had an empty index and showed 55,015 apparent staged deletions. Work stopped; the exact new path, `.git`-only directory and zero index entries were verified before `git read-tree -mu HEAD` initialized that worktree. Afterwards it had 55,015 index entries, 61 root items including `.git`, no staged changes and clean status. No existing work was reset, cleaned or overwritten. Receipt required-field/Markdown/whitespace and explicit staged/base-to-head scope checks are required before push.

## Preservation, model and delivery

Only `Codex_Reply_ShiftCommanderAstra_R44.md` changes in this courier branch. No target code/config/data/test/report files change in R44. Original courier remains on `codex/durable-session-participant-linking`; its Earl HTML, tracked/untracked Python caches, heartbeat and `supabase/.temp/` are unrelated and preserved. Original ShiftCommander remains dirty on `codex/base44-worker-consolidation`, ahead four unpublished commits (`3287eb4`, `9a49b9e`, `69bc1fb`, `55d6a05`); its calendar mirror, availability backup, slot data/generator/tests and all prior worktrees remain preserved. The unfinished R37 receipt is not modified. No cleanup, merge, rebase, force-push or new timer.

Current matching-thread local `turn_context` reports `model=gpt-6-astra` at `2026-09-14T07:23:03.565Z`, CLI `0.153.4`. Only allowlisted fields were emitted; this is local runtime evidence, not provider attestation. Existing project launcher CheckOnly at `2026-09-14T03:25:29.2291843-04:00` reports `can_launch=false`, dispatcher worker lock held/inaccessible. One active worker continued; no duplicate launch or lock/lease/machine-default change. The existing launcher remains at `E:\GitHub\shiftcommander_v2_codex_issue214_r2\scripts\Start-AstraReview.ps1`; it is a Codex review launcher, not an operational application launcher. No normal localhost application URL was started or verified.

Processing and syntax/artifact validation were local; GitHub reads, the pickup comment and receipt push are remote. **Persisted locally and pushed for review; not merged, activated or deployed.** No privileged operational reads/writes, database upgrades, account provisioning, routing changes, calendar cutover or member communications occurred. Root Reply/Read R44 collisions were checked across fetched history and the new path before creation. Only Codex writes this new Reply; no Read marker or retired mutable mailbox is used.

## Persistent-system proof contract

Expected outcome: one real authenticated availability save survives restart and feeds legal explained publication with the same revision in every rendered view. Last complete real-world success timestamp: **unestablished**. Cadence includes the confirmed Wednesday 23:59 publication boundary and the approved source-freshness window, which still needs operational proof. Failure means lost saves, unreadable storage, stale sources, unauthorized/illegal assignments, divergent views or missed publication. Whole-workflow observer, its own heartbeat and recovery/escalation delivery remain unproven; local tests are not that observer and Brian must not become its routine detector.

The candidate, retained tests and reports remain usable. Recovery guidance is [docs/RELEASE_CHECKLIST_ISSUE214_R6.md](https://github.com/Brian910cpr/shiftcommander_v2/blob/5e81303e8f2cc306251ae61bd8566c3763548b83/docs/RELEASE_CHECKLIST_ISSUE214_R6.md): preserve failed evidence, distinguish current-state schema upgrade from stale-backup recovery, restore approved credentials without resurrecting revoked sessions, reconcile staffing/audit history, then prove staged behavior before cutover. Account/authority decisions require the owner/operator; safely reproducible backend defects remain eligible for local repair.
