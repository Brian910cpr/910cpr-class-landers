# Amy Scheduling Policy Audit

Updated: 2026-06-28T10:35:00

## Review Fix Summary

- Brian example dates are treated as illustrative only; Amy calendar source is authoritative for dated windows.
- `instructor_4180671442` is now explicitly included in policy identity matching because generated dynamic candidates use that ID.
- Amy candidates are resolved from `dynamic_offers_preview.json` with start/end, course, source window, instructor, location, scheduler consumption, and occupancy overlap checks.
- Standing policy is separated from calendar-derived dated windows.
- Existing public non-dynamic Amy records are separated from public dynamic offers.
- Remote `origin/main` movement from `f8db04` to `0a2e0d` is documented for review before any future merge/deploy.

## Date/Source Verification

- Source calendar key: `amy_availability`
- Calendar ID: `c_94724071aa31a0063fbc48be80fdc73d76e604cad5043ff088156eb97e50be97@group.calendar.google.com`
- Snapshot file: `data/runtime/calendar_snapshots/amy_availability.json`
- Snapshot generated at: `2026-06-19T17:21:21.505124-04:00`

### 2026-06-22

- Grouped window: `2026-06-22T13:00:00-04:00` to `2026-06-22T18:00:00-04:00`
- Preferred anchor start: `2026-06-22T14:00:00-04:00`
- Grouping rule: `soft_hard_event_pairing`
- Inconsistencies: `none`
- Source events:
  - `23rccrjmrdj4p77iko7r2manhn@google.com` title=`Soft` raw=`20260622T170000Z`-`20260622T180000Z` utc=`2026-06-22T17:00:00+00:00`-`2026-06-22T18:00:00+00:00` local=`2026-06-22T13:00:00-04:00`-`2026-06-22T14:00:00-04:00`
  - `7ocuqjieb677urrtttnnhrgbu1@google.com` title=`Hard` raw=`20260622T180000Z`-`20260622T220000Z` utc=`2026-06-22T18:00:00+00:00`-`2026-06-22T22:00:00+00:00` local=`2026-06-22T14:00:00-04:00`-`2026-06-22T18:00:00-04:00`

### 2026-06-23

- Grouped window: `2026-06-23T13:00:00-04:00` to `2026-06-23T18:00:00-04:00`
- Preferred anchor start: `2026-06-23T14:00:00-04:00`
- Grouping rule: `soft_hard_event_pairing`
- Inconsistencies: `none`
- Source events:
  - `2nnr8jg3pka88l9ge2om43aa49@google.com` title=`Soft` raw=`20260623T170000Z`-`20260623T180000Z` utc=`2026-06-23T17:00:00+00:00`-`2026-06-23T18:00:00+00:00` local=`2026-06-23T13:00:00-04:00`-`2026-06-23T14:00:00-04:00`
  - `26hucabntrqk2qhdnngaq2defb@google.com` title=`Hard` raw=`20260623T180000Z`-`20260623T220000Z` utc=`2026-06-23T18:00:00+00:00`-`2026-06-23T22:00:00+00:00` local=`2026-06-23T14:00:00-04:00`-`2026-06-23T18:00:00-04:00`

### 2026-06-26

- Grouped window: `2026-06-26T13:00:00-04:00` to `2026-06-26T18:00:00-04:00`
- Preferred anchor start: `2026-06-26T14:00:00-04:00`
- Grouping rule: `soft_hard_event_pairing`
- Inconsistencies: `none`
- Source events:
  - `50158s5pctungp0irmfpod7spk@google.com` title=`Soft` raw=`20260626T170000Z`-`20260626T180000Z` utc=`2026-06-26T17:00:00+00:00`-`2026-06-26T18:00:00+00:00` local=`2026-06-26T13:00:00-04:00`-`2026-06-26T14:00:00-04:00`
  - `5rqq5vfpia8up7mejs56nc4p9g@google.com` title=`Hard` raw=`20260626T180000Z`-`20260626T220000Z` utc=`2026-06-26T18:00:00+00:00`-`2026-06-26T22:00:00+00:00` local=`2026-06-26T14:00:00-04:00`-`2026-06-26T18:00:00-04:00`

## Amy Identity Mapping

- `instructor_4180671442` / Amy Arnold: authoritative People catalog roster ID and generated dynamic candidate ID.
- `amy` / Amy: scheduler/calendar config key.
- `a___arnold` / A. Arnold: schedule-derived display alias from public schedule snapshots.

Policy matching must include all three IDs, especially `instructor_4180671442`, because Amy dynamic candidates use that ID.

## Resolved Amy Candidate Rows

Resolved candidate count: `300`

- `offer-209811-instructor_4180671442-20260623-1800` 2026-06-23T18:00:00-04:00 to 2026-06-23T19:30:00-04:00 course=`209811` `AHA ACLS HeartCode` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:00:00-04:00` to `2026-06-23T20:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-209811-instructor_4180671442-20260623-1815` 2026-06-23T18:15:00-04:00 to 2026-06-23T19:45:00-04:00 course=`209811` `AHA ACLS HeartCode` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:15:00-04:00` to `2026-06-23T20:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-209811-instructor_4180671442-20260623-1830` 2026-06-23T18:30:00-04:00 to 2026-06-23T20:00:00-04:00 course=`209811` `AHA ACLS HeartCode` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:30:00-04:00` to `2026-06-23T20:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-209811-instructor_4180671442-20260623-1845` 2026-06-23T18:45:00-04:00 to 2026-06-23T20:15:00-04:00 course=`209811` `AHA ACLS HeartCode` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:45:00-04:00` to `2026-06-23T21:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-209811-instructor_4180671442-20260623-1900` 2026-06-23T19:00:00-04:00 to 2026-06-23T20:30:00-04:00 course=`209811` `AHA ACLS HeartCode` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:00:00-04:00` to `2026-06-23T21:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-209811-instructor_4180671442-20260623-1915` 2026-06-23T19:15:00-04:00 to 2026-06-23T20:45:00-04:00 course=`209811` `AHA ACLS HeartCode` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:15:00-04:00` to `2026-06-23T21:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-209811-instructor_4180671442-20260623-1930` 2026-06-23T19:30:00-04:00 to 2026-06-23T21:00:00-04:00 course=`209811` `AHA ACLS HeartCode` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:30:00-04:00` to `2026-06-23T21:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-209811-instructor_4180671442-20260623-1945` 2026-06-23T19:45:00-04:00 to 2026-06-23T21:15:00-04:00 course=`209811` `AHA ACLS HeartCode` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:45:00-04:00` to `2026-06-23T22:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-209806-instructor_4180671442-20260623-1800` 2026-06-23T18:00:00-04:00 to 2026-06-23T20:00:00-04:00 course=`209806` `AHA BLS Provider` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:00:00-04:00` to `2026-06-23T20:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209806-instructor_4180671442-20260623-1815` 2026-06-23T18:15:00-04:00 to 2026-06-23T20:15:00-04:00 course=`209806` `AHA BLS Provider` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:15:00-04:00` to `2026-06-23T21:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209806-instructor_4180671442-20260623-1830` 2026-06-23T18:30:00-04:00 to 2026-06-23T20:30:00-04:00 course=`209806` `AHA BLS Provider` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:30:00-04:00` to `2026-06-23T21:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209806-instructor_4180671442-20260623-1845` 2026-06-23T18:45:00-04:00 to 2026-06-23T20:45:00-04:00 course=`209806` `AHA BLS Provider` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:45:00-04:00` to `2026-06-23T21:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209806-instructor_4180671442-20260623-1900` 2026-06-23T19:00:00-04:00 to 2026-06-23T21:00:00-04:00 course=`209806` `AHA BLS Provider` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:00:00-04:00` to `2026-06-23T21:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209806-instructor_4180671442-20260623-1915` 2026-06-23T19:15:00-04:00 to 2026-06-23T21:15:00-04:00 course=`209806` `AHA BLS Provider` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:15:00-04:00` to `2026-06-23T22:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-359474-instructor_4180671442-20260623-1800` 2026-06-23T18:00:00-04:00 to 2026-06-23T20:00:00-04:00 course=`359474` `AHA BLS Provider Renewal` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:00:00-04:00` to `2026-06-23T20:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-359474-instructor_4180671442-20260623-1815` 2026-06-23T18:15:00-04:00 to 2026-06-23T20:15:00-04:00 course=`359474` `AHA BLS Provider Renewal` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:15:00-04:00` to `2026-06-23T21:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-359474-instructor_4180671442-20260623-1830` 2026-06-23T18:30:00-04:00 to 2026-06-23T20:30:00-04:00 course=`359474` `AHA BLS Provider Renewal` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:30:00-04:00` to `2026-06-23T21:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-359474-instructor_4180671442-20260623-1845` 2026-06-23T18:45:00-04:00 to 2026-06-23T20:45:00-04:00 course=`359474` `AHA BLS Provider Renewal` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:45:00-04:00` to `2026-06-23T21:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-359474-instructor_4180671442-20260623-1900` 2026-06-23T19:00:00-04:00 to 2026-06-23T21:00:00-04:00 course=`359474` `AHA BLS Provider Renewal` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:00:00-04:00` to `2026-06-23T21:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-359474-instructor_4180671442-20260623-1915` 2026-06-23T19:15:00-04:00 to 2026-06-23T21:15:00-04:00 course=`359474` `AHA BLS Provider Renewal` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:15:00-04:00` to `2026-06-23T22:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-210549-instructor_4180671442-20260623-1800` 2026-06-23T18:00:00-04:00 to 2026-06-23T19:00:00-04:00 course=`210549` `AHA HeartCode BLS` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:00:00-04:00` to `2026-06-23T19:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-210549-instructor_4180671442-20260623-1815` 2026-06-23T18:15:00-04:00 to 2026-06-23T19:15:00-04:00 course=`210549` `AHA HeartCode BLS` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:15:00-04:00` to `2026-06-23T20:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-210549-instructor_4180671442-20260623-1830` 2026-06-23T18:30:00-04:00 to 2026-06-23T19:30:00-04:00 course=`210549` `AHA HeartCode BLS` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:30:00-04:00` to `2026-06-23T20:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-210549-instructor_4180671442-20260623-1845` 2026-06-23T18:45:00-04:00 to 2026-06-23T19:45:00-04:00 course=`210549` `AHA HeartCode BLS` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:45:00-04:00` to `2026-06-23T20:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-210549-instructor_4180671442-20260623-1900` 2026-06-23T19:00:00-04:00 to 2026-06-23T20:00:00-04:00 course=`210549` `AHA HeartCode BLS` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:00:00-04:00` to `2026-06-23T20:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-210549-instructor_4180671442-20260623-1915` 2026-06-23T19:15:00-04:00 to 2026-06-23T20:15:00-04:00 course=`210549` `AHA HeartCode BLS` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:15:00-04:00` to `2026-06-23T21:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-210549-instructor_4180671442-20260623-1930` 2026-06-23T19:30:00-04:00 to 2026-06-23T20:30:00-04:00 course=`210549` `AHA HeartCode BLS` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:30:00-04:00` to `2026-06-23T21:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-210549-instructor_4180671442-20260623-1945` 2026-06-23T19:45:00-04:00 to 2026-06-23T20:45:00-04:00 course=`210549` `AHA HeartCode BLS` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:45:00-04:00` to `2026-06-23T21:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-210549-instructor_4180671442-20260623-2000` 2026-06-23T20:00:00-04:00 to 2026-06-23T21:00:00-04:00 course=`210549` `AHA HeartCode BLS` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T20:00:00-04:00` to `2026-06-23T21:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-210549-instructor_4180671442-20260623-2015` 2026-06-23T20:15:00-04:00 to 2026-06-23T21:15:00-04:00 course=`210549` `AHA HeartCode BLS` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T20:15:00-04:00` to `2026-06-23T22:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-440431-instructor_4180671442-20260623-1800` 2026-06-23T18:00:00-04:00 to 2026-06-23T20:30:00-04:00 course=`440431` `BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing)` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:00:00-04:00` to `2026-06-23T21:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-440431-instructor_4180671442-20260623-1815` 2026-06-23T18:15:00-04:00 to 2026-06-23T20:45:00-04:00 course=`440431` `BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing)` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:15:00-04:00` to `2026-06-23T21:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-440431-instructor_4180671442-20260623-1830` 2026-06-23T18:30:00-04:00 to 2026-06-23T21:00:00-04:00 course=`440431` `BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing)` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:30:00-04:00` to `2026-06-23T21:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-440431-instructor_4180671442-20260623-1845` 2026-06-23T18:45:00-04:00 to 2026-06-23T21:15:00-04:00 course=`440431` `BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing)` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:45:00-04:00` to `2026-06-23T22:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-344085-instructor_4180671442-20260623-1800` 2026-06-23T18:00:00-04:00 to 2026-06-23T19:30:00-04:00 course=`344085` `AHA Heartsaver CPR AED` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:00:00-04:00` to `2026-06-23T20:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-344085-instructor_4180671442-20260623-1815` 2026-06-23T18:15:00-04:00 to 2026-06-23T19:45:00-04:00 course=`344085` `AHA Heartsaver CPR AED` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:15:00-04:00` to `2026-06-23T20:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-344085-instructor_4180671442-20260623-1830` 2026-06-23T18:30:00-04:00 to 2026-06-23T20:00:00-04:00 course=`344085` `AHA Heartsaver CPR AED` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:30:00-04:00` to `2026-06-23T20:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-344085-instructor_4180671442-20260623-1845` 2026-06-23T18:45:00-04:00 to 2026-06-23T20:15:00-04:00 course=`344085` `AHA Heartsaver CPR AED` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:45:00-04:00` to `2026-06-23T21:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-344085-instructor_4180671442-20260623-1900` 2026-06-23T19:00:00-04:00 to 2026-06-23T20:30:00-04:00 course=`344085` `AHA Heartsaver CPR AED` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:00:00-04:00` to `2026-06-23T21:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-344085-instructor_4180671442-20260623-1915` 2026-06-23T19:15:00-04:00 to 2026-06-23T20:45:00-04:00 course=`344085` `AHA Heartsaver CPR AED` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:15:00-04:00` to `2026-06-23T21:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-344085-instructor_4180671442-20260623-1930` 2026-06-23T19:30:00-04:00 to 2026-06-23T21:00:00-04:00 course=`344085` `AHA Heartsaver CPR AED` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:30:00-04:00` to `2026-06-23T21:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-344085-instructor_4180671442-20260623-1945` 2026-06-23T19:45:00-04:00 to 2026-06-23T21:15:00-04:00 course=`344085` `AHA Heartsaver CPR AED` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:45:00-04:00` to `2026-06-23T22:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209808-instructor_4180671442-20260623-1800` 2026-06-23T18:00:00-04:00 to 2026-06-23T18:45:00-04:00 course=`209808` `AHA Heartsaver CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:00:00-04:00` to `2026-06-23T19:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209808-instructor_4180671442-20260623-1815` 2026-06-23T18:15:00-04:00 to 2026-06-23T19:00:00-04:00 course=`209808` `AHA Heartsaver CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:15:00-04:00` to `2026-06-23T19:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209808-instructor_4180671442-20260623-1830` 2026-06-23T18:30:00-04:00 to 2026-06-23T19:15:00-04:00 course=`209808` `AHA Heartsaver CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:30:00-04:00` to `2026-06-23T20:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209808-instructor_4180671442-20260623-1845` 2026-06-23T18:45:00-04:00 to 2026-06-23T19:30:00-04:00 course=`209808` `AHA Heartsaver CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:45:00-04:00` to `2026-06-23T20:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209808-instructor_4180671442-20260623-1900` 2026-06-23T19:00:00-04:00 to 2026-06-23T19:45:00-04:00 course=`209808` `AHA Heartsaver CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:00:00-04:00` to `2026-06-23T20:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209808-instructor_4180671442-20260623-1915` 2026-06-23T19:15:00-04:00 to 2026-06-23T20:00:00-04:00 course=`209808` `AHA Heartsaver CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:15:00-04:00` to `2026-06-23T20:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209808-instructor_4180671442-20260623-1930` 2026-06-23T19:30:00-04:00 to 2026-06-23T20:15:00-04:00 course=`209808` `AHA Heartsaver CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:30:00-04:00` to `2026-06-23T21:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209808-instructor_4180671442-20260623-1945` 2026-06-23T19:45:00-04:00 to 2026-06-23T20:30:00-04:00 course=`209808` `AHA Heartsaver CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:45:00-04:00` to `2026-06-23T21:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209808-instructor_4180671442-20260623-2000` 2026-06-23T20:00:00-04:00 to 2026-06-23T20:45:00-04:00 course=`209808` `AHA Heartsaver CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T20:00:00-04:00` to `2026-06-23T21:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209808-instructor_4180671442-20260623-2015` 2026-06-23T20:15:00-04:00 to 2026-06-23T21:00:00-04:00 course=`209808` `AHA Heartsaver CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T20:15:00-04:00` to `2026-06-23T21:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209808-instructor_4180671442-20260623-2030` 2026-06-23T20:30:00-04:00 to 2026-06-23T21:15:00-04:00 course=`209808` `AHA Heartsaver CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T20:30:00-04:00` to `2026-06-23T22:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209809-instructor_4180671442-20260623-1800` 2026-06-23T18:00:00-04:00 to 2026-06-23T21:00:00-04:00 course=`209809` `AHA Heartsaver First Aid CPR AED` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:00:00-04:00` to `2026-06-23T21:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209809-instructor_4180671442-20260623-1815` 2026-06-23T18:15:00-04:00 to 2026-06-23T21:15:00-04:00 course=`209809` `AHA Heartsaver First Aid CPR AED` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:15:00-04:00` to `2026-06-23T22:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-329495-instructor_4180671442-20260623-1800` 2026-06-23T18:00:00-04:00 to 2026-06-23T18:45:00-04:00 course=`329495` `AHA Heartsaver First Aid CPR AED - Blended` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:00:00-04:00` to `2026-06-23T19:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-329495-instructor_4180671442-20260623-1815` 2026-06-23T18:15:00-04:00 to 2026-06-23T19:00:00-04:00 course=`329495` `AHA Heartsaver First Aid CPR AED - Blended` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:15:00-04:00` to `2026-06-23T19:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-329495-instructor_4180671442-20260623-1830` 2026-06-23T18:30:00-04:00 to 2026-06-23T19:15:00-04:00 course=`329495` `AHA Heartsaver First Aid CPR AED - Blended` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:30:00-04:00` to `2026-06-23T20:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-329495-instructor_4180671442-20260623-1845` 2026-06-23T18:45:00-04:00 to 2026-06-23T19:30:00-04:00 course=`329495` `AHA Heartsaver First Aid CPR AED - Blended` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:45:00-04:00` to `2026-06-23T20:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-329495-instructor_4180671442-20260623-1900` 2026-06-23T19:00:00-04:00 to 2026-06-23T19:45:00-04:00 course=`329495` `AHA Heartsaver First Aid CPR AED - Blended` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:00:00-04:00` to `2026-06-23T20:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-329495-instructor_4180671442-20260623-1915` 2026-06-23T19:15:00-04:00 to 2026-06-23T20:00:00-04:00 course=`329495` `AHA Heartsaver First Aid CPR AED - Blended` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:15:00-04:00` to `2026-06-23T20:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-329495-instructor_4180671442-20260623-1930` 2026-06-23T19:30:00-04:00 to 2026-06-23T20:15:00-04:00 course=`329495` `AHA Heartsaver First Aid CPR AED - Blended` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:30:00-04:00` to `2026-06-23T21:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-329495-instructor_4180671442-20260623-1945` 2026-06-23T19:45:00-04:00 to 2026-06-23T20:30:00-04:00 course=`329495` `AHA Heartsaver First Aid CPR AED - Blended` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:45:00-04:00` to `2026-06-23T21:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-329495-instructor_4180671442-20260623-2000` 2026-06-23T20:00:00-04:00 to 2026-06-23T20:45:00-04:00 course=`329495` `AHA Heartsaver First Aid CPR AED - Blended` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T20:00:00-04:00` to `2026-06-23T21:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-329495-instructor_4180671442-20260623-2015` 2026-06-23T20:15:00-04:00 to 2026-06-23T21:00:00-04:00 course=`329495` `AHA Heartsaver First Aid CPR AED - Blended` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T20:15:00-04:00` to `2026-06-23T21:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-329495-instructor_4180671442-20260623-2030` 2026-06-23T20:30:00-04:00 to 2026-06-23T21:15:00-04:00 course=`329495` `AHA Heartsaver First Aid CPR AED - Blended` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T20:30:00-04:00` to `2026-06-23T22:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- `offer-351632-instructor_4180671442-20260623-1800` 2026-06-23T18:00:00-04:00 to 2026-06-23T21:00:00-04:00 course=`351632` `AHA Heartsaver Pediatric First Aid / CPR / AED` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:00:00-04:00` to `2026-06-23T21:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-351632-instructor_4180671442-20260623-1815` 2026-06-23T18:15:00-04:00 to 2026-06-23T21:15:00-04:00 course=`351632` `AHA Heartsaver Pediatric First Aid / CPR / AED` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:15:00-04:00` to `2026-06-23T22:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-251545-instructor_4180671442-20260623-1800` 2026-06-23T18:00:00-04:00 to 2026-06-23T18:45:00-04:00 course=`251545` `AHA Heartsaver Pediatric First Aid CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:00:00-04:00` to `2026-06-23T19:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-251545-instructor_4180671442-20260623-1815` 2026-06-23T18:15:00-04:00 to 2026-06-23T19:00:00-04:00 course=`251545` `AHA Heartsaver Pediatric First Aid CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:15:00-04:00` to `2026-06-23T19:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-251545-instructor_4180671442-20260623-1830` 2026-06-23T18:30:00-04:00 to 2026-06-23T19:15:00-04:00 course=`251545` `AHA Heartsaver Pediatric First Aid CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:30:00-04:00` to `2026-06-23T20:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-251545-instructor_4180671442-20260623-1845` 2026-06-23T18:45:00-04:00 to 2026-06-23T19:30:00-04:00 course=`251545` `AHA Heartsaver Pediatric First Aid CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:45:00-04:00` to `2026-06-23T20:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-251545-instructor_4180671442-20260623-1900` 2026-06-23T19:00:00-04:00 to 2026-06-23T19:45:00-04:00 course=`251545` `AHA Heartsaver Pediatric First Aid CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:00:00-04:00` to `2026-06-23T20:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-251545-instructor_4180671442-20260623-1915` 2026-06-23T19:15:00-04:00 to 2026-06-23T20:00:00-04:00 course=`251545` `AHA Heartsaver Pediatric First Aid CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:15:00-04:00` to `2026-06-23T20:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-251545-instructor_4180671442-20260623-1930` 2026-06-23T19:30:00-04:00 to 2026-06-23T20:15:00-04:00 course=`251545` `AHA Heartsaver Pediatric First Aid CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:30:00-04:00` to `2026-06-23T21:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-251545-instructor_4180671442-20260623-1945` 2026-06-23T19:45:00-04:00 to 2026-06-23T20:30:00-04:00 course=`251545` `AHA Heartsaver Pediatric First Aid CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T19:45:00-04:00` to `2026-06-23T21:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-251545-instructor_4180671442-20260623-2000` 2026-06-23T20:00:00-04:00 to 2026-06-23T20:45:00-04:00 course=`251545` `AHA Heartsaver Pediatric First Aid CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T20:00:00-04:00` to `2026-06-23T21:30:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-251545-instructor_4180671442-20260623-2015` 2026-06-23T20:15:00-04:00 to 2026-06-23T21:00:00-04:00 course=`251545` `AHA Heartsaver Pediatric First Aid CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T20:15:00-04:00` to `2026-06-23T21:45:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-251545-instructor_4180671442-20260623-2030` 2026-06-23T20:30:00-04:00 to 2026-06-23T21:15:00-04:00 course=`251545` `AHA Heartsaver Pediatric First Aid CPR AED Online` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T20:30:00-04:00` to `2026-06-23T22:00:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window'] overlaps=0
- `offer-209812-instructor_4180671442-20260623-1800` 2026-06-23T18:00:00-04:00 to 2026-06-23T19:30:00-04:00 course=`209812` `AHA PALS HeartCode` instructor=`instructor_4180671442` location=`NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office` source_window=`26hucabntrqk2qhdnngaq2defb@google.com` consumption=`2026-06-23T18:00:00-04:00` to `2026-06-23T20:15:00-04:00` flags=['starts_at_or_after_6pm_when_not_allowed', 'ends_after_6pm', 'scheduler_consumption_ends_after_6pm', 'outside_explicit_window', 'scheduler_consumption_outside_explicit_window', 'skills_check_without_anchor_or_manual_unlock'] overlaps=0
- ... 220 more in JSON

## Proposed Config Shape

Standing durable policy belongs in `data/config/instructor_scheduling_policy.json`. Calendar-derived dated windows belong in runtime/audit output or a dated review/override file, not in permanent standing policy.

```json
{
  "standing_policy_file": "data/config/instructor_scheduling_policy.json",
  "standing_policy": {
    "instructor_policies": {
      "amy": {
        "enabled_for_public_dynamic_scheduling": false,
        "mode": "explicit_only_anchor_gated",
        "applies_to_instructor_ids": [
          "instructor_4180671442",
          "amy",
          "a___arnold"
        ],
        "calendar_source_key": "amy_availability",
        "hard_guardrails": {
          "no_start_before": "13:00",
          "no_start_at_or_after": "18:00",
          "no_end_after": "18:00",
          "saturday_requires_explicit_window": true,
          "location_specific_only": true
        },
        "allowed_anchor_course_families": [
          "ACLS_RENEWAL",
          "ACLS_INITIAL",
          "PALS_RENEWAL",
          "PALS_INITIAL",
          "BLS_APPROVED_HIGH_VALUE"
        ],
        "skills_check_unlock_rule": "same_window_anchor_seated_claimed_created_or_manual_override_required",
        "minimum_anchor_requirement": {
          "same_availability_window": true,
          "same_location": true,
          "anchor_status_any_of": [
            "seated",
            "claimed",
            "created"
          ]
        },
        "preferred_anchor_start_policy": {
          "source": "explicit_window.preferred_anchor_start",
          "default_if_missing": "window_start plus 60 minutes, capped by explicit override review"
        },
        "duration_safety": {
          "acls_pals_anchor_requires_conservative_scheduler_consumption": true,
          "transition_buffer_minutes_minimum": "CONFIG_REQUIRED"
        },
        "manual_override_fields": [
          "manual_override",
          "approved_by",
          "approved_at",
          "approval_reason"
        ]
      }
    }
  },
  "calendar_derived_window_records_runtime_or_review_only": {
    "source": "data/runtime/calendar_snapshots/amy_availability.json + audit grouping",
    "records": [
      {
        "date": "2026-06-22",
        "source_calendar_key": "amy_availability",
        "source_event_ids": [
          "23rccrjmrdj4p77iko7r2manhn@google.com",
          "7ocuqjieb677urrtttnnhrgbu1@google.com"
        ],
        "event_titles": [
          "Soft",
          "Hard"
        ],
        "raw_timestamps": [
          {
            "event_id": "23rccrjmrdj4p77iko7r2manhn@google.com",
            "start_raw": "20260622T170000Z",
            "end_raw": "20260622T180000Z",
            "utc_start": "2026-06-22T17:00:00+00:00",
            "utc_end": "2026-06-22T18:00:00+00:00"
          },
          {
            "event_id": "7ocuqjieb677urrtttnnhrgbu1@google.com",
            "start_raw": "20260622T180000Z",
            "end_raw": "20260622T220000Z",
            "utc_start": "2026-06-22T18:00:00+00:00",
            "utc_end": "2026-06-22T22:00:00+00:00"
          }
        ],
        "local_timestamps": [
          {
            "event_id": "23rccrjmrdj4p77iko7r2manhn@google.com",
            "local_start": "2026-06-22T13:00:00-04:00",
            "local_end": "2026-06-22T14:00:00-04:00"
          },
          {
            "event_id": "7ocuqjieb677urrtttnnhrgbu1@google.com",
            "local_start": "2026-06-22T14:00:00-04:00",
            "local_end": "2026-06-22T18:00:00-04:00"
          }
        ],
        "grouped_window_start": "2026-06-22T13:00:00-04:00",
        "grouped_window_end": "2026-06-22T18:00:00-04:00",
        "preferred_anchor_start": "2026-06-22T14:00:00-04:00",
        "grouping_rule": "soft_hard_event_pairing",
        "grouping_explanation": "Contiguous same-date Soft availability immediately followed by Hard availability; grouped as one explicit Amy window while preserving Soft as pre-anchor edge and Hard as preferred anchor edge.",
        "conversion_or_grouping_inconsistencies": []
      },
      {
        "date": "2026-06-23",
        "source_calendar_key": "amy_availability",
        "source_event_ids": [
          "2nnr8jg3pka88l9ge2om43aa49@google.com",
          "26hucabntrqk2qhdnngaq2defb@google.com"
        ],
        "event_titles": [
          "Soft",
          "Hard"
        ],
        "raw_timestamps": [
          {
            "event_id": "2nnr8jg3pka88l9ge2om43aa49@google.com",
            "start_raw": "20260623T170000Z",
            "end_raw": "20260623T180000Z",
            "utc_start": "2026-06-23T17:00:00+00:00",
            "utc_end": "2026-06-23T18:00:00+00:00"
          },
          {
            "event_id": "26hucabntrqk2qhdnngaq2defb@google.com",
            "start_raw": "20260623T180000Z",
            "end_raw": "20260623T220000Z",
            "utc_start": "2026-06-23T18:00:00+00:00",
            "utc_end": "2026-06-23T22:00:00+00:00"
          }
        ],
        "local_timestamps": [
          {
            "event_id": "2nnr8jg3pka88l9ge2om43aa49@google.com",
            "local_start": "2026-06-23T13:00:00-04:00",
            "local_end": "2026-06-23T14:00:00-04:00"
          },
          {
            "event_id": "26hucabntrqk2qhdnngaq2defb@google.com",
            "local_start": "2026-06-23T14:00:00-04:00",
            "local_end": "2026-06-23T18:00:00-04:00"
          }
        ],
        "grouped_window_start": "2026-06-23T13:00:00-04:00",
        "grouped_window_end": "2026-06-23T18:00:00-04:00",
        "preferred_anchor_start": "2026-06-23T14:00:00-04:00",
        "grouping_rule": "soft_hard_event_pairing",
        "grouping_explanation": "Contiguous same-date Soft availability immediately followed by Hard availability; grouped as one explicit Amy window while preserving Soft as pre-anchor edge and Hard as preferred anchor edge.",
        "conversion_or_grouping_inconsistencies": []
      },
      {
        "date": "2026-06-26",
        "source_calendar_key": "amy_availability",
        "source_event_ids": [
          "50158s5pctungp0irmfpod7spk@google.com",
          "5rqq5vfpia8up7mejs56nc4p9g@google.com"
        ],
        "event_titles": [
          "Soft",
          "Hard"
        ],
        "raw_timestamps": [
          {
            "event_id": "50158s5pctungp0irmfpod7spk@google.com",
            "start_raw": "20260626T170000Z",
            "end_raw": "20260626T180000Z",
            "utc_start": "2026-06-26T17:00:00+00:00",
            "utc_end": "2026-06-26T18:00:00+00:00"
          },
          {
            "event_id": "5rqq5vfpia8up7mejs56nc4p9g@google.com",
            "start_raw": "20260626T180000Z",
            "end_raw": "20260626T220000Z",
            "utc_start": "2026-06-26T18:00:00+00:00",
            "utc_end": "2026-06-26T22:00:00+00:00"
          }
        ],
        "local_timestamps": [
          {
            "event_id": "50158s5pctungp0irmfpod7spk@google.com",
            "local_start": "2026-06-26T13:00:00-04:00",
            "local_end": "2026-06-26T14:00:00-04:00"
          },
          {
            "event_id": "5rqq5vfpia8up7mejs56nc4p9g@google.com",
            "local_start": "2026-06-26T14:00:00-04:00",
            "local_end": "2026-06-26T18:00:00-04:00"
          }
        ],
        "grouped_window_start": "2026-06-26T13:00:00-04:00",
        "grouped_window_end": "2026-06-26T18:00:00-04:00",
        "preferred_anchor_start": "2026-06-26T14:00:00-04:00",
        "grouping_rule": "soft_hard_event_pairing",
        "grouping_explanation": "Contiguous same-date Soft availability immediately followed by Hard availability; grouped as one explicit Amy window while preserving Soft as pre-anchor edge and Hard as preferred anchor edge.",
        "conversion_or_grouping_inconsistencies": []
      }
    ]
  },
  "note": "June dates are not hard-coded into durable standing policy. They are calendar-derived runtime/review records unless intentionally promoted to dated manual overrides."
}
```

## Existing Public Non-Dynamic Amy Records

| Class/session ID | Course name | Date/time | Public URL/source | Existing Enrollware class | Dynamic? | Flag reason |
| --- | --- | --- | --- | --- | --- | --- |
| `10009277` | AHA PALS Instructor Renewal | 2026-07-01T00:00:00 to 2026-07-01T01:00:00 | `docs/classes/10009277.html` | yes | non-dynamic |  |
| `13673156` | AHA ACLS Provider (Initial) | 2026-07-01T14:00:00 to 2026-07-01T18:00:00 | `docs/classes/13673156.html` | yes | non-dynamic |  |
| `13673166` | AHA ACLS Provider (Renewal) | 2026-07-01T14:00:00 to 2026-07-01T18:00:00 | `docs/classes/13673166.html` | yes | non-dynamic |  |
| `13673176` | AHA PALS Provider | 2026-07-01T14:00:00 to 2026-07-01T18:00:00 | `docs/classes/13673176.html` | yes | non-dynamic |  |
| `13673186` | AHA PALS Renewal | 2026-07-01T14:00:00 to 2026-07-01T18:00:00 | `docs/classes/13673186.html` | yes | non-dynamic |  |
| `13673157` | AHA ACLS Provider (Initial) | 2026-07-06T14:00:00 to 2026-07-06T18:00:00 | `docs/classes/13673157.html` | yes | non-dynamic |  |
| `13673167` | AHA ACLS Provider (Renewal) | 2026-07-06T14:00:00 to 2026-07-06T18:00:00 | `docs/classes/13673167.html` | yes | non-dynamic |  |
| `13673177` | AHA PALS Provider | 2026-07-06T14:00:00 to 2026-07-06T18:00:00 | `docs/classes/13673177.html` | yes | non-dynamic |  |
| `13673187` | AHA PALS Renewal | 2026-07-06T14:00:00 to 2026-07-06T18:00:00 | `docs/classes/13673187.html` | yes | non-dynamic |  |
| `13673158` | AHA ACLS Provider (Initial) | 2026-07-10T14:00:00 to 2026-07-10T18:00:00 | `docs/classes/13673158.html` | yes | non-dynamic |  |
| `13673168` | AHA ACLS Provider (Renewal) | 2026-07-10T14:00:00 to 2026-07-10T18:00:00 | `docs/classes/13673168.html` | yes | non-dynamic |  |
| `13673178` | AHA PALS Provider | 2026-07-10T14:00:00 to 2026-07-10T18:00:00 | `docs/classes/13673178.html` | yes | non-dynamic |  |
| `13673188` | AHA PALS Renewal | 2026-07-10T14:00:00 to 2026-07-10T18:00:00 | `docs/classes/13673188.html` | yes | non-dynamic |  |
| `13673159` | AHA ACLS Provider (Initial) | 2026-07-15T14:00:00 to 2026-07-15T18:00:00 | `docs/classes/13673159.html` | yes | non-dynamic |  |
| `13673169` | AHA ACLS Provider (Renewal) | 2026-07-15T14:00:00 to 2026-07-15T18:00:00 | `docs/classes/13673169.html` | yes | non-dynamic |  |
| `13673179` | AHA PALS Provider | 2026-07-15T14:00:00 to 2026-07-15T18:00:00 | `docs/classes/13673179.html` | yes | non-dynamic |  |
| `13673189` | AHA PALS Renewal | 2026-07-15T14:00:00 to 2026-07-15T18:00:00 | `docs/classes/13673189.html` | yes | non-dynamic |  |
| `12776435` | AHA HeartCode BLS | 2026-07-16T11:45:00 to 2026-07-16T12:30:00 | `docs/classes/12776435.html` | yes | non-dynamic | skills_check_like_existing_public_class_review_anchor_manual_context |
| `13673160` | AHA ACLS Provider (Initial) | 2026-07-16T14:00:00 to 2026-07-16T18:00:00 | `docs/classes/13673160.html` | yes | non-dynamic |  |
| `13673170` | AHA ACLS Provider (Renewal) | 2026-07-16T14:00:00 to 2026-07-16T18:00:00 | `docs/classes/13673170.html` | yes | non-dynamic |  |
| `13673180` | AHA PALS Provider | 2026-07-16T14:00:00 to 2026-07-16T18:00:00 | `docs/classes/13673180.html` | yes | non-dynamic |  |
| `13673190` | AHA PALS Renewal | 2026-07-16T14:00:00 to 2026-07-16T18:00:00 | `docs/classes/13673190.html` | yes | non-dynamic |  |
| `13673161` | AHA ACLS Provider (Initial) | 2026-07-20T14:00:00 to 2026-07-20T18:00:00 | `docs/classes/13673161.html` | yes | non-dynamic |  |
| `13673171` | AHA ACLS Provider (Renewal) | 2026-07-20T14:00:00 to 2026-07-20T18:00:00 | `docs/classes/13673171.html` | yes | non-dynamic |  |
| `13673181` | AHA PALS Provider | 2026-07-20T14:00:00 to 2026-07-20T18:00:00 | `docs/classes/13673181.html` | yes | non-dynamic |  |
| `13673191` | AHA PALS Renewal | 2026-07-20T14:00:00 to 2026-07-20T18:00:00 | `docs/classes/13673191.html` | yes | non-dynamic |  |
| `13673162` | AHA ACLS Provider (Initial) | 2026-07-21T14:00:00 to 2026-07-21T18:00:00 | `docs/classes/13673162.html` | yes | non-dynamic |  |
| `13673172` | AHA ACLS Provider (Renewal) | 2026-07-21T14:00:00 to 2026-07-21T18:00:00 | `docs/classes/13673172.html` | yes | non-dynamic |  |
| `13673182` | AHA PALS Provider | 2026-07-21T14:00:00 to 2026-07-21T18:00:00 | `docs/classes/13673182.html` | yes | non-dynamic |  |
| `13673192` | AHA PALS Renewal | 2026-07-21T14:00:00 to 2026-07-21T18:00:00 | `docs/classes/13673192.html` | yes | non-dynamic |  |
| `13673163` | AHA ACLS Provider (Initial) | 2026-07-24T14:00:00 to 2026-07-24T18:00:00 | `docs/classes/13673163.html` | yes | non-dynamic |  |
| `13673173` | AHA ACLS Provider (Renewal) | 2026-07-24T14:00:00 to 2026-07-24T18:00:00 | `docs/classes/13673173.html` | yes | non-dynamic |  |
| `13673185` | AHA PALS Provider | 2026-07-24T14:00:00 to 2026-07-24T18:00:00 | `docs/classes/13673185.html` | yes | non-dynamic |  |
| `13673193` | AHA PALS Renewal | 2026-07-24T14:00:00 to 2026-07-24T18:00:00 | `docs/classes/13673193.html` | yes | non-dynamic |  |
| `13673164` | AHA ACLS Provider (Initial) | 2026-07-29T14:00:00 to 2026-07-29T18:00:00 | `docs/classes/13673164.html` | yes | non-dynamic |  |
| `13673174` | AHA ACLS Provider (Renewal) | 2026-07-29T14:00:00 to 2026-07-29T18:00:00 | `docs/classes/13673174.html` | yes | non-dynamic |  |
| `13673183` | AHA PALS Provider | 2026-07-29T14:00:00 to 2026-07-29T18:00:00 | `docs/classes/13673183.html` | yes | non-dynamic |  |
| `13673194` | AHA PALS Renewal | 2026-07-29T14:00:00 to 2026-07-29T18:00:00 | `docs/classes/13673194.html` | yes | non-dynamic |  |
| `12776437` | AHA HeartCode BLS | 2026-07-30T11:45:00 to 2026-07-30T12:30:00 | `docs/classes/12776437.html` | yes | non-dynamic | skills_check_like_existing_public_class_review_anchor_manual_context |
| `13673165` | AHA ACLS Provider (Initial) | 2026-07-30T14:00:00 to 2026-07-30T18:00:00 | `docs/classes/13673165.html` | yes | non-dynamic |  |
| `13673175` | AHA ACLS Provider (Renewal) | 2026-07-30T14:00:00 to 2026-07-30T18:00:00 | `docs/classes/13673175.html` | yes | non-dynamic |  |
| `13673184` | AHA PALS Provider | 2026-07-30T14:00:00 to 2026-07-30T18:00:00 | `docs/classes/13673184.html` | yes | non-dynamic |  |
| `13673195` | AHA PALS Renewal | 2026-07-30T14:00:00 to 2026-07-30T18:00:00 | `docs/classes/13673195.html` | yes | non-dynamic |  |

## Remote Main Change Report

- From: `f8db04ab236c9394ec33c407bbbf155f2eb89504`
- Current `origin/main`: `0a2e0dcebe6cfd90d3c02fddf4c5666a70c6805d`
- Commits between them: `1`
- Changed files: `364`
- Expected assessment: Appears to be an automated/expected public schedule refresh from Enrollware iCal based on commit subject and changed generated docs/data schedule artifacts; still should be reviewed before merge/deploy because it moved origin/main after the prior deployment checkpoint.
- Production check: HTTP `200`, matches 0a2e0d schedule JSON: `True`, matches f8db04 schedule JSON: `False`
- Do not pull/reset/merge/deploy until this remote movement is reviewed.

## Final Verdict

Amy is not currently safe to enable for public dynamic scheduling.

Strict public dynamic Amy offers remain `0`. Existing public Amy records are non-dynamic Enrollware classes. Amy dynamic candidates exist in audit/preview data and must remain non-public until explicit-window, anchor-gated, manual-override-aware policy is implemented and tested.
