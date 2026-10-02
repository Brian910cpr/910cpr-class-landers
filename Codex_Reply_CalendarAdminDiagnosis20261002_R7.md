# Issue338 bounded admin-refresh diagnosis R7

Timestamp:2026-10-02 UTC
Branch:fix/calendar-open-shifts-20261002
Previous local commit:2d86f73de
State:DIAGNOSTIC COMPLETE; admin trigger cause unresolved; public block-edge task remains BLOCKED awaiting owner reply. No production code/settings change.

## Evidence

Admin workflow315399794 schedules at minutes7,17,27,37,47,57 onmain. Public workflow301038681 schedules at13,43 onmain. Both use concurrency group schedule-publish-main with cancel-in-progress=false. Serialization can delay existing jobs, but no new queued admin run is visible; it does not explain absent run creation by itself.

Admin's latest scheduled run is36948145959 at00:52:13UTC, successful. The manual admin run36968821283 at05:24:54UTC also succeeded. The bounded no-cache exact-workflow query still returns those runs and no subsequent scheduled admin invocation. Repository/Actions/workflow are enabled; defaultbranch and cron exist onmain. Recent changes034e76d23/47053dcee adjusted checkout/build inputs/tests, notcron. No invoked generator failure establishes an admin scheduler rootcause. GitHub status reports no incident; official docs allow delayed/dropped schedules, which remains a possibility rather than a specific diagnosis.

Public scheduled run36970091836 started05:41:46UTC and finished05:48:57UTC (about7m11s), succeeded and deployedadf0b6a3d through Pages36970625997. Live schedule advanced05:48UTC, selectors05:44UTC, with BLSexpiry07:15:56UTC and Heartsaver07:16:40UTC. Exact bytes/rendered public proof remains in scheduled-public-refresh-verification.json. Admin availability stayed05:26:42UTC.

## Current impact

A targeted scan of the eight configured public course-board HTML files found no admin_availability reference; onlydocs/admin/dashboard.html consumes it. Public BLS/Heartsaver use block-selector-availability JSON and retain real classes when synthesis expires. Therefore stale admin availability is currently an Operations display/source-age problem, not proof that customer offers are currently hidden. Public selectors are fresh from the successful scheduled public refresh.

The missing faster admin cadence still reduces redundancy and timely propagation of calendar-only changes. The public workflow refreshes calendar snapshots only when iCal/canonical changes, forced/push build, OR its existing publication-renewal guard requests a build. Correction to prior incomplete hash-gating analysis:the public workflow already has an expiry-renewal guard, so unchanged sourcehashes do not always prevent publication renewal.

That guard is $renewBefore=UtcNow.AddMinutes(10), checking BLS/Heartsaver/ACLS/PALS. A30-minute public schedule plus observed7-minute build does not guarantee refresh before expiry with only10-minute lookahead. Example using current BLSexpiry07:15:56:an unchanged-hash06:43 check is more than10minutes early and may skip;07:13 sees2m56 remaining, shorter than observed build, so an expiry gap is possible. Hashchanges may trigger earlier work, so this is a demonstrated timing-risk pattern, not a claim that the future gap has occurred. Do not extend expiry or bypass sourcevalidation.

The local replacement Operations model fails closed on source age over30minutes; it is not deployed. Incumbent dashboard warns after10minutes. Neither display is evidence that the pending customer block-edge replacement has been released.

## Safest scoped recommendations, not implemented

1. When the public workflow already exports fresh snapshots/builds liveavailability, invoke the existing sanitizedpublish_admin_availability there as well, preserving its source-status timestamps and current publication validation. This mirrors existing fresh data into the missing admin projection without a new trigger/access path or booking-policy change. It improves freshness on public builds but does not restore10-minute admincron.
2. Review a public renewal lookahead that covers its30-minute cadence plus build/queue allowance (for example45minutes), keeping validUntil and source/roster/collision checks unchanged. It causes earlier actual validation, not leaseextension. Measure additional build cost; prefer a targeted feed refresh if a later authorized implementation makes that necessary. This is smaller than the previously proposed workflow_run chain; do not implement a new chain as part of this diagnostic.
3. Escalate the specific missing admin schedule deliveries and inconsistent event-filter API indexing to GitHub Support with the existing evidence bundle. No supportmessage sent. Do not disable/enable workflows, changepermissions or re-registercron speculatively without an identified cause and authorization.

No recommendation was implemented, no manualrefresh requested, no denied bridge retried, no source session/registration/payment mutated. Unknown roster/moved-source guards remain unchanged. No broad tests/builds were run for this read-only report. Exact scheduler cause is the remaining diagnostic blocker; stop this boundeddiagnostic rather than continuing unchanged polling. Parent retains the pending precise ownerapproval question. Earl/Jackson changes remain untouched.

Source:https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
