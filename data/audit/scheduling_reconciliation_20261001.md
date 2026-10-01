# Scheduling reconciliation — October 2–3, 2026

Checkpoint: 2026-10-01 03:34 UTC. Review branch: `codex/scheduling-reconciliation-20261001`, based on `origin/main` commit `2de00b799248529cdf986d39dd63373da905664c`.

## What is proven

The production database and two protected runtime functions were repaired and verified. A local publication built from fresh Enrollware iCal, Google Calendar snapshots, and the deployed demand endpoint produces only the real October 2 starts (08:45, 10:45, 12:45), with participant counts 2, 1, 2. October 3 shows the 09:00–11:30 offsite commitment and HeartCode at 12:30, with a 60-minute occupied window. The public BLS Initial browser preview offers only 12:45 on October 2.

The frontend/publication changes are locally persisted and validated at this checkpoint; production merge and browser verification remain pending. This is not an unattended roster synchronization claim. Brian confirmed that no automated export exists. Fresh complete rosters were read through the authenticated Enrollware UI; no Enrollware records were edited. Source proof expires after 60 minutes. Subsequent stale evidence must become unknown, never zero, and stop synthesis on affected dates.

## Before and after truth

All clock times below are America/New_York. Participant names/contact details and raw roster pages are deliberately excluded from this public repository report.

| Case / stable external ID | Fresh Enrollware evidence | Before canonical / workspace | After production database |
|---|---|---|---|
| Oct 2 Family & Friends, `14495100`, schedule `51496` | 08:45–10:45; two active registrations | No canonical class; Gmail proposal remained pending | Canonical class created; two registrations; original proposal workspace adopted and scheduled |
| Oct 2 BLS Renewal, `14382096`, schedule `51487` | 10:45–12:45; one active registration | Correct time and one stored registration; old proof | Same canonical and workspace IDs; fresh complete proof; one registration |
| Oct 2 BLS Initial, `14501248`, schedule `51499` | 12:45–14:45; two active registrations | Correct time; zero canonical registrations; no workspace | Same canonical ID; two registrations and workspace; native checkout/public/open settings preserved |
| Oct 3 Christ Community | Private operational commitment, 09:00–11:30; also confirmed in inverse calendar | Canonical private/closed class; no workspace | Same canonical private/closed class; workspace created; solid occupancy without needing registrations |
| Oct 3 HeartCode, `14186226`, schedule `51478` | 12:30–13:00 source display; one active registration | Canonical/workspace 10:00–11:00; stale evidence | Same canonical/workspace IDs at 12:30–13:00; occupied through 13:30 using reviewed 60-minute course rule; private/closed settings preserved |

Exact UUIDs, before values, after values, source observation timestamp, repair job, and source digest are in `data/audit/scheduling_reconciliation_20261001.json`. Repair job `96694269-ae2c-40d5-a505-f734eb18ec45`: four reconciled classes, zero quarantines. Common conservative source observation: `2026-10-01T03:00:49.497Z`. The complete four-class snapshot and six individual registration statuses were reread immediately before reconciliation. The source SHA-256 is `ad65db520b1f2bd375818301e115e84b7d6644f41d7a44e45a59c83e5fa856b4`.

Fresh calendar export confirms Oct 2 ADR hard block **17:00 through Oct 3 07:00**, and Oct 3 Christ Community **09:00–11:30**. The supplied calendar screenshots themselves show September 29 and September 30; they did not establish those October facts. The attached Landscape screenshot had a 09:30 HSI no-candidate cell selected; the inverse-gap diagnosis was separately reproduced on the live page.

## Proven points of divergence

1. **Incomplete source collection.** `scripts/enrollware_roster_reconciliation.py` accepts complete authenticated roster snapshots but no unattended collector is connected. iCal refreshes class times, not full roster membership. Gmail notices are not proof of a complete roster. Database read time must not renew source observation time.
2. **Native checkout rejected external roster truth.** `public.reconcile_enrollware_roster_batch` previously accepted only selected Enrollware sources. BLS Initial already had an exact external ID but `source=landerware_public_offer`, `registration_backend=landerware`; its source roster could not reconcile. The repaired RPC accepts this exact linked identity while preserving native registrations and checkout/visibility settings. Native checkout plus external class now requires complete external proof in `_shared/external-roster-proof.ts`.
3. **Workspace projection excluded real classes and lost identity on moves.** `public.sync_enrollware_class_session_to_landerware` previously filtered to Enrollware sources and rebuilt workspaces. It now upserts through a unique `class_session_id` FK for all operational sources, preserves workspace UUID/documents/workflow state, and projects private/manual classes too. Verified proposal adoption uses explicit evidence identity, not a fuzzy time match.
4. **External ID concealed a stale occurrence.** `scripts/canonical_scheduling_demand.py::resolve_canonical_demand` previously matched an external class ID without rejecting a changed start. It now reports `STALE_ANCHOR`, closes both old and new dates for synthesis, and does not promote the old time. Canonical edits invalidate prior external proof in a database trigger.
5. **Inverse availability was treated as sufficient supply on occupied days.** `scripts/block_start_time_selector.py::build_block_schedule_page` generated free-gap starts, while `scripts/apply_anchor_policy.py` ran later and separately from Landscape. The generator now finalizes the shared decision once. Real classes remain; unrelated synthetic starts disappear on occupied days; any incomplete reconciliation closes synthesis. Barnacles require explicit existing course-pool compatibility, matching instructor/location, and an adjacent occupied boundary. Existing hard conflict rules remain in force.
6. **Short positive ICS duration under-reserved occupancy.** `build_occupancy` now uses the maximum of source end, canonical consumption end, and the existing reviewed course consumption minimum. It also includes private/native canonical commitments independently of the calendar feed.
7. **Diagnostic clock and publication disagreed.** `publish_scheduling_landscape.py::parse_dt` now converts to Eastern. The diagnostic matrix consumes final selector decisions, not pre-policy candidates. The new daily summary exposes real classes/counts, hard blocks, actual offers, missing/stale evidence, and workspace gaps. Independent final alarms identify orphan offers and hard-block collisions without requiring a cell click. Overnight labels identify previous/next day.
8. **Failed refresh left old offers published indefinitely.** A malformed test fixture (`cluster_id` missing) was blocking the admin refresh; run `36805400761` failed. The fixture is corrected. New selector feeds expire within 20 minutes, and synthetic offers also expire when their supporting roster evidence does. Public HTML refuses expired/malformed feeds, rechecks at registration clicks, and refreshes every five minutes. Referenced JavaScript has a new asset version. Publication accepts an explicitly finalized empty feed so a safe closure can replace unsafe old inventory.

9. **An external-ID column also held native event slugs.** Explicit `source=landerware_event` rows with nonnumeric local slugs keep native registration authority. Numeric Enrollware IDs still require external proof even with native checkout. `supabase/migrations/20261001032240_native_event_identity_health.sql` aligns the reconciliation health query with this distinction and excludes irrelevant historical unmatched rows.
10. **Real offers bypassed calendar vetoes.** The wider preview exposed an October 7 17:30 Heartsaver offer overlapping Brian's 02:45–21:45 busy block. `veto_calendar_collisions` now checks all candidate offers before finalization, suppresses conflicting booking, and emits `HARD_BLOCK_COLLISION`. It preserves the actual class/roster and occupancy for operator resolution. No class was moved or cancelled to hide the conflict.

## Authority and update contract

`Authenticated Enrollware complete roster/class snapshot → validated importer → service-only transactional reconcile RPC → class_sessions + registrations → stable landerware_sessions workspace projection`

`Current Enrollware iCal + canonical demand + canonical course consumption + private/manual commitments + fresh inverse busy calendar → hard-legal candidates → one final anchor/reconciliation policy → compact public selector feeds + diagnostic feed`

- `class_sessions` owns operational scheduling fields; `registrations` owns participant membership. Source identity and observed-at proof remain attached to the canonical record.
- `landerware_sessions` owns workspace documents and workflow. It cannot independently change the time, course, external class identity, location, or instructor of a linked canonical class. Existing unlinked proposals remain proposals until explicit evidence reconciles them.
- Cancellation/completion project to workspace lifecycle. Native registrations are not removed merely because an external roster omits them. Complete absence can remove only source-owned membership.
- Brian's inverse calendar is a hard veto, never evidence of paid demand. An empty day still follows existing open-day policy; this change does not invent opening hours or prohibit all overnight work.
- Unknown roster count is `null` plus an explicit reason. It is never converted to zero. Existing source class occupancy remains visible while newly synthesized offers fail closed.
- Current user-facing admin pages use `canonical-session-workspace`; the old `session-workspace` adapter is not the authority for these pages.
- No competing course catalog was introduced. Existing `data/inventory/course_consumption_rules.json` supplies duration and compatibility; unknown metadata is not guessed.

## Deployed backend components

- Supabase project `wktwgcnwdvbebcobgyey`.
- Migration: `supabase/migrations/20261001024838_canonical_scheduling_projection.sql`, applied after PostgreSQL regression and SQL parse validation. Includes rollback-scoped production assertions preserving workspace identity/documents and rejecting independent schedule edits.
- Migration: `supabase/migrations/20261001032240_native_event_identity_health.sql`, applied after PostgreSQL regression and SQL parse validation.
- `canonical-scheduling-demand` version 7; bundle SHA-256 `7fe8b356e359ecbeb9b5d581c931faafa4f60126d75cc876b607415223c884f3`.
- `canonical-session-workspace` version 11; bundle SHA-256 `cc94d1da27b126ed7d4ba19d63de89556da7d31b85d35c510c38001730396a3a`.
- Existing authentication and `verify_jwt=false` custom-auth configuration were preserved; no anonymous participant access was added. Production bundles matched the checked-in baseline before replacement.
- Protected live endpoint proof: [run 36810335487](https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36810335487), generated `2026-10-01T03:24:31.574Z`: 33 sessions, 7 known counts, 26 unknown; repeat content equal; OPTIONS 204; anonymous read 401.

## Validation and preview

- 91 focused Python tests passed in 16.443 seconds (exact command in the repository reply).
- 49 Node endpoint/proof/selector/filter tests passed.
- One PostgreSQL lifecycle integration test passed, with assertions for replay, full/empty roster, stale proof, quarantine, stable workspace/documents after a move, immutable linked schedule, mixed native/external registrations, exact proposal adoption, private commitments, and service-only permissions.
- Syntax validation passed for 47 Python/JavaScript units, including inline public-page scripts. Both migrations passed SQL parsing. No source credentials or participant contact details are committed.
- Live source refresh: 263 Enrollware events ingested; one reviewed non-session excluded; 29 future schedule rows; 174 Brian busy events; 202 inverse availability windows. Three calendar exports succeeded; two other instructors had no events. Preview generation writes only a scratch directory and does not run the sitewide generator.
- Oct 2 final Landscape: three public starts, 159 unrelated/unreconciled candidates suppressed, three real classes, counts 2/1/2, no reconciliation error. Oct 3: two real classes, no public starts because source classes are private/closed, 299 candidates suppressed, no stale 10:00 class.
- Local browser verified BLS Initial Oct 2: `12:45 PM` only, registration target retains Enrollware ID `14501248`. Diagnostic preview visibly shows the three categories and error summary above the original matrix.
- A broad historical artifact test run was not clean because it expects ignored/stale generated source files and earlier rendered artifacts. It is not used as proof of this repair; focused production CI regressions are the acceptance suite. Do not report the entire repository test suite green.

Latest bounded preview: `2026-10-01T03:31:03.376132+00:00`; all eight selector feeds validated. Exact counts and rejection reasons are in `data/audit/scheduling_reconciliation_preview_proof_20261001.json`. Browser verified October 2 and 3 truth cards and October 7 loud collision/stale-roster alarms with no public booking.

## Remaining release and operational work

1. Commit/push this branch and obtain final approval for the existing production refresh. User-provided AGENTS explicitly requires approval before a sitewide generator. Merging changed workflow/test paths triggers `scripts.run_validated_public_build`, which can inspect all 1,075 tracked HTML pages; the last successful equivalent run built 28 class pages and changed 47 files. Expected scope: public class/course/location/selector pages, index/sitemap, public JSON/ICS feeds and build metadata, plus the bounded admin refresh and calendar snapshots. Inspect unexpected changes; do not blindly stage the tree.
2. Run required CI, merge, let the existing production host deploy, and verify live HTML + versioned JavaScript + JSON + actual rendered Oct 2–3 behavior. At this checkpoint the local preview is not a deployed frontend fix.
3. Connect a complete authenticated roster collector, or explicitly operate the existing complete-roster importer. No unattended export/API is configured. No credentials were copied from the browser. The system is intentionally fail-closed as evidence ages; it is not `HEALTHY` unattended synchronization.

The database components are CONNECTED and individually PROVEN. Local publication is BUILT and browser-validated. The combined production process is not yet PROVEN/MONITORED/HEALTHY. A deployment alone cannot close the collector gap. The October 7 existing class/calendar conflict still requires an operational scheduling decision; publication suppression does not resolve the commitment itself. The next operational integration must preserve complete-roster coverage, source timestamps, exact external IDs, cancellation/reschedule status, and quarantine behavior, and needs an approved credentialed source rather than an assumption that iCal or Gmail is complete.
