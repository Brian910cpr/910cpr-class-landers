# March 2027 Enrollware Exit Roadmap

Status: read-only operational roadmap. This document does not modify public pages, call Enrollware, create appointments, change appointment URLs, enable Worker routes, deploy, or commit.

## Executive Target

Target cutoff: **March 1, 2027**.

The current deterministic appointmentDayId window is bridge infrastructure, not the long-term scheduling system. The target is for Lander/910CPR to own core scheduling operations by March 2027. The known bridge window currently runs through about **2027-04-30**, so March 2027 should be treated as the operational decision point and April 2027 as contingency runway.

If full replacement is not ready by March 2027, the fallback is to renew or refresh appointmentDayId ranges before the current window expires.

## Current Bridge State

Active appointment containers:

- `shipyard_brian_continuous_20260621_20270430`: Brian / NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office / appointmentDayId 260670 through 260983 / dates 2026-06-21 through 2027-04-30

Current pipeline state from audit files:

- Fixed future schedule sessions: 249
- Fixed schedule last listed start: `2026-08-14T12:45:00-04:00`
- Dynamic offers read by public filter: 694
- Public sellable dynamic offers kept: 0
- Schedule seeds selected: 0
- Appointment URL previews generated: 0

Current container-blocking reasons:

```json
{
  "missing_container_for_instructor": 465,
  "location_mismatch": 229
}
```

This means Enrollware bridge dependency remains active, and dynamic public scheduling is not ready to replace the fixed/bridge path.

## Critical Deadlines

- **Now through Q3 2026:** keep shadow scheduling accurate; do not rely on dynamic output publicly.
- **Q4 2026:** internal preview should be usable enough for Brian/admin review.
- **January 2027:** decide whether replacement is realistically on track; start renewal/refresh fallback if not.
- **February 2027:** limited public pilot or fallback renewal should already be in motion.
- **March 1, 2027:** operational cutoff decision. Either Lander owns the critical path or Enrollware bridge renewal is executed.
- **April 30, 2027:** current known appointmentDayId window ends; do not wait until this date to decide.

## What Lander Must Own Before Enrollware Can Be Retired

Lander must own or intentionally replace these operational responsibilities:

- Schedule generation from availability, course rules, instructors, resources, and occupancy.
- Customer-facing public schedule display.
- Click-time availability recheck.
- Registration intake.
- Payment or payment delegation.
- Roster management.
- Attendance/completion tracking.
- Card/certificate workflow support or export.
- Admin review and override tools.
- Reporting and reconciliation needed to operate classes.
- Data retention and backup/export strategy.

Enrollware can become backup-only only after these are covered or explicitly retained somewhere else.

## Phase 1: Shadow dynamic scheduling

Goal: Run the dynamic scheduler beside fixed Enrollware classes with no customer-facing behavior change.

Required components:
- Class Report ingestion
- course_catalog.json
- people_catalog.json
- live availability snapshots
- dynamic offer generation
- audit reports

Current repo artifacts already built:
- `scripts/build_sessions_current.py`
- `scripts/build_schedule_future.py`
- `scripts/export_calendar_snapshots.py`
- `scripts/build_live_availability_snapshot.py`
- `scripts/generate_dynamic_offers.py`
- `data/audit/dynamic_offers_preview.json`

Missing work:
- Keep calendar export reliable
- Close remaining course/container mismatches
- Operator review cadence

Go/no-go criteria:
- No public pages changed
- No appointments created
- Occupancy blocks existing classes
- Reports explain all major rejection reasons

Rollback plan: Stop running preview pipeline and continue fixed Enrollware schedule only.

## Phase 2: Internal live preview

Goal: Let Brian/admin review proposed dynamic seeds before they are public.

Required components:
- reviewable seed reports
- container coverage reports
- admin preview surface or files
- manual approval process

Current repo artifacts already built:
- `scripts/filter_public_sellable_offers.py`
- `scripts/select_schedule_seeds.py`
- `data/audit/public_sellable_offers_preview.json`
- `data/audit/schedule_seeds_preview.json`
- `data/audit/appointment_container_coverage_review.md`

Missing work:
- Internal preview UI
- review annotations/import path
- clear approval records

Go/no-go criteria:
- Seeds are understandable
- No seed is published automatically
- Rejected seeds are traceable to policy reasons

Rollback plan: Hide/ignore internal preview output; keep fixed public schedule.

## Phase 3: Limited public pilot

Goal: Publish a very small set of dynamic options for one proven path only.

Required components:
- confirmed appointment container
- URL preview success
- customer fallback message
- feature flag
- manual monitoring

Current repo artifacts already built:
- `data/inventory/appointment_containers.json`
- `scripts/build_seed_appointment_url_preview.py`
- `worker/recheck_seed_worker_plan.md`

Missing work:
- Nonzero Brian + Shipyard URL-capable seeds
- disabled-by-default public wiring
- click-time recheck implementation

Go/no-go criteria:
- At least one reviewed seed generates correct preview URL
- No missing container coverage for pilot path
- Rollback flag tested

Rollback plan: Disable dynamic flag and show fixed schedule/contact fallback.

## Phase 4: Container-backed Enrollware bridge

Goal: Use Enrollware as enrollment/roster endpoint while Lander owns offer selection.

Required components:
- appointment container registry
- server-side URL rebuild
- click-time calendar recheck
- occupancy refresh
- bridge monitoring

Current repo artifacts already built:
- `data/inventory/appointment_containers.json`
- `scripts/build_seed_appointment_url_preview.py`
- `worker/src/recheckSeed.ts`

Missing work:
- Worker route implementation
- Google API auth
- server-side deterministic URL rebuild
- runtime monitoring/logging

Go/no-go criteria:
- Worker refuses stale/invalid seeds
- Worker rebuilds URL from trusted config
- No browser-supplied URL is trusted

Rollback plan: Return buttons to fixed Enrollware class links only.

## Phase 5: Native Lander registration/payment

Goal: Move registration intent, customer intake, and payment into Lander-controlled flow.

Required components:
- registration intake model
- customer records
- payment provider
- confirmation flow
- admin review tools

Current repo artifacts already built:
- `docs/910cpr_lander_scheduler_scope_lock.md`
- `data/config/people_catalog.json`
- `data/config/course_catalog.json`

Missing work:
- Registration schema
- payment integration decision
- receipt/refund flow
- privacy/security review

Go/no-go criteria:
- Payment and registration state are reliable
- Manual admin recovery path exists
- No duplicate booking risk

Rollback plan: Stop native checkout and route registrations back to Enrollware.

## Phase 6: Native roster/attendance/card workflow support

Goal: Support the operational workflows Enrollware currently covers after payment.

Required components:
- roster management
- attendance
- instructor view
- completion status
- card/certificate workflow integration or export

Current repo artifacts already built:
- `data/config/course_catalog.json`
- `data/config/people_catalog.json`
- `docs/910cpr_lander_scheduler_punchlist.md`

Missing work:
- Roster UI
- attendance capture
- completion/card workflow design
- audit trail
- exports

Go/no-go criteria:
- Admin can run a class from Lander data
- Completion/card workflow is accounted for
- Records are auditable

Rollback plan: Keep Enrollware as roster/source of record until workflow parity exists.

## Phase 7: Enrollware fallback reduction

Goal: Reduce Enrollware from scheduling brain to backup/exception path.

Required components:
- native registration confidence
- native roster confidence
- operational reporting
- support procedures

Current repo artifacts already built:
- `docs/schedule_handoff_transition_plan.md`
- `docs/scheduler_pipeline_operator_runbook.md`

Missing work:
- Production operating checklist
- incident response
- data backup/export strategy
- owner signoff

Go/no-go criteria:
- Most normal classes can be sold and managed without Enrollware
- Fallback remains tested
- No critical workflow depends on appointmentDayId bridge

Rollback plan: Renew/refresh appointmentDayId ranges and keep Enrollware as active bridge.

## Phase 8: Enrollware exit or backup-only mode

Goal: Choose whether to retire Enrollware from core operations or retain it as a backup.

Required components:
- final workflow parity review
- data retention/export
- financial reconciliation
- support docs
- owner approval

Current repo artifacts already built:
- `This roadmap`
- `scheduler audit artifacts`

Missing work:
- Final business decision
- data migration/export plan
- vendor cancellation/renewal decision

Go/no-go criteria:
- Lander owns scheduling, registration, payment, roster, attendance, and reporting needed for operations
- Backup mode is explicitly documented if retained

Rollback plan: Keep/renew Enrollware as backup-only or active bridge if any critical native workflow is not ready.


## March 2027 Cutoff Checklist

- Native schedule generation produces reviewed public options.
- Click-time recheck is live or an equivalent server-side safety gate exists.
- Registration intake is native or bridge-safe.
- Payment handling is native or intentionally delegated.
- Roster/attendance/completion/card workflow is native or formally retained in Enrollware.
- Fallback plan for renewed appointmentDayId ranges is ready by January 2027.
- Owner go/no-go decision is made no later than March 1, 2027.

## Risks Of Waiting Until April 2027

- The current appointmentDayId bridge can expire before native replacement is ready.
- Renewal/refresh work may need vendor/admin lead time.
- Dynamic scheduling may still be blocked by missing containers or click-time recheck.
- Public pages could lose sellable options if fixed classes taper off and dynamic seeds are not ready.
- Roster/payment/card workflows may lag behind scheduling and become the real blocker.
- Emergency renewal under time pressure increases operational risk.

## Fallback If Appointment Windows Are Renewed Anyway

Renewing appointment windows is acceptable as a safety bridge if March 2027 readiness is incomplete.

Fallback plan:

1. Renew or refresh appointmentDayId ranges before January/February 2027 becomes urgent.
2. Keep Enrollware as enrollment/roster endpoint while Lander continues to own offer selection in preview or limited-live mode.
3. Add renewed ranges to `data/inventory/appointment_containers.json` only after confirmation.
4. Keep confirmed-container filtering enabled.
5. Continue building native registration/payment/roster capabilities behind the bridge.
6. Re-run the exit decision once native workflows are operationally complete.

## Current Dependency Risks

- Current deterministic appointmentDayId bridge depends on known container ranges that expire around 2027-04-30.
- Public sellable dynamic offers currently filter to 0 under confirmed-container policy.
- Lander does not yet own registration/payment/roster/attendance/card workflows.
- Waiting until April 2027 leaves no operational buffer if native replacement or renewed container ranges fail.

## Next Safest Build Step

Implement an internal preview/admin surface for dynamic seeds and close confirmed container coverage so at least one Brian + Shipyard seed can preview a URL, before any public wiring.
