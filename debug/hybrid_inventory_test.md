# Hybrid Inventory Test

Generated: 2026-04-28T00:27:05.320613-04:00

## Scheduled Inventory

- Total future scheduled sessions: 1486
- Sessions with enrolled_count >= 1: 17
- Sessions with direct `enroll?id=` registration URLs: 1486

## Hub Checks

- `bls.html`: popular=True, scheduled=True, flexible=True
- `acls.html`: popular=True, scheduled=True, flexible=True
- `pals.html`: popular=False, scheduled=True, flexible=True
- `heartsaver.html`: popular=True, scheduled=True, flexible=True

## Appointment Endpoint

- May 31, 2026 returned 12 enrollment URLs (HTTP 200)
- January 1, 2027 returned 10 enrollment URLs (HTTP 200)
- Access-Control-Allow-Origin header present: False

### Sample URLs

- https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=250514&startTime=12:00 AM&courseId=463119
- https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=250514&startTime=2:00 AM&courseId=463119
- https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=250514&startTime=4:00 AM&courseId=463119
- https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=250513&startTime=12:00 AM&courseId=463119
- https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=250513&startTime=2:00 AM&courseId=463119
- https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=250513&startTime=4:00 AM&courseId=463119

## Constraint

Enrollware did not advertise Access-Control-Allow-Origin in the tested response headers, so the on-page flexible inventory widget must fail gracefully and offer the live open-seat page when the browser blocks cross-origin POSTs.
