# Schedule Handoff Transition Plan

This is a read-only operating plan for moving 910CPR from fixed Enrollware-listed classes toward dynamic seed/stack scheduling without creating a public schedule gap.

**Do not delete real classes yet.** Fixed Enrollware classes remain the public schedule source until dynamic seeds are proven, reviewed, container-backed, and protected by click-time recheck.

## Current State

- Fixed Enrollware classes are hard occupancy and the current public schedule source.
- `data/sessions_current.json` contains 255 current sessions from the Class Report ingest.
- `docs/data/schedule_future.json` contains 249 future public schedule sessions.
- Current listed public schedule range: `2026-06-22T08:30:00-04:00` through `2026-08-14T12:45:00-04:00`.
- Amy sessions found in the Class Report ingest: 10.
- Brian sessions found in the Class Report ingest: 223.
- Dynamic public sellable offers currently kept: 0.
- Schedule seeds currently selected: 0.
- Appointment URL previews currently generated: 0.

The current dynamic pipeline is therefore not ready to replace fixed public classes. It can run as future-fill/shadow intelligence, but it should not become the only customer-facing schedule source yet.

## Operating Principle

Fixed classes cover the known schedule. Dynamic seed/stack scheduling fills future openings only after fixed classes taper off and only where the path is reviewed and reversible.

The scheduler should answer: given availability, course rules, instructor qualification, resource/container support, and existing occupancy, which classes can honestly be offered?

## Handoff Date Concept

A handoff date is the first date after which a specific course, location, or instructor path may use dynamic seeds as the primary source of new public options.

The handoff date should not be global at first. It should be scoped by:

- course family
- location/resource
- instructor
- appointment container coverage
- registration URL support
- click-time recheck readiness

Recommended default: no dynamic handoff date is active until a path has at least one reviewed, URL-capable seed and a rollback path.

## Per-Course Handoff Dates

| Course family | Fixed sessions currently listed | Last listed fixed start | Handoff rule |
|---|---:|---|---|
| BLS | 150 | 2026-08-14T12:45:00-04:00 | Keep fixed classes until this family has reviewed dynamic seeds and URL-capable registration path. |
| Heartsaver | 71 | 2026-07-31T17:30:00-04:00 | Keep fixed classes until this family has reviewed dynamic seeds and URL-capable registration path. |
| ACLS | 22 | 2026-07-29T08:30:00-04:00 | Keep fixed classes until this family has reviewed dynamic seeds and URL-capable registration path. |
| PALS | 4 | 2026-06-26T14:00:00-04:00 | Keep fixed classes until this family has reviewed dynamic seeds and URL-capable registration path. |
| aha_pals_instructor_renewal | 1 | 2026-07-01T00:00:00-04:00 | Keep fixed classes until this family has reviewed dynamic seeds and URL-capable registration path. |
| HSI | 1 | 2026-08-14T12:45:00-04:00 | Keep fixed classes until this family has reviewed dynamic seeds and URL-capable registration path. |

Per-course handoff should be conservative:

- BLS and Heartsaver can be first candidates because they are high-volume and simpler operationally.
- ACLS and PALS should remain fixed or protected-pilot until instructor/resource/format rules are verified.
- HSI, ARC, USCG, and uncommon courses should stay manual/fixed until course-specific registration and container behavior is confirmed.

## Per-Location Handoff Rules

| Location/resource shown in current schedule | Fixed sessions currently listed | Last listed fixed start | Handoff rule |
|---|---:|---|---|
| :: Wilmington; Shipyard Blvd - B | 239 | 2026-08-14T12:45:00-04:00 | Treat as hard occupancy; dynamic public use requires container/resource confirmation. |
| :: Wilmington; Shipyard Blvd - A | 10 | 2026-06-26T14:00:00-04:00 | Treat as hard occupancy; dynamic public use requires container/resource confirmation. |

Location rules:

- Shipyard should remain one customer-facing public location.
- Shipyard A/B/C should be internal resources for conflict checks, not separate public locations.
- Dynamic public offers require a confirmed active appointment container for the instructor/location/date path.
- Off-site, private, TBD, or customer locations should not become public dynamic options without explicit policy.

## Confirmed Appointment Containers

| Container ID | Instructor | Location | Valid dates | Status |
|---|---|---|---|---|
| shipyard_brian_continuous_20260621_20270430 | Brian | NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office | 2026-06-21 to 2027-04-30 | active |

Current confirmed-container policy is enabled: `True`.

Current hidden container reasons:

```json
{
  "missing_container_for_instructor": 465,
  "location_mismatch": 229
}
```

This means the dynamic pipeline is correctly refusing to advance offers that cannot be tied to a known active appointment container.

## Per-Instructor Pilot Rules

### Brian

Brian + Shipyard confirmed-container-only mode is the safest first limited live path.

Rules:

- Only publish dynamic seeds that match Brian, Shipyard canonical public location, and the active confirmed appointment container.
- Existing fixed Enrollware classes remain hard occupancy.
- Do not infer off-site Brian containers.
- Do not infer Shipyard A/B/C as separate appointment containers.
- If no Brian + Shipyard live availability aligns with the confirmed container, publish zero dynamic seeds.

### Amy

Amy remains protected pilot.

Rules:

- Amy existing Enrollware sessions are hard occupancy.
- Amy availability may create internal preview offers, not broad public dynamic scheduling.
- Amy ACLS/PALS public seeds should only be promoted after confirmed container coverage and reviewed pilot policy.
- Amy HeartCode/skills stack-fill candidates may be tracked separately, but should not be public primary seeds until a compatible advanced class is confirmed/books.
- Current Amy stack-fill candidates found: 66.

### Other Instructors

Other instructors should remain inactive, manual, subcontractor, or preview-only unless Brian explicitly approves:

- assignment mode
- availability source
- dynamic offer eligibility
- appointment container coverage
- course qualifications

## What Happens When Fixed Classes Run Out

When fixed Enrollware classes run out for a family/location/instructor path:

1. Keep the public page from going empty by showing a contact/help fallback if no reviewed dynamic seeds exist.
2. Use shadow/internal-preview dynamic output to identify replacement seeds.
3. Publish only seeds that are container-backed and pass live recheck.
4. Keep manual fixed-class creation available as a fallback.
5. Do not remove the fixed schedule source until the dynamic path has demonstrated continuity.

If dynamic seeds are not ready by the handoff window, the operational answer is to add/extend fixed Enrollware classes, not to publish unverified dynamic options.

## Required Before Deleting Or Stopping Fixed Enrollware Classes

Do not delete, stop, or let fixed classes expire as the only source of public options until all of this is true for the target path:

- Current Class Report has been ingested.
- `data/sessions_current.json` represents existing occupancy.
- Live availability snapshot is current.
- Dynamic offer generation uses live availability first and occupancy blocks correctly.
- Public sellable filtering keeps nonzero reviewed offers for the target path.
- Schedule seed selection produces intentional seeds.
- Deterministic appointment URL preview succeeds for intended seeds.
- Click-time Worker recheck is available and tested behind a flag.
- Customer fallback copy exists for unavailable or expired seeds.
- Admin can quickly disable dynamic offers and return to fixed schedule only.

## Transition Modes

### 1. Shadow Mode

Dynamic runs, writes audit files, and is not public.

Use when:

- validating course catalog, People policy, availability snapshots, occupancy, and appointment containers
- comparing dynamic candidates against fixed Enrollware schedule
- identifying missing containers or mismatched locations

Exit criteria:

- reports are stable
- no surprise public paths
- known blockers are documented

### 2. Internal Preview Mode

Admin can review dynamic seeds, but customers still see the fixed schedule.

Use when:

- Brian wants to approve seed choices
- Amy protected pilot candidates need review
- stack-fill candidates need operational validation

Exit criteria:

- reviewed seeds are intentional
- blocked reasons are explainable
- no seed depends on guessed container/location behavior

### 3. Limited Live Mode

Only Brian + Shipyard confirmed-container-backed seeds may become public.

Use when:

- live availability produces Brian + Shipyard offers
- deterministic appointment URL preview succeeds
- click-time recheck is ready or the rollout is still behind a private/internal flag

Exit criteria:

- customers can safely reach correct Enrollware registration pages
- fallback messaging works
- fixed schedule remains available as backup

### 4. Expanded Pilot

Amy and other containers can be added only after confirmation.

Use when:

- Amy container support is confirmed
- Amy advanced-course rules are approved
- HeartCode stack-fill logic is intentionally enabled or remains internal only
- other instructor assignment modes and containers are reviewed

Exit criteria:

- each pilot instructor/location/course path has explicit policy and rollback

### 5. Full Dynamic Mode

Dynamic seeds/stack scheduling becomes the normal source of public options.

Use only after:

- enough coverage exists across courses, instructors, locations, and containers
- Worker recheck is live and monitored
- Enrollware remains the roster/enrollment endpoint
- manual/fixed-class fallback remains available

## Rollback Plan

Rollback should be simple and operational, not architectural:

1. Disable dynamic public flag or route.
2. Hide dynamic buttons/seeds.
3. Continue serving fixed Enrollware schedule data.
4. Keep Class Report ingestion running so occupancy remains accurate.
5. Manually add fixed Enrollware classes for urgent schedule gaps.
6. Review audit files before re-enabling dynamic output.

## Minimum Go-Live Checklist

- Fixed Enrollware classes remain available until replacement dynamic seeds are verified.
- Class Report ingestion is current.
- Live calendar snapshot is current.
- Existing occupancy blocks dynamic offers.
- Confirmed active appointment container exists for each live instructor/location path.
- URL preview succeeds for each intended live seed.
- Worker click-time recheck is available before broad public wiring.
- Customer fallback exists if a seed disappears.
- Brian manually approves the first live seed set.

## Risks If Fixed Classes Are Deleted Too Early

- Public schedule vacuum if dynamic seeds remain filtered to zero.
- Customers cannot self-select dates if no confirmed-container-backed seed is public.
- Amy or other instructor availability could be exposed without registration URL support.
- Existing class occupancy could stop blocking offers if the Class Report pipeline is not current.
- Manual support burden increases because the site may show too few options or no options.
- Recovery may require emergency fixed class creation.

## Safest Next Operational Step

Keep fixed Enrollware classes live and continue running shadow/internal-preview dynamic scheduling. The next practical unlock is confirmed appointment-container coverage that allows at least Brian + Shipyard dynamic seeds to survive filtering and produce deterministic appointment URL previews.
