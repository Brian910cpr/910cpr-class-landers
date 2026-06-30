# Public booking destination audit

Audit-only plus bridge-page copy cleanup. No deploy was performed and booking behavior was not changed.

## Counts
- total_booking_buttons_scanned: 2766
- booking_destination_counts_by_category: {'C_910cpr_bridge_detail_page': 1427, 'B_direct_reviewed_appointment_seed': 60, 'A_direct_real_enrollware_class': 1279}
- bridge_row_count: 1427
- bridge_page_count: 296
- invalid_destination_count: 0
- bridge_invalid_final_url_count: 0
- invalid_appointment_href_count: 0
- appointmentDayId_missing_courseId_count: 0
- appointmentDayId_missing_startTime_count: 0

## HSI BLS Challenge row
- `docs/hsi.html` 2026-08-14T12:45:00-04:00 -> `/classes/13601272.html#ForwardToEnrollware` -> final `https://coastalcprtraining.enrollware.com/enroll?id=13601272` valid=True category=C_910cpr_bridge_detail_page
- `docs/classes/12776866.html`  -> `https://coastalcprtraining.enrollware.com/enroll?id=13601272` -> final `https://coastalcprtraining.enrollware.com/enroll?id=13601272` valid=True category=A_direct_real_enrollware_class
- `docs/classes/13601272.html`  -> `https://coastalcprtraining.enrollware.com/enroll?id=13601272` -> final `https://coastalcprtraining.enrollware.com/enroll?id=13601272` valid=True category=A_direct_real_enrollware_class
- `docs/classes/index.html`  -> `https://coastalcprtraining.enrollware.com/enroll?id=13601272` -> final `https://coastalcprtraining.enrollware.com/enroll?id=13601272` valid=True category=A_direct_real_enrollware_class
- `docs/locations/nc-wilmington-4018-shipyard-blvd-room-b-910cpr-s-office.html`  -> `/classes/13601272.html#ForwardToEnrollware` -> final `https://coastalcprtraining.enrollware.com/enroll?id=13601272` valid=True category=C_910cpr_bridge_detail_page
- `docs/topics/hsi.html`  -> `https://coastalcprtraining.enrollware.com/enroll?id=13601272` -> final `https://coastalcprtraining.enrollware.com/enroll?id=13601272` valid=True category=A_direct_real_enrollware_class
- `docs/topics-year/hsi-2026.html`  -> `https://coastalcprtraining.enrollware.com/enroll?id=13601272` -> final `https://coastalcprtraining.enrollware.com/enroll?id=13601272` valid=True category=A_direct_real_enrollware_class

## Findings
- Direct Enrollware rows use `/enroll?id=<class_id>`.
- Reviewed appointment seeds use `/enroll?appointmentDayId=<id>&startTime=<time>&courseId=<course_id>`.
- Bridge/detail rows use local `/classes/<class_id>.html` pages, sometimes with `#ForwardToEnrollware`, and the scanned bridge pages contain final Enrollware `/enroll?id=<class_id>` URLs.
- The HSI BLS Challenge bridge behavior is valid-looking and preserves the extra detail page before registration.

## Invalid examples
- None.

## Validation scan
- Invalid appointment-only href count: 0
- appointmentDayId missing courseId count: 0
- appointmentDayId missing startTime count: 0
- Rendered visible text hits for blocked phrases: {}
