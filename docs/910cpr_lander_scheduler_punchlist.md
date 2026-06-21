# 910CPR Lander Scheduler Redesign Punch-List

Generated: 2026-06-18

Scope: technical inventory and planning notes only. No runtime data, generated public pages, Enrollware IDs, deployment settings, or behavior were changed.

## 1. Current Repo Structure

### Key Folders

- `docs/`
  - Public static site output for GitHub Pages.
  - Contains generated HTML pages, public JSON under `docs/data/`, runtime JS/CSS under `docs/assets/`, `sitemap.xml`, and public hub pages such as `bls.html`, `acls.html`, `pals.html`, `heartsaver.html`, `uscg-elementary-first-aid-cpr.html`, and `schedule.html`.
  - Treat most HTML here as generated output, not source.

- `scripts/`
  - Main Python build, sync, audit, inventory, and scheduler scripts.
  - Important current builders: `build_sessions_current.py`, `build_schedule_future.py`, `build_landers.py`, `build_course_landers.py`, `build_courses.py`, `build_locations.py`, `build_course_at_city.py`, `build_slug_hubs.py`, `build_index_and_sitemap.py`, `build_control_booth.py`.
  - Scheduler/inventory experiments live here too: `free_time_scheduler.py`, `hybrid_inventory.py`, `inventory_controller.py`, `inventory_resolver_v1.py`, `build_hub_offer_model_report.py`, `build_appointment_offer_inventory.py`.

- `data/`
  - Internal source/config/generated data.
  - Important source/config areas:
    - `data/config/`
    - `data/inventory/`
    - `data/raw/`
    - `data/state/`
  - Important generated/internal outputs:
    - `data/sessions_current.json`
    - `data/runtime/*.json`
    - `data/audit/*.json`

- `worker/`
  - Cloudflare Worker scaffold for requestable free-time offers.
  - Current worker is explicitly dry-run/not wired for Enrollware class creation.

- `tests/`
  - Unit tests for inventory rules and inventory controller.
  - Current tests prove appointmentDayId math, inventory candidate generation, and inventory rule behavior.

- `debug/`
  - Reports, audits, screenshots, generated diagnostics, stale class quarantine, and runtime debug artifacts.
  - Useful for investigation but risky as source of truth because it contains historical outputs and large generated dumps.

- `build/`, root `.bat` files, root legacy Python files
  - Multiple build entry points exist, some current and some legacy.
  - `build/build_all_v4.bat`, `run_stack.bat`, and documented modern module commands are safer than root legacy scripts.

- `CUSTOMER_images/`, `raw/`, `logs/`
  - Images, raw exports, archives, and build logs.
  - Useful operational artifacts, but not scheduler source of truth.

### Obsolete, Duplicated, Or Risky Areas

- `scripts/build_all.py` references scripts that do not appear to exist in the current stack (`build_public_schedule.py`, `build_course_pages.py`, `build_class_landers.py`). Do not use as the scheduler redesign entry point.
- `build/build_all_v3.bat` is legacy and centers on `data/schedule.json`; the modern hub stack centers on `data/sessions_current.json` and `docs/data/schedule_future.json`.
- `scripts/build_landers_BACKUP.py`, root `build_index.py`, root `build_discovery.py`, and multiple legacy public schedule builders should be treated as compatibility/legacy until proven active.
- `scripts/prebuild_cleanup_validate.py` is documented as risky because it can delete `docs/data/*.json`, which may include important runtime settings.
- `debug/quarantine/`, `debug/backups/`, `scripts/__pycache__/`, `supervisor/__pycache__/`, and large generated JSON/HTML should not be used as planning source unless explicitly auditing historical behavior.

## 2. Existing Lander / Static Build Flow

### Current Public Page Generation

The documented modern flow is:

1. `python -m scripts.build_sessions_current`
   - Reads Class Report / live export-style data and course map config.
   - Writes `data/sessions_current.json`.

2. `python -m scripts.build_schedule_future`
   - Reads `data/sessions_current.json`.
   - Writes `docs/data/schedule_future.json`.

3. Page builders consume `docs/data/schedule_future.json` and config:
   - `scripts/build_landers.py` -> `docs/classes/*.html`
   - `scripts/build_course_landers.py` -> `docs/courses/*.html`
   - `scripts/build_courses.py` -> `docs/courses/*.html`
   - `scripts/build_locations.py` -> `docs/locations/*.html`
   - `scripts/build_course_at_city.py` -> `docs/course-at-city/*.html`
   - `scripts/build_slug_hubs.py` -> root hub pages in `docs/`
   - `scripts/build_request_group_session.py` -> request/group page
   - `scripts/build_index_and_sitemap.py` -> index pages and sitemap

4. Verification/control:
   - `scripts/build_control_booth.py`
   - `scripts/verify_generated_stack.py`
   - `scripts/check_schedule_integrity.py`

### Static, API-Backed, Or Mixed?

- Public pages are primarily static HTML + static JSON served from `docs/`.
- Runtime browser JS fetches static JSON and manipulates UI.
- `docs/assets/hybrid-inventory.js` attempts browser-side Enrollware appointment availability calls; this is mixed behavior and may be limited by CORS.
- Cloudflare Worker scaffold exists for requestable offers, but creation/recheck are not production-wired.
- There is no current public backend that recomputes schedule availability server-side for the static site.

## 3. hot_sync / Enrollware Data Flow

### Located hot_sync / Enrollware Files

- `scripts/enrollware_sync.py`
  - Reads tabular Enrollware-like exports.
  - Normalizes sessions, extracts course metadata from HTML/longdesc/name attributes, compares master/export rows, and writes runtime sync outputs.

- `scripts/ew_ingest.py`
  - Parses course export and Class Report XLSX files into normalized course/session records.
  - Extracts course IDs from embedded Enrollware HTML metadata.

- `scripts/ew_schedule_watcher.py`
  - Fetches Enrollware schedule feed data using `scripts/course_ids.json`.
  - Writes `data/sessions_current.json` and rotates `data/sessions_previous.json`.
  - This appears older/riskier because it writes a different shape to `data/sessions_current.json` than the modern `build_sessions_current.py` pipeline.

- `scripts/free_time_scheduler.py`
  - Has hot-sync references in calendar merge/debug counters.
  - Generates proposed sessions and customer-facing offers from calendar blocks/config, not live Enrollware as schedule brain.

- `data/runtime/enrollware_sync/<timestamp>/`
  - Historical desired/current sync data.
  - Contains normalized desired sessions with Enrollware course HTML, registration URLs, and course IDs.

- `data/state/appointment_claims_test.json`
  - State-like test data for appointment claims.

- `debug/enrollware_*`
  - Appointment probe, course match, and cleanup reports.
  - Useful for auditing but should not be treated as current source of truth without rerun.

### Divergence Risks

- `data/Class Report.xlsx`, `data/raw/classes_raw_live.csv`, `data/raw/students_raw_live.csv`, `data/sessions_current.json`, `docs/data/schedule_future.json`, Enrollware public schedule feeds, and generated HTML can drift if not rebuilt in the correct order.
- `docs/data/customer_facing_offers.json` is expected by `build_slug_hubs.py` but was not present in this checkout during inspection.
- Requestable offer debug reports can show candidate offers that are not actually present on public pages.
- `ew_schedule_watcher.py` can overwrite `data/sessions_current.json` with a feed snapshot shape that may not match the modern richer internal session model.
- Generated pages may contain stale baked links if source JSON changed but pages were not rebuilt.

## 4. Course ID And Course Mapping

### Key Mapping Files

- `data/config/course_map.json`
  - Main structured course metadata keyed by stable Enrollware course ID/course number.
  - Contains `course_id`, `course_number`, `course_key`, official/clean titles, aliases, family, subtype, certifying body, delivery mode, course code, provider, schedule URL, schedule anchor, images, descriptions, and active flags.

- `data/course_aliases.json`
  - Legacy/active aliases mapping older Enrollware course names and embedded HTML to canonical metadata.
  - Contains `legacy_alias` and `active_alias_needs_review` statuses.

- `data/inventory/course_consumption_rules.json`
  - Course duration/capacity/appointment eligibility/inventory behavior keyed by course IDs and course families.

- `scripts/course_ids.json`
  - Small list of course IDs used by `ew_schedule_watcher.py`.
  - Currently too narrow to be global source of truth.

- `data/audit/unmapped_courses.json`
  - Identifies sessions that failed mapping.

- `debug/enrollware_appointment_course_match_*`
  - Historical appointment/course matching reports.

### Mapping Chain

Current mapping appears to connect:

- Enrollware embedded HTML `name="<course id>"` / `longdesc="r:<id>|t:<code>|cb:<body>|..."`
- `data/config/course_map.json` course IDs and aliases
- normalized `course_key` / `course_code`
- generated page slugs and schedule grouping
- Enrollware registration URLs such as `https://coastalcprtraining.enrollware.com/enroll?id=<class id>`

### Guessed Or Hard-Coded IDs

- `data/config/course_map.json` appears intended as authoritative. Do not invent or modify IDs without Brian/Enrollware confirmation.
- `scripts/course_ids.json` is hard-coded and incomplete.
- `debug/requestable_appointment_url_report.json` previously showed configured deterministic appointment course IDs only for selected BLS-related courses. Treat debug report IDs as evidence, not a source of truth.
- `data/inventory/appointment_containers.json` contains confirmed appointmentDayId range metadata. Treat it as constrained operational config, not proof that every course is safe for appointment URL generation.

## 5. Appointment Bridge / Deterministic Appointment URLs

### Located Logic

- `scripts/free_time_scheduler.py`
  - `calculate_appointment_day_id()`
  - `format_enrollware_start_time()`
  - `build_enrollware_appointment_url()`
  - `generate_requestable_appointment_url_report()`

- `scripts/inventory_controller.py`
  - `compute_appointment_day_id()`
  - `validate_appointment_day_id()`
  - `select_appointment_container()`
  - `build_registration_url()`

- `data/inventory/appointment_containers.json`
  - Confirmed owned appointmentDayId range for Shipyard/Brian.

- `worker/free-time-offer-worker.js`
  - Confirmation/check/open-registration scaffold.
  - Looks up trusted offers by slug/token from KV/D1/R2/env-style JSON.
  - Currently recheck/creation are not wired for production.

- `wrangler.toml`
  - Worker route/config for `schedule.910cpr.com/*`.
  - `CREATION_ENABLED=false`, `DRY_RUN=true`, `ALLOW_PUBLIC_CREATION=false`.

### Active / Preview / Disabled

- Static Enrollware class registration links are active in generated pages.
- Deterministic appointment URL generation exists in Python and inventory controller code.
- Requestable appointment URLs appear report-only/preview-oriented unless corresponding config is enabled.
- Worker is dry-run scaffold only; it returns "Enrollware creation not wired" for creation path.
- Public schedule should not depend on appointment URL creation as the scheduling brain yet.

### Dynamic Availability Impact

If dynamic availability generated appointment options, the bridge would need:

- trusted offer storage keyed by stable offer ID/slug
- click-time availability recheck against the same solver inputs
- explicit course ID allowlist confirmed by Brian/Enrollware
- appointmentDayId range validation per instructor/location/container
- rate limiting and locking
- clear distinction between "offer displayed" and "Enrollware registration opened"
- audit log and hot-sync absorption path so generated offers do not diverge from Enrollware roster reality

## 6. Scheduling Constraints Already Present

| Constraint | Status | Evidence / Notes |
|---|---|---|
| Instructor availability | Present but incomplete | `data/inventory/instructor_availability.json` has prototype blocks. `data/config/calendar_sources.json` declares explicit/inverse calendar modes. Needs authoritative production model. |
| Instructor qualification | Present but incomplete | `instructor_certification_ceiling`, allowed/fallback families in inventory blocks. Needs per-instructor credential source and expiration handling. |
| Location / room availability | Present but incomplete | Inventory blocks include `location_name` and `room_or_resource_name`; appointment containers include location/resource metadata. Needs room calendar/resource ownership model. |
| Resource conflicts | Present but incomplete | Inventory controller checks block overlap in simple time intervals. Full room/resource conflict model is not complete. |
| Course duration | Present and usable | `data/inventory/course_consumption_rules.json`; `free_time_scheduler.py` also uses `duration_minutes`/cleanup from templates. Needs one canonical duration source. |
| Course capacity | Present but incomplete | `default_capacity`, public schedule seats/students, Enrollware seats fields exist. Needs clear capacity math for generated offers vs existing classes. |
| Setup/cleanup buffers | Present but incomplete | `free_time_scheduler.py` evaluates cleanup/travel buffers; inventory rules focus on reservation blocks. Needs unified buffer policy. |
| Blocked/unavailable times | Present and usable for existing scheduler | `free_time_scheduler.py` loads calendar blocks and rejects overlaps. Calendar source declarations exist. Needs new solver adapter. |
| Google Calendar / ICS imports | Present but incomplete | `free_time_scheduler.py` has ICS parsing/fetching. `data/config/calendar_sources.json` declares sources and missing-access policies. Needs production credential/URL handling and tests. |
| DNS / Do Not Schedule markers | Present | Brian inverse blocking calendar declaration and DoNotSchedule handling in `free_time_scheduler.py`. |
| ADR / employment blocks | Present | `free_time_scheduler.py` tracks ADR blocks and Brian ADR blocks in debug/report counts. Needs clear ownership model in new solver. |
| Booked classes | Present | Existing sessions loaded through Class Report/live exports/schedule_future and Enrollware sync outputs. Needs canonical occupancy/reservation model. |
| Course/instructor/location compatibility | Present but incomplete | Inventory controller has allowed families and fallback logic; not yet integrated as canonical scheduler. |
| Dynamic public solver endpoint | Not found / scaffold only | Worker exists, but click-time recheck and creation are explicitly not wired. |

## 7. Current Visual / Design System

### Located UI Assets

- `docs/assets/hub-ui.js`
  - Major runtime UI behavior for hub pages.

- `docs/assets/booking-home.js`
  - Homepage schedule loading and display.

- `docs/assets/hybrid-inventory.js`
  - Browser appointment availability widget behavior.

- `docs/assets/session-expiry.js`, `docs/assets/live-sessions.js`
  - Runtime session pruning/sorting helpers.

- `docs/assets/theme-resolver.js`
  - Theme resolution behavior.

- `assets/css/site-theme.css`
  - Theme variables and gradient-heavy style overrides.

- `docs/assets/themes/`
  - Theme assets folder.

- Generated HTML from Python builders
  - Several templates are embedded directly in builder scripts, especially `build_slug_hubs.py` and page builders.

### Why Current UI May Feel Cartoonish

- Heavy gradients, chips, large rounded pills, alert-style banners, and many visual treatments compete for attention.
- Some generated pages mix routing, trust, schedule, emergency, flexible inventory, and registration concerns in one page.
- Styling is distributed between generated HTML, runtime JS expectations, and CSS/theme overrides.
- Some labels/buttons are operational/debug-like ("Request This Time", preview-only, emergency fallback) rather than polished customer-facing product language.
- Long mobile pages can arise when many course families or schedule groups render together.

### Premium Design Opportunities

- Establish one small design-token layer: color, spacing, radius, shadow, typography, border.
- Use mostly white/neutral surfaces, restrained blue/teal accent, and fewer gradients.
- Separate page types:
  - course chooser
  - course detail
  - format selector
  - schedule results
  - admin/review
- Prefer compact cards/tables with strong hierarchy over chip-heavy walls.
- Keep status/preview/admin language out of public customer UI.
- Make mobile-first schedule selection one column with short sections.

## 8. Cloudflare / Hosting / Worker Readiness

### Hosting Found

- `docs/` static site appears to be served by GitHub Pages.
- `docs/CNAME` exists per runbook notes.
- `wrangler.toml` exists for a Cloudflare Worker named `free-time-offer-worker`.
- `worker/free-time-offer-worker.js` exists.
- `worker/FREE_TIME_WORKER_DEPLOY_NOTES.md` documents dry-run behavior and safe deploy command.
- `render.yaml` exists for a separate Facebook post machine admin web service, not the schedule solver.

### Existing API / Server Code

- Cloudflare Worker scaffold:
  - `GET /o/<offer_slug>`
  - `GET /check-time`
  - `POST /open-registration`
  - trusted offer lookup via KV/D1/OFFER_DATA_JSON
  - local/static fallback behavior
  - creation disabled

- Local/admin servers:
  - `scripts/json_admin_server.py`
  - `scripts/inventory_control_admin_server.py`
  - likely intended for local/admin use, not public production scheduling.

### Needed For Lightweight Dynamic Scheduler Endpoint

- A read-only solver endpoint first: input course family/format/location/date range, output sellable options.
- Server-side access to trusted availability data, not public HTML scraping.
- Cache strategy for public requests.
- Signed/admin-only mutation path if any write occurs.
- Durable storage for offer IDs, click-time locks, and audit logs.
- Hard fail-closed behavior when calendar or Enrollware data is stale/unavailable.

## 9. Recommended Next-Phase Architecture

### Keep Static

- SEO course pages, location pages, course-at-city pages, informational pages, sitemap.
- Course chooser/routing pages.
- General course descriptions and "which class do I need?" content.
- Public fallback schedule views from last known safe data.

### Make Dynamic

- Availability solving.
- Sellable option generation.
- Click-time recheck.
- Admin overlay/review view.
- Requestable appointment confirmation/open-registration bridge.

### Google Calendar Should Control

- Instructor availability windows where explicit calendars are used.
- Brian inverse blocking / Do Not Schedule blocks.
- Personal/employment/ADR blocks if they are reliable calendar feeds.
- Room/resource calendars if adopted.

Google Calendar should not own course duration, course compatibility, capacity, course IDs, or Enrollware roster truth.

### Enrollware Should Continue To Handle

- Roster/enrollment/payment endpoint.
- Official enrolled/seat counts until replaced.
- Existing class registration URLs.
- Course IDs and class IDs as confirmed external identifiers.

Enrollware should not be the scheduling brain for generated options.

### Lander Scheduler Engine Should Own

- Normalized availability windows.
- Course duration/format/eligibility rules.
- Instructor qualification matching.
- Room/resource constraints.
- Existing class occupancy and momentum.
- Candidate generation and ranking.
- Public-safe offer publication.
- Auditability and admin review state.

## 10. Implementation Phases

### Phase 1: Inventory And Safety Rails

- Confirm active build command and active public data sources.
- Freeze current source-of-truth file list.
- Add read-only audits for stale/missing schedule files.
- Document every dynamic/preview flag and ensure default fail-closed behavior.
- Confirm Enrollware course IDs with Brian; do not infer missing IDs.

### Phase 2: Data Model For Availability / Occupancy / Courses

- Create canonical normalized models:
  - course definition
  - course format
  - instructor qualification
  - availability window
  - room/resource
  - existing booking
  - sellable offer
  - suppression/rejection reason
- Consolidate course duration/capacity into one source.
- Map legacy schedule/current session fields into the new model.

### Phase 3: Read-Only Dynamic Availability Preview

- Build a local read-only solver that consumes static snapshots and calendar feeds.
- Output preview JSON and admin-readable rejection report.
- No public page changes yet.
- Compare solver output to current `schedule_future.json` and Enrollware classes.

### Phase 4: Admin Overlay Calendar / View

- Generate or serve an internal admin view showing:
  - availability windows
  - DNS/ADR/personal blocks
  - booked classes
  - candidate sellable options
  - rejected candidates with reasons
- Keep it read-only until Brian signs off.

### Phase 5: Public Schedule UI Redesign

- Redesign public schedule as:
  - choose course family
  - choose format
  - view matching dates
- Use premium clinical/professional design tokens.
- Keep registration links untouched unless generated by approved bridge.

### Phase 6: Appointment / Enrollment Bridge

- Promote Worker from scaffold to controlled bridge only after solver and admin review are trusted.
- Use server-side trusted offer lookup and click-time recheck.
- Enable deterministic appointment URLs only for confirmed course IDs/ranges.
- Keep Enrollware class creation disabled until an explicit write-path spec exists.

### Phase 7: Production Hardening

- Monitoring and audit logs.
- Rate limits and locking.
- Stale data fail-closed policy.
- Rollback plan.
- Secret management and environment validation.
- End-to-end tests for safe public offer publication.

## Safest Starting Point

Start with a read-only solver audit module that consumes:

- `data/config/course_map.json`
- `data/inventory/course_consumption_rules.json`
- `data/inventory/availability_window_policies.json`
- `data/config/calendar_sources.json`
- `data/sessions_current.json`
- `docs/data/schedule_future.json`

It should write only to `debug/` or `data/audit/` and should not modify generated pages or Enrollware behavior.

## Biggest Risks

- Multiple build paths can write overlapping schedule/session outputs.
- `data/sessions_current.json` has more than one possible writer.
- Missing or stale `docs/data/customer_facing_offers.json` can make generated public behavior differ from debug reports.
- Course ID mapping has authoritative, alias, debug, and legacy sources; only confirmed config should drive public registration.
- Worker exists but is not production-ready for creation/recheck.
- Public pages are static; changes require rebuild and deploy, while runtime JS can hide or alter behavior after load.
- Debug reports can look operational but may be historical.

## Missing Information Needed From Brian

- Confirm which Enrollware course IDs are safe for deterministic appointment URLs.
- Confirm whether overnight appointments should be publicly sellable for each course family/format.
- Confirm instructor qualification matrix and expiration dates.
- Confirm room/resource constraints for Shipyard and any other locations.
- Confirm whether Google Calendar should use explicit availability, inverse blocking, or both per instructor.
- Confirm source of truth for occupied seats/registrations.
- Confirm whether the future system should create Enrollware classes automatically or only route to pre-created appointment containers.
- Confirm desired premium public schedule UX priorities: fastest booking, highest-margin classes first, already-forming first, or requirement-driven routing first.
