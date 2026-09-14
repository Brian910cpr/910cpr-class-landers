# ShiftCommander Astra R38 prerequisite assessment

Assignment: [issue #214](https://github.com/Brian910cpr/910cpr-class-landers/issues/214), dispatch `SHIFTCOMMANDER_ASTRA_20260913_R1`.
Timestamp: 2026-09-14T01:02:18-04:00 (America/New_York).
Work-item state: BLOCKED for release. This receipt records a completed prerequisite/queue assessment, not a new application implementation or release.
Persistent-system evidence state: BUILT with retained local synthetic validation; the complete operational workflow is not PROVEN, MONITORED or HEALTHY.

## Branches, exact commits and pickup

- Courier worktree: `E:\GitHub\910cpr-class-landers_codex_issue214_receipt_r38`.
- Courier branch: `codex/issue-214-shiftcommander-receipt-r38`; base commit `bd7db4fe9ab105b52d94487cd248ea772f4623f0`. This communication-only commit's final SHA/content verification is reported on #214 after push, avoiding a self-referential SHA.
- Target read-only assessment: `E:\GitHub\shiftcommander_v2_codex_issue214_r9`, branch `codex/issue-214-release-gate-verification-r9`, commit `16d0ace259b485a7585decbef24c74e94bd69f5c`.
- Application remains `ba0365a250d18297a262b96ab7f15cf3fe6f1780`, branch `codex/issue-214-private-boundary-r8`, [draft PR #10](https://github.com/Brian910cpr/shiftcommander_v2/pull/10).
- Fresh GitHub readback: PR #10 OPEN/draft, three original changed files, `statusCheckRollup=[]`. Serving PRs #5-#10 remain OPEN/draft; migration PRs #3/#4 remain OPEN. Target `origin/main` remains `67a3f88f1b54fa2ffbd285df7df969cea7837616`. Repository refs do not prove hosting health.
- [R38 pickup](https://github.com/Brian910cpr/910cpr-class-landers/issues/214#issuecomment-5659238191).

## Findings and work performed

Read the full issue body and all 79 pre-pickup comments, pinned `Codex_Mailbox/SHIFTCOMMANDER_ASTRA_20260913_R1.md`, original/current courier AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, LANDERWARE_PROOF_AND_HEALTH_STANDARD.md, docs/CODEX_INSTRUCTIONS.md, issue #116, and target AGENTS.md/project boundaries/confirmed scheduling rules/RULES.md/DATA_CONTRACT.md. Read migration/overlay material from the consolidation checkout and R8/R9 release evidence from the reviewed candidate. Historical migration claims do not establish current serving authority.

The R8 review and [R36 acknowledgement](https://github.com/Brian910cpr/910cpr-class-landers/blob/91039997dfe03e4b0f051835535e2e3e14598355/Codex_Read_ShiftCommanderAstra_R36.md) prohibit a speculative implementation/merge/deploy round ahead of unchanged prerequisites. Fresh issue/ref/queue evidence supplies no clearing configuration, approved current staffing snapshot or new reproduced independent application defect. No unchanged failing provider-auth path was retried.

| Exact blocker | Required next evidence/action |
|---|---|
| Minimum Cloudflare serving metadata access remains unverified after the prior Pages metadata HTTP 401. | Account operator restores Pages project/deployment, Worker routing and D1 binding metadata reads, or supplies an approved sanitized export. Verify actual serving paths before staging. A bridge credential and unrelated Sites/LanderWare deployment do not establish these permissions. |
| Persistent real authentication has no approved operational configuration. | Approve persistent filesystem and exact `SC_AUTH_DB_PATH`, schema v2 readiness, privately provisioned real member/named supervisor accounts, signing configuration and inherited/deployed settings. Keep secrets out of issues/receipts. Do not activate against schema v1 or restore stale sessions. |
| Current ADR staffing inputs and provenance remain unapproved/unreconciled. | Identify/approve current roster/certifications, unit-specific `qualOp`, explicit availability consent, staffing demand and calendar snapshot. Retain ADR Google Calendar published-staffing authority. The prior 170-shift observation ending August 10 is historical, not a fresh live read. |

After those gates, the original scope still requires real scoped clients/authentication, availability -> legal resolver -> supervisor review -> publication, member/mobile/wallboard agreement, hosted backup/recovery, observer proof, secure Windows startup and phone/SMS/email integrations. No staffing policy, production authority or credentials were invented.

The last pre-pickup R37 issue comment reports a bridge credential exposed in that prior session's diagnostic output. That is inherited incident evidence, not a new exposure by R38. No rotation/containment proof has been supplied. Private operator review and coordinated rotation remain outstanding; no value was copied into this receipt or used/changed by this run.

## Validation and evidence limits

Local AST parse and in-memory compile of `server.py`, `engine/auth_store.py`, `engine/live_state_store.py` passed without bytecode writes. PowerShell parser validation of `E:\GitHub\shiftcommander_v2_codex_issue214_r2\scripts\Start-AstraReview.ps1` passed. Exact outputs:

```text
SYNTAX: 3 Python sources passed; no bytecode written
SYNTAX: Astra PowerShell launcher passed
```

`git diff ba0365a250d18297a262b96ab7f15cf3fe6f1780 HEAD --name-only` in R9 returns only `docs/RELEASE_VERIFICATION_ISSUE214_R9.md`; its worktree is clean. No candidate application/data changes. Retained `E:\GitHub\shiftcommander_v2_codex_issue214_r9\debug\verification_r9\combined_final.log` was read, not rerun:

```text
Ran 160 tests in 189.801s
OK
FINAL: tests=160 failures=0 errors=0 skips=0
```

These are prior local synthetic tests, including Windows process restart/recovery and resolver regressions, not new R38 behavioral tests or CI/staging/production proof. Initial read attempts used the wrong `debug/auth_r9` log path and looked for courier docs in the target repository; both were corrected with existing exact paths. No application failure was inferred from those lookup errors.

Important review sources remain [R9 verification](https://github.com/Brian910cpr/shiftcommander_v2/blob/16d0ace259b485a7585decbef24c74e94bd69f5c/docs/RELEASE_VERIFICATION_ISSUE214_R9.md), [R8 checklist](https://github.com/Brian910cpr/shiftcommander_v2/blob/ba0365a250d18297a262b96ab7f15cf3fe6f1780/docs/RELEASE_CHECKLIST_ISSUE214_R8.md), `286876e7d506bd127e14c2852f65c827815a8fa7:docs/RELEASE_EVIDENCE_ISSUE214_R2.json` (`read_only_checks`), and `5e81303e8f2cc306251ae61bd8566c3763548b83:docs/RELEASE_CHECKLIST_ISSUE214_R6.md` (schema/recovery). Existing candidate, tests, release checklist and recovery guidance remain usable.

## Runtime and preservation

Matching active-session local `turn_context` reports `model=gpt-6-astra` at `2026-09-14T04:55:22.416Z`; matching session metadata and `codex --version` report CLI `0.153.4`. These sanitized local fields are not provider-side attestation. [Official CLI documentation](https://learn.chatgpt.com/docs/developer-commands?surface=cli) was fetched; documentation/configuration is not runtime proof.

Existing R2 `scripts/Start-AstraReview.ps1 -RepoPath E:/GitHub/shiftcommander_v2_codex_issue214_r9 -CheckOnly` returned `can_launch=false` at `2026-09-14T00:58:32.7325761-04:00`, dispatcher lock held/inaccessible. One current worker continued; no duplicate launch, lock/lease/default change or timer was introduced. The Astra launcher is a worker entry point, not a verified operational app launcher; no working normal application URL is claimed.

Original courier changes in `docs/Earl/index.html`, tracked/untracked Python caches, `ops/handoff/codex_heartbeat.json` and `supabase/.temp/` remain untouched. Original ShiftCommander calendar mirror, untracked availability backup/slot generator/data/tests and four unpublished commits on `codex/base44-worker-consolidation` remain preserved (`git rev-list --left-right --count` reports `0 4`). No unfinished merge/rebase/cherry-pick/revert was found in either original checkout or R9. The untracked `Codex_Reply_ShiftCommanderAstra_R37.md` in its earlier courier worktree is preserved and not included here.

The new courier sparse setup initially showed 59 root files missing in a .git-only directory. Stopped/reviewed the complete 55,014-entry index and empty staged diff. `git checkout-index --all` then populated only the new worktree's non-sparse files without overwrite/force; status became clean. No existing checkout was reset, cleaned, restored, rebased or merged. No generator ran.

## Independent backend queue

Swept all open CODEX items and checked current comments/ownership before selecting additional work. No independent narrow backend repair was established outside existing active work and explicit gates; no second issue was implemented or mutated.

- #226 is explicitly active on `codex/class-record-details-intake`; preserve canonical class/person/credential/document work and do not duplicate its implementation.
- #227 is new. Its receipt at `bd7db4fe9ab105b52d94487cd248ea772f4623f0:Codex_Reply_Issue227.md` reports a first Sites slice deployed at 04:00:39Z, Sites source `f02400fd26ead001a61bc715aee73ee8b47f94f7`. It explicitly lacks authenticated roster/finance/scheduler integration. This is that workstream's deployment evidence, not independent R38 verification. Preserve that delivery and establish scheduler lineage before edits; it clears none of #214's three prerequisites. Its proposed SEO markup work is a distinct frontend slice.
- #215 reports private owner access delivered through PR #225. Preserve it; do not repeat obsolete claims that all owner pages require the old shared key. Legacy Worker/finance integration, individual instructor identity, static data privacy and monitoring remain separate work.
- #216 still needs private finance inputs and full operational proof; its old credential prose must be read alongside newer #215 access delivery.
- #219 needs individual instructor identity/assignment scope and authenticated click-through. Existing document controls are delivered; do not substitute owner access for instructor authorization.
- #223's 19-class/13-registration reconciliation is already returned. Preserve it; source end-time correction and owner/API/UI proof remain distinct. No duplicate import.
- #140 still reports scheduled occupancy HTTP 401 at run `34796567750`. Preserve the account/parity gate and fail-closed publishers; no unchanged credential retry or repository workaround.

## Persistent proof, deployment and next action

Expected outcome: real authenticated availability survives restart and produces an explainable legal schedule, reviewed/published consistently across all views. Success evidence must tie save, persisted revision, resolver decisions, approval and rendered views together. Last successful complete operational proof: not established. Expected cadence includes Wednesday 23:59 publication; current source-freshness and operational observer windows remain unproven. Failure conditions include unavailable/schema-invalid auth storage, stale staffing inputs, lost saves, unauthorized/illegal assignments, inconsistent views or missed publication. Component fail-closed checks do not prove the overall outcome; independent observer, observer heartbeat and escalation delivery are unverified. Brian must not become the routine detector.

Recovery remains R6/R9's protected credential-only recovery to a distinct store, reconciliation of password/audit history and staged verification; do not resurrect old sessions or assume unsetting `SC_AUTH_DB_PATH` is safe rollback. Account-level action is required for metadata/private provisioning; owner/operator authority is required for staffing-source approval and the inherited credential incident.

Exact changed file: `Codex_Reply_ShiftCommanderAstra_R38.md` only. Local prerequisite validation complete; this root receipt is the only intended commit/push. No application code/data changes, build, merge, deployment, candidate activation, database upgrade, source-authority cutover or member communication occurred. GitHub reads/pickup/push are remote; code inspection/syntax checks are local. No current production-health claim.

Next ChatGPT action: review this receipt and retain #214 and the draft stack open/unmerged. Supply the minimum sanitized serving-metadata evidence, privately approved persistent-auth readiness, and approved current ADR input provenance through the existing issue handshake, with private operator handling of the R37 credential incident. Then dispatch coordinated staging/recovery/client work. An unchanged wake cannot clear these gates; resume implementation on changed prerequisites or a reproduced independent defect. Preserve #226/#227's active deliveries and the complete original release scope.
