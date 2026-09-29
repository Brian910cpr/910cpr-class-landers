# Issue 305 production proof, R2

- Timestamp: 2026-09-29T12:34:00.068122+00:00 (08:34 Eastern)
- Branch: main
- Work-item state: VERIFIED
- Persistent-system evidence: PROVEN (not a claim of broader monitoring health)
- Implementation: 6d15a96fe980bf532023e85ce0b016b0c31588a6
- PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/306
- Merge: a03701e9c47333af3e9bfa705a8856a98f454426
- Canonical publication: 44626399e238a3663ef03aaeade1127d2d32de19
- Public publication: 878dd34e6bc6107a31a7ef1607ee5fa6196ece44

## End-to-end result

Admin refresh run 36567812415 and public refresh run 36567812629 both succeeded. The new regression gate passed in both production workflows. GitHub Pages build/deploy/report and Cloudflare Pages checks succeeded for the public publication.

Live HTTPS verification after publication: all six expected windows match in /data/schedule_future.json, /data/admin_schedule.json and /data/landerware.ics. Latest served schedule generation matches public commit: 2026-09-29T08:29:50.701646-04:00. Family & Friends class page /classes/14495100.html includes the corrected 2026-10-02T10:45:00-04:00 end.

| Session | Course | Date | Occupied time (Eastern) |
|---|---|---|---|
|14288234|Heartsaver First Aid CPR AED|Sep 29|18:00–20:30|
|14400433|BLS Renewal|Sep 30|17:30–19:30|
|14495100|Family & Friends CPR|Oct 2|08:45–10:45|
|14382096|BLS Renewal|Oct 2|10:45–12:45|
|14501248|BLS Initial|Oct 2|12:45–14:45|
|14186226|BLS HeartCode|Oct 3|10:00–11:00|

Scanned all eight live selector feeds. For dynamic offers using Brian's inverse-availability source, computed each full schedulerConsumptionMinutes interval and compared with all six occupied intervals. Conflicting offer count: 21 before publication, 0 after publication, still 0 in final verification. Existing seated classes are not misclassified as conflicting dynamic offers.

Live nonzero preservation check: all 21 positive-duration source events present in the published future schedule retained their original end. Full source replay preserved all 163 positive durations across 262 source events. 72 targeted tests passed, including six real zero-duration fixtures and 18 positive-duration variant checks. Broad artifact-based selector suite remains baseline-equivalent (19 failures, 18 errors), as described in R1; no green claim for that suite.

## Published selector counts

| Feed | Availability blocks evaluated | Public offers | Rejected candidates |
|---|---:|---:|---:|
| bls | 200 | 8609 | 1826 |
| acls | 200 | 8 | 10428 |
| pals | 200 | 8 | 10428 |
| heartsaver | 200 | 16010 | 4850 |
| uscg_first_aid_cpr_aed | 200 | 5273 | 1683 |
| hsi | 200 | 6325 | 627 |
| arc | 200 | 8460 | 1968 |
| family_cpr | 200 | 2735 | 742 |

Counts reflect the refreshed source snapshots and existing policies, not only this patch. The isolated regression proves 106 synthetic candidates -> 82 occupancy rejections + 24 nonconflicting retained offers. Production overlap verification directly establishes removal of the 21 unsafe offers; overall offer totals also change with normal availability refresh.

## Root cause / limits

Five source zero-duration events already normalized at baseline. Family & Friends had no legacy map entry, so later name-only identity recognition left it without a duration-rule lookup key. The canonical catalog supplies course 252737 and its existing 120-minute rule. Resolution now happens before canonical projections, anchors and both public-offer occupancy consumers. No durations, buffers, demand counts, course IDs or source records were invented.

Raw Enrollware iCal is upstream-owned and still reports its raw zero ends. LanderWare's canonical feed and public availability are corrected. A current/future class with unresolved duration stops ingestion before writing output or generating new offers; regression tests run on both refresh paths. Historical unresolved ARC row is outside current availability and remains source evidence.

No database, secret, registration, payment or customer message changes. Observer health beyond the successful refresh/regression/publication checks is not independently proven. Recovery remains the existing refresh workflows, with a session-specific failure for unresolved current/future duration. No Brian action required.

Files changed in this follow-up: this receipt only. Exact next action: retain existing scheduled refreshes; investigate any future unresolved-duration error using its source course/session metadata. Application repair and requested six-occurrence live proof are complete.
