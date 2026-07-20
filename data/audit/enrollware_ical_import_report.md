# Enrollware iCal Import Report

- Generated at: `2026-07-20T11:51:28.433709-04:00`
- Source: `enrollware_ical`
- iCal events read: `389`
- Public sessions created: `389`
- Skipped events: `0`
- Registration unavailable sessions marked not direct-bookable: `359`
- Unmapped sessions: `30`
- Prior sessions read: `489`
- Classes removed compared with prior source: `114`
- Stale manual/Class Report sessions excluded: `114`
- Stale Zapier/Google Sheet public schedule sessions excluded: `0`

Zapier/Google Sheet registration events are not used as the public schedule source in this build path.
They remain separate registration-signal/audit inputs only.

## Removed Examples

| Session ID | Course | Start | Location |
|---|---|---|---|
| `12774059` | AHA ACLS HeartCode | 2026-04-13T08:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774069` | AHA ACLS HeartCode | 2026-04-18T08:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774096` | AHA ACLS HeartCode | 2026-07-20T08:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774297` | AHA BLS Provider (Initial) | 2026-04-13T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774298` | AHA BLS Provider (Initial) | 2026-04-20T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774301` | AHA BLS Provider (Initial) | 2026-04-15T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774307` | AHA BLS Provider (Initial) | 2026-04-17T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774337` | AHA BLS Provider (Initial) | 2026-07-20T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774338` | AHA BLS Provider (Initial) | 2026-07-27T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774347` | AHA BLS Provider (Initial) | 2026-07-24T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774348` | AHA BLS Provider (Initial) | 2026-07-31T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774519` | AHA BLS Provider (Initial) | 2026-04-14T18:45:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774526` | AHA BLS Provider (Initial) | 2026-04-18T18:15:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774527` | AHA BLS Provider (Initial) | 2026-04-17T18:15:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774586` | AHA BLS Provider (Initial) | 2026-07-25T18:15:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774590` | AHA BLS Provider (Initial) | 2026-07-24T18:15:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774591` | AHA BLS Provider (Initial) | 2026-07-31T18:15:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774595` | AHA BLS Provider (Initial) | 2026-07-22T18:45:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774599` | AHA BLS Provider (Initial) | 2026-07-27T18:15:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12775262` | AHA BLS Provider (Renewal) | 2026-04-14T18:45:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |

## Registration Unavailable Exclusions

| Session ID | Reason | Course | Start | Location |
|---|---|---|---|---|
| `13295696` | enrollware_registration_closed | AHA ACLS Provider (Initial) | 2026-04-22T13:00:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13361769` | enrollware_registration_closed | BLS Provider (NHCSO) | 2026-04-22T13:00:00-04:00 | New Hanover County Sheriff’s Office |
| `12774518` | enrollware_registration_closed | AHA BLS Provider (Initial) | 2026-04-22T18:45:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12775263` | enrollware_registration_closed | AHA BLS Provider (Renewal) | 2026-04-22T18:45:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13295699` | enrollware_registration_closed | AHA ACLS Provider (Initial) | 2026-04-23T13:00:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13295719` | enrollware_registration_closed | AHA ACLS Provider (Renewal) | 2026-04-23T13:00:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13295740` | enrollware_registration_closed | AHA PALS Provider | 2026-04-23T13:00:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13295763` | enrollware_registration_closed | AHA PALS Renewal | 2026-04-23T13:00:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12776760` | enrollware_registration_closed | AHA Heartsaver® First Aid CPR AED | 2026-04-23T18:45:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12776309` | enrollware_registration_closed | AHA BLS HeartCode® | 2026-04-24T08:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13369209` | enrollware_registration_closed | AHA BLS Provider (Initial) | 2026-04-24T09:15:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12776125` | enrollware_registration_closed | AHA Heartsaver® First Aid CPR AED – Blended | 2026-04-24T11:45:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774308` | enrollware_registration_closed | AHA BLS Provider (Initial) | 2026-04-24T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12775505` | enrollware_registration_closed | AHA BLS Provider (Renewal) | 2026-04-24T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12775750` | enrollware_registration_closed | AHA Heartsaver® First Aid CPR AED – Blended | 2026-04-24T17:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774070` | enrollware_registration_closed | AHA ACLS HeartCode | 2026-04-25T08:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12775961` | enrollware_registration_closed | AHA Heartsaver® First Aid CPR AED | 2026-04-25T09:15:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12776855` | enrollware_registration_closed | USCG Elementary First Aid | CPR (AHA Heartsaver®) | 2026-04-25T09:15:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12776415` | enrollware_registration_closed | AHA BLS HeartCode® | 2026-04-25T11:45:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12775504` | enrollware_registration_closed | AHA BLS Provider (Renewal) | 2026-04-25T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12776643` | enrollware_registration_closed | AHA BLS Provider (Initial) | 2026-04-25T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12935911` | enrollware_registration_closed | AHA - Family & Friends® CPR | 2026-04-26T14:30:00-04:00 | Gate's Residence: 310 Tanbridge Rd |
| `12774060` | enrollware_registration_closed | AHA ACLS HeartCode | 2026-04-27T08:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12775492` | enrollware_registration_closed | AHA BLS Provider (Renewal) | 2026-04-27T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13295700` | enrollware_registration_closed | AHA ACLS Provider (Initial) | 2026-04-27T13:00:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13295721` | enrollware_registration_closed | AHA ACLS Provider (Renewal) | 2026-04-27T13:00:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13295741` | enrollware_registration_closed | AHA PALS Provider | 2026-04-27T13:00:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13295764` | enrollware_registration_closed | AHA PALS Renewal | 2026-04-27T13:00:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12775737` | enrollware_registration_closed | HSI Adult First Aid | Blended Learning Online Coursework with In-Person Skills Testing | 2026-04-27T17:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774515` | enrollware_registration_closed | AHA BLS Provider (Initial) | 2026-04-27T18:15:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12775259` | enrollware_registration_closed | AHA BLS Provider (Renewal) | 2026-04-27T18:15:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13295701` | enrollware_registration_closed | AHA ACLS Provider (Initial) | 2026-04-28T13:00:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774066` | enrollware_registration_closed | AHA ACLS HeartCode | 2026-04-29T08:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12776851` | enrollware_registration_closed | USCG Elementary First Aid | CPR (AHA Heartsaver®) | 2026-04-29T09:15:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12776121` | enrollware_registration_closed | AHA Heartsaver® First Aid CPR AED – Blended | 2026-04-29T11:45:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13383019` | enrollware_registration_closed | HSI BLS and Adult First Aid | Blended Learning | 2026-04-29T11:46:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774302` | enrollware_registration_closed | AHA BLS Provider (Initial) | 2026-04-29T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13396835` | enrollware_registration_closed | BLS Provider (NHCSO) | 2026-04-29T13:00:00-04:00 | New Hanover County Sheriff’s Office |
| `12776691` | enrollware_registration_closed | AHA Heartsaver® First Aid CPR AED – Blended | 2026-04-30T08:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12783377` | enrollware_registration_closed | HSI BLS and Adult First Aid | Blended Learning | 2026-04-30T08:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12776411` | enrollware_registration_closed | AHA BLS HeartCode® | 2026-04-30T11:45:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12776761` | enrollware_registration_closed | AHA Heartsaver® First Aid CPR AED | 2026-04-30T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `10009275` | enrollware_registration_closed | AHA - PALS Instructor Renewal | 2026-05-01T00:00:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `11341057` | enrollware_registration_closed | AHA - BLS Instructor Renewal | 2026-05-01T00:00:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12776331` | enrollware_registration_closed | AHA BLS HeartCode® | 2026-05-01T08:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12776134` | enrollware_registration_closed | AHA Heartsaver® First Aid CPR AED – Blended | 2026-05-01T11:45:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13402247` | enrollware_registration_closed | HSI BLS and Adult First Aid | Blended Learning | 2026-05-01T11:45:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `13455396` | enrollware_registration_closed | AHA - BLS Provider - Renewal Instructor-led Classroom program for BLS Renewal | 2026-05-01T11:45:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12774317` | enrollware_registration_closed | AHA BLS Provider (Initial) | 2026-05-01T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |
| `12775514` | enrollware_registration_closed | AHA BLS Provider (Renewal) | 2026-05-01T12:30:00-04:00 | NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office |

## Unmapped Examples

- `13361769`: BLS Provider (NHCSO) (2026-04-22T13:00:00-04:00)
- `12935911`: AHA - Family & Friends® CPR (2026-04-26T14:30:00-04:00)
- `12775737`: HSI Adult First Aid | Blended Learning Online Coursework with In-Person Skills Testing (2026-04-27T17:30:00-04:00)
- `13396835`: BLS Provider (NHCSO) (2026-04-29T13:00:00-04:00)
- `10009275`: AHA - PALS Instructor Renewal (2026-05-01T00:00:00-04:00)
- `11341057`: AHA - BLS Instructor Renewal (2026-05-01T00:00:00-04:00)
- `13455396`: AHA - BLS Provider - Renewal Instructor-led Classroom program for BLS Renewal (2026-05-01T11:45:00-04:00)
- `13415860`: AHA - BLS - Become an American Heart Association Instructor (2026-05-05T00:35:00-04:00)
- `13416978`: BLS Provider (NHCSO) (2026-05-06T13:00:00-04:00)
- `13417016`: BLS Provider (NHCSO) (2026-05-06T13:00:00-04:00)
- `10009265`: AHA - PALS Instructor Renewal (2026-06-01T00:00:00-04:00)
- `10009276`: AHA - PALS Instructor Renewal (2026-06-01T00:00:00-04:00)
- `10009277`: AHA - PALS Instructor Renewal (2026-07-01T00:00:00-04:00)
- `11341054`: AHA - BLS Instructor Renewal (2026-06-01T00:00:00-04:00)
- `12775764`: AHA - Family & Friends® CPR (2026-05-16T16:30:00-04:00)
- `12776775`: AHA - Family & Friends® CPR (2026-06-04T18:15:00-04:00)
- `13415738`: HSI Adult/Child/Infant CPR AED | Blended Learning Blended Learning with In-Person, Instructor-Led Skills Session (2026-05-11T17:30:00-04:00)
- `13446978`: BLS Provider (NHCSO) (2026-05-13T13:00:00-04:00)
- `13502472`: BLS Provider (NHCSO) (2026-05-20T13:00:00-04:00)
- `13556744`: BLS Provider (NHCSO) (2026-05-27T13:00:00-04:00)
