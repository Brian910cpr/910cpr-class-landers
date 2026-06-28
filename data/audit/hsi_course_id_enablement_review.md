# HSI Course ID Enablement Review

Generated: 2026-06-28T14:48:16

## Verdict

Do not deploy this review build yet. Rendered proof is PARTIAL: presentation selected 8 dynamic offers, but only 5 rendered in HTML; 3 new HSI selected offers are missing from rendered pages.

## Counts

- Enabled course IDs before: `['445670', '344085', '209808', '209809', '329495', '351632', '251545']`
- Enabled course IDs after: `['445670', '344085', '209808', '209809', '329495', '351632', '251545', '463743', '371954', '374378', '422270', '449422']`
- HSI public sellable before/after: `5` / `14`
- HSI rendered actual before/after: `2` / `2`
- Total public sellable dynamic before/after: `14` / `23`
- Total rendered actual before/after: `5` / `5`

## New Public Sellable HSI Offers

- `offer-371954-instructor_24057895173-20260704-1430` courseId `371954` HSI Adult First Aid | CPR AED - Blended Learning start `2026-07-04T14:30:00` appointmentDayId `260683` container `shipyard_brian_continuous_20260621_20270430` hours_ok `True` risk `low: course name is HSI-labeled`
- `offer-449422-instructor_24057895173-20260704-1430` courseId `449422` HSI Pediatric First Aid | CPR AED - Blended start `2026-07-04T14:30:00` appointmentDayId `260683` container `shipyard_brian_continuous_20260621_20270430` hours_ok `True` risk `low: course name is HSI-labeled`
- `offer-463743-instructor_24057895173-20260704-1430` courseId `463743` HSI BLS Challenge start `2026-07-04T14:30:00` appointmentDayId `260683` container `shipyard_brian_continuous_20260621_20270430` hours_ok `True` risk `low: course name is HSI-labeled`
- `offer-371954-instructor_24057895173-20260704-1445` courseId `371954` HSI Adult First Aid | CPR AED - Blended Learning start `2026-07-04T14:45:00` appointmentDayId `260683` container `shipyard_brian_continuous_20260621_20270430` hours_ok `True` risk `low: course name is HSI-labeled`
- `offer-449422-instructor_24057895173-20260704-1445` courseId `449422` HSI Pediatric First Aid | CPR AED - Blended start `2026-07-04T14:45:00` appointmentDayId `260683` container `shipyard_brian_continuous_20260621_20270430` hours_ok `True` risk `low: course name is HSI-labeled`
- `offer-463743-instructor_24057895173-20260704-1445` courseId `463743` HSI BLS Challenge start `2026-07-04T14:45:00` appointmentDayId `260683` container `shipyard_brian_continuous_20260621_20270430` hours_ok `True` risk `low: course name is HSI-labeled`
- `offer-371954-instructor_24057895173-20260704-1500` courseId `371954` HSI Adult First Aid | CPR AED - Blended Learning start `2026-07-04T15:00:00` appointmentDayId `260683` container `shipyard_brian_continuous_20260621_20270430` hours_ok `True` risk `low: course name is HSI-labeled`
- `offer-449422-instructor_24057895173-20260704-1500` courseId `449422` HSI Pediatric First Aid | CPR AED - Blended start `2026-07-04T15:00:00` appointmentDayId `260683` container `shipyard_brian_continuous_20260621_20270430` hours_ok `True` risk `low: course name is HSI-labeled`
- `offer-463743-instructor_24057895173-20260704-1500` courseId `463743` HSI BLS Challenge start `2026-07-04T15:00:00` appointmentDayId `260683` container `shipyard_brian_continuous_20260621_20270430` hours_ok `True` risk `low: course name is HSI-labeled`

## New Presentation-Selected HSI Offers

- `offer-371954-instructor_24057895173-20260704-1445` courseId `371954` HSI Adult First Aid | CPR AED - Blended Learning start `2026-07-04T14:45:00` appointmentDayId `260683` hours_ok `True` risk `low: course name is HSI-labeled`
- `offer-449422-instructor_24057895173-20260704-1445` courseId `449422` HSI Pediatric First Aid | CPR AED - Blended start `2026-07-04T14:45:00` appointmentDayId `260683` hours_ok `True` risk `low: course name is HSI-labeled`
- `offer-463743-instructor_24057895173-20260704-1445` courseId `463743` HSI BLS Challenge start `2026-07-04T14:45:00` appointmentDayId `260683` hours_ok `True` risk `low: course name is HSI-labeled`

## New Rendered HSI Offers Actually Found In HTML

- None of the newly enabled course IDs were found rendered in HTML by proof.

## Missing Rendered Offers

- `offer-371954-instructor_24057895173-20260704-1445` courseId `371954` HSI Adult First Aid | CPR AED - Blended Learning expected href `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A45%20PM&courseId=371954` pages `[]` rendered=`False`
- `offer-449422-instructor_24057895173-20260704-1445` courseId `449422` HSI Pediatric First Aid | CPR AED - Blended expected href `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A45%20PM&courseId=449422` pages `[]` rendered=`False`
- `offer-463743-instructor_24057895173-20260704-1445` courseId `463743` HSI BLS Challenge expected href `https://coastalcprtraining.enrollware.com/enroll?appointmentDayId=260683&startTime=2%3A45%20PM&courseId=463743` pages `[]` rendered=`False`

## HSI CPR AED / 344085 Risk

Mapping HSI CPR AED card to AHA Heartsaver CPR AED 344085 appears to be a mapping bug or intentional cross-brand fallback that needs explicit Brian approval. It should be blocked or renamed before public HSI CPR AED traffic is sent to this checkout.

Recommended action: Do not present 344085 as HSI CPR AED unless explicitly approved; prefer a real HSI CPR AED courseId or label it as AHA Heartsaver.

## Validation

- Rendered dynamic proof: `PARTIAL` - 5 of 8 public sellable dynamic appointment-seed offers render; 3 are absent from HTML.
- Public offer integrity audit failed: `False`
- Tests: `Ran 137 tests; OK`
