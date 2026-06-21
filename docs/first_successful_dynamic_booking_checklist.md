# First Successful Dynamic Booking Checklist

Status: read-only operating checklist. This checklist does not modify public pages, deploy, enable Worker routes, call Enrollware, create appointments, change appointment URLs, or commit.

## Goal

Prove one real dynamic booking chain end to end without pretending the system is live before each dependency is verified.

Success means:

Availability + course rules + People policy + occupancy + confirmed appointment container + seed strategy + registration proof + hot-sync + Class Report confirmation all line up for one real class.

## Status Runner

Run:

```powershell
python -m scripts.check_first_dynamic_booking_status
```

Outputs:

- `data/audit/first_dynamic_booking_status.json`
- `data/audit/first_dynamic_booking_status_report.md`

The runner reads existing audit outputs only and stops conceptually at the first failing link. It does not call Enrollware or create appointments.

## Success Chain

### 1. Live Calendar Availability Produces Brian + Shipyard Block

Pass condition:

- `data/audit/live_availability_snapshot_preview.json` contains at least one available Brian Ennis block at the canonical Shipyard location.

Current blocker if failing:

- Brian has no Shipyard availability block in the local live snapshot, or location/instructor normalization does not match.

### 2. Dynamic Offers Are Generated From Live Availability

Pass condition:

- `scripts.generate_dynamic_offers` uses `live_availability_snapshot`.
- At least one dynamic offer is generated.

Current blocker if failing:

- Live snapshot missing/invalid, or dynamic offer generation falls back to legacy availability.

### 3. Confirmed-Container Public Filter Keeps At Least One Offer

Pass condition:

- `data/audit/public_sellable_offers_preview.json` contains at least one offer after confirmed-container filtering.

Current blocker if failing:

- Missing confirmed container for instructor.
- Location mismatch.
- Date outside container range.
- AppointmentDayId outside range.

### 4. Seed Selection Selects At Least One Seed

Pass condition:

- `data/audit/schedule_seeds_preview.json` contains at least one selected seed.

Current blocker if failing:

- No public sellable offers exist.
- Seed strategy hides every offer.
- Amy protected pilot or mix rules intentionally prevent selection.

### 5. Deterministic Appointment URL Preview Generates At Least One URL

Pass condition:

- `data/audit/seed_appointment_url_preview.json` contains at least one preview URL.

Current blocker if failing:

- No selected seed exists.
- Seed cannot match an active appointment container.
- appointmentDayId calculation is outside trusted range.

### 6. Internal/Admin Preview Shows Customer-Facing Button

Pass condition:

- An internal/admin preview displays the selected seed with the button that would be customer-facing later.
- The button is review-only or disabled until explicitly approved.

Current blocker if failing:

- No internal preview surface exists yet.

### 7. Manual Click/Registration Creates Class In Enrollware

Pass condition:

- Brian/admin manually clicks the reviewed path and confirms the intended Enrollware class/registration exists.

Current blocker if failing:

- This requires manual proof and cannot be inferred from local audit files.

### 8. Routine Public Enrollware Scrape/Hot-Sync Sees Created Class

Pass condition:

- Existing read-only public scrape/hot-sync sees the created class.

Current blocker if failing:

- No created test class exists yet, or hot-sync does not detect it.

### 9. Lander Treats Created Class As Real Occupancy

Pass condition:

- The created class appears in `data/sessions_current.json` or the appropriate schedule snapshot.
- Dynamic offer generation recalculates around it and blocks overlapping options.

Current blocker if failing:

- The class has not entered local occupancy, or overlap rejection is not visible.

### 10. Class Report Later Confirms Roster Details

Pass condition:

- Updated `Class Report.xlsx` includes the created class and roster details.
- `scripts.build_sessions_current` imports it cleanly.

Current blocker if failing:

- Class Report has not been refreshed after the test booking.

## Current Expected Status

The current expected first failing link is the confirmed-container public filter. Live availability and dynamic offers exist, but confirmed-container policy currently keeps zero public sellable offers.

The next single action should be to add or align a Brian + Shipyard availability/container-backed path so at least one offer survives confirmed-container filtering.
