# Latest ChatGPT Bundle

Codex rendered validated auto-public appointment seed `seed_7457baba994578af` into actual public hub HTML.

Changed implementation:

- `scripts/build_slug_hubs.py` now loads validated auto-public appointment seed offers from the hub offer model.
- Matching appointment seeds render as a separate hub-only appointment section inside the appropriate tab.
- The rendered card uses the appointment URL directly and marks:
  - `data-offer-source="auto_public_appointment_seed"`
  - `data-real-enrollware-session="false"`
  - `data-standalone-class-lander-allowed="false"`
  - `data-class-lander-created="false"`
  - `data-public-schedule-row-created="false"`

Public output changed:

- `docs/bls.html`

Rendered link:

`https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260714`

Safety:

- No class landers created.
- `public_schedule.json` unchanged.
- `live-schedule_future.json` unchanged.
- `docs/data/*` unchanged.
- Needs-review and blocked seeds were not rendered.
- Claimed slot winner validation passed.
- Hub render preview validation passed with 0 violations.

Preflight note:

`run_lander_safety_preflight.py` reported `failed_validation` because public files are dirty after intentionally rendering `docs/bls.html`; stale Enrollware offer review remains a separate blocker.
