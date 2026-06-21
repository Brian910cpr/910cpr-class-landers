# Scheduler Pipeline Operator Runbook

Status: read-only operator runbook. This pipeline does not modify public pages, call Enrollware, create appointments, enable Worker routes, deploy, or wire public buttons.

## Current Read-Only Pipeline Order

Run from the repo root:

```powershell
python -m scripts.export_calendar_snapshots
python -m scripts.build_live_availability_snapshot
python -m scripts.generate_dynamic_offers
python -m scripts.filter_public_sellable_offers
python -m scripts.select_schedule_seeds
python -m scripts.build_seed_appointment_url_preview
```

## Step 1: Export Calendar Snapshots

Command:

```powershell
python -m scripts.export_calendar_snapshots
```

Reads:

- `data/config/calendar_sources.json`
- `data/config/people_catalog.json`
- Optional private local file: `data/private/calendar_secrets.local.json`
- Optional environment variables:
  - `AMY_AVAILABILITY_ICS_URL`
  - `NICK_AVAILABILITY_ICS_URL`
  - `BRIAN_BLOCKING_CALENDAR_ICS_URL`

Writes:

- `data/runtime/calendar_snapshots/{source_id}.json`
- `data/audit/calendar_snapshot_export_summary.json`
- `data/audit/calendar_snapshot_export_report.md`

Safe success looks like:

- Calendar sources found is greater than zero.
- Snapshots are written under `data/runtime/calendar_snapshots/`.
- Events exported per source are plausible.
- Private event descriptions are not printed to terminal or reports.
- Failed calendars explain whether Secret iCal URL or Google API auth is likely needed.

## Step 2: Build Live Availability Snapshot

Command:

```powershell
python -m scripts.build_live_availability_snapshot
```

Reads:

- `data/config/calendar_sources.json`
- `data/config/people_catalog.json`
- `data/config/course_catalog.json`
- `data/audit/live_availability_recheck_requirements.json`
- Preferred runtime snapshots: `data/runtime/calendar_snapshots/*.json`
- Legacy fallback snapshots if runtime snapshots are absent:
  - `data/calendar/live_calendar_events_snapshot.json`
  - `data/audit/live_calendar_events_snapshot.json`
  - `data/inventory/live_calendar_events_snapshot.json`

Writes:

- `data/audit/live_availability_snapshot_preview.json`
- `data/audit/live_availability_snapshot_report.md`

Safe success looks like:

- Configured calendar sources are found.
- Amy and Brian map to people records when present.
- Live availability blocks are generated from runtime calendar snapshots.
- DNS markers are counted if present.
- Missing or empty calendars are explained rather than treated as open availability.

## Step 3: Generate Dynamic Offers

Command:

```powershell
python -m scripts.generate_dynamic_offers
```

Reads:

- `data/config/course_catalog.json`
- `data/config/people_catalog.json`
- `data/inventory/instructor_availability.json`
- `data/sessions_current.json`
- `docs/data/schedule_future.json`

Writes:

- `data/audit/dynamic_offers_preview.json`
- `data/audit/dynamic_offers_report.md`

Safe success looks like:

- Scheduler-enabled instructors are considered.
- Courses with valid duration, capacity, appointment eligibility, and instructor qualification are considered.
- Dynamic offers are generated only inside known availability windows.
- Rejections are grouped by practical blocker reason.

Known limitation:

- `scripts.generate_dynamic_offers.py` may still need to prefer `data/audit/live_availability_snapshot_preview.json` over the older `data/inventory/instructor_availability.json`. Until that is updated, the live calendar snapshot may be built successfully but not yet drive generated offers.

## Step 4: Filter Public Sellable Offers

Command:

```powershell
python -m scripts.filter_public_sellable_offers
```

Reads:

- `data/audit/dynamic_offers_preview.json`
- `data/config/course_catalog.json`
- `data/config/public_offer_policy.json`

Writes:

- `data/audit/public_sellable_offers_preview.json`
- `data/audit/public_sellable_offers_report.md`

Safe success looks like:

- Dynamic offers are read.
- Public policy keeps only allowed course families, lead times, start times, and capacity modes.
- Hidden offers are preserved with reasons.
- Public sellable offer counts are small enough to review.

## Step 5: Select Schedule Seeds

Command:

```powershell
python -m scripts.select_schedule_seeds
```

Reads:

- `data/audit/public_sellable_offers_preview.json`
- `data/config/seed_strategy_policy.json`

Writes:

- `data/audit/schedule_seeds_preview.json`
- `data/audit/schedule_seeds_report.md`

Safe success looks like:

- Seeds are selected as intentional schedule seeds, not every possible offer.
- Mix goals by date and family are reported.
- Amy advanced-course timing rules are enforced.
- Hidden offers include strategy reasons.

## Step 6: Build Seed Appointment URL Preview

Command:

```powershell
python -m scripts.build_seed_appointment_url_preview
```

Reads:

- `data/audit/schedule_seeds_preview.json`
- `data/config/course_catalog.json`
- `data/inventory/appointment_containers.json`

Writes:

- `data/audit/seed_appointment_url_preview.json`
- `data/audit/seed_appointment_url_report.md`

Safe success looks like:

- Selected seeds are read.
- Appointment containers are matched.
- AppointmentDayId values are computed from trusted local container config.
- Deterministic Enrollware URLs are previewed only.
- `seeds_blocked` is zero or every blocked seed has a clear reason.

## What Is Still Not Live

- Public pages are not using this pipeline.
- Public buttons are not wired to dynamic seeds.
- The Worker `/api/recheck-seed` route is not enabled.
- Enrollware appointment/class creation is not enabled.
- Google API click-time recheck is not implemented.
- The Worker does not redirect customers to dynamic appointment URLs.

## Safe Success Checklist

Before treating a run as useful for review:

- Calendar events exported.
- Live availability blocks generated.
- Dynamic offers generated.
- Public sellable offers filtered.
- Seeds selected.
- Appointment URLs previewed.
- Seeds blocked is zero or explained.
- No public files changed.
- No Enrollware network calls occurred.
- No Worker routes were enabled.
- No deployment occurred.

## Rollback And Safety Notes

- All current outputs are local preview/audit files under `data/audit/` and `data/runtime/`.
- If a run looks wrong, do not publish or wire anything. Delete or ignore the affected preview files and rerun after correcting config.
- Do not commit private calendar feed URLs.
- Keep secrets in environment variables or ignored local files such as `data/private/calendar_secrets.local.json`.
- Do not trust browser-submitted appointment URLs. The Worker must eventually rebuild URLs server-side from trusted appointment container config.
- Do not treat missing calendar data as open availability.
- Do not enable Worker routing without explicit manual approval.
- Do not wire public buttons until the internal preview page and local Worker recheck pass.

## Next Activation Phases

1. Wire dynamic offer generation to prefer the live availability snapshot.
2. Build an internal preview page for Brian/admin review only.
3. Enable the Worker recheck endpoint locally only, behind an explicit disabled-by-default flag.
4. Wire public page behavior behind a feature flag.
5. Deploy to production only after manual approval and a rollback plan.

## Next Safest Implementation Step

Update `scripts.generate_dynamic_offers.py` so it reads `data/audit/live_availability_snapshot_preview.json` as the preferred availability source when present and valid, while retaining `data/inventory/instructor_availability.json` as an explicit fallback. Keep the output read-only and add tests proving old availability data is not used when a valid live snapshot exists.

