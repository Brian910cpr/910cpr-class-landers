# BLS seed render handoff trace

## Plain answer
Selected seed URL previews were valid, but URL-preview seed rows did not carry BLS tab IDs into the slug hub tab renderer. The page builder only renders appointment seeds inside a tab when tab_ids or the course_key mapping matches that tab.

The first disappearing stage before this fix was `scripts/build_slug_hubs.py` in `appointment_offers_for_tab`: selected BLS URL-preview rows reached the BLS hub list but did not carry tab IDs, and their Course Catalog keys did not match the older tab mapping keys.

## Counts
- August BLS public sellable candidates: 24
- August AHA BLS enabled-course public sellable candidates: 18
- August BLS selected seeds: 4
- August BLS URL previews: 4
- Selected August BLS rendered before fix: 0
- Selected August BLS rendered after fix: 4
- Duplicate selected seed rows after fix: 0

## Page inventory source
- Builder: `scripts/build_slug_hubs.py`
- Real Enrollware/Class Report rows: `docs/data/schedule_future.json` or canonical Class Report schedule when authoritative.
- Selected appointment seed rows: `data/audit/seed_appointment_url_preview.json`.
- Candidate pool only: `data/audit/public_sellable_offers_preview.json`.
- Output page: `docs/bls.html`.

## Fix
Selected URL-preview seed rows now carry tab IDs, `seed_id`, `source_offer_id`, and `appointmentDayId` into the existing slug hub tab renderer. No public policy gates or course IDs were loosened.
