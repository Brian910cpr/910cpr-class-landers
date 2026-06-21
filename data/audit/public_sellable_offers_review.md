# Public Sellable Offers Review

This is a Brian-friendly review report for filtered public-sellable dynamic offers. It does not modify offer generation, public policy, public pages, Enrollware behavior, appointment URLs, Worker behavior, generated HTML, or docs output.

## Summary

- Total sellable offers: 144
- Source dynamic offers read by filter: 1808
- Policy file: `data/config/public_offer_policy.json`
- Enabled families: BLS, Heartsaver, ACLS, PALS
- Disabled families: ARC, HSI, USCG
- Allowed start minutes: 00, 30
- Max offers per day: 24

## Offers By Date

- `2026-06-22`: 24
- `2026-06-23`: 24
- `2026-06-24`: 24
- `2026-06-25`: 24
- `2026-06-26`: 24
- `2026-06-27`: 24

## Offers By Family

- `ACLS`: 5
- `BLS`: 56
- `Heartsaver`: 78
- `PALS`: 5

## Hidden Reason Examples From Policy Filter

- `start_minute_not_allowed`: 862
- `max_total_offers_per_day_exceeded`: 658
- `course_family_disabled`: 282
- `course_family_not_enabled`: 282

### Example Hidden Offers

| Reason | Date | Time | Course | Family |
| --- | --- | --- | --- | --- |
| `start_minute_not_allowed` | 2026-06-22 | 08:45-10:45 | AHA BLS Provider | BLS |
| `course_family_disabled` | 2026-06-22 | 08:30-11:30 | USCG Elementary First Aid | CPR (AHA Heartsaver) | USCG |
| `course_family_not_enabled` | 2026-06-22 | 08:30-11:30 | USCG Elementary First Aid | CPR (AHA Heartsaver) | USCG |
| `max_total_offers_per_day_exceeded` | 2026-06-22 | 09:30-10:15 | AHA Heartsaver Pediatric First Aid CPR AED Online | Heartsaver |

## Brian Review Instructions

Use the CSV `brian_review` column with one of these actions:

- `approve`: Offer looks appropriate for public review/publish testing later.
- `hide`: Offer should remain hidden even if it passes current policy.
- `adjust time`: Time is close but should be shifted before public use.
- `adjust policy`: The filtering rule should change instead of editing one offer.

Suggested workflow: review the first few offers per date/family, mark obvious bad patterns as `adjust policy`, and avoid one-off edits until policy issues are clear.

## 2026-06-22


### BLS (10)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:30 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260622-0830` |
| 08:30-10:30 | AHA BLS Provider Renewal | Brian Ennis | 6 | high | `offer-359474-instructor_24057895173-20260622-0830` |
| 08:30-09:30 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260622-0830` |
| 08:30-11:00 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | Brian Ennis | 18 | high | `offer-440431-instructor_24057895173-20260622-0830` |
| 09:00-11:00 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260622-0900` |
| 09:00-11:00 | AHA BLS Provider Renewal | Brian Ennis | 6 | high | `offer-359474-instructor_24057895173-20260622-0900` |
| 09:00-10:00 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260622-0900` |
| 09:00-11:30 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | Brian Ennis | 18 | high | `offer-440431-instructor_24057895173-20260622-0900` |
| 09:30-11:30 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260622-0930` |
| 09:30-10:30 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260622-0930` |

### Heartsaver (14)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:00 | AHA Heartsaver CPR AED | Brian Ennis | 10 | high | `offer-344085-instructor_24057895173-20260622-0830` |
| 08:30-09:15 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260622-0830` |
| 08:30-11:30 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260622-0830` |
| 08:30-09:15 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 2 | high | `offer-329495-instructor_24057895173-20260622-0830` |
| 08:30-11:30 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 12 | high | `offer-351632-instructor_24057895173-20260622-0830` |
| 08:30-09:15 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 2 | high | `offer-251545-instructor_24057895173-20260622-0830` |
| 09:00-10:30 | AHA Heartsaver CPR AED | Brian Ennis | 10 | high | `offer-344085-instructor_24057895173-20260622-0900` |
| 09:00-09:45 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260622-0900` |
| 09:00-12:00 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260622-0900` |
| 09:00-09:45 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 2 | high | `offer-329495-instructor_24057895173-20260622-0900` |
| 09:00-12:00 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 12 | high | `offer-351632-instructor_24057895173-20260622-0900` |
| 09:00-09:45 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 2 | high | `offer-251545-instructor_24057895173-20260622-0900` |
| 09:30-10:15 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260622-0930` |
| 09:30-12:30 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260622-0930` |

## 2026-06-23


### ACLS (5)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:00 | AHA ACLS HeartCode | Amy Arnold | 1 | high | `offer-209811-instructor_4180671442-20260623-0830` |
| 08:30-12:30 | AHA ACLS Provider (Initial) | Amy Arnold | 6 | high | `offer-241108-instructor_4180671442-20260623-0830` |
| 08:30-12:30 | AHA ACLS Provider (Renewal) | Amy Arnold | 6 | high | `offer-209818-instructor_4180671442-20260623-0830` |
| 09:00-10:30 | AHA ACLS HeartCode | Amy Arnold | 1 | high | `offer-209811-instructor_4180671442-20260623-0900` |
| 09:00-13:00 | AHA ACLS Provider (Renewal) | Amy Arnold | 6 | high | `offer-209818-instructor_4180671442-20260623-0900` |

### BLS (6)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:30 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260623-0830` |
| 08:30-10:30 | AHA BLS Provider Renewal | Brian Ennis | 6 | high | `offer-359474-instructor_24057895173-20260623-0830` |
| 08:30-09:30 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260623-0830` |
| 08:30-11:00 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | Brian Ennis | 18 | high | `offer-440431-instructor_24057895173-20260623-0830` |
| 09:00-11:00 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260623-0900` |
| 09:00-10:00 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260623-0900` |

### Heartsaver (8)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:00 | AHA Heartsaver CPR AED | Brian Ennis | 10 | high | `offer-344085-instructor_24057895173-20260623-0830` |
| 08:30-09:15 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260623-0830` |
| 08:30-11:30 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260623-0830` |
| 08:30-09:15 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 2 | high | `offer-329495-instructor_24057895173-20260623-0830` |
| 08:30-11:30 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 12 | high | `offer-351632-instructor_24057895173-20260623-0830` |
| 08:30-09:15 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 2 | high | `offer-251545-instructor_24057895173-20260623-0830` |
| 09:00-09:45 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260623-0900` |
| 09:00-12:00 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260623-0900` |

### PALS (5)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:00 | AHA PALS HeartCode | Amy Arnold | 1 | high | `offer-209812-instructor_4180671442-20260623-0830` |
| 08:30-12:30 | AHA PALS Provider | Amy Arnold | 6 | high | `offer-209805-instructor_4180671442-20260623-0830` |
| 08:30-12:30 | AHA PALS Renewal | Amy Arnold | 6 | high | `offer-251496-instructor_4180671442-20260623-0830` |
| 09:00-10:30 | AHA PALS HeartCode | Amy Arnold | 1 | high | `offer-209812-instructor_4180671442-20260623-0900` |
| 09:00-13:00 | AHA PALS Provider | Amy Arnold | 6 | high | `offer-209805-instructor_4180671442-20260623-0900` |

## 2026-06-24


### BLS (10)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:30 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260624-0830` |
| 08:30-10:30 | AHA BLS Provider Renewal | Brian Ennis | 6 | high | `offer-359474-instructor_24057895173-20260624-0830` |
| 08:30-09:30 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260624-0830` |
| 08:30-11:00 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | Brian Ennis | 18 | high | `offer-440431-instructor_24057895173-20260624-0830` |
| 09:00-11:00 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260624-0900` |
| 09:00-11:00 | AHA BLS Provider Renewal | Brian Ennis | 6 | high | `offer-359474-instructor_24057895173-20260624-0900` |
| 09:00-10:00 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260624-0900` |
| 09:00-11:30 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | Brian Ennis | 18 | high | `offer-440431-instructor_24057895173-20260624-0900` |
| 09:30-11:30 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260624-0930` |
| 09:30-10:30 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260624-0930` |

### Heartsaver (14)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:00 | AHA Heartsaver CPR AED | Brian Ennis | 10 | high | `offer-344085-instructor_24057895173-20260624-0830` |
| 08:30-09:15 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260624-0830` |
| 08:30-11:30 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260624-0830` |
| 08:30-09:15 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 2 | high | `offer-329495-instructor_24057895173-20260624-0830` |
| 08:30-11:30 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 12 | high | `offer-351632-instructor_24057895173-20260624-0830` |
| 08:30-09:15 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 2 | high | `offer-251545-instructor_24057895173-20260624-0830` |
| 09:00-10:30 | AHA Heartsaver CPR AED | Brian Ennis | 10 | high | `offer-344085-instructor_24057895173-20260624-0900` |
| 09:00-09:45 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260624-0900` |
| 09:00-12:00 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260624-0900` |
| 09:00-09:45 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 2 | high | `offer-329495-instructor_24057895173-20260624-0900` |
| 09:00-12:00 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 12 | high | `offer-351632-instructor_24057895173-20260624-0900` |
| 09:00-09:45 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 2 | high | `offer-251545-instructor_24057895173-20260624-0900` |
| 09:30-10:15 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260624-0930` |
| 09:30-12:30 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260624-0930` |

## 2026-06-25


### BLS (10)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:30 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260625-0830` |
| 08:30-10:30 | AHA BLS Provider Renewal | Brian Ennis | 6 | high | `offer-359474-instructor_24057895173-20260625-0830` |
| 08:30-09:30 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260625-0830` |
| 08:30-11:00 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | Brian Ennis | 18 | high | `offer-440431-instructor_24057895173-20260625-0830` |
| 09:00-11:00 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260625-0900` |
| 09:00-11:00 | AHA BLS Provider Renewal | Brian Ennis | 6 | high | `offer-359474-instructor_24057895173-20260625-0900` |
| 09:00-10:00 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260625-0900` |
| 09:00-11:30 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | Brian Ennis | 18 | high | `offer-440431-instructor_24057895173-20260625-0900` |
| 09:30-11:30 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260625-0930` |
| 09:30-10:30 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260625-0930` |

### Heartsaver (14)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:00 | AHA Heartsaver CPR AED | Brian Ennis | 10 | high | `offer-344085-instructor_24057895173-20260625-0830` |
| 08:30-09:15 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260625-0830` |
| 08:30-11:30 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260625-0830` |
| 08:30-09:15 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 2 | high | `offer-329495-instructor_24057895173-20260625-0830` |
| 08:30-11:30 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 12 | high | `offer-351632-instructor_24057895173-20260625-0830` |
| 08:30-09:15 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 2 | high | `offer-251545-instructor_24057895173-20260625-0830` |
| 09:00-10:30 | AHA Heartsaver CPR AED | Brian Ennis | 10 | high | `offer-344085-instructor_24057895173-20260625-0900` |
| 09:00-09:45 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260625-0900` |
| 09:00-12:00 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260625-0900` |
| 09:00-09:45 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 2 | high | `offer-329495-instructor_24057895173-20260625-0900` |
| 09:00-12:00 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 12 | high | `offer-351632-instructor_24057895173-20260625-0900` |
| 09:00-09:45 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 2 | high | `offer-251545-instructor_24057895173-20260625-0900` |
| 09:30-10:15 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260625-0930` |
| 09:30-12:30 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260625-0930` |

## 2026-06-26


### BLS (10)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:30 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260626-0830` |
| 08:30-10:30 | AHA BLS Provider Renewal | Brian Ennis | 6 | high | `offer-359474-instructor_24057895173-20260626-0830` |
| 08:30-09:30 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260626-0830` |
| 08:30-11:00 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | Brian Ennis | 18 | high | `offer-440431-instructor_24057895173-20260626-0830` |
| 09:00-11:00 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260626-0900` |
| 09:00-11:00 | AHA BLS Provider Renewal | Brian Ennis | 6 | high | `offer-359474-instructor_24057895173-20260626-0900` |
| 09:00-10:00 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260626-0900` |
| 09:00-11:30 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | Brian Ennis | 18 | high | `offer-440431-instructor_24057895173-20260626-0900` |
| 09:30-11:30 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260626-0930` |
| 09:30-10:30 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260626-0930` |

### Heartsaver (14)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:00 | AHA Heartsaver CPR AED | Brian Ennis | 10 | high | `offer-344085-instructor_24057895173-20260626-0830` |
| 08:30-09:15 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260626-0830` |
| 08:30-11:30 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260626-0830` |
| 08:30-09:15 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 2 | high | `offer-329495-instructor_24057895173-20260626-0830` |
| 08:30-11:30 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 12 | high | `offer-351632-instructor_24057895173-20260626-0830` |
| 08:30-09:15 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 2 | high | `offer-251545-instructor_24057895173-20260626-0830` |
| 09:00-10:30 | AHA Heartsaver CPR AED | Brian Ennis | 10 | high | `offer-344085-instructor_24057895173-20260626-0900` |
| 09:00-09:45 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260626-0900` |
| 09:00-12:00 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260626-0900` |
| 09:00-09:45 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 2 | high | `offer-329495-instructor_24057895173-20260626-0900` |
| 09:00-12:00 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 12 | high | `offer-351632-instructor_24057895173-20260626-0900` |
| 09:00-09:45 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 2 | high | `offer-251545-instructor_24057895173-20260626-0900` |
| 09:30-10:15 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260626-0930` |
| 09:30-12:30 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260626-0930` |

## 2026-06-27


### BLS (10)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:30 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260627-0830` |
| 08:30-10:30 | AHA BLS Provider Renewal | Brian Ennis | 6 | high | `offer-359474-instructor_24057895173-20260627-0830` |
| 08:30-09:30 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260627-0830` |
| 08:30-11:00 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | Brian Ennis | 18 | high | `offer-440431-instructor_24057895173-20260627-0830` |
| 09:00-11:00 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260627-0900` |
| 09:00-11:00 | AHA BLS Provider Renewal | Brian Ennis | 6 | high | `offer-359474-instructor_24057895173-20260627-0900` |
| 09:00-10:00 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260627-0900` |
| 09:00-11:30 | BLS Provider Blended Learning (Online Course; Group; In-person Skills Testing) | Brian Ennis | 18 | high | `offer-440431-instructor_24057895173-20260627-0900` |
| 09:30-11:30 | AHA BLS Provider | Brian Ennis | 6 | high | `offer-209806-instructor_24057895173-20260627-0930` |
| 09:30-10:30 | AHA HeartCode BLS | Brian Ennis | 1 | high | `offer-210549-instructor_24057895173-20260627-0930` |

### Heartsaver (14)

| Time | Course | Instructor | Capacity | Confidence | Offer ID |
| --- | --- | --- | ---: | --- | --- |
| 08:30-10:00 | AHA Heartsaver CPR AED | Brian Ennis | 10 | high | `offer-344085-instructor_24057895173-20260627-0830` |
| 08:30-09:15 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260627-0830` |
| 08:30-11:30 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260627-0830` |
| 08:30-09:15 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 2 | high | `offer-329495-instructor_24057895173-20260627-0830` |
| 08:30-11:30 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 12 | high | `offer-351632-instructor_24057895173-20260627-0830` |
| 08:30-09:15 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 2 | high | `offer-251545-instructor_24057895173-20260627-0830` |
| 09:00-10:30 | AHA Heartsaver CPR AED | Brian Ennis | 10 | high | `offer-344085-instructor_24057895173-20260627-0900` |
| 09:00-09:45 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260627-0900` |
| 09:00-12:00 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260627-0900` |
| 09:00-09:45 | AHA Heartsaver First Aid CPR AED - Blended | Brian Ennis | 2 | high | `offer-329495-instructor_24057895173-20260627-0900` |
| 09:00-12:00 | AHA Heartsaver Pediatric First Aid / CPR / AED | Brian Ennis | 12 | high | `offer-351632-instructor_24057895173-20260627-0900` |
| 09:00-09:45 | AHA Heartsaver Pediatric First Aid CPR AED Online | Brian Ennis | 2 | high | `offer-251545-instructor_24057895173-20260627-0900` |
| 09:30-10:15 | AHA Heartsaver CPR AED Online | Brian Ennis | 2 | high | `offer-209808-instructor_24057895173-20260627-0930` |
| 09:30-12:30 | AHA Heartsaver First Aid CPR AED | Brian Ennis | 12 | high | `offer-209809-instructor_24057895173-20260627-0930` |
