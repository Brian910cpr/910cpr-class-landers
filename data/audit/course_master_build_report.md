# Course Master Build Report

Generated inventory/schema report. Course Master is not authoritative for production behavior yet.

## Recommendation

- Promote/rename `course_catalog.json` directly to `course_master.json`: `False`
- Generate `course_master.json` from `course_catalog.json` plus Enrollware export: `True`
- Keep `course_catalog.json` as legacy/source input only: `False`
- Summary: Use course_catalog.json as the preferred seed and current scheduler source, generate course_master.json as the normalized review layer, then promote after missing scheduler/rendering/export gaps are resolved.

## Counts

- Course records created: `30`
- Complete: `0`
- Needs review: `30`
- Incomplete: `0`
- Inactive: `0`

## Field Comparison

- Fields present in `course_catalog.json` but missing from `course-export.xlsx`: `appointment_allowed, appointment_container_required, blended_classroom_skills, classroom_only, cleanup_buffer_minutes, course_id, course_key, default_capacity, delivery_type, deterministic_url_supported, duration_minutes, family, known_appointmentDayId_range, manual_only, maximum_capacity, minimum_capacity, official_title, online_only, provider, relationships, renewal_or_initial, required_instructor_certifications, required_resources, setup_buffer_minutes, short_title, source_trace, subtype`
- Fields present in `course-export.xlsx` but missing from `course_catalog.json`: `Add-ons, Allows Unscheduled Students?, Card Type, Class Price, Description, Discipline, Keycode Bank, Name, Online Only?, Secondary Card Type, Shipping Price, eCard Code`
- Scheduling fields neither file provides fully: `setup_buffer_minutes, cleanup_buffer_minutes, scheduler_consumption_minutes`
- Public rendering fields neither file provides fully: `slug_page, hub_tab`

## Audit Answers

- Every public sellable dynamic offer resolves to Course Master: `True`
- Courses used by public sellable offers: `209806, 209808, 209809, 210549, 251545, 329495, 344085, 351632, 359474, 445670`
- Public sellable dynamic offers missing Course Master data: `none`
- Courses lacking duration/scheduler consumption: `209811, 241108, 209818, 369209, 410694, 444919, 248288, 248287, 209806, 359474, 210549, 440431, 374378, 422270, 371954, 463743, 448630, 449422, 344085, 209808, 209809, 329495, 351632, 251545, 209812, 209805, 251496, 253768, 359827`
- Courses lacking public page/tab mapping: `369209, 410694, 444919, 248288, 248287, 440431, 374378, 422270, 371954, 463743, 448630, 449422, 253768, 359827`
- Courses lacking Enrollware courseId: `none`
- Manual review fields before authoritative: `base_price, card_type, cleanup_buffer_minutes, hub_tab, scheduler_consumption_minutes, setup_buffer_minutes, slug_page`

## Most Common Missing Fields

- `setup_buffer_minutes`: `29`
- `cleanup_buffer_minutes`: `29`
- `scheduler_consumption_minutes`: `29`
- `base_price`: `28`
- `card_type`: `28`
- `slug_page`: `14`
- `hub_tab`: `14`
