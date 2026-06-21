# Location / Resource Normalization Report

Read-only report. No public pages, Enrollware calls, appointments, appointment URL behavior, Worker routes, deploys, or commits were changed.

## Summary

- Canonical Shipyard restored: True
- Canonical public location: NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office
- Live Shipyard blocks: 7
- Dynamic Shipyard offers generated: 465
- Container-backed public offers kept: 0
- Public sellable offers kept: 0
- Seeds selected: 0
- URL previews generated: 0

## Shipyard Aliases

- NC - Wilmington: 4018 Shipyard Blvd @ 910CPR's Office
- :: Wilmington; Shipyard Blvd
- Wilmington; Shipyard Blvd
- Shipyard Office

## Internal Resources

| Resource | Confirmed container? | Notes |
| --- | --- | --- |
| :: Wilmington; Shipyard Blvd - A | False | Internal resource alias only until Brian/Enrollware confirms a deterministic appointment container. |
| :: Wilmington; Shipyard Blvd - B | False | Internal resource alias only until Brian/Enrollware confirms a deterministic appointment container. |
| :: Wilmington; Shipyard Blvd - C | False | Internal resource alias only until Brian/Enrollware confirms a deterministic appointment container. |
| :: Wilmington; Shipyard Blvd - C (Other) | False | Internal resource alias only until Brian/Enrollware confirms a deterministic appointment container. |
| Shipyard Office | True | Matches the currently confirmed Brian Shipyard appointment container resource label. |

## Current Interpretation

- Shipyard A/B/C are internal resources under the canonical Shipyard public location, not separate public locations.
- Matching now compares canonical public location for appointment-container checks.
- Internal resource labels remain available on offers for later resource-level conflict logic.
- No A/B/C deterministic appointment containers were inferred or added.

## Why URL Previews Are Still Zero

- The only Brian Shipyard live block in the current snapshot is `00:00-00:00`, so it is not a usable offer window.
- Amy Shipyard offers are protected pilot / stack-fill candidates but are not broad public dynamic seeds and do not have confirmed Amy containers.

