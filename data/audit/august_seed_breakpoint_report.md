# August Seed Breakpoint Report

Status: upstream source mismatch resolved; downstream rendering was not deployed. No deploy was performed.

## Plain Answers

A. First disappearance: `resolved_at_dynamic_offers_preview`. August now reaches active dynamic offers with `20901` August rows.
B. Cause: the original availability source/horizon break was RRULE expansion in the live calendar snapshot export. Course Master gates remain downstream.
C. Smallest fix: keep RRULE expansion in `scripts/export_calendar_snapshots.py`, regenerate live availability, then rerun the existing dynamic/public/seed URL pipeline without bypassing filters.
D. Rows after fix: current artifacts include August dynamic offers and August appointment URL previews; exact rows are listed in `august_bls_seed_pipeline.csv` and `august_heartsaver_seed_pipeline.csv`.
E. Risks: report-only availability must not bypass conflict checks, appointment container/date bounds, Course Master review gates, UNKNOWN course suppression, public sellable limits, or rendered-page verification.

## Stage Counts

- Dynamic offers total: 42993
- Dynamic offers in August: 20901
- Public sellable offers total: 210
- Public sellable offers in August: 60
- Selected seeds total: 27
- Selected August seeds: 6
- Appointment URL previews total: 27
- Appointment URL previews in August: 6
- August BLS selected proposals in seed simulation: 8
- August Heartsaver selected proposals in seed simulation: 0
- August public seed rows rendered: 0

## Filter Reasons

August dynamic offers now reach public filtering. Current overall public filter reasons are:
- `outside_public_dynamic_hours`: 24024
- `course_id_not_enabled`: 19799
- `course_family_disabled`: 17840
- `course_family_not_enabled`: 17840
- `max_offers_per_course_per_week_exceeded`: 9143
- `max_total_offers_per_day_exceeded`: 651
- `inside_minimum_lead_time`: 237

## Course Master Gate Finding

Course Master has conservative gates, but those gates are downstream of the RRULE/live-snapshot fix. They must stay in place for UNKNOWN/unreviewed rows. If Course Master is promoted into this path, the AHA BLS/Heartsaver appointment-seed flags are currently too conservative/stale for rows already proven elsewhere in the seed pipeline. See `course_master_gate_blockers_for_august.csv` for exact rows.

## Emergency manual fallback

If the seed fix is not approved fast enough, Brian would need to manually create only the minimum August Enrollware classes that cover the currently selected BLS August proposals in `august_bls_seed_pipeline.csv`. This is an emergency safety net, not the primary solution.
