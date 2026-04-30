# 910CPR Data Flow Map

## Source Of Truth
- `data/Class Report.xlsx` (authoritative session list)

## Canonical Build Flow
1. `scripts/prebuild_cleanup_validate.py`
2. `scripts/build_sessions_current.py` -> `data/sessions_current.json`
3. `scripts/build_schedule_future.py` -> `docs/data/schedule_future.json`
4. Page builders read `docs/data/schedule_future.json` and render outputs

## Session ID Origin
- Primary: `Registration Link` query param `id=...` in `Class Report.xlsx`
- Fallback: `ID` column in `Class Report.xlsx`

## Files That Write Schedule-Like JSON
- `scripts/build_sessions_current.py` writes:
  - `data/sessions_current.json`
- `scripts/build_schedule_future.py` writes:
  - `docs/data/schedule_future.json`
- `scripts/build_schedule_json.py` writes (configured output):
  - often `data/schedule.json`
- `scripts/build_public_schedule_compat.py` writes:
  - `docs/data/public_schedule.json`

## Files That Read Schedule-Like JSON
- `scripts/build_schedule_future.py` reads:
  - `data/sessions_current.json`
- `scripts/build_landers.py` reads:
  - `docs/data/schedule_future.json`
  - `data/schedule.json` (full-data fallback/reference)
- `scripts/build_slug_hubs.py` reads:
  - `docs/data/schedule_future.json`
  - `data/sessions_current.json`
- `scripts/build_course_landers.py` reads:
  - `docs/data/schedule_future.json`
- `scripts/build_index_and_sitemap.py` reads:
  - `docs/data/schedule_future.json`
- `scripts/build_index.py` reads:
  - `docs/data/schedule.json`
- `scripts/build_public_schedule_json.py` reads:
  - `data/schedule.json` (fallback `docs/data/schedule.json`)
- `scripts/build_public_schedule_compat.py` reads:
  - `data/schedule.json`
- `scripts/build_sessions.py` reads:
  - `data/schedule.json`
- `scripts/build_sessions_from_public.py` reads:
  - `docs/data/public_schedule.json`
- `docs/assets/booking-home.js` fetches:
  - `/data/public_schedule.json`
  - `/public_schedule.json`
  - `/data/schedule_future.json`

## Duplicate / Alternate Schedule Sources Found
- `data/sessions_current.json`
- `docs/data/schedule_future.json`
- `docs/data/schedule.json`
- `data/schedule.json`
- `docs/data/public_schedule.json`
- `docs/public_schedule.json`
- `docs/data/schedule_future----Revert!!.json` (backup/legacy copy)

## Conflicting Paths / Risk Flags
- `scripts/build_sessions_current.py` previously preferred `data/raw/Class Report.xlsx` over `data/Class Report.xlsx` (fixed).
- `docs/data/schedule_future----Revert!!.json` is a stale alternate source and should never be used.
- `data/schedule.json` is referenced by older scripts and may not be regenerated in every run unless explicitly built.
- `docs/public_schedule.json` and `docs/data/public_schedule.json` can drift if only one is rebuilt.

## Not Regenerated Every Run (Flagged)
- `docs/data/schedule_future----Revert!!.json`
- `docs/public_schedule.json` (unless explicit public schedule build step runs)
- `data/schedule.json` (unless explicit schedule-json build runs)
