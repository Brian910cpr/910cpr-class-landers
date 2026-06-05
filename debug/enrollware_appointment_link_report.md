# Enrollware Appointment Link Test Report

- Generated at: 2026-06-05T07:54:08.087847-04:00
- Appointment links enabled: False
- Fail closed: True
- Formula: appointmentDayId = appointment_start_day_id + real calendar day offset from appointment_start_date
- No guessed IDs used: True

## Day ID Tests
- Brian 2026-06-21: expected 260670, got 260670 (PASS)
- Brian 2026-08-04: expected 260714, got 260714 (PASS)
- Brian 2026-08-14: expected 260724, got 260724 (PASS)
- Amy 2026-06-06: expected 261393, got 261393 (PASS)
- Amy 2026-06-07: expected 261394, got 261394 (PASS)
- Amy 2026-08-14: expected 261462, got 261462 (PASS)
- Nick 2026-06-06: expected 261013, got 261013 (PASS)
- Nick 2026-06-07: expected 261014, got 261014 (PASS)
- Nick 2026-08-14: expected 261082, got 261082 (PASS)

## URL Tests
- Brian 2026-08-14 12:45 PM bls: https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260724&startTime=12:45%20PM&courseId=209806 (PASS)

## Fail-Closed Tests
- date before configured start date: PASS (requested date is before instructor appointment start date)
- date after valid_through_date: PASS (requested date is after instructor valid_through_date)
- unknown instructor: PASS (instructor day base is missing for Unknown)
- missing course ID: PASS (course ID is missing for bls-renewal)
- invalid requested_start: PASS (requested_start is invalid)
- disabled outside explicit test mode: PASS (enrollware appointment links are disabled)

Missing course IDs: bls-renewal, heartcode-bls-skills
