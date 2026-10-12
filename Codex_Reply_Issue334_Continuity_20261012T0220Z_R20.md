# Issue #334 continuity checkpoint R20

Timestamp: 2026-10-12T02:20:00Z (UTC).
Branch: codex/issue334-continuity-20261012-r20.
Inspected production commit: 6ee7da28c500e82b46ecb775116c2f3f3c637e5a. Receipt commit is the pushed branch tip (reported on issue and in final response).
State: IN_PROGRESS; release/cloud-observer gates remain BLOCKED. Persistent evidence: PROVEN for recent publisher-to-Pages cycles, not HEALTHY for the overall booking system.

## Execution and findings
Execution acknowledged before implementation: https://github.com/Brian910cpr/910cpr-class-landers/issues/334#issuecomment-6116555374 . Read full issue body/comments, current root AGENTS.md, CODEX_HANDOFF_PROTOCOL.md, design ethos and proof standard. Latest owner continuity instruction takes priority; no arbitrary third-party authorization used.

Exact durable evidence: data/audit/issue334_continuity_20261012_r20.json. It contains all three publication SHAs, both family timestamps/counts, Pages IDs and calculated delivery margins.

- Publication 162903d1203c8d1e6b206143ece3f02164a56302: Pages 38193723228 completed 01:55:46Z; both feeds valid through 02:08:59.292885Z.
- Publication 49690a1ea655d2721e2fe32f9d4b0d40b37bb20f: Pages 38194405870 completed 02:06:19Z, 160.292885 seconds before prior expiry. Both feeds then valid through 02:19:22.627560Z.
- Publication 6ee7da28c500e82b46ecb775116c2f3f3c637e5a: Pages 38195054954 completed 02:16:08Z, 194.627560 seconds before prior expiry. Both feeds then valid through 02:29:29.213089Z.
- Cache-busted public reads at 02:18:26Z/02:18:29Z matched the latest publication and were unexpired. BLS: 87 dates, 1,512 starts, 3,991 offers. Heartsaver: 81 dates, 1,506 starts, 8,297 offers. These family totals do not establish pediatric/blended-specific availability.
- Both families still evaluate only 190/210 windows: 20 failures and 20 uncertainty issues. This is separate from expiry and remains scoped to existing PR #385; neither #385 nor #383 was replaced or merged.

## Exact fault boundary and safety implication
The effective lease is NOT the 90-minute value in scripts/apply_anchor_policy.py:572. Current source coverage in scripts/build_live_availability_snapshot.py:848-849 sets valid_until to earliest calendar observation +15 minutes, freshness_minutes=15. scripts/layered_publication_adapter.py:129 clamps coverage to source freshness and rejects expired proof; line 209 transfers that expiry to offers. The public selector drops stale publications through ResolvedSelectorAvailability.publicationExpired/datesForPublication (scripts/build_bls_block_schedule_pilot.py:2324-2325).

A ten-minute refresh interval plus approximately four-minute build and one-minute Pages delivery has little reserve. Two recent deliveries met their deadlines; the historical screenshot cycle's exact latency cause is NOT proven by this checkpoint. A cooldown fix alone cannot create a missed-cycle reserve under a 15-minute source lease. Extending only publication TTL would not safely solve this, and weakening source freshness would permit stale occupancy proof. No freshness, conflict, reconciliation or fail-closed gate was changed.

## Validation and limitations
- node --check worker/availability-refresh-watchdog.mjs: passed.
- node --test tests/availability_refresh_watchdog.test.mjs: 15 passed, 0 failed.
- python -B -m unittest tests.test_layered_publication_adapter: 21 passed.
- Audit JSON parsed locally; both delivery margins positive and live payloads unexpired.
- Pages completion is delivery evidence, not continuous CDN or rendered-browser observation. No browser proof, registration submission or payment was exercised. Two publication transitions are evidenced; uninterrupted customer behavior between samples is not claimed.
- Python urllib public read returned HTTP 403; PowerShell Invoke-RestMethod succeeded. This is a client-path limitation, not evidence of an outage.

## Preservation and deployment
Original E:/GitHub/910cpr-class-landers dirty work remains untouched. Its git fetch failed with bad object 6e61cabca5981d1389e52c60d95424d9893bb50f and bad remote ref origin/codex/group-training-experience; no cleanup/reset/repack repair attempted. Used independent clean shallow clone E:/GitHub/issue334-continuity-20261012. Windows case-colliding tracked docs/Earl/index.html and docs/Jackson/index.html show modified after checkout; intentionally not staged. Only this receipt and the named audit JSON are intended changes.
No application change, generator, workflow dispatch, merge or deployment performed. Draft PR #372 untouched. Existing PR #383 and #385 preserved. No new implementation PR created. No ops/handoff/next_task.md used. Temporary audit script stays outside repository in the local TEMP directory.
Queue scanned across 30 open CODEX items; no narrow unassigned backend item was selected that would safely avoid active assignments and this P0 priority.

## Proof contract and blockers
Expected outcome: both selectors retain legal current appointment inventory. Expected cadence: admin cron ten minutes; watchdog checks use existing publisher with 9m30s minimum dispatch cooldown. Effective source window: 15 minutes. Last successful proof: live matching payloads at 02:18:26Z/02:18:29Z following Pages 38195054954. Failure: public expiry, empty unexpected inventory, unresolved windows, or late delivery. Observer: existing local timer and repository observer/cloud watchdog design. Independent cloud observer remains unproven; prior owner encrypted GITHUB_ACTIONS_TOKEN gate is unchanged and no credentials were requested/read/exposed. No fresh cloud activation proof obtained; do not call MONITORED/HEALTHY. Owner still risks discovering selector failures until independent observation is proven.

Next concrete engineering action: on the existing implementation stream, inspect timer run history and exact fetch-to-Pages phase timing for the screenshot's stale cycle; assess reducing existing dispatch interval (with active-run deduplication intact) rather than expanding freshness. Keep source proof live and fail closed. In parallel with that same scoped stream, finish Oct14 canonical anchor duration/pre-post analysis on existing #385/#383 before release. Current 20 failed windows are not occupancy evidence.

Release blocker: owner explicitly requires exact broad-generated-output scope and rollback plan before specific release approval. Neither a blanket rebuild nor deployment is authorized by 'move forward'. No new release approval requested here because canonical Oct14 analysis and full scope are not yet complete. Existing account action: repository-restricted Actions read/write token only as encrypted Cloudflare GITHUB_ACTIONS_TOKEN for independent observer; no additional owner action invented. Keep #334 open.
