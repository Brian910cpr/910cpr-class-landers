# ChatGPT Bundle

## Completed task

Rendered the validated auto-public appointment seed offer inside the normal BLS Upcoming dates list instead of a separate appointment section.

## Key implementation

Updated `scripts/build_slug_hubs.py` so appointment seed offers are copied into the same `upcoming_sessions` collection as real Enrollware classes and requestable offers. Appointment seed rows are marked with `_appointment_seed_offer`, sorted by `start_datetime`, and rendered through the existing card flow.

The appointment-specific standalone section is no longer appended to the BLS hub output.

## Rendered example

```html
<article class="slug-pill slug-appointment-seed-offer" data-offer-source="auto_public_appointment_seed" data-public-display-item-type="appointment_seed_offer" data-real-enrollware-session="false" data-standalone-class-lander-allowed="false" data-class-lander-created="false" data-public-schedule-row-created="false" data-seed-id="seed_7457baba994578af" data-course-key="aha_bls_initial" data-appointment-day-id="260714" data-course-id="209806" data-start="2026-08-04T13:00:00-04:00" data-end="2026-08-04T16:00:00-04:00">
```

```html
<a class="button small primary" href="https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260714" data-offer-source="auto_public_appointment_seed" data-public-display-item-type="appointment_seed_offer" data-real-enrollware-session="false" data-standalone-class-lander-allowed="false" data-class-lander-created="false" data-public-schedule-row-created="false" data-seed-id="seed_7457baba994578af" data-course-key="aha_bls_initial" data-appointment-day-id="260714" data-course-id="209806" data-start="2026-08-04T13:00:00-04:00" data-end="2026-08-04T16:00:00-04:00">Book Seat</a>
```

## Validation facts

- Separate appointment section count in `docs/bls.html`: 0
- `Available appointment slot` text count: 0
- Appointment seed card count: 1
- Known seed occurrences: 2
- Appointment URL occurrences: 1
- Needs-review/blocked seed marker occurrences: 0
- `public_schedule.json`: unchanged
- `live-schedule_future.json`: unchanged
- `docs/data/*`: unchanged
- `docs/classes/*`: unchanged

## Preflight note

Safety preflight still reports `failed_validation` because the public BLS page is intentionally dirty after the render and stale offer review blockers remain. The hub render validation itself passed with zero violations.

## Recommended commit

```powershell
git add scripts/build_slug_hubs.py docs/bls.html ops/handoff/latest_codex_report.md ops/handoff/latest_validation_run.txt ops/handoff/latest_git_status.txt ops/handoff/latest_chatgpt_bundle.md
git commit -m "Merge appointment seeds into BLS upcoming dates"
```
