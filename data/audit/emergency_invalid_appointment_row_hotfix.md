# Emergency Invalid Appointment Row Hotfix

Generated: 2026-06-30T16:26:50
Branch: `codex/emergency-invalid-appointment-row-hotfix`
Deploy performed: no

## Result

Ready for emergency deploy: yes

## Source Trace

- First bad source: `scripts/build_appointment_offer_inventory.py::appointment_mapping_for`
- Acceptance stage: `scripts/build_hub_offer_model_report.py::seed_display_classification`
- Public render stage: `scripts/build_slug_hubs.py::is_renderable_appointment_seed_offer / render_appointment_seed_offer_card`
- Why allowed before: Public render eligibility required a non-empty appointment_registration_url but did not require startTime and courseId query parameters.

## Before / After

- Broken rows found before: 5
- Invalid appointment rows after: 0
- appointmentDayId-only public rows after: 0
- BLS shipyard-only rows after: 0
- Selected seed rows after: 6
- Real Enrollware/link rows after: 108
- Duplicate href rows after: 0
- Invalid Book This Class URL remains: False

## Fix

- Added centralized guard: `scripts/build_slug_hubs.py::is_valid_appointment_seed_registration_url`
- Suppresses: appointmentDayId-only or incomplete appointment tuple URLs before public rendering
- Preserves: real /enroll?id rows and reviewed selected seed rows with appointmentDayId/startTime/courseId

## Validation

- public_offer_integrity_audit: PASS Audit failed: False
- audit_august_bls_seed_quality: PASS selected/rendered 6
- audit_bls_seed_time_preference: PASS rendered 6 duplicate 0
- audit_bls_public_offer_policy_enablement: PASS selected 6
- unittest_discover: PASS 165 tests OK
- rendered_html_scan: PASS no incomplete appointmentDayId hrefs; no shipyard-only BLS rows
