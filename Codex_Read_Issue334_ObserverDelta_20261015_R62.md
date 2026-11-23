# Issue 334 — observer comparison R62

Timestamp: 2026-10-15T18:15:14Z (UTC).
Branch: codex/issue334-location-proof-20261014-r56.
Existing draft PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/393
Base commit: 9e406544087469c55ff36e78b3348988aa2bb0a0. Receipt commit: pushed branch tip and originating issue completion comment (avoids self-reference).
State: BLOCKED for production release. Keep #334 open.

Execution acknowledged before evidence work: https://github.com/Brian910cpr/910cpr-class-landers/issues/334#issuecomment-6199061173 . Read issue history, repository AGENTS.md and CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard. Original E:/GitHub/910cpr-class-landers is dirty and lacks the protocol on its old branch; preserved untouched. Used existing clean sparse clone E:/GitHub/910cpr-issue334-r58 on the SAME PR393 stream. Fast-forwarded only the existing supervisor acknowledgment commit; no conflict resolution, reset, cleanup, rebase or force-push. No changes to draft #372 or other assignments.

## Evidence and exact findings

Downloaded requested retained artifact without workflow dispatch:
`gh run download 38661126617 --repo Brian910cpr/910cpr-class-landers --name public-booking-observation-38661126617 --dir E:/GitHub/issue334-r62-observer`

Scheduled run 38661126617 failed, created 2026-10-15T00:37:52Z, updated 00:38:01Z, head 1cae2cbfebf2ec2d89c8b2cde95a129046a9837c. Artifact11937864383 retained byte-for-byte in data/audit/issue334_observer_r62_requested.json, SHA256 91af8078bc54139de7c92f23085dbfe5f57168a4f4a7b21a64f6025c293e4251. Observed 00:37:57.609766Z. All eight families: 441 input/normalized sources, 189 input windows/187 evaluated/2 failed. Exact reason (count2 in each family):
`missing directional travel rule: :: Wilmington; Shipyard Blvd - B->4018 Shipyard Blvd, Room B, 910CPR Office`
This matches R61 exactly. BLS3571/88dates, HS7458/87; both unexpired at sample. October14 dayFailedWindows=0; dayOffers=0 is not the failure trigger.

Also retained newest available scheduled observer38751780783, created14:28:57Z, observed14:29:02.270314Z, failure. Artifact11981966731 downloaded to E:/GitHub/issue334-r62-latest and retained byte-for-byte in data/audit/issue334_observer_r62_latest.json, SHA2564a238d23337d468b52a708369eb5ce4231775c0e2ae62b30afac921e5cd8c183. All eight families191input/189evaluated/2failed. Exact reason in each (count2):
`missing directional travel rule: 4018 Shipyard Blvd, Room B, 910CPR Office->:: Wilmington; Shipyard Blvd - B`
This is the opposite direction, previously observed in R58/R49. Same known endpoint pair; no new root cause established. Do not add a guessed one-way travel rule or infer Room B assignment.

Current read-only probe:
`python -B scripts/audit_family_publication_coverage.py --live --continuity --day 2026-10-15 --output data/audit/issue334_live_r62.json`
Exact exit: coverage_exit=1 (expected fail-closed coverage alert).
Observed18:14:57.013343Z, all eight families190input/188evaluated/2failed, same native-label-to-Shipyard direction as latest observer. BLS3472/88dates, HS7239/87, both unexpired through18:20:16.387230Z. All October15 dayFailedWindows=0 and dayOffers=0; today's absence is not explained by these two failures. ACLS8/5dates and PALS6/3 remain seated-only with publicationExpired=true; no dynamic qualification proof inferred. Other totals ARC3467/86dates, HSI2388/86, USCG2390/87, Family1079/84. Rolling sources/counts differ between samples; no causal explanation or production after-count inferred.

The first comparison assertion incorrectly required identical direction in all three reports and failed. Corrected validation explicitly asserts requested forward direction and latest/live reverse direction; PASS. No application patch made. Exact failed-window dates are absent from these summaries; November3 attribution comes from retained authenticated provenance and branch probe, not new proof here.

## Validation and changed files

PASS: AST syntax for scripts/audit_family_publication_coverage.py and data/audit/issue334_probe_r57_check.py; JSON parsing; all3 reports contain8families; exact directional reasons/count2; evaluated=input-2; dayFailedWindows0; BLS/HS unexpired at observation; original downloaded byte equality. git diff --check PASS. Production coverage remains FAIL; evidence checks are not recovery proof.
Previous55focused tests and authenticated190/190 zero-failure branch probe38546492384 reused, no implementation changes justify rerunning cloud generation. Reproducible original probe/checker and exact occupied interval proof: data/audit/issue334_probe_r57.md, data/audit/issue334_probe_r57_original.json, data/audit/issue334_probe_r57.json, data/audit/issue334_probe_r57_check.py. Source rationale/provenance/scope/rollback: data/audit/issue334_location_r56.md and data/audit/issue334_location_r56_proof.json.

Only intended files committed/pushed:
- data/audit/issue334_observer_r62_requested.json
- data/audit/issue334_observer_r62_latest.json
- data/audit/issue334_live_r62.json
- Codex_Reply_Issue334_ObserverDelta_20261015_R62.md

Downloaded artifact directories outside repo intentionally excluded. No participant PII/secrets included. Original dirty pages, bytecode, untracked receipts and runtime files preserved. No generators, application/config/public-output edits, competing publisher, activation retry, merge or production deployment. Existing preview automation is not production proof.

## Exact blockers and next action

Specific owner approval for existing PR393 plus documented normal-publisher40-60 expected generated/state-file scope remains absent. PR reviews empty; Cloudflare bot preview and prior execution receipts are not owner approval. The latest originating instruction retains the existing gate. No duplicate approval alert issued.

Concrete release remains venue-only proven normalization plus existing conservative primary-room fallback, preserving other-instructor conflicts and explicit Room A. No Room B inference. Expected normal refresh-admin-availability output:17selector/alias/redirect HTML,8familyfeeds, workflow-allowlisted canonical/admin/landscape/anchor/ical data, current native class pages, calendar snapshots and audits/status; no full class/hub rebuild. Stop above10unexpected files. Exact scope/rollback in data/audit/issue334_location_r56.md and data/audit/issue334_probe_r57.md.

Next: resolve existing specific release decision on #334. After approval, recheck #383 compatibility and current authenticated branch probe if stale; reuse393 and normal publisher; verify all8LIVE families zero failed windows, November3 noon-2PM occupied interval retained, rendered legal BLS/HS starts and matching assets/GET handoff without registration/payment submission, then successive renewals before expiry. Rollback is a reviewed revert of only PR393 source/config, followed by normal publisher, retaining fail-closed checks.

Independent cloud gate: AVAILABILITY_WATCHDOG_HEALTH_URL API still HTTP404. Existing repository-restricted Actions read/write credential provisioning and encrypted Cloudflare GITHUB_ACTIONS_TOKEN storage remain account-level gate. No secret contents inspected or transmitted; no activation retry. No duplicate owner alert.

Queue swept: open issues and PRs reviewed. Backend scheduling383/408, checkout387, documents389/406, finance388, fleet374/375 and auth218 retain existing assignments/gates. New independently prepared items also have existing PRs396-408. No safe unassigned narrow backend quick win selected; no competing deep stream or duplicate PR created.

## Persistent proof boundary

Repair BUILT/authenticated dry-run validated; historical customer publication PROVEN, overall HEALTHY unestablished. Last retained end-to-end release proof: data/audit/issue334_direct_p0_release_20261012.md; no fresh browser/checkout proof here. Current component admin38782093069 and Pages38782779643 succeeded; admin38783479359 in progress at bounded check. These cannot override current failed coverage.

Expected outcome: legal customer-selectable inventory renewed before effective source expiry (~15minutes), all windows evaluated without uncertainty. Configured public observer cadence5minutes. Latest retained natural observer14:29Z failed, with preceding starts09:51/05:08Z; sustained5minute cadence not proven. Failure signals expired feeds or failed/unevaluated windows. Public observer and supervisor detect failures; independent observer health/recovery not proven while health URL absent. CYBERPC awake/login/network dependency remains; Brian must not be routine monitor. Recovery: scoped existing release decision and live proof, then secure cloud provisioning and independent timer-to-publication/observer recovery proof. Owner action remains only existing specific release decision and secure account provisioning; no new diagnosis request.
