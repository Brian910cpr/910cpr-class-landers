# First Successful Dynamic Booking Status

Status: read-only diagnostic. This runner does not modify public pages, call Enrollware, create appointments, change appointment URLs, enable Worker routes, deploy, or commit.

## Summary

- First failing link: 8
- Current blocker: No created dynamic class has been observed in local sessions yet.
- Next single action: Run existing read-only hot-sync/scrape after a manual test booking exists.

## Success Chain

| # | Stage | Status | Current value | Blocker |
|---:|---|---|---|---|
| 1 | Live calendar availability produces at least one Brian offerable-time block | PASS | `5` |  |
| 2 | Dynamic offers are generated from live availability | PASS | `{"availability_source_used": "live_availability_snapshot", "offers_generated": 640, "brian_shipyard_offers": 340}` |  |
| 3 | Confirmed-container public filter keeps at least one offer | PASS | `{"public_sellable_offers_kept": 83, "container_hidden_reasons": {"missing_container_for_instructor": 300}}` |  |
| 4 | Seed selection selects at least one seed | PASS | `{"seeds_selected": 5, "input_offers_read": 83}` |  |
| 5 | Deterministic appointment URL preview generates at least one URL | PASS | `{"urls_previewed": 5, "seeds_blocked": 0, "blocked_by_reason": {}}` |  |
| 6 | Internal/admin preview shows the customer-facing button | PASS | `{"preview_rows_rendered": 5, "urls_matched": 5, "missing_urls": 0}` |  |
| 7 | Manual click/registration creates class in Enrollware | PASS | `{"matched_registration_signals": 2, "matched_seed_ids": ["seed-offer-209806-instructor_24057895173-20260621-1700", "seed-offer-209806-instructor_24057895173-20260621-1700"], "courseSchedIds": ["13657403"]}` |  |
| 8 | Routine public Enrollware scrape/hot-sync sees the created class | FAIL | `"manual_not_confirmed"` | No created dynamic class has been observed in local sessions yet. |
| 9 | Lander treats that class as real occupancy and recalculates around it | FAIL | `{"sessions_current_count": 255, "schedule_future_count": 249}` | No dynamic test class marker is present to verify recalculation around it. |
| 10 | Class Report later confirms roster details | FAIL | `{"class_report_rows_read": 255, "sessions_current_written": 255}` | Current Class Report ingest exists, but no dynamic test booking can be identified yet. |

## Files Read

- live_availability: `E:\GitHub\910cpr-class-landers\data\audit\live_availability_snapshot_preview.json`
- dynamic_offers: `E:\GitHub\910cpr-class-landers\data\audit\dynamic_offers_preview.json`
- public_sellable_offers: `E:\GitHub\910cpr-class-landers\data\audit\public_sellable_offers_preview.json`
- schedule_seeds: `E:\GitHub\910cpr-class-landers\data\audit\schedule_seeds_preview.json`
- seed_url_preview: `E:\GitHub\910cpr-class-landers\data\audit\seed_appointment_url_preview.json`
- internal_dynamic_seed_preview: `E:\GitHub\910cpr-class-landers\data\audit\internal_dynamic_seed_preview.json`
- appointment_seed_registration_matches: `E:\GitHub\910cpr-class-landers\data\audit\appointment_seed_registration_matches.json`
- sessions_current: `E:\GitHub\910cpr-class-landers\data\sessions_current.json`
- schedule_future: `E:\GitHub\910cpr-class-landers\docs\data\schedule_future.json`
- class_report_ingest: `E:\GitHub\910cpr-class-landers\data\audit\class_report_ingest_summary.json`
