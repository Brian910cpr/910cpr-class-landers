# Issue #297 — source-gated continuation

- Assignment: Brian910cpr/910cpr-class-landers#297.
- Timestamp: 2026-10-11T02:30:24Z (UTC).
- Branch: codex/issue297-source-gate-20261011.
- Base commit: ff183709b4027dcca534145e250cbf298a8bd915. Receipt commit is the pushed branch tip; no substantive code commit in this dispatch.
- Work-item state: BLOCKED. Existing reconciliation implementation is BUILT / CONNECTED; previous complete-source cycles were PROVEN. Current external bridge is not HEALTHY.

## Execution and findings

Read the full issue body/history, repository AGENTS.md, CODEX_HANDOFF_PROTOCOL.md and LANDERWARE_PROOF_AND_HEALTH_STANDARD.md. Acknowledged this dispatch before implementation:
https://github.com/Brian910cpr/910cpr-class-landers/issues/297#issuecomment-6104621002

Latest owner acceptance (2026-10-11T02:19:17Z) says the native October 13 09:00 status correction is accepted and the two attendees must not be recreated or moved. Preserved that correction. No production SQL, registration mutation, billing, accommodation-note change, or source-watermark renewal occurred in this dispatch. Payment provenance and accommodation fulfillment remain unverified.

Exact blocker: available computer/browser inventory is `{"apps":[],"browsers":[]}`. No current completeness-guaranteed Enrollware snapshot or authorized unattended source was supplied to this dispatch. Tool discovery exposes no dedicated Enrollware roster connector. Gmail notices, calendar discovery, old snapshots and canonical rereads cannot establish complete current roster/lifecycle truth. Stop point: before calling `reconcile_enrollware_roster_batch` with new source data.

GitHub remains usable. Existing observer run 38102658022 was inspected rather than redundantly rerun. Its logged result at 2026-10-11T01:41:29.2023850Z is:

```json
{"healthy":false,"gap_count":35,"signature":"19ba82fef698694ac99cbe6c28d302eb0a7178d46e1d7c655a28df6b098f448e"}
```

https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/38102658022

This is last observed remote evidence, not a fresh source read. Unknown counts remain unknown. Prior narrow native proof is in protected demand run 38102614367 and owner consistency run 38102617030; this dispatch did not independently repeat their live queries. Prior receipt: `Codex_Reply_Issue297_NativeStatusRepair_20261011_R1.md` on `codex/issue297-status-proof-20261010`, tip 75dad74e3c083bcfdbd633da7f84f411198121d9.

## Local validation

Ran locally, without apply mode or generators:

```text
python -B -m unittest tests.test_enrollware_roster_reconciliation
Ran 6 tests in 0.001s — OK
node --test tests/enrollware_roster_proof.test.cjs
9 tests, 9 pass, 0 fail
Python AST syntax validation:
scripts/enrollware_roster_reconciliation.py
scripts/audit_enrollware_reconciliation.py
Syntax: 2 files passed
```

These tests verify stale/incomplete/duplicate identities fail closed, explicit empty rosters establish zero, source watermarks affect immutable fingerprints, cancellation needs matching source membership, external classes require proof even with native checkout, and native/external mixed seats retain their authority boundaries. Node emitted only its existing experimental stripTypeScriptTypes warning. No new tests or application changes were needed for a missing-source gate.

## Persistence and safety

Only intended changed file: `Codex_Reply_Issue297_SourceGate_20261011T023024Z_R1.md`.

Created isolated worktree `E:/GitHub/910cpr-issue297-source-gate-20261011` from downloaded current-main objects. Original dirty `E:/GitHub/910cpr-class-landers` and all other worktrees/assignments preserved. A normal fetch failed with `fatal: bad object refs/remotes/origin/codex/group-training-experience`; no ref deletion, cleanup, rebase, reset or repair attempted. Worktree creation succeeded from the existing downloaded main commit. Windows checkout reports unrelated case-collision modifications in `docs/Earl/index.html` and `docs/Jackson/index.html`; left unstaged and uncommitted. No file intentionally left untracked by this dispatch.

Scanned open [CODEX] queue and existing PRs. Existing fleet backend continuations are already on PR374/375; Studio is PR372; Activity Monitor #373 is gated after the P1 foundation. No independent narrow fix was established that could safely supersede these assignments; no competing deep stream or duplicate PR created. No applicable open reconciliation PR needs these receipt-only changes. PR372 remains draft, unmerged and undeployed.

Deployment status: validated locally; receipt committed/pushed on named branch; no merge, application deployment, full build, public generation or customer-facing verification performed. Public recovery and Stage 6 remain gated.

## Proof contract and next action

Expected outcome: exact external session and registration identities reconcile from complete current rosters, then protected owner schedule/demand return current counts without public PII. Freshness window: 60 minutes from genuine source observation; DB reads cannot renew it. Last complete-source proof recorded in issue history: 2026-09-27 05:56–05:57 UTC, now expired. Last observer execution inspected: 2026-10-11 01:41 UTC, correctly failing on 35 gaps. Observer `.github/workflows/verify-canonical-participants.yml` notifies existing #297 only on changed signatures. A recent successful observer query is evidence it ran; continuous observer-supervisor health was not independently proven here and is not claimed.

Brian/account-level action remains required once: authorize/provision a completeness-guaranteed unattended Enrollware source, or restore authenticated browser access for a bounded current snapshot. Brian must not become the recurring manual monitor/source carrier.

Exact engineering continuation: obtain current complete roster/lifecycle snapshot using schema `enrollware-complete-roster.v1`; preserve private input outside the repo; validate with `scripts/enrollware_roster_reconciliation.py` and apply through existing `reconcile_enrollware_roster_batch`; investigate quarantined exact identities, verify protected owner/demand response and all remaining gaps, then follow normal publication gates and verify actual selectors plus a later scheduled cycle. Do not recreate/move the two accepted native attendees, fabricate source timestamps, infer counts from notices, weaken UNKNOWN gates, merge PR372 or deploy it. Keep #297 open.
