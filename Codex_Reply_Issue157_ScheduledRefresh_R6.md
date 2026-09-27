# Codex Reply: #157 / #297 actual scheduled-refresh result

Timestamp: 2026-09-27T07:25:00Z (03:25 EDT)
Assignment: existing #157 demand-led Anchor continuation; #297 canonical reconciliation prerequisite.
Branch: `codex/issue-157-scheduled-refresh-proof`
Evidence commit: `c8c9b4ad32c5c1c4678ec47ae0969bbd3d9aafbd`
Work-item state: BLOCKED at persistent source freshness / FAILED scheduled Anchor persistence; existing implementation remains MERGED and DEPLOYED.

## Material result

The first observed repaired publisher with an actual `schedule` event ran and deployed successfully, but **did not preserve the Anchor/Barnacle result**. After the genuine roster watermark expired, the publisher correctly changed registration demand to unknown/null, then published zero demand Anchors and expanded scattered offers. This is not a successful end-to-end persistence proof, despite green publisher and Pages jobs.

- Admin publisher [36302085641](https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36302085641): actual event `schedule`, created 07:06:27 UTC, completed 07:09:48 UTC; input `e8627d810d548e761b0992e3908655e3705e8740`.
- Published revision `aac74d95cde6e39e4c8115a70353ecae1b35c166`; Pages [36302251069](https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36302251069) succeeded at 07:10:54 UTC. An ancestry check confirms repair merge `32d2380893cbe4723d650b6968e5bbd9b46ab4b5` is included.
- Anchors: **12 -> 0**. Canonical demand audit: 0 matched, 38 failed closed; public unknown-demand occurrences: **0 -> 31**.
- BLS inventory: 203 availability blocks and 91 dates remain; offers **8,110 -> 8,593**, start times **2,964 -> 3,145**, rejected offers 1,918 -> 1,924. Generated publication scope was 58 files, 286 insertions and 348 deletions, under the existing approved publisher.
- The full public publisher's latest actual schedule event remained pre-repair run 36286577970 at the check. Earlier full push/manual publication proof is preserved; it is not mislabeled as a scheduled event.

## Current source and canonical evidence

Last genuine complete-source observation was 05:56:16.932 UTC, expiring at 06:56:16.932 UTC. This verification did not reread or mutate customer rosters, renew observations, or infer counts from notices. Read-only SQL at 07:15:25 UTC reports 37 stale instructional sessions and one classified non-session.

Both incident canonical relationships remain stored, one active relationship each: 14361098 -> `a9fd9bf2-43c8-46b7-a289-176d7989be8b`; 14421081 -> `913abd99-b8aa-48d9-a9f2-549387fb9c4f`. **Stored 1/1 is not a claim of current authoritative roster counts after expiry.** Public rows retain exact external-ID joins but expose `active_registration_count: null`, `count_available: false`, `demand_status: stale_reconciliation` and `demand_basis: unknown`.

The three Brunswick classes remain canonically reconciled; freshness loss does not turn them back into missing sessions. The owner-confirmed renewal deadline 11341058 remains explicitly excluded from instructional sessions, schedule, calendar and Anchor demand. Its approved location remains 4018 Shipyard Blvd, Wilmington, NC, per the owner's clarification and preserved `Codex_Reply_Issue297_ShipyardClarification.md` on commit `44fff9b003f3b1fda5c4e81e21a391c046ed30f2`. No midnight instructional class was invented.

## Live proof and exact results

At 07:20:06 UTC, the verification script checked live BLS HTML, all seven referenced first-party CSS/JS assets, Anchor/public schedule/BLS selector/admin JSON and iCal. All **13 resources matched deployed Git bytes**. The deadline page returns 404 and is absent from schedule/admin/calendar.

Actual browser interaction, begun 07:20:24 UTC, confirmed:

- September 27 Renewal: PM 1:00 PM, Register link external class 14361098.
- September 27 HeartCode: PM 6:30 PM, Register link external class 14421081.
- Tuesday September 29 BLS Initial now exposes nine times (09:00 through 11:00, then 20:30 through 22:00), instead of the prior two Barnacles at 11:00 and 20:30.
- Saturday October 3 BLS Initial now exposes 26 times, instead of the prior two Barnacles at 08:00 and 11:00. The first link targets appointmentDayId 260774 / courseId 209806 / 07:00.
- No browser errors and no checkout/booking submissions. Scheduled-class stars in the UI are not proof of canonical demand Anchor membership; live Anchor JSON is empty.

The existing health observer was rerun read-only as [36302890561](https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36302890561). It correctly failed at 07:22:41 UTC, with 37 `stale_reconciliation` gaps, and posted [existing #297 evidence](https://github.com/Brian910cpr/910cpr-class-landers/issues/297#issuecomment-5853764228). Signature: `06fe4c9a65a6101516356a9076a93fafae1546af96e0950eb5017c8e4bd968e4`. The final failed step intentionally calls `core.setFailed` for unhealthy reconciliation; this is not an authentication or notification failure.

No application code changed in this observation. Verification-script syntax compilation, JSON serialization/parse assertions, source-staleness assertions, Git ancestry, resource-byte comparisons and the four UI scenarios passed. The target persistence assertion **failed**. Prior CI proof (54 Python, 18 TypeScript and one PostgreSQL test) remains historical evidence, not a newly repeated suite. Unrelated selector-suite failures were not expanded into scope.

## Delivery and persistent-system states

- **BUILT:** existing #157/#297 code and repairs remain built. No new application patch in this receipt.
- **CONNECTED:** endpoint, runtime, publishers and public selector exchange data; an unattended complete-current-roster source remains unconnected.
- **PROVEN:** prior fresh-source publication cycle and isolated lifecycle tests passed. Current actual scheduled demand/Anchor persistence is **FAILED**.
- **MERGED:** PR197 `b9297d128143b99b62d273770e0a7304a4d17b98` and continuation PR303 `32d2380893cbe4723d650b6968e5bbd9b46ab4b5` remain merged. Brian's explicit R3 acceptance/publication authorization was already satisfied; no renewed approval is requested. Original R3 receipt blob `eecc7ad144a4e53997792cdbb6a3019678a7831a` remains unchanged.
- **DEPLOYED:** `aac74d95cde6e39e4c8115a70353ecae1b35c166` via the actual scheduled publisher and Pages run above.
- **LIVE-VERIFIED:** deployed bytes, incident times/targets and deadline exclusion pass; persistent Anchor/Barnacle outcome fails.
- **MONITORED:** this task detected the actual event; existing reconciliation observer detected and posted stale state when invoked. Its configured cadence is twice hourly, but reliable scheduled observer cadence is not established by this manual invocation. Do not claim overall HEALTHY.

Last successful end-to-end public proof was 06:09:10 UTC at `e8627d810d548e761b0992e3908655e3705e8740`, using public data from `e2b0fbadf317da1cdf29a5bb411e7d09f224396f`. The source expiry is the failure boundary. The publication structural/exclusion check can pass with zero demand Anchors; it does not establish freshness or persistent compaction.

## Remaining action and exact boundaries

The next source action under existing #297 is to connect an authorized complete current Enrollware roster export/API/event source to `reconcile_enrollware_roster_batch`, with exact source identities and genuine observation times. Then rerun canonical health, #157 demand projection, normal publication, actual UI proof and a later scheduled cycle before claiming persistent success. Review stale-source publication behavior within these existing issues; do not redesign `daily_anchor_stack_v1` or silently retain stale numeric counts.

No concrete access call failed here: GitHub, live public pages and canonical read-only SQL were accessible. The missing dependency is the unattended authoritative source input/contract, not a blanket permission error or unfinished maintenance. Identifying/authorizing that source is the smallest unresolved owner/source-provider action if it is not already available. Repeated database reads cannot supply it, and repeated manual imports cannot prove unattended health.

Direct/native/admin/bookmarked Enrollware bookings remain outside LanderWare selector controls. Incident customer navigation channels remain unknown. Stage 6 stays gated. No booking, registration lifecycle, infrastructure permission, production code, ranking rule or source timestamp was changed during this observation.

Changed files: `data/audit/issue157_scheduled_refresh_proof.json` and this new immutable receipt. All previous receipts are preserved. Local verification helper and private source material remain outside Git; unrelated `supabase/.temp/` remains untracked. The actual repository remote and clean named branch were verified, and no competing coding owner was active. Observable local model configuration is `gpt-6-astra`, reasoning effort `xhigh`; it is configuration evidence, not independent runtime attestation.

The dedicated scheduled-event observation is now recorded with a failed outcome. Its bounded watch can be paused without treating the repair as complete; the source dependency and failed result remain on #157/#297 and in the existing reconciliation-health observer.
