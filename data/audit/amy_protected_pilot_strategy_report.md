# Amy Protected Pilot Strategy Report

Read-only strategy report. Amy protected-pilot logic does not publish offers, create appointments, call Enrollware, change public pages, or enable Worker routes.

## Summary

- Amy mode: protected_pilot
- Amy protected pilot seeds selected: 0
- Amy stack-fill candidates found: 0

## Hidden By Protected Pilot Reason

- None

## Stack-Fill Candidates

- None

## Rule

- Amy ACLS/PALS Initial/Renewal can become protected pilot public seeds only at 14:00.
- Amy HeartCode/skills at or after 13:00 are stack-fill candidates only and are not publicly exposed yet.
- Existing Enrollware/session occupancy remains a hard blocker upstream in dynamic offer generation.
