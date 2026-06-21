# Hub Offer Model Report

> REPORT ONLY - NO PUBLIC PAGES, CTAS, ENROLLWARE LINKS, OR CLASS LANDERS MODIFIED

- Generated at: 2026-06-21T03:02:23.392081-04:00
- Source mode: auto
- Current Enrollware source: E:\GitHub\910cpr-class-landers\data\sessions_current.json
- Current Enrollware source available: True
- Hubs checked: 10
- Hubs with current Enrollware classes: 8
- Hubs with approved seed offers: 3
- Hubs with needs-review seed offers: 5
- Hubs empty: 2
- Current Enrollware classes suppressed by cutoff: 0
- Approved but not public ready: 0
- Hubs using current classes: 8
- Hubs using approved seed offers: 0
- Hubs using request CTA: 1
- Hubs using call-to-schedule: 1
- Hubs needs review: 0
- Hubs suppressing offer block: 0
- Empty-state type counts: {"show_call_to_schedule": 1, "show_current_classes": 8, "show_request_class_cta": 1}
- Suppressed offers by reason: {}

## Display Contract

- `current_enrollware_class`: real future Enrollware-backed class/session that can be modeled as a hub class offer.
- `approved_seed_offer`: report-only generated availability approved for public hub display; hub offer only, not a class lander.
- `needs_review_seed_offer`: generated availability with a valid publishable target but no public approval yet.
- `suppressed_approved_but_not_public_ready`: seed is approved, but its publication-mode readiness gate blocks display. Real class/session modes require current Enrollware presence; appointment seed mode requires a valid appointment URL and does not require current Enrollware presence.
- `suppressed_missing_enrollware`: Enrollware source is unavailable for validation.
- `suppressed_not_approved`: seed exists but approval state blocks public display.
- `suppressed_missing_registration_target`: seed lacks a valid registration target/publishability gate.
- `suppressed_cutoff_window`: Enrollware-backed offer is hidden from public display because it starts within the configured cutoff window; direct/manual registration may still be available.

## Empty-State Contract

- `show_current_classes`: current Enrollware-backed classes exist; show the normal class/session offer block.
- `show_approved_seed_offers`: no current classes, but approved hub-only seed offers are available.
- `show_request_class_cta`: no modeled offers; show a request-class path instead of fake dates.
- `show_call_to_schedule`: professional available-by-request/contact message.
- `show_check_back_soon`: neutral fallback when a public offer block is still appropriate.
- `suppress_hub_offer_block`: hide the offer block until real/approved offers exist.
- `needs_review`: no safe fallback rule was found.

## Hubs

### bls_dental_assistant_wilmington (seo_hubs)
- Path: /bls/dental-assistant-wilmington-nc
- Course key: aha_bls_initial
- Current Enrollware classes: 141
- Current classes suppressed by cutoff: 0
- Approved seed offers: 8
- Needs-review seed offers: 2
- Suppressed seed offers: 0
- Would appear empty: False
- Empty-state type: show_current_classes
- Empty-state headline: Current classes available
- Empty-state body: Show current Enrollware-backed class/session offers for this hub.
- Recommended CTA: View available classes -> existing_hub_schedule_block
- Caution flags: needs_review_seed_offers_exist
  - Current: 2026-06-22 12:30 PM - AHA BLS Provider (session 12774325)
  - Current: 2026-06-22 12:30 PM - AHA BLS Provider Renewal (session 12775527)
  - Current: 2026-06-22 6:15 PM - AHA BLS Provider Renewal (session 12775294)
  - Current: 2026-06-23 8:30 AM - AHA HeartCode BLS (session 12776273)
  - Current: 2026-06-23 11:45 AM - AHA HeartCode BLS (session 12776419)
  - Approved seed: 2026-08-03 1:00 PM - AHA BLS Initial (seed_f7b314e904b117e2)
  - Approved seed: 2026-08-03 9:00 AM - AHA BLS Renewal (seed_a551b998a0e43e79)
  - Approved seed: 2026-08-04 1:00 PM - AHA BLS Initial (seed_7457baba994578af)
  - Approved seed: 2026-08-04 9:00 AM - AHA BLS Renewal (seed_39f23793bbafaecc)
  - Approved seed: 2026-08-05 1:00 PM - AHA BLS Initial (seed_90b2c2b9dca23c00)
  - Needs review seed: 2026-08-05 11:00 AM - AHA BLS HeartCode Skills (seed_8db3493d37758377)
  - Needs review seed: 2026-08-05 9:00 AM - AHA BLS Renewal (seed_99a39ce1521a1dad)

### bls_healthcare_provider_wilmington (seo_hubs)
- Path: /bls/healthcare-provider-wilmington-nc
- Course key: aha_bls_initial
- Current Enrollware classes: 141
- Current classes suppressed by cutoff: 0
- Approved seed offers: 8
- Needs-review seed offers: 2
- Suppressed seed offers: 0
- Would appear empty: False
- Empty-state type: show_current_classes
- Empty-state headline: Current classes available
- Empty-state body: Show current Enrollware-backed class/session offers for this hub.
- Recommended CTA: View available classes -> existing_hub_schedule_block
- Caution flags: needs_review_seed_offers_exist
  - Current: 2026-06-22 12:30 PM - AHA BLS Provider (session 12774325)
  - Current: 2026-06-22 12:30 PM - AHA BLS Provider Renewal (session 12775527)
  - Current: 2026-06-22 6:15 PM - AHA BLS Provider Renewal (session 12775294)
  - Current: 2026-06-23 8:30 AM - AHA HeartCode BLS (session 12776273)
  - Current: 2026-06-23 11:45 AM - AHA HeartCode BLS (session 12776419)
  - Approved seed: 2026-08-03 1:00 PM - AHA BLS Initial (seed_f7b314e904b117e2)
  - Approved seed: 2026-08-03 9:00 AM - AHA BLS Renewal (seed_a551b998a0e43e79)
  - Approved seed: 2026-08-04 1:00 PM - AHA BLS Initial (seed_7457baba994578af)
  - Approved seed: 2026-08-04 9:00 AM - AHA BLS Renewal (seed_39f23793bbafaecc)
  - Approved seed: 2026-08-05 1:00 PM - AHA BLS Initial (seed_90b2c2b9dca23c00)
  - Needs review seed: 2026-08-05 11:00 AM - AHA BLS HeartCode Skills (seed_8db3493d37758377)
  - Needs review seed: 2026-08-05 9:00 AM - AHA BLS Renewal (seed_99a39ce1521a1dad)

### acls (slug_hubs)
- Path: /acls.html
- Course key: None
- Current Enrollware classes: 17
- Current classes suppressed by cutoff: 0
- Approved seed offers: 0
- Needs-review seed offers: 1
- Suppressed seed offers: 0
- Would appear empty: False
- Empty-state type: show_current_classes
- Empty-state headline: Current classes available
- Empty-state body: Show current Enrollware-backed class/session offers for this hub.
- Recommended CTA: View available classes -> existing_hub_schedule_block
- Caution flags: needs_review_seed_offers_exist
  - Current: 2026-06-22 2:00 PM - AHA ACLS Provider (Initial) (session 13472467)
  - Current: 2026-06-22 2:00 PM - AHA ACLS Provider (Renewal) (session 13472475)
  - Current: 2026-06-23 2:00 PM - AHA ACLS Provider (Initial) (session 13472468)
  - Current: 2026-06-23 2:00 PM - AHA ACLS Provider (Renewal) (session 13472476)
  - Current: 2026-06-26 2:00 PM - AHA ACLS Provider (Initial) (session 13472469)
  - Needs review seed: 2026-08-04 1:30 PM - ACLS HeartCode Skills (seed_bf300a7015f05101)

### arc (slug_hubs)
- Path: /arc.html
- Course key: None
- Current Enrollware classes: 0
- Current classes suppressed by cutoff: 0
- Approved seed offers: 0
- Needs-review seed offers: 0
- Suppressed seed offers: 0
- Would appear empty: True
- Empty-state type: show_call_to_schedule
- Empty-state headline: Red Cross classes are available by request
- Empty-state body: No current Red Cross class dates are modeled for this hub. Use a professional contact or group-training path instead of showing placeholder dates.
- Recommended CTA: Request Red Cross training -> /group-training.html
- Caution flags: do_not_show_fake_dates, empty_arc_hub
- Empty fallback message: No currently scheduled public offers are modeled for this hub yet. Students should use the current Enrollware-backed registration path.

### bls (slug_hubs)
- Path: /bls.html
- Course key: None
- Current Enrollware classes: 151
- Current classes suppressed by cutoff: 0
- Approved seed offers: 8
- Needs-review seed offers: 2
- Suppressed seed offers: 0
- Would appear empty: False
- Empty-state type: show_current_classes
- Empty-state headline: Current classes available
- Empty-state body: Show current Enrollware-backed class/session offers for this hub.
- Recommended CTA: View available classes -> existing_hub_schedule_block
- Caution flags: needs_review_seed_offers_exist
  - Current: 2026-06-22 12:30 PM - AHA BLS Provider (session 12774325)
  - Current: 2026-06-22 12:30 PM - AHA BLS Provider Renewal (session 12775527)
  - Current: 2026-06-22 6:15 PM - AHA BLS Provider Renewal (session 12775294)
  - Current: 2026-06-23 8:30 AM - AHA HeartCode BLS (session 12776273)
  - Current: 2026-06-23 11:45 AM - AHA HeartCode BLS (session 12776419)
  - Approved seed: 2026-08-03 1:00 PM - AHA BLS Initial (seed_f7b314e904b117e2)
  - Approved seed: 2026-08-03 9:00 AM - AHA BLS Renewal (seed_a551b998a0e43e79)
  - Approved seed: 2026-08-04 1:00 PM - AHA BLS Initial (seed_7457baba994578af)
  - Approved seed: 2026-08-04 9:00 AM - AHA BLS Renewal (seed_39f23793bbafaecc)
  - Approved seed: 2026-08-05 1:00 PM - AHA BLS Initial (seed_90b2c2b9dca23c00)
  - Needs review seed: 2026-08-05 11:00 AM - AHA BLS HeartCode Skills (seed_8db3493d37758377)
  - Needs review seed: 2026-08-05 9:00 AM - AHA BLS Renewal (seed_99a39ce1521a1dad)

### group-training (slug_hubs)
- Path: /group-training.html
- Course key: None
- Current Enrollware classes: 214
- Current classes suppressed by cutoff: 0
- Approved seed offers: 0
- Needs-review seed offers: 0
- Suppressed seed offers: 0
- Would appear empty: False
- Empty-state type: show_current_classes
- Empty-state headline: Current classes available
- Empty-state body: Show current Enrollware-backed class/session offers for this hub.
- Recommended CTA: View available classes -> existing_hub_schedule_block
- Caution flags: none
  - Current: 2026-06-22 12:30 PM - AHA BLS Provider (session 12774325)
  - Current: 2026-06-22 12:30 PM - AHA BLS Provider Renewal (session 12775527)
  - Current: 2026-06-22 2:00 PM - AHA ACLS Provider (Initial) (session 13472467)
  - Current: 2026-06-22 2:00 PM - AHA ACLS Provider (Renewal) (session 13472475)
  - Current: 2026-06-22 6:15 PM - AHA BLS Provider Renewal (session 12775294)

### heartsaver (slug_hubs)
- Path: /heartsaver.html
- Course key: None
- Current Enrollware classes: 59
- Current classes suppressed by cutoff: 0
- Approved seed offers: 0
- Needs-review seed offers: 0
- Suppressed seed offers: 0
- Would appear empty: False
- Empty-state type: show_current_classes
- Empty-state headline: Current classes available
- Empty-state body: Show current Enrollware-backed class/session offers for this hub.
- Recommended CTA: View available classes -> existing_hub_schedule_block
- Caution flags: none
  - Current: 2026-06-23 9:15 AM - AHA Heartsaver First Aid CPR AED (session 12775990)
  - Current: 2026-06-23 6:15 PM - AHA Heartsaver First Aid CPR AED (session 12776773)
  - Current: 2026-06-25 8:30 AM - AHA Heartsaver First Aid CPR AED - Blended (session 12776699)
  - Current: 2026-06-25 8:30 AM - AHA Heartsaver Pediatric First Aid CPR AED Online (session 12783390)
  - Current: 2026-06-25 9:15 AM - AHA Heartsaver First Aid CPR AED (session 13652911)

### hsi (slug_hubs)
- Path: /hsi.html
- Course key: None
- Current Enrollware classes: 1
- Current classes suppressed by cutoff: 0
- Approved seed offers: 0
- Needs-review seed offers: 0
- Suppressed seed offers: 0
- Would appear empty: False
- Empty-state type: show_current_classes
- Empty-state headline: Current classes available
- Empty-state body: Show current Enrollware-backed class/session offers for this hub.
- Recommended CTA: View available classes -> existing_hub_schedule_block
- Caution flags: none
  - Current: 2026-08-14 12:45 PM - HSI BLS Challenge (session 13601272)

### pals (slug_hubs)
- Path: /pals.html
- Course key: None
- Current Enrollware classes: 6
- Current classes suppressed by cutoff: 0
- Approved seed offers: 0
- Needs-review seed offers: 1
- Suppressed seed offers: 0
- Would appear empty: False
- Empty-state type: show_current_classes
- Empty-state headline: Current classes available
- Empty-state body: Show current Enrollware-backed class/session offers for this hub.
- Recommended CTA: View available classes -> existing_hub_schedule_block
- Caution flags: needs_review_seed_offers_exist
  - Current: 2026-06-23 2:00 PM - AHA PALS Provider (session 13472483)
  - Current: 2026-06-23 2:00 PM - AHA PALS Renewal (session 13472490)
  - Current: 2026-06-26 2:00 PM - AHA PALS Provider (session 13472484)
  - Current: 2026-06-26 2:00 PM - AHA PALS Renewal (session 13472491)
  - Current: 2026-07-01 12:00 AM - AHA - PALS Instructor Renewal (session 10009277)
  - Needs review seed: 2026-08-04 3:00 PM - PALS HeartCode Skills (seed_4e08b9a5ea5e8c69)

### uscg-elementary-first-aid-cpr (slug_hubs)
- Path: /uscg-elementary-first-aid-cpr.html
- Course key: None
- Current Enrollware classes: 0
- Current classes suppressed by cutoff: 0
- Approved seed offers: 0
- Needs-review seed offers: 0
- Suppressed seed offers: 0
- Would appear empty: True
- Empty-state type: show_request_class_cta
- Empty-state headline: Need this class for your group?
- Empty-state body: No current public class dates are modeled for this hub. Use a request path or contact workflow instead of showing fake dates.
- Recommended CTA: Request a class -> /group-training.html
- Caution flags: none
- Empty fallback message: No currently scheduled public offers are modeled for this hub yet. Students should use the current Enrollware-backed registration path.
