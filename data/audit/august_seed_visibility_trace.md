# August Seed Visibility Trace

## BLS Pipeline

| stage | input_files | output_files | total_count | august_count | notes |
|---|---|---|---|---|---|
| raw_class_report | data/raw/classes_raw_live.csv |  | 545 | 3 | Existing Enrollware class safety-net rows. |
| visible_rendered_pages | docs/bls.html; docs/acls.html; docs/pals.html; docs/courses/heartsaver-first-aid-cpr-aed.html; docs/courses/heartsaver-cpr-aed.html; docs/courses/heartsaver-pediatric-first-aid-cpr-aed.html; docs/heartsaver.html; docs/hsi.html; docs/arc.html | docs/*.html | 227 | 8 | Rows parsed from customer-facing stacked pages. |
| dynamic_offers | data/audit/dynamic_offers_preview.json | data/audit/dynamic_offers_preview.json | 690 |  |  |
| public_sellable | data/audit/public_sellable_offers_preview.json | data/audit/public_sellable_offers_preview.json | 14 |  |  |
| schedule_seeds | data/audit/schedule_seeds_preview.json | data/audit/schedule_seeds_preview.json |  |  |  |
| seed_url_preview | data/audit/seed_appointment_url_preview.json | data/audit/seed_appointment_url_preview.json |  |  |  |
| internal_dynamic_seed_preview | data/audit/internal_dynamic_seed_preview.json | data/audit/internal_dynamic_seed_preview.json |  |  |  |
| presentation_policy | data/audit/dynamic_offer_presentation_policy_report.json | data/audit/dynamic_offer_presentation_policy_report.json | 5 |  |  |
| rendered_proof | data/audit/rendered_dynamic_offer_proof.json | data/audit/rendered_dynamic_offer_proof.json | 5 |  |  |
| schedule_future | docs/data/schedule_future.json | docs/data/schedule_future.json | 220 | 3 |  |
| sessions_current | data/sessions_current.json | data/sessions_current.json |  |  | File missing or non-row output. |
| slug_hubs | data/config/slug_hubs.json | data/config/slug_hubs.json |  |  |  |
| course_catalog | data/config/course_catalog.json | data/config/course_catalog.json |  |  |  |
| course_map | data/config/course_map.json | data/config/course_map.json |  |  |  |

## Heartsaver Pipeline

| stage | input_files | output_files | total_count | august_count | notes |
|---|---|---|---|---|---|
| raw_class_report | data/raw/classes_raw_live.csv |  | 545 |  | Existing Enrollware class safety-net rows. |
| visible_rendered_pages | docs/bls.html; docs/acls.html; docs/pals.html; docs/courses/heartsaver-first-aid-cpr-aed.html; docs/courses/heartsaver-cpr-aed.html; docs/courses/heartsaver-pediatric-first-aid-cpr-aed.html; docs/heartsaver.html; docs/hsi.html; docs/arc.html | docs/*.html | 227 |  | Rows parsed from customer-facing stacked pages. |
| dynamic_offers | data/audit/dynamic_offers_preview.json | data/audit/dynamic_offers_preview.json | 690 |  |  |
| public_sellable | data/audit/public_sellable_offers_preview.json | data/audit/public_sellable_offers_preview.json | 14 |  |  |
| schedule_seeds | data/audit/schedule_seeds_preview.json | data/audit/schedule_seeds_preview.json |  |  |  |
| seed_url_preview | data/audit/seed_appointment_url_preview.json | data/audit/seed_appointment_url_preview.json |  |  |  |
| internal_dynamic_seed_preview | data/audit/internal_dynamic_seed_preview.json | data/audit/internal_dynamic_seed_preview.json |  |  |  |
| presentation_policy | data/audit/dynamic_offer_presentation_policy_report.json | data/audit/dynamic_offer_presentation_policy_report.json | 5 |  |  |
| rendered_proof | data/audit/rendered_dynamic_offer_proof.json | data/audit/rendered_dynamic_offer_proof.json | 5 |  |  |
| schedule_future | docs/data/schedule_future.json | docs/data/schedule_future.json | 220 |  |  |
| sessions_current | data/sessions_current.json | data/sessions_current.json |  |  | File missing or non-row output. |
| slug_hubs | data/config/slug_hubs.json | data/config/slug_hubs.json |  |  |  |
| course_catalog | data/config/course_catalog.json | data/config/course_catalog.json |  |  |  |
| course_map | data/config/course_map.json | data/config/course_map.json |  |  |  |
