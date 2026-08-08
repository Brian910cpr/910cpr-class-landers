# LanderWare Agent Interface — Phase 1 Architecture

## Existing scheduling path

```text
Scheduling Inputs
  data/Class Report.xlsx (real Enrollware classes)
  ADR + DoNotSchedule calendars
  hot-sync active entries
  free_time_scheduler_config.json (course templates and policy)
        ↓
Normalization / Course Mapping
  scripts/build_sessions_current.py
  scripts/course_identity_resolver.py::resolve_course_identity
  scripts/free_time_scheduler.py::load_existing_enrollware_sessions
        ↓
Scheduling Resolver
  scripts/free_time_scheduler.py::load_current_calendar_blocks
  scripts/free_time_scheduler.py::build_offer_seeds
  scripts/free_time_scheduler.py::evaluate_candidate_session
        ↓
Conflict / Constraint Evaluation
  overlapping_blocks (calendar and Enrollware conflicts)
  estimate_drive_minutes / required_buffer_minutes (travel)
  duration_minutes + cleanup_minutes (consumption window)
  same_program_gap_status (repeat gap)
  offer frequency and horizon selection (public compaction)
        ↓
Availability Generation
  scripts/build_schedule_future.py → docs/data/schedule_future.json
  scripts/free_time_scheduler.py::generate_customer_facing_offers
    → docs/data/customer_facing_offers.json
        ↓
Current Web Presentation
  scripts/build_slug_hubs.py and scripts/build_course_landers.py
  generated docs/ pages
```

## Constraints and ownership

- Course identity is normalized through `course_identity_resolver.py`, aliases, Course Master, and the scheduler's configured course templates. Course Master still has review gates and is not independently promoted to scheduling authority here.
- Existing seated-class capacity comes from the Enrollware Class Report and flows through `schedule_future.json`. Remaining capacity is only returned when both capacity and enrollment (or an explicit available-seat field) are reliable.
- Dynamic availability is owned by `free_time_scheduler.py`. It merges ADR, DoNotSchedule, Class Report, schedule fallback, and active hot-sync records into blocking calendar events.
- `evaluate_candidate_session` applies duration, cleanup, overlap, location, and travel-buffer rules. `build_offer_seeds`, `same_program_gap_status`, and the selection functions apply anchor/stacking, repeat-gap, notice, frequency, daily/weekly cap, and horizon-spread behavior.
- Private calendar URLs are read from environment/local secrets and are redacted from reports. Public/private location behavior is represented by scheduler location configuration and appointment-container policy.
- `inventory_resolver_v1.py` is not the public-bookability boundary: it contains explicitly approximate durations and recommendation logic.

## Natural reusable boundary

The safest Phase 1 boundary is the pair of final machine-readable contracts already consumed by the public presentation:

- `docs/data/schedule_future.json` for real seated Enrollware sessions.
- `docs/data/customer_facing_offers.json` for dynamic options that have already passed resolver and presentation-policy selection.

`scripts/landerware_agent_interface.py` provides `identify_course` and `find_availability` over those contracts. It performs filtering and response shaping only; it does not recreate scheduling decisions. Missing dynamic inventory fails closed and never creates an offer.

## Presentation coupling and next extraction

Dynamic resolution and JSON/report/page writes are mixed in `free_time_scheduler.py::generate_customer_facing_offers`. A later transport service that must calculate on demand should first extract that function into a pure resolver returning the existing payload, leaving the current writer and website builder as consumers. That extraction needs fixture parity tests before deployment. Phase 1 intentionally avoids it.

## Phase 1 transport

The initial transport is a provider-neutral JSON CLI, suitable for local workflows and as the core behind a later HTTP or MCP adapter:

```powershell
python -m scripts.landerware_agent_interface identify_course --request '{"course_key":"bls-renewal"}'
python -m scripts.landerware_agent_interface find_availability --request '{"course":{"course_key":"bls-renewal"},"date_from":"2026-08-12","date_to":"2026-08-14"}'
```

No registration, payment, hold, reschedule, cancellation, or customer mutation capability is present.
