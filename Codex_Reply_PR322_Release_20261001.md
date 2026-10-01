# PR 322 release receipt

Timestamp: 2026-10-01T10:17:00Z
Branch: codex/scheduling-reconciliation-20261001 (receipt only)
Work-item state: BLOCKED for full acceptance; PR MERGED; public output DEPLOYED.

## Findings and work

Latest head e7e2f6e26be1970b8248e5c6be6857c3f8af114a had four successful PR workflow checks and successful Cloudflare preview. PR was open, non-draft, mergeable. Owner comment 5924504885 explicitly superseded the old approval gate. No current failed check or merge conflict prevented merge; the remaining release action had not been executed. GitHub does not expose a separate historical reason for inaction.

Merged with expected-head SHA guard at 2026-10-01T10:04:41Z: 1e540d1bce6242cc3eb001ce6a1a8a78a1bb6d21. Existing push triggers started public/admin refresh and Pages.

Public refresh run 36846836870 passed all tests, source fetches, build, admin reconciliation, Anchor policy, strict links, and final public inventory validation. Published 540624b5e8f (59 files, documented public-output scope). Pages run 36847569957 successfully deployed refreshed output. Initial merge Pages run 36846836301 also passed.

## Real customer-surface proof

Live https://www.910cpr.com/bls.html:
- October 12 Initial calendar and Start Times show only starred 5:00 PM; all eleven named orphan starts absent. Register target retains Enrollware ID 14135047.
- October 12 Renewal shows only starred 9:00 AM; target ID 14184954.
- October 2 Initial shows only starred 12:45 PM; target ID 14501248.
- October 3 is unavailable for public BLS/skills booking, consistent with preserved private/closed HeartCode status. Fresh Landscape occupied-duration proof remains pending.
- Old publication missing validUntil rendered temporarily unavailable, proving live fail-closed load behavior. New feed validUntil is 2026-10-01T10:28:41.802241+00:00; generatedAt 2026-10-01T06:06:45.390972 (business local timestamp). No clock mutation or forced production expiry was used.
- Live resolved-selector-availability.js and scheduling-landscape-lanes.js byte-match merged source. Expiry/shared selector regression: 26 Node tests passed.
- Landscape visibly reports STALE PUBLICATION on the existing September 30 feed; fresh build/error/collision truth is NOT verified.

## Stop condition and exact blocker

Admin refresh run 36846836916 / job 110321282563 passed every generation and validation step, then failed Commit changed dashboard data at 2026-10-01T10:16:24Z. The queued push event checked out 1e540d1 although public refresh had advanced main to 540624b5e8f. Its generated commit 9b9d347207d conflicted when rebased onto main across class HTML, selectors, admin_schedule, anchor_state, schedule_future, and ICS. It aborted and refused to overwrite newer data. No admin output was published. Owner stop-on-surprise instruction honored: no retry, force push, manual conflict resolution, or workflow repair performed.

Exact remaining action: launch a NEW Refresh admin availability run from CURRENT main (workflow_dispatch or next scheduled run), not a rerun tied to old merge SHA. Observe validation and publication, wait for its Pages deployment, then verify fresh Landscape Oct 2/3/7/12, occupied durations, honest stale/unknown roster errors, Oct 7 HARD_BLOCK_COLLISION with no public booking, build ID/feed timestamps, and updated offer expiry. Do not claim complete acceptance until those succeed.

Work environment has merge capability and read/log tools, but no workflow-dispatch connector action; cloud GitHub browser is signed out. No owner credential changes required. If immediate manual dispatch is desired, owner can use Actions > Refresh admin availability > Run workflow, branch main; otherwise existing scheduled cadence is available. No new permission or architecture decision is needed for that established path, but this receipt does not assume future success.

Persistent evidence state: public merge-refresh-deploy-selector loop PROVEN at approximately 2026-10-01T10:13Z. Combined scheduling publication not PROVEN/MONITORED/HEALTHY. Admin cadence configured every 10 minutes; observer health not established. Known roster collector gap and Oct 7 underlying operational conflict unchanged. Recovery is rebuild from current main; escalation is only if that fresh run also fails or customer proof contradicts policy.

Exact assignment changes: this receipt only; no application code changed during release continuation.
