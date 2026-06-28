# Schedule Seeds Preview Report

This is a read-only seed strategy preview. Seeds are stack seeds, not a final public menu. No public pages, Enrollware calls, appointments, appointment URLs, Worker settings, or docs output were changed.

## Summary

- Input offers read: 14
- Appointment-container filter enabled: True
- Appointment-container-backed offers kept: 14
- Seeds selected: 1
- Amy advanced-course violations removed: 0
- Amy mode: protected_pilot
- Amy stack-fill candidates found: 48
- Seeds by date: {'2026-07-04': 1}
- Seeds by family: {'Heartsaver': 1}
- Seeds by start minute: {'30': 1}
- Quarter-hour seeds selected: 0

## Missing Inputs

- None

## Offers Hidden By Strategy Reason

- `family_mix_target_already_met`: 10
- `optional_mix_not_available`: 2
- `scheduler_consumption_window_overlap`: 2
- `required_mix_not_available`: 1
- `same_start_time_already_seeded`: 1

## Amy Protected Pilot Hidden By Reason

- None

## Offers Hidden By Appointment Container Reason

- None

## Mix Goal Status By Date

### 2026-07-04

| Family | Target | Selected | Required | Met | Available After Hard Rules |
| --- | ---: | ---: | --- | --- | ---: |
| ACLS | 1 | 0 | False | True | 0 |
| BLS | 1 | 0 | True | False | 0 |
| HSI | 1 | 0 | False | False | 3 |
| Heartsaver | 1 | 1 | True | True | 11 |
| PALS | 1 | 0 | False | True | 0 |


## Examples By Date

### 2026-07-04

| Time | Course | Family | Instructor | Source Offer |
| --- | --- | --- | --- | --- |
| 14:30-15:15 | AHA Heartsaver First Aid CPR AED - Blended | Heartsaver | Brian Ennis | `offer-329495-instructor_24057895173-20260704-1430` |


## Quarter-Hour Stack Fit Notes

- No `:15` or `:45` seeds were selected in this run. They remain allowed and can win when they create a better stack.
## Next Step

- Build a deterministic appointment URL preview from these seeds without creating appointments or changing public pages.
