# Codex Reply: #157 / #297 publication guard and source-access boundary

Timestamp: 2026-09-29T15:16:00Z (11:16 EDT)
Branch: `codex/issue-297-source-refresh`
Substantive commit: `9cf670c9a00f6a345c44eea02058e2a66a3c3915`
Evidence commit: `946244519030f36e7b774790bf1a5398c51250d0`
Normal merge: PR307, `e0bb74e8225f29055412c2e9635b857b3821340a`, 2026-09-29T15:09:51Z.
Work-item state: **BLOCKED at current authoritative source access; public-selector recovery is incomplete.** The publication guard is MERGED, DEPLOYED and production-tested. This is not completion of the requested chain.

## Implemented and proven repair

The prior real scheduled publication dropped all 12 demand Anchors when complete-roster evidence expired and then published expanded scattered offers. Its structural validator accepted that replacement. The targeted repair re-resolves public occurrences against canonical demand validated at the final publication step. Unknown, missing, ambiguous or expired public demand now rejects publication before the commit. Proven zero and positive counts pass. Unknown private/quarantined records outside public inventory do not block unrelated public rows. The code neither rewrites unknown as zero nor changes ranking or promotes an Anchor.

Both existing publishers already call `scripts.validate_public_refresh_output` before committing their output. The shared gate now enforces source freshness at that point, including expiry during a long build. No alternate scheduler, database, source feed or ticket was created. Stage 6 remains gated.

Changed source/test/config files:

- `scripts/validate_public_refresh_output.py`: final canonical-demand publication gate.
- `tests/test_validate_public_refresh_output.py`: source expiry during build, current zero/positive counts, missing/ambiguous joins and private-source isolation.
- `.github/workflows/anchor-policy-ci.yml`: run the publication regressions in the existing CI workflow.

Evidence/report files added: `data/audit/issue157_publication_guard_proof.json` and this unused immutable receipt. Every previous receipt remains unchanged, including R3 and the failed scheduled R6 evidence on its pushed branch.

## Exact validation and production result

Local changed-module `compile()` syntax checks and `git diff --check` passed. Command:

`python -m unittest tests.test_validate_public_refresh_output tests.test_demand_publication tests.test_anchor_state tests.test_apply_anchor_policy tests.test_canonical_scheduling_demand tests.test_fetch_canonical_scheduling_demand tests.test_selector_clock tests.test_enrollware_roster_reconciliation`

Result: **61 tests passed** locally. [Anchor policy CI 36587901009](https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36587901009) passed **61 Python + 18 TypeScript + 1 isolated PostgreSQL test**. All PR checks were green and PR307 was CLEAN/MERGEABLE; merged normally with exact-head matching, no admin override or bypass. Existing R3 acceptance and PR197 merge `b9297d128143b99b62d273770e0a7304a4d17b98` remain satisfied; PR197 was not reopened or replaced.

[Pages 36588087068](https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36588087068) successfully deployed revision `e0bb74e8225f29055412c2e9635b857b3821340a`. At 15:12:16 UTC, live BLS HTML, all seven referenced first-party assets and five JSON/calendar resources matched that Git revision. No public asset changed in this patch, so no new CSS/JS version reference was needed.

[Production admin publisher 36588090830](https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36588090830), actual event `workflow_dispatch`, ran the normal publication chain against live sources. At 15:14:02 UTC, **Validate reconciled public inventory before publication** failed with `Refusing publication with unknown canonical demand; preserving published inventory.` **Commit changed dashboard data was skipped.** The run completed failure at 15:14:06 UTC, and remote main remained `e0bb74e8225f29055412c2e9635b857b3821340a`. This proves the production refusal behavior, not successful source/Anchor recovery and not a scheduled-event proof.

## Current reconciliation queue and source evidence

The four original findings retain their established dispositions: Brunswick 13895152/13895154/13895155 have canonical sessions at the approved private location; 11341058 is an owner-confirmed renewal deadline at approved 4018 Shipyard, excluded from instructional sessions. They were not rolled back or relabeled to force health green.

An authenticated browser pass on September 27 reread all **38 class forms and 20 displayed roster entries**. Incident displayed counts were **1/1**, observed at 14:56:41.367 / 14:56:42.548 UTC. The separate registration lifecycle verification then failed because the source browser target closed. No complete reconciliation batch was applied from this unfinished pass. The environment resumed on September 29; none of those old observations were treated as current, and no source watermark was renewed.

Read-only canonical SQL at 2026-09-29T15:10:15 UTC, covering September 26 forward, reports 37 stale instructional sessions and one classified non-session. [Current health run 36587963026](https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36587963026) correctly failed: its current/future projection scope has **32 stale canonical sources plus two new missing canonical sessions**:

- `14495100`: October 2 at 08:45 Eastern, course 252737, Family & Friends CPR, Shipyard B.
- `14501248`: October 2 at 12:45 Eastern, course 209806, BLS Initial, Shipyard B.

These are projected identities, not proof of current roster counts. The existing #297 observer had already detected them in [comment 5886455059](https://github.com/Brian910cpr/910cpr-class-landers/issues/297#issuecomment-5886455059); the new run confirms the same signature without duplicate alarm spam. They remain in the same reconciliation queue pending authoritative source verification through the existing path.

The current public baseline has zero demand Anchors and 30 unknown public occurrences, with BLS 8,608 offers / 3,142 starts / 90 dates. This is **not a recovered selector**. The September 27 incident classes are now past and correctly absent from current future inventory; do not reinsert them to manufacture a live proof. Preserve their historical incident proof and use current future classes for the subsequent real publication cycle.

## Exact access boundary and next action

The source-browser failure is reproducible: selecting the existing Enrollware tab timed out; creating a fresh source tab timed out waiting for browser webview attachment; the documented visibility/focus recovery also timed out on that source tab. Discovery still lists the source tab, but that does not prove its DOM can be read. No current complete roster or actual rendered public-selector check was possible after the browser failure. GitHub, live HTTP and Supabase read-only SQL are accessible. The initial GitHub DNS failure recovered; it is not an outstanding blocker.

The smallest immediate owner action is to **reopen Enrollware admin in Codex's browser or restart the browser panel so the authenticated page attaches**. This was requested in the active task. Do not bypass the browser restriction by extracting cookies/session tokens or treating old files as new source truth.

Brian instructed **no Zapier use**. No Zapier setting, credential or payload was used or changed. Inspection found an existing registration webhook but no class/status-change webhook; that configuration alone cannot establish complete current roster truth. No authorized unattended complete-roster API/export input was identified in the inspected repository/environment configuration. An unattended source connection remains a separate unresolved dependency; a one-time fresh browser import does not prove its health.

After source access returns: read complete current rosters and lifecycle states, including the two new October 2 identities and the incident records for historical reconciliation; apply the existing `reconcile_enrollware_roster_batch` path; rerun #297 health and protected demand; run the normal publisher; verify the actual public selector; then observe a genuine later scheduled refresh retaining correct results. Keep all current checks and the new refusal guard in place.

## State accounting

- **BUILT:** publication guard and regression tests.
- **CONNECTED:** shared validator is used by both normal publishers. Complete unattended roster input is not connected.
- **PROVEN:** isolated tests and production publication refusal. Current source-to-Anchor-to-selector recovery remains unproven.
- **MERGED:** PR307 above, in addition to previously merged PR197/303.
- **DEPLOYED:** `e0bb74e8225f29055412c2e9635b857b3821340a`; live bytes verified.
- **LIVE-VERIFIED:** HTTP baseline only for this resumed phase. Actual browser selector and later successful scheduled preservation remain blocked/unproven.
- **MONITORED:** existing #297 observer detected stale/missing relationships; its September 29 scheduled evidence predates this manual confirmation. Overall system is not HEALTHY.

No real booking, registration lifecycle, source timestamp, permission, ranking rule or Stage 6 state was changed. Direct/native/admin/bookmarked Enrollware booking remains outside LanderWare selector controls. Unrelated selector-suite failures were not taken into scope. Unrelated `supabase/.temp/` remains untracked; private historical files and scratch helpers remain outside Git. Source access recovery, rather than unrelated maintenance or another approval of R3, is the immediate next dependency.
