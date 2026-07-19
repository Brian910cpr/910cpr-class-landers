# Sitewide Link / Button Audit

Audit-only report. No links, public pages, Enrollware behavior, deployment settings, or source data were changed by this script.

## 1. Summary Counts

- Public HTML files scanned: 234
- Links/buttons scanned: 3294
- Broken: 0
- Suspicious: 0
- Review: 61
- Low confidence needing review: 3

### By Destination Type

- anchor: 14
- class_lander: 1014
- course_hub: 946
- enrollware_booking: 695
- external: 14
- internal_page: 441
- missing_or_empty: 58
- phone: 112

### By Confidence

- HIGH: 2150
- LOW: 3
- MEDIUM: 1141

## 2. Broken Links

_None found._

## 3. Suspicious/Misdirected Links

_None found._

## 4. Enrollware Booking-Link Mismatches

_None found._

## 5. Internal Page Mismatches

| Status | Confidence | Source | Text | Destination | Notes |
|---|---:|---|---|---|---|
| REVIEW | LOW | `docs/renewal-email.html` | (no text) | `/` | link has no visible text or aria-label |
| REVIEW | LOW | `docs/renewal-email.html` | (no text) | `/classes` | link has no visible text or aria-label |
| REVIEW | LOW | `docs/renewal-email.html` | (no text) | `/` | link has no visible text or aria-label |

## 6. Duplicate Labels With Different Destinations

- Duplicate label groups found: 55

| Status | Confidence | Source | Text | Destination | Notes |
|---|---:|---|---|---|---|
| OK | MEDIUM | `docs/classes/12774337.html` | Continue to Registration | `https://coastalcprtraining.enrollware.com/enroll?id=12774337` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/classes/12774338.html` | Continue to Registration | `https://coastalcprtraining.enrollware.com/enroll?id=12774338` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/classes/12774347.html` | Continue to Registration | `https://coastalcprtraining.enrollware.com/enroll?id=12774347` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 8:30 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260734&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 8:30 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260748&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 8:30 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260755&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 8:45 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260734&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 8:45 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260748&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 8:45 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260755&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 9:00 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260734&startTime=9%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 9:00 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260748&startTime=9%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 9:00 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260755&startTime=9%3A...` | booking parameters present; exact row match needs spot check |
| OK | HIGH | `docs/course-at-city/acls-wilmington.html` | Book Seat | `/acls.html` |  |
| OK | HIGH | `docs/course-at-city/acls-wilmington.html` | Book Seat | `/acls.html` |  |
| OK | HIGH | `docs/course-at-city/acls-wilmington.html` | Book Seat | `/acls.html` |  |
| OK | HIGH | `docs/topics-year/acls-2020.html` | Open topic support page | `/topics/acls.html` |  |
| OK | HIGH | `docs/topics-year/acls-2021.html` | Open topic support page | `/topics/acls.html` |  |
| OK | HIGH | `docs/topics-year/acls-2022.html` | Open topic support page | `/topics/acls.html` |  |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 8:00 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260720&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 8:00 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260727&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 8:00 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260720&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 8:15 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260720&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 8:15 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260727&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 8:15 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260720&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | Register for 8:30 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260742&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | Register for 8:30 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260749&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | Register for 8:30 AM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260756&startTime=8%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 6:00 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260713&startTime=6%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 6:00 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260741&startTime=6%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 6:00 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260713&startTime=6%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 6:15 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260713&startTime=6%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 6:15 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260741&startTime=6%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 6:15 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260713&startTime=6%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 2:30 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260699&startTime=2%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 2:30 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260706&startTime=2%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 2:30 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260699&startTime=2%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 2:45 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260699&startTime=2%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 2:45 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260706&startTime=2%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 2:45 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260699&startTime=2%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 3:00 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260699&startTime=3%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 3:00 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260706&startTime=3%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 3:00 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260699&startTime=3%3A...` | booking parameters present; exact row match needs spot check |
| OK | HIGH | `docs/years/2026.html` | Open archive support bucket | `/topics-year/bls-2026.html` |  |
| OK | HIGH | `docs/years/2026.html` | Open archive support bucket | `/topics-year/heartsaver-2026.html` |  |
| OK | HIGH | `docs/years/2026.html` | Open archive support bucket | `/topics-year/acls-2026.html` |  |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 6:30 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260713&startTime=6%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-cpr-aed.html` | 6:30 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260713&startTime=6%3A...` | booking parameters present; exact row match needs spot check |
| OK | MEDIUM | `docs/courses/heartsaver-first-aid-cpr-aed.html` | 6:30 PM | `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260713&startTime=6%3A...` | booking parameters present; exact row match needs spot check |
| OK | HIGH | `docs/classes/course-at-city/aha-acls-provider-initial--wilmington.html` | July 29, 2026 at 2:00 PM | `/classes/13673164.html` |  |
| OK | HIGH | `docs/classes/course-at-city/aha-acls-provider-renewal--wilmington.html` | July 29, 2026 at 2:00 PM | `/classes/13673174.html` |  |

_Showing first 50 of 71 items. See CSV for all rows._

## 7. Low-Confidence Items Needing Brian Review

| Status | Confidence | Source | Text | Destination | Notes |
|---|---:|---|---|---|---|
| REVIEW | LOW | `docs/renewal-email.html` | (no text) | `/` | link has no visible text or aria-label |
| REVIEW | LOW | `docs/renewal-email.html` | (no text) | `/classes` | link has no visible text or aria-label |
| REVIEW | LOW | `docs/renewal-email.html` | (no text) | `/` | link has no visible text or aria-label |

## 8. Recommended Fixes

- Review duplicate labels with multiple destinations; many generic CTAs are expected, but course-name labels should be consistent.
- Spot-check low-confidence generic booking links against their visible class row/date/time before treating them as fully audited.

Full CSV: `debug/sitewide_link_button_audit.csv`
