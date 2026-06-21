# Manual Enrollware Proof Result

Read-only proof. No public pages, Enrollware form submission, appointment creation, appointment URL change, Worker route, deploy, or commit was performed.

## Seed Tested

- Seed: `seed-offer-209806-instructor_24057895173-20260621-1700`
- Source offer: `offer-209806-instructor_24057895173-20260621-1700`
- Expected course: `AHA BLS Provider`
- Expected course ID: `209806`
- Expected appointmentDayId: `260670`
- Expected customer start: `2026-06-21 5:00 PM`
- Lander scheduler lock: `2026-06-21 5:00 PM` to `2026-06-21 7:45 PM`

## Enrollware Page Observed

- Page title: `Class Enrollment`
- URL remained: `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260670&startTime=5%3A00%20PM&courseId=209806`
- Course shown: `AHA BLS Provider (Initial)`
- Hidden course ID field: `209806`
- Date/time shown: `Sun 6/21/2026 from 5:00 PM to 6:00 PM`
- Location shown: `NC - Wilmington: 4018 Shipyard Blvd; Room B @ 910CPR's Office`
- Price shown: `$75.00`
- Registration button visible: `Continue with Registration`

## Result

- Correct registration path: yes
- Correct course: yes
- Correct appointment date: yes
- Correct customer-facing start time: yes
- Accidental appointment creation: no submit/continue action was performed

## Notes

- Enrollware displays a one-hour appointment block for this deterministic URL.
- This confirms the need for Lander's separate scheduler consumption window.
- Lander should continue locking the instructor/resource through `7:45 PM` for this BLS Provider seed even though Enrollware displays `5:00 PM to 6:00 PM`.
- Enrollware shows `Room B`; Lander preview currently shows the public location as Shipyard Office.
