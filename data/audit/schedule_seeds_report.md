# Schedule Seeds Preview Report

This is a read-only seed strategy preview. Seeds are stack seeds, not a final public menu. No public pages, Enrollware calls, appointments, appointment URLs, Worker settings, or docs output were changed.

## Summary

- Input offers read: 83
- Appointment-container filter enabled: True
- Appointment-container-backed offers kept: 83
- Seeds selected: 5
- Amy advanced-course violations removed: 0
- Amy mode: protected_pilot
- Amy stack-fill candidates found: 48
- Seeds by date: {'2026-06-21': 1, '2026-06-22': 2, '2026-06-23': 1, '2026-07-04': 1}
- Seeds by family: {'BLS': 4, 'Heartsaver': 1}
- Seeds by start minute: {'00': 5}
- Quarter-hour seeds selected: 0

## Missing Inputs

- None

## Offers Hidden By Strategy Reason

- `scheduler_consumption_window_overlap`: 32
- `family_mix_target_already_met`: 27
- `same_start_time_already_seeded`: 19
- `optional_mix_not_available`: 8

## Amy Protected Pilot Hidden By Reason

- None

## Offers Hidden By Appointment Container Reason

- None

## Mix Goal Status By Date

### 2026-06-21

| Family | Target | Selected | Required | Met | Available After Hard Rules |
| --- | ---: | ---: | --- | --- | ---: |
| ACLS | 1 | 0 | False | True | 0 |
| BLS | 1 | 1 | True | True | 10 |
| Heartsaver | 1 | 0 | True | False | 14 |
| PALS | 1 | 0 | False | True | 0 |

### 2026-06-22

| Family | Target | Selected | Required | Met | Available After Hard Rules |
| --- | ---: | ---: | --- | --- | ---: |
| ACLS | 1 | 0 | False | True | 0 |
| BLS | 1 | 1 | True | True | 7 |
| Heartsaver | 1 | 1 | True | True | 17 |
| PALS | 1 | 0 | False | True | 0 |

### 2026-06-23

| Family | Target | Selected | Required | Met | Available After Hard Rules |
| --- | ---: | ---: | --- | --- | ---: |
| ACLS | 1 | 0 | False | True | 0 |
| BLS | 1 | 1 | True | True | 2 |
| Heartsaver | 1 | 0 | True | False | 9 |
| PALS | 1 | 0 | False | True | 0 |

### 2026-07-04

| Family | Target | Selected | Required | Met | Available After Hard Rules |
| --- | ---: | ---: | --- | --- | ---: |
| ACLS | 1 | 0 | False | True | 0 |
| BLS | 1 | 1 | True | True | 10 |
| Heartsaver | 1 | 0 | True | False | 14 |
| PALS | 1 | 0 | False | True | 0 |


## Examples By Date

### 2026-06-21

| Time | Course | Family | Instructor | Source Offer |
| --- | --- | --- | --- | --- |
| 17:00-19:00 | AHA BLS Provider | BLS | Brian Ennis | `offer-209806-instructor_24057895173-20260621-1700` |

### 2026-06-22

| Time | Course | Family | Instructor | Source Offer |
| --- | --- | --- | --- | --- |
| 06:00-07:00 | AHA HeartCode BLS | BLS | Brian Ennis | `offer-210549-instructor_24057895173-20260622-0600` |
| 12:00-15:00 | AHA Heartsaver First Aid CPR AED | Heartsaver | Brian Ennis | `offer-209809-instructor_24057895173-20260622-1200` |

### 2026-06-23

| Time | Course | Family | Instructor | Source Offer |
| --- | --- | --- | --- | --- |
| 08:00-09:00 | AHA HeartCode BLS | BLS | Brian Ennis | `offer-210549-instructor_24057895173-20260623-0800` |

### 2026-07-04

| Time | Course | Family | Instructor | Source Offer |
| --- | --- | --- | --- | --- |
| 12:00-14:00 | AHA BLS Provider | BLS | Brian Ennis | `offer-209806-instructor_24057895173-20260704-1200` |


## Quarter-Hour Stack Fit Notes

- No `:15` or `:45` seeds were selected in this run. They remain allowed and can win when they create a better stack.
## Next Step

- Build a deterministic appointment URL preview from these seeds without creating appointments or changing public pages.
