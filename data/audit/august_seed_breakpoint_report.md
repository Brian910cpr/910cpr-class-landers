# August Seed Breakpoint Report

Status: blocked before public rendering. No deploy was performed.

## Plain Answers

A. First disappearance: `data/audit/dynamic_offers_preview.json`. August exists in `debug/seed_simulation_report.json`, but active dynamic offers contain `0` August rows.
B. Cause: availability source/horizon. The active dynamic generator is reading live availability blocks that stop at July 4, not the August report-only base-horizon availability. Course Master gates are not the first blocker.
C. Smallest fix: promote/regenerate reviewed August Wilmington availability into the active availability source consumed by dynamic offer generation, then rerun the existing public filter, seed selection, URL preview, public inventory, and hub rendering steps.
D. Rows after fix: BLS Wilmington rows should come from the August Brian selected proposals listed in `august_bls_seed_pipeline.csv`; no Heartsaver August Wilmington selected proposals currently exist in the seed simulation.
E. Risks: report-only availability must not bypass conflict checks, appointment container/date bounds, Course Master review gates, UNKNOWN course suppression, public sellable limits, or rendered-page verification.

## Stage Counts

- Dynamic offers total: 690
- Dynamic offers in August: 0
- Public sellable offers total: 14
- Public sellable offers in August: 0
- Selected seeds total: 1
- Selected August seeds: 0
- Appointment URL previews total: 3
- Appointment URL previews in August: 0
- August BLS selected proposals in seed simulation: 8
- August Heartsaver selected proposals in seed simulation: 0
- August public seed rows rendered: 0

## Filter Reasons

No August dynamic offers reach public filtering, so there are no August public-filter rejection reasons yet. Current overall public filter reasons are:
- `inside_minimum_lead_time`: 644
- `course_id_not_enabled`: 387
- `missing_container_for_instructor`: 300
- `course_family_disabled`: 199
- `course_family_not_enabled`: 199
- `outside_public_dynamic_hours`: 183
- `max_offers_per_course_per_week_exceeded`: 8

## Course Master Gate Finding

Course Master has conservative gates, but those gates are downstream of the first August break. They must stay in place for UNKNOWN/unreviewed rows. If Course Master is promoted into this path, the AHA BLS/Heartsaver appointment-seed flags are currently too conservative/stale for rows already proven elsewhere in the seed pipeline. See `course_master_gate_blockers_for_august.csv` for exact rows.

## Emergency manual fallback

If the seed fix is not approved fast enough, Brian would need to manually create only the minimum August Enrollware classes that cover the currently selected BLS August proposals in `august_bls_seed_pipeline.csv`. This is an emergency safety net, not the primary solution.
