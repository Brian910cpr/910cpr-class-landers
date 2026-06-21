# Instructor Availability Report

- Generated at: 2026-06-19T16:58:39.258521-04:00
- Report only: True
- Public behavior changed: False
- Source mode: live
- Fixture loaded: True (data\fixtures\instructor_calendar_events.json)
- Live ICS policy: Live mode uses only the configured *_ICS_URL environment variables. Public Google Calendar CID web URLs are not converted to ICS URLs here; public/basic.ics or private ICS URLs must be supplied explicitly.

## Brian (brian)
- Calendar source loaded: True (brian_do_not_schedule)
- Instructor mode: inverse_blocking
- Events source: live
- Events found: 0
- HARD windows: 0
- SOFT edge windows: 0
- UNAVAILABLE/blocking events: 0
- Final usable windows: 0
- Ignored events: 0
- Warnings: 2

  - Warning: No live ICS URL configured in BRIAN_BLOCKING_CALENDAR_ICS_URL. Public Google Calendar CID web URLs are not fetched directly; provide a public/basic ICS URL or private ICS URL via the configured environment variable.
  - Warning: Brian is inverse-blocking only in this report. No availability windows were invented; future offer generation needs a configured candidate-window generator.

## Amy (amy)
- Calendar source loaded: True (amy_availability)
- Instructor mode: explicit_availability
- Events source: live
- Events found: 0
- HARD windows: 0
- SOFT edge windows: 0
- UNAVAILABLE/blocking events: 0
- Final usable windows: 0
- Ignored events: 0
- Warnings: 2

  - Warning: No live ICS URL configured in AMY_AVAILABILITY_ICS_URL. Public Google Calendar CID web URLs are not fetched directly; provide a public/basic ICS URL or private ICS URL via the configured environment variable.
  - Warning: No HARD/SOFT events found; explicit-availability instructor has no offerable availability.

## Nick (nick)
- Calendar source loaded: True (nick_availability)
- Instructor mode: explicit_availability
- Events source: live
- Events found: 0
- HARD windows: 0
- SOFT edge windows: 0
- UNAVAILABLE/blocking events: 0
- Final usable windows: 0
- Ignored events: 0
- Warnings: 2

  - Warning: No live ICS URL configured in NICK_AVAILABILITY_ICS_URL. Public Google Calendar CID web URLs are not fetched directly; provide a public/basic ICS URL or private ICS URL via the configured environment variable.
  - Warning: No HARD/SOFT events found; explicit-availability instructor has no offerable availability.
