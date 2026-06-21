# Schedule Seeds Preview Report

This is a read-only seed strategy preview. Seeds are stack seeds, not a final public menu. No public pages, Enrollware calls, appointments, appointment URLs, Worker settings, or docs output were changed.

## Summary

- Input offers read: 11
- Appointment-container filter enabled: True
- Appointment-container-backed offers kept: 11
- Seeds selected: 3
- Amy advanced-course violations removed: 0
- Amy mode: protected_pilot
- Amy stack-fill candidates found: 48
- Seeds by date: {'2026-06-22': 1, '2026-06-23': 1, '2026-07-04': 1}
- Seeds by family: {'HSI': 3}
- Seeds by start minute: {'00': 3}
- Quarter-hour seeds selected: 0

## Missing Inputs

- None

## Offers Hidden By Strategy Reason

- `family_mix_target_already_met`: 8
- `required_mix_not_available`: 6
- `optional_mix_not_available`: 6

## Amy Protected Pilot Hidden By Reason

- None

## Offers Hidden By Appointment Container Reason

- None

## Mix Goal Status By Date

### 2026-06-22

| Family | Target | Selected | Required | Met | Available After Hard Rules |
| --- | ---: | ---: | --- | --- | ---: |
| ACLS | 1 | 0 | False | True | 0 |
| BLS | 1 | 0 | True | False | 0 |
| HSI | 1 | 1 | False | True | 4 |
| Heartsaver | 1 | 0 | True | False | 0 |
| PALS | 1 | 0 | False | True | 0 |

### 2026-06-23

| Family | Target | Selected | Required | Met | Available After Hard Rules |
| --- | ---: | ---: | --- | --- | ---: |
| ACLS | 1 | 0 | False | True | 0 |
| BLS | 1 | 0 | True | False | 0 |
| HSI | 1 | 1 | False | True | 3 |
| Heartsaver | 1 | 0 | True | False | 0 |
| PALS | 1 | 0 | False | True | 0 |

### 2026-07-04

| Family | Target | Selected | Required | Met | Available After Hard Rules |
| --- | ---: | ---: | --- | --- | ---: |
| ACLS | 1 | 0 | False | True | 0 |
| BLS | 1 | 0 | True | False | 0 |
| HSI | 1 | 1 | False | True | 4 |
| Heartsaver | 1 | 0 | True | False | 0 |
| PALS | 1 | 0 | False | True | 0 |


## Examples By Date

### 2026-06-22

| Time | Course | Family | Instructor | Source Offer |
| --- | --- | --- | --- | --- |
| 06:00-06:45 | HSI BLS and Adult First Aid | Blended Learning | HSI | Brian Ennis | `offer-445670-instructor_24057895173-20260622-0600` |

### 2026-06-23

| Time | Course | Family | Instructor | Source Offer |
| --- | --- | --- | --- | --- |
| 08:00-08:45 | HSI BLS and Adult First Aid | Blended Learning | HSI | Brian Ennis | `offer-445670-instructor_24057895173-20260623-0800` |

### 2026-07-04

| Time | Course | Family | Instructor | Source Offer |
| --- | --- | --- | --- | --- |
| 12:00-12:45 | HSI BLS and Adult First Aid | Blended Learning | HSI | Brian Ennis | `offer-445670-instructor_24057895173-20260704-1200` |


## Quarter-Hour Stack Fit Notes

- No `:15` or `:45` seeds were selected in this run. They remain allowed and can win when they create a better stack.
## Next Step

- Build a deterministic appointment URL preview from these seeds without creating appointments or changing public pages.
