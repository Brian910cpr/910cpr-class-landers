# ShiftCommander issue #214 — R45 prerequisite assessment

- Assignment: [Brian910cpr/910cpr-class-landers#214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214), dispatch `SHIFTCOMMANDER_ASTRA_20260913_R1`, continuing reviewed R44.
- Timestamp: 2026-09-14T03:52:00-04:00, America/New_York.
- Work-item state: **BLOCKED** for release. This dispatch completed a read-only prerequisite assessment and the required courier receipt; no application implementation round.
- Persistent-system evidence: **BUILT**, with retained synthetic validation and partial live connectivity. Full operational PROVEN, MONITORED and HEALTHY remain unestablished.
- Courier branch: `codex/issue-214-shiftcommander-receipt-r45`.
- Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r45`.
- Courier base commit: `387be9c0c16a6d6b8184fed30b59a17a5eec5bbf`. This communication-only commit contains the single new root receipt; its commit SHA is discoverable from the pushed branch and returned on #214.
- Target assessment worktree/branch: `E:\GitHub\shiftcommander_v2_codex_issue214_r9`, `codex/issue-214-release-gate-verification-r9` at `16d0ace259b485a7585decbef24c74e94bd69f5c`, used read-only.
- Application commit: `ba0365a250d18297a262b96ab7f15cf3fe6f1780`, [ShiftCommander draft PR #10](https://github.com/Brian910cpr/shiftcommander_v2/pull/10), branch `codex/issue-214-private-boundary-r8`. Fresh GitHub readback: OPEN/draft; unchanged three files; `statusCheckRollup=[]`. Serving-stack PRs #5–#10 remain open/draft; migration PRs #3/#4 remain open. Nothing merged.
- Target remote main: `67a3f88f1b54fa2ffbd285df7df969cea7837616`. A Git ref is not evidence of hosting health.

## Authority and findings

Read the full issue body and all 94 pre-pickup comments, pinned `ccc2a6c8ca626e6e650836a3014ac26cdac82496:Codex_Mailbox/SHIFTCOMMANDER_ASTRA_20260913_R1.md`, original/current courier AGENTS.md, CODEX_HANDOFF_PROTOCOL.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md, #116, target AGENTS.md, docs/PROJECT_BOUNDARIES.md, docs/CONFIRMED_SCHEDULING_RULES.md, RULES.md, DATA_CONTRACT.md, migration/overlay records, and R8/R9/R43 release evidence. The protocol is absent on the original dirty courier branch; its fetched origin/main version governs this receipt. Historical migration status and RULES.md audit findings are not current release proof.

The [supervisor review at 07:35:59Z](https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-5660603019) explicitly retires the blanket Cloudflare metadata-access blocker and prohibits release or a duplicate implementation/routing/auth-cutover round. It still requires private auth configuration, current ADR inputs and credential-incident disposition. No subsequent clearing evidence appeared before this receipt. [R45 pickup](https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-5660741248) was recorded at 07:49:45Z.

R43's connected-provider evidence is usable and must not be replaced with the older blanket access blocker. Independently checked all three full committed blobs against GitHub at target commit `0420626ad718898061332e4ff1e7f073f92dd37e`, branch `codex/issue-214-provider-metadata-r43`:

| Exact target path | Verified Git blob | Bytes |
|---|---|---:|
| [docs/RELEASE_METADATA_ISSUE214_R43.md](https://github.com/Brian910cpr/shiftcommander_v2/blob/0420626ad718898061332e4ff1e7f073f92dd37e/docs/RELEASE_METADATA_ISSUE214_R43.md) | `1c451b449d07cae4e63f76d4bac57479771d9f9d` | 12417 |
| docs/PROVIDER_METADATA_ISSUE214_R43.json | `2a46ba64eaf91bad353f6189b32ef3bb9f4074ab` | 8036 |
| docs/PUBLIC_SERVING_ISSUE214_R43.json | `e9e954bc2d5d36e60fa9a8c5f0c2807208acf632` | 4899 |

These are retained observations from 06:54–06:59 UTC, not new R45 provider probes. Local relationship checks confirm 13 successful metadata records, the Worker's `DB` identity matching the actual `adr_fr_scheduler` D1 UUID, nine public HTTP records (eight 200, one 530), the Pages JS API host pointing to Render, and the failed custom API hostname pointing to the down/zero-connection tunnel. JSON selectors are `observations[key=pages_project].data.canonical_deployment`, `observations[key=worker_settings|worker_version].data.bindings`, `observations[key=d1_database].data`, `observations[key=sc-api.adr-fr.org|sc_api_tunnel].data`; public records are keyed by `url`, with `status`, `fields`, `assets` and `api_hosts`.

R43 records Pages deployment `3e7c40e1-e950-4301-83fa-5c85a98b9db9`, June 3 consolidation commit `9d949049bc7f5bf6acf937ef79ea90ef9987d0b9`. Render reports `quick_test_mode=true`, `demo_supervisor_bypass=true`, `auth_mode=quick_test`; the anonymous Worker session reports `authenticated=true`, `role=admin`, `local_worker_session=true`. Neither is a secure release lane. `sc-api.adr-fr.org` is not a demonstrated repair target for the default Pages-to-Render workflow. No operational rows or credentials were read to make this assessment.

## Exact blockers and next action

1. **Approved persistent real auth is missing.** Owner/operator must approve the persistent filesystem and exact `SC_AUTH_DB_PATH`, schema version 2 readiness, real named member/supervisor accounts, signing material and inherited hosting configuration. Existing draft code does not establish these approvals. Do not activate against schema v1, disable the serving legacy lane blindly, or substitute invented accounts.
2. **Current ADR staffing authority is unapproved/unreconciled.** Supply an approved current roster/certifications, per-unit `qualOp`, explicit availability consent, demand and calendar provenance. The prior 170-shift schedule ending August 10 is historical R2 evidence. Preserve ADR Google Calendar's published-staffing authority and Blank = do not auto-schedule; stale seeds cannot establish consent or current staffing.
3. **R37's reported bridge-credential exposure needs private operator disposition.** Coordinate containment/rotation as applicable and retain sanitized proof that the old credential is rejected. No credential value was retrieved, repeated, used, changed or placed in this receipt. Do not publish credentials or raw account configuration on GitHub.
4. **Coordinated staged release proof follows those prerequisites.** Verify the Pages-to-Render client and scoped bootstrap/session contract; secure or exclude alternate Worker/static paths; prove availability → durable readback/restart → legal resolver → supervisor review/publication with the same revision across member, supervisor, mobile and wallboard. Then prove hosted credential/schedule recovery, freshness detection and observer health. No routing/auth cutover, merge or deployment is authorized by this receipt.

User/account-level action is required for items 1–3. The exact next ChatGPT action is to obtain and record those approvals and sanitized incident disposition on #214, keep #214 and its draft stack open, then dispatch coordinated staging against R43's verified serving paths. Do not request Cloudflare metadata-access restoration again for the working connector route. Resume independent implementation when a reproduced defect or changed prerequisite supplies a safe action; this mandatory receipt does not request another identical blocked implementation round.

The entire release scope remains: legal/explainable shortages and OPEN seats; Blank, partial/overnight/DST, ALS/driver, locks/protected assignments, OT/fairness, swaps, duplicates and unauthorized edits; open-shift/release workflows; secure Windows application startup/shutdown; and phone/SMS/email intake with identity/provenance, deduplication, ambiguity review and retry/failure handling.

## Validation and reusable work

Fresh R45 local checks passed: AST parse plus in-memory compilation of `server.py`, `engine/auth_store.py`, `engine/live_state_store.py`; PowerShell parsing of the existing R2 `scripts/Start-AstraReview.ps1`; complete remote blob/content/hash comparisons above; JSON metadata/routing/binding/HTTP relationships; candidate/ref/PR scope and unfinished-Git-operation readback. No application imports, bytecode, fixtures, generators, operational mirror writes or provider/public HTTP probes ran.

Retained R9 log `E:\GitHub\shiftcommander_v2_codex_issue214_r9\debug\verification_r9\combined_final.log` was read, not rerun:

```text
Ran 160 tests in 189.801s
OK
FINAL: tests=160 failures=0 errors=0 skips=0
```

Those unchanged tests establish local synthetic auth/audit/Windows process restart/credential-only recovery/resolver behavior, not CI, browser, staging or complete production proof. Exact reproducer and eight-suite inventory: [docs/RELEASE_VERIFICATION_ISSUE214_R9.md](https://github.com/Brian910cpr/shiftcommander_v2/blob/16d0ace259b485a7585decbef24c74e94bd69f5c/docs/RELEASE_VERIFICATION_ISSUE214_R9.md). Principal review sources remain `server.py`, `engine/auth_store.py`, `engine/live_state_store.py`, `tests/smoke/test_private_serving_boundary.py`, `tests/smoke/test_temporary_password_gate.py`, `tests/smoke/test_durable_auth.py`, `tests/smoke/test_auth_audit.py`, `tests/smoke/test_serving_auth_safeguards.py`, `tests/smoke/test_beta_session_safeguards.py`, `tests/smoke/test_live_state_store.py`, and `tests/resolver/test_hard_filters.py` at the candidate.

Recovery guidance remains `5e81303e8f2cc306251ae61bd8566c3763548b83:docs/RELEASE_CHECKLIST_ISSUE214_R6.md`; full checklist/client limitations remain `ba0365a250d18297a262b96ab7f15cf3fe6f1780:docs/RELEASE_CHECKLIST_ISSUE214_R8.md`. R43 supersedes their old metadata-access blocker. Preserve failed storage/evidence, validate a protected backup, recover credentials into a distinct store without resurrecting revoked sessions, reconcile later password/audit changes and staffing history, then prove staged behavior before approved switching. Removing `SC_AUTH_DB_PATH` is not an assumed safe rollback.

No new application failure was reproduced. One diagnostic initially used the nonexistent filename `scripts/start_astra_review.ps1`; the documented `scripts/Start-AstraReview.ps1` was then read, parsed and checked successfully. The sparse courier initially left exactly 60 tracked root files absent. Work stopped; verified its .git-only directory, empty staged diff and 60 root-only non-skip index paths, then populated existing index entries using non-forced `git checkout-index --all`. Readback became clean. No original file was overwritten or removed.

## Independent backend queue assessment

Swept all 34 open issues, all seven titles beginning `[CODEX]`, and the relevant current comments. No newly eligible unconflicted narrow backend repair was established. Only #214 was advanced; no secondary issue, code, database or deployment was modified.

| Item | Current evidence and eligibility |
|---|---|
| #140 HOT production | New 07:35:29Z supervisor evidence reports run `34816187549` on `387be9c0c16a6d6b8184fed30b59a17a5eec5bbf` failing occupancy reconciliation after a successful full public build. Exact GitHub Actions `HOT_SYNC_ADMIN_KEY`/deployed-validator parity and both publisher proofs remain required. Preserve fail-closed publication; no unchanged-auth rerun or repository-only workaround. This is reported issue evidence, not a fresh log/prod probe by R45. |
| #226 / #209 | Class-record intake is explicitly active on `codex/class-record-details-intake` and overlaps canonical registries. Preserve its work; no competing deep implementation. |
| #227 | Accepted deployed Sites preview; 05:53:06Z review defers customer SEO/features while backend freshness/auth/reconciliation is blocked. Preserve owner-session authority and existing data truth. |
| #215 | 02:25:18Z evidence reports private owner access deployed/delivered through PR #225 and revoked temporary test access. Do not repeat the old claim that every owner page needs a copied key. Financial/legacy Hot Sync/inbox connections, individual instructor identities, static/public data privacy and monitoring remain separate unfinished work. Its success does not approve ShiftCommander accounts. |
| #216 | NOW page delivered; current balances/full bill inputs and whole-workflow observer proof remain unestablished. Cash prompts cannot be invented. Owner-session delivery in #215 supersedes its older access setup requirement. |
| #219 | View/Remove controls deployed; individual instructor identity/assignment scope and actual authenticated click-through remain open. Owner access is not instructor authorization; do not distribute the owner credential. |
| #223 | Existing 19-class/13-participant reconciliation and authenticated source roster evidence are delivered. Do not reimport. Class 51431 still needs authoritative end-time correction (19:30 is explicit provisional treatment), and owner/API/UI proof is distinct from source/database verification. |

Other paused/blocked items retain their dependencies. No duplicate implementation, independent credential retry or speculative broader refactor was started.

## Runtime, persistence and proof limits

Matching active-thread local session metadata reports CLI `0.153.4`; its latest `turn_context` records `model=gpt-6-astra` at `2026-09-14T07:46:17.516Z`. Session identity was matched locally and only allowlisted fields returned. This is local runtime evidence, not provider-side attestation or merely a prompt/config edit. The official [model controls documentation](https://learn.chatgpt.com/docs/models?surface=cli) confirms per-launch `-m`; it does not prove account/runtime selection.

Reusable project launcher: `E:\GitHub\shiftcommander_v2_codex_issue214_r2\scripts\Start-AstraReview.ps1 -RepoPath E:\GitHub\shiftcommander_v2_codex_issue214_r9 -CheckOnly`. At `2026-09-14T03:49:14.4149738-04:00`, it returned `can_launch=false`, dispatcher lock held/inaccessible, `runtime_model_verified=false`. That last field belongs to launcher preflight; the separate matched active-session record establishes the current model. Continue this worker; do not launch another or change lock/lease/machine defaults. Once legitimately free, omit CheckOnly for the existing project-scoped Astra launch. This is an agent launcher, not an application launcher. No verified normal operational localhost URL exists; prior synthetic servers use temporary loopback ports.

Expected operational outcome: a real authenticated save survives restart and produces legal explained publication matching all views. Last successful full real-world proof/timestamp: **not established**. Required cadence includes Wednesday 23:59 publication and approved source freshness. Lost saves, unreadable/schema-invalid storage, stale inputs, illegal assignments, mismatched views or missed publication are failures. Whole-workflow observer, observer heartbeat and escalation delivery remain unproven; local tests are not that monitor. The latest supervisor review demonstrates the earlier receipt round trip, not current R45 acknowledgement or whole-system health. Brian must not become the routine detector.

Original courier `codex/durable-session-participant-linking` retains `docs/Earl/index.html`, tracked/untracked Python caches, the pre-existing heartbeat and `supabase/.temp/` dirt. Original ShiftCommander `codex/base44-worker-consolidation` retains the modified calendar mirror, untracked availability backup/slot generator/data/tests and four unpublished commits: `3287eb47c95c6286c5194fef13730458e1279c1b`, `9a49b9ecdaa6268722aa8cd52f5f4f8dc42d1c31`, `69bc1fb13773622465f47a8b88d48a06b26966ce`, `55d6a05b919c1661845902b35eda14c9d4935f02`. No unfinished merge/cherry-pick/revert/rebase marker was found in either original checkout or R9. Previous worktrees/receipts remain preserved.

Exact changed file: **Codex_Reply_ShiftCommanderAstra_R45.md** only, persisted locally in the isolated courier. No target source/config/test/data change or new target PR. Explicit one-file staging, required-field/Markdown/whitespace and base-to-head checks are enforced before commit/push. No new untracked artifacts are intended in this courier. No Codex_Read marker or retired mutable mailbox was written.

Deployment status: **not merged, not deployed, not activated**. Local assessment/validation only; GitHub provides issue/ref/blob reads and the required receipt push. No application publication, auth cutover, account provisioning, operational database migration, routing change, calendar-authority change, member communications or paid service action occurred. Final #214/UI return supplies the receipt commit and verified remote readback. Keep the issue and draft stack open pending the exact gates above.
