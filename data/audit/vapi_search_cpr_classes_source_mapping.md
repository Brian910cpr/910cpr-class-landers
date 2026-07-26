# Vapi Search CPR Classes Source Mapping

Endpoint: `GET /voice/search-cpr-classes`

Worker source: generated block-selector availability snapshots.

Production source URLs:

- `https://www.910cpr.com/data/block-selector-availability/bls.json`
- `https://www.910cpr.com/data/block-selector-availability/acls.json`
- `https://www.910cpr.com/data/block-selector-availability/pals.json`
- `https://www.910cpr.com/data/block-selector-availability/heartsaver.json`
- `https://www.910cpr.com/data/block-selector-availability/arc.json`
- `https://www.910cpr.com/data/block-selector-availability/hsi.json`

Local source files:

- `docs/data/block-selector-availability/bls.json`
- `docs/data/block-selector-availability/acls.json`
- `docs/data/block-selector-availability/pals.json`
- `docs/data/block-selector-availability/heartsaver.json`
- `docs/data/block-selector-availability/arc.json`
- `docs/data/block-selector-availability/hsi.json`

## Source Structure

Each file has:

- `schemaVersion`
- `generatedAt`
- `pageKey`
- `publicPage`
- `sourceArtifacts`
- `authority`
- `counts`
- `liveAvailabilityGuard`
- `dates[]`

Offer rows are nested at:

`dates[] -> startTimes[] -> courses[]`

The Worker only adapts rows where `course.publicSelectable === true`. It does not re-run scheduling, cap, location, Course Master, or sellability rules.

## Field Mapping

| Vapi field | Source field | Status |
| --- | --- | --- |
| `generated_at` | newest source `generatedAt` | Present |
| `timezone` | fixed project timezone | Safely derived as `America/New_York` |
| `offer_id` | deterministic composite | Safely derived from program, date, start time, location, course ID, and source offer identity |
| `course_id` | `course.courseId` | Present |
| `appointment_day_id` | `course.appointmentDayId` | Present for appointment rows, `null` for seated Enrollware rows |
| `program` | `course.courseFamily` | Present |
| `course_type` | `course.courseName` | Safely derived for BLS Initial/Renewal/HeartCode and ACLS/PALS Initial; otherwise `null` |
| `delivery_method` | `course.deliveryMode` plus `course.courseName` | Safely normalized to `In Person`, `HeartCode`, or `Blended` |
| `date` | `course.date` | Present |
| `start_time` | `course.startTime` | Present |
| `display_time` | `course.displayStartTime` | Present; derived if missing |
| `display_date` | `course.displayDate` | Present; derived if missing |
| `location` | `course.location` | Present; normalized from public display location |
| `seats_available` | no consistent source field | Unavailable, returned as `null` unless source later emits it |
| `price` | no consistent source field | Unavailable, returned as `null` unless source later emits it |
| `currency` | project default | Safely derived as `USD` |
| `registration_status` | `sourceAvailabilityBlock.registrationStatus` or public-selectable status | Present for seated rows; safely derived as `open` for public-selectable appointment rows |

## Availability Snapshot Differences

- BLS, Heartsaver, ARC, HSI, and Family/USCG-style snapshots include generated appointment rows backed by `appointmentDayId`, `startTime`, and `courseId`.
- ACLS and PALS snapshots currently include seated Enrollware rows from `docs/data/schedule_future.json`; those rows use `registrationUrl` and have no `appointmentDayId`.
- `family_cpr.json` and `uscg_first_aid_cpr_aed.json` exist locally, but this first Vapi implementation uses the six requested program files only: BLS, ACLS, PALS, Heartsaver, ARC, and HSI.
- Price and live seat availability are not present in the generated block-selector snapshots or current `docs/data/schedule_future.json`.

## Staleness

The endpoint reads generated JSON snapshots published with the static site. Maximum practical staleness is the time since the most recent successful resolver/build plus GitHub Pages/public-site deployment and CDN propagation.

Current local snapshot `generatedAt`: `2026-07-24T23:34:58.664477`.

This is not zero-staleness live resolver execution; it is a generated snapshot adapter by design.

## Safety

The Worker rejects:

- rows where `publicSelectable !== true`
- appointment rows missing the full tuple: `appointmentDayId`, `startTime`, and `courseId`
- rows with invalid `YYYY-MM-DD` dates or invalid `HH:MM` start times
- rows with non-open `sourceAvailabilityBlock.registrationStatus`

The endpoint never returns `registration_url` or `appointmentUrl`.
