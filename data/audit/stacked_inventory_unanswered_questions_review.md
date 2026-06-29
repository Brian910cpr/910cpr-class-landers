# Stacked Inventory Unanswered Questions Review

## Verdict

The previous audit did not answer enough of the operational questions directly. This follow-up matrix ties the visible customer rows, August inventory, July 4 check rows, and Course Master review gates into direct answers.

## Direct Answers

### Are visible BLS rows mostly real Class Report rows?

Yes. 115 of 120 visible BLS rows are current Class Report/enroll?id rows; 5 are appointment-seed rows.

### Are visible Heartsaver rows mostly real Class Report rows?

Mixed. First Aid CPR AED is mostly Class Report, CPR AED is entirely appointment-seed in this snapshot, and Pediatric is mostly Class Report with one seed.

### What are the July 4 Check-this-date/time rows?

They are appointment-seed rows, not Class Report enroll?id classes. They come from the dynamic presentation/build output and use appointmentDayId URLs.

### Does August have enough visible public inventory?

No. August public visibility is thin and inconsistent. The snapshot has only a small set of visible August rows, and the dynamic pipeline reports no August BLS or Heartsaver public-sellable offers.

### Can Course Master currently be treated as authoritative for scheduling?

No. The review sheet still marks many public/dynamic-used courses as dynamic_offer_allowed=false, appointment_seed_allowed=false, or review_needed_for_scheduling=true.

### Minimum safe business action for August?

Do not wait for the smart layer alone. Create/verify real Enrollware August BLS and Heartsaver rows first, then use dynamic appointment seeds only where course/container/page/CTA mapping is proven and Course Master contradictions are resolved.

## Visible Row Source Counts

| Course group | Total | Class Report rows | Appointment seed rows |
|---|---:|---:|---:|
| BLS | 120 | 115 | 5 |
| Heartsaver First Aid CPR AED | 44 | 42 | 2 |
| Heartsaver CPR AED | 3 | 0 | 3 |
| Heartsaver Pediatric First Aid CPR AED | 6 | 5 | 1 |
| ACLS | 30 | 30 | 0 |
| PALS | 22 | 22 | 0 |
| HSI | 2 | 1 | 1 |

## Requested Time Checks

### BLS requested times

| Time | Total | Class Report | Appointment seed |
|---|---:|---:|---:|
| 09:15 | 20 | 20 | 0 |
| 12:30 | 31 | 31 | 0 |
| 18:15 | 24 | 24 | 0 |
| 18:45 | 10 | 10 | 0 |

### Heartsaver First Aid CPR AED requested times

| Time | Total | Class Report | Appointment seed |
|---|---:|---:|---:|
| 09:15 | 8 | 8 | 0 |
| 18:15 | 7 | 7 | 0 |

### ACLS requested 2 PM

| Time | Total | Class Report | Appointment seed |
|---|---:|---:|---:|
| 14:00 | 20 | 20 | 0 |

### PALS requested 2 PM

| Time | Total | Class Report | Appointment seed |
|---|---:|---:|---:|
| 14:00 | 21 | 21 | 0 |

## July 4 Check-This-Date/Time Rows

| Page | Course | Time | courseId | appointmentDayId | Offer ID |
|---|---|---:|---:|---:|---|
| /courses/heartsaver-first-aid-cpr-aed.html | AHA Heartsaver First Aid CPR AED - Blended | 2:30 PM - 3:15 PM | 329495 | 260683 |  |
| /courses/heartsaver-first-aid-cpr-aed.html | AHA Heartsaver First Aid CPR AED - Blended | 2:45 PM - 3:30 PM | 329495 | 260683 | offer-329495-instructor_24057895173-20260704-1445 |
| /courses/heartsaver-cpr-aed.html | AHA Heartsaver CPR AED | 2:45 PM - 4:15 PM | 344085 | 260683 | offer-344085-instructor_24057895173-20260704-1445 |
| /courses/heartsaver-cpr-aed.html | AHA Heartsaver CPR AED Online | 2:45 PM - 3:30 PM | 209808 | 260683 | offer-209808-instructor_24057895173-20260704-1445 |
| /courses/heartsaver-cpr-aed.html | AHA Heartsaver CPR AED | 2:45 PM - 4:15 PM | 344085 | 260683 | offer-344085-instructor_24057895173-20260704-1445 |
| /courses/heartsaver-pediatric-first-aid-cpr-aed.html | AHA Heartsaver Pediatric First Aid CPR AED Online | 2:45 PM - 3:30 PM | 251545 | 260683 | offer-251545-instructor_24057895173-20260704-1445 |
| /hsi.html | HSI BLS and Adult First Aid \| Blended Learning | 2:45 PM - 3:30 PM | 445670 | 260683 | offer-445670-instructor_24057895173-20260704-1445 |

## August Visibility

| Course key | Total visible August rows | Class Report rows | Appointment seed rows |
|---|---:|---:|---:|
| aha_acls | 1 | 1 | 0 |
| aha_bls | 7 | 2 | 5 |
| aha_pals | 1 | 1 | 0 |
| hsi | 1 | 1 | 0 |

## Course Master Contradictions

These rows are especially important because the review sheet says the course is not scheduling-ready or seed-allowed, while public sellable dynamic output is already using it.

| course_key | courseId | used by public dynamic | dynamic allowed | seed allowed | scheduling review | missing fields |
|---|---:|---|---|---|---|---|
| aha_heartsaver_cpr_aed | 344085 | true | false | false | true | setup_buffer_minutes; cleanup_buffer_minutes; scheduler_consumption_minutes |
| aha_heartsaver_cpr_aed_online | 209808 | true | false | false | true | setup_buffer_minutes; cleanup_buffer_minutes; scheduler_consumption_minutes; base_price; card_type |
| aha_heartsaver_first_aid_cpr_aed_blended | 329495 | true | false | false | true | setup_buffer_minutes; cleanup_buffer_minutes; scheduler_consumption_minutes; base_price; card_type |
| aha_heartsaver_pediatric_first_aid_cpr_aed_online | 251545 | true | false | false | true | setup_buffer_minutes; cleanup_buffer_minutes; scheduler_consumption_minutes; base_price; card_type |

## Corrected Minimum Safe Fix

1. Treat real Enrollware/Class Report rows as the source of truth for immediate August visibility.
2. Manually create or verify August BLS and Heartsaver rows before relying on the appointment-seed layer for customer-facing coverage.
3. Resolve Course Master contradictions before allowing it to unlock scheduling automatically.
4. Keep appointment-seed offers behind proven courseId, appointmentDayId, page/tab, location, lead-time, and occupancy gates.
5. Do not make Course Master authoritative yet.

## Files

- `data/audit/stacked_inventory_unanswered_questions_review.json`
- `data/audit/course_master_inventory_gate_matrix.csv`
- `data/audit/stacked_inventory_unanswered_questions_review.md`
