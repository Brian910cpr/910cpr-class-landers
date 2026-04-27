# Enrollware Sync Dry Run

- Generated: `2026-04-27T07:48:16.149427-04:00`
- Master schedule: `E:\GitHub\910cpr-class-landers\data\Class Report.xlsx`
- Enrollware export: `E:\GitHub\910cpr-class-landers\data\enrollware_export.xlsx`

## Summary

- Desired sessions: `1491`
- Enrollware sessions: `1448`
- Validation issues: `859`
- Would create: `1483`
- Would update: `0`
- Would skip: `6`
- Duplicate risk: `2`
- Missing in Enrollware: `1483`
- Extra in Enrollware: `1440`

## Validation Issues

- `error` `missing_datetime`: Session is missing a start or end time.
- `error` `missing_datetime`: Session is missing a start or end time.
- `error` `missing_datetime`: Session is missing a start or end time.
- `error` `missing_datetime`: Session is missing a start or end time.
- `error` `missing_datetime`: Session is missing a start or end time.
- `error` `missing_datetime`: Session is missing a start or end time.
- `error` `missing_datetime`: Session is missing a start or end time.
- `error` `missing_datetime`: Session is missing a start or end time.
- `error` `missing_datetime`: Session is missing a start or end time.
- `error` `closed_day`: Session falls on a closed day: 2026-12-25
- `error` `closed_day`: Session falls on a closed day: 2026-12-25
- `error` `closed_day`: Session falls on a closed day: 2026-12-25
- `error` `closed_day`: Session falls on a closed day: 2026-12-25
- `error` `closed_day`: Session falls on a closed day: 2026-12-25
- `error` `closed_day`: Session falls on a closed day: 2026-12-25
- `error` `closed_day`: Session falls on a closed day: 2026-12-25
- `error` `duplicate_slot`: Duplicate desired slot detected 2 times.
- `error` `location_overlap`: Location overlap for Wilmington; Shipyard Blvd.
- `error` `location_overlap`: Location overlap for Wilmington; Shipyard Blvd.
- `error` `location_overlap`: Location overlap for Wilmington; Shipyard Blvd.
- `error` `location_overlap`: Location overlap for Wilmington; Shipyard Blvd.
- `error` `location_overlap`: Location overlap for Wilmington; Shipyard Blvd.
- `error` `location_overlap`: Location overlap for Wilmington; Shipyard Blvd.
- `error` `location_overlap`: Location overlap for Wilmington; Shipyard Blvd.
- `error` `location_overlap`: Location overlap for Wilmington; Shipyard Blvd.
- ... and `834` more

## Would Create

- `209811` No exact Enrollware match found for desired session.
- `359474` No exact Enrollware match found for desired session.
- `241108` No exact Enrollware match found for desired session.
- `209818` No exact Enrollware match found for desired session.
- `209805` No exact Enrollware match found for desired session.
- `251496` No exact Enrollware match found for desired session.
- `445670` No exact Enrollware match found for desired session.
- `209806` No exact Enrollware match found for desired session.
- `359474` No exact Enrollware match found for desired session.
- `241108` No exact Enrollware match found for desired session.
- `209818` No exact Enrollware match found for desired session.
- `209805` No exact Enrollware match found for desired session.
- `251496` No exact Enrollware match found for desired session.
- `209811` No exact Enrollware match found for desired session.
- `253768` No exact Enrollware match found for desired session.
- `329495` No exact Enrollware match found for desired session.
- `209806` No exact Enrollware match found for desired session.
- `359474` No exact Enrollware match found for desired session.
- `329495` No exact Enrollware match found for desired session.
- `445670` No exact Enrollware match found for desired session.
- ... and `1463` more

## Duplicate Risk

- `aha pals instructor renewal` Multiple Enrollware sessions match this desired slot.
- `aha pals instructor renewal` Multiple Enrollware sessions match this desired slot.

## Extra In Enrollware

- `48226` Enrollware contains a class not present in desired sessions.
- `49970` Enrollware contains a class not present in desired sessions.
- `48376` Enrollware contains a class not present in desired sessions.
- `49414` Enrollware contains a class not present in desired sessions.
- `49619` Enrollware contains a class not present in desired sessions.
- `48537` Enrollware contains a class not present in desired sessions.
- `49208` Enrollware contains a class not present in desired sessions.
- `48232` Enrollware contains a class not present in desired sessions.
- `50669` Enrollware contains a class not present in desired sessions.
- `49975` Enrollware contains a class not present in desired sessions.
- `48375` Enrollware contains a class not present in desired sessions.
- `49419` Enrollware contains a class not present in desired sessions.
- `50516` Enrollware contains a class not present in desired sessions.
- `50760` Enrollware contains a class not present in desired sessions.
- `50249` Enrollware contains a class not present in desired sessions.
- `50586` Enrollware contains a class not present in desired sessions.
- `50176` Enrollware contains a class not present in desired sessions.
- `49988` Enrollware contains a class not present in desired sessions.
- `48390` Enrollware contains a class not present in desired sessions.
- `49436` Enrollware contains a class not present in desired sessions.
- ... and `1420` more

## Safety

- No classes were created, edited, or deleted in this phase.
- Extra Enrollware classes are flagged for manual review only.
