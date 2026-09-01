# Hx Historical Location Authority Review

No production changes, historical import, or application deployment occurred.

## Classification summary

| Classification | Distinct labels | Rows |
| --- | ---: | ---: |
| CANONICAL HISTORICAL LOCATION CANDIDATE | 126 | 3,837 |
| SAFE ALIAS TO EXISTING LOCATION | 0 | 0 |
| SOURCE-ONLY / DO NOT CANONICALIZE | 10 | 245 |
| AMBIGUOUS / REVIEW REQUIRED | 6 | 176 |

## Session effect

- Fully canonicalized before: **2,063**
- After all safe archive-only candidates: **3,439**
- Increase: **1,376**

## Historical completeness policy

An otherwise supported historical session should be allowed to exist with instructor and/or duration explicitly unknown. Unknown is evidence state, not a guessed value. Such sessions must remain archive-only and excluded from operational scheduling, payroll, capacity, and duration projections.

The production contract currently makes `class_sessions.lead_instructor_id`, `location_id`, and `end_at` NOT NULL. Therefore this recommendation is not directly importable yet: instructor-unknown needs either the canonical historical placeholder plus explicit missing-evidence state or a reviewed nullable-field change; duration-unknown needs a reviewed nullable `end_at`/historical evidence path and must never use a fabricated end time. Likewise, `locations` has `public` but not the proposed `historical_only`/`scheduling_status` guards, so an enforceable archive-only boundary requires schema review before candidate creation.

```json
{
  "allow_both_unknown": 3570,
  "allow_unknown_duration": 3465,
  "allow_unknown_instructor": 3543,
  "strict_current": 3439
}
```

## Frequency-ranked inventory

| Source label | Count | Course families | Date range | Source metadata | Existing exact map | Reusable | Character | Classification |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| NC - Holly Ridge: 325 Sound Rd, Unit 204; 910CPR's Office @ Parkhill Village (across the street from Holly Ridge Community Center) | 749 | ACLS, American Red Cross, BLS, Family & Friends, Heartsaver, Other / legacy, PALS | 2021-02-01T18:00:00-05:00 — 2024-12-12T09:00:00-05:00 | 325 Sound Rd, Holly Ridge | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| CFCC: North Campus / Blue Clay Rd | 360 | BLS | 2022-03-29T13:00:00-04:00 — 2022-12-15T13:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| 910CPR Office @ Hinton Ave, Wlmington | 318 | ACLS, BLS, First Aid / CPR AED, Heartsaver, Other / legacy, PALS | 2020-08-13T17:00:00-04:00 — 2021-02-17T09:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Surf City Fire Station #25 | 192 | BLS, Heartsaver | 2021-12-27T09:00:00-05:00 — 2024-08-22T09:00:00-04:00 | Surf City | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Thompson Child and Family Focus | 181 | Heartsaver | 2020-10-05T11:00:00-04:00 — 2024-10-11T09:30:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| [missing] | 170 | ACLS, BLS, Heartsaver, Other / legacy, PALS | 2019-11-25T18:00:00-05:00 — 2020-08-12T20:00:00-04:00 | label only | no | no | missing, source_only | SOURCE-ONLY / DO NOT CANONICALIZE |
| Balfour Beatty US: Havelock / James City / Thurman | 121 | Heartsaver | 2020-08-21T08:00:00-04:00 — 2024-06-18T07:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Holly Ridge: 809 Lenox Dr | 112 | ACLS, BLS, Heartsaver, PALS | 2019-12-19T10:30:00-05:00 — 2024-08-11T08:00:00-04:00 | 809 Lenox Dr, Holly Ridge | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Colchester Hayward Volunteer Fire Company | 75 | BLS, Heartsaver | 2021-03-14T09:00:00-04:00 — 2023-03-11T09:00:00-05:00 | Colchester | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| CT - Colchester | 71 | BLS, Heartsaver | 2021-06-01T17:00:00-04:00 — 2023-08-14T17:00:00-04:00 | Colchester | no | no | insufficient_specificity | AMBIGUOUS / REVIEW REQUIRED |
| Northchase Nursing & Rehab | 71 | BLS | 2021-04-08T09:00:00-04:00 — 2022-12-29T09:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Miller-Motte College: Jacksonville | 68 | BLS | 2021-08-04T15:00:00-04:00 — 2023-05-04T13:00:00-04:00 | Jacksonville | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Balfour Beatty US: Fayetteville Outerloop | 61 | Heartsaver | 2020-08-20T08:00:00-04:00 — 2024-06-20T08:00:00-04:00 | Fayetteville | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Surf City Police Department | 55 | BLS | 2021-04-16T15:00:00-04:00 — 2024-09-24T17:30:00-04:00 | Surf City | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Karen Beasley Sea Turtle Rescue and Rehabilitation Center | 54 | Heartsaver | 2021-11-09T09:00:00-05:00 — 2023-11-09T18:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| MedNorth @ 305 Harnett | 48 | BLS | 2024-01-25T08:00:00-05:00 — 2024-11-14T08:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| MedNorth @ Warner Temple AME Zion Church | 47 | BLS | 2022-12-01T08:00:00-05:00 — 2023-06-08T08:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| 19 Oak Ridge Dr, Colchester, CT | 40 | BLS, Heartsaver | 2020-12-18T14:00:00-05:00 — 2023-05-12T16:30:00-04:00 | 19 Oak Ridge Dr, Colchester | no | no | address_only, insufficient_specificity | AMBIGUOUS / REVIEW REQUIRED |
| NC - Jacksonville: Catalyst Church | 40 | BLS, Heartsaver | 2022-11-09T18:00:00-05:00 — 2024-04-17T18:00:00-04:00 | Jacksonville | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Riccobene Associates Family Dentistry: Gallery Park | 40 | BLS | 2021-07-16T09:00:00-04:00 — 2024-09-14T13:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Emereau: Bladen Charter School | 37 | BLS, Heartsaver | 2023-11-08T09:30:00-05:00 — 2024-05-29T13:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Broadway at the Beach | 33 | BLS, Heartsaver | 2020-05-27T09:00:00-04:00 — 2020-09-16T10:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| May Center for ABA Services in Jacksonville | 32 | Heartsaver, Other / legacy | 2020-10-30T09:00:00-04:00 — 2023-05-31T09:00:00-04:00 | Jacksonville | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Liberty Commons Rehabilitation Center | 30 | BLS | 2022-08-30T18:00:00-04:00 — 2022-10-06T08:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Balfour Beatty US - Office | 29 | Heartsaver | 2020-08-18T08:00:00-04:00 — 2024-08-30T08:30:00-04:00 | label only | no | no | insufficient_specificity | AMBIGUOUS / REVIEW REQUIRED |
| Filmwerks - Dell Breakroom | 29 | Heartsaver | 2020-12-02T08:00:00-05:00 — 2022-01-12T08:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Fort Fisher National Guard Training Center | 29 | Heartsaver | 2023-06-27T09:00:00-04:00 — 2023-06-27T09:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Balfour Beatty US: Harkers Island | 28 | Heartsaver | 2022-05-03T12:00:00-04:00 — 2022-05-03T12:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Onslow Water and Sewer Authority | 28 | Heartsaver | 2022-11-14T08:00:00-05:00 — 2022-11-28T08:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| New Beginnings Community Church - Preschool Program | 27 | Heartsaver | 2022-11-21T09:00:00-05:00 — 2024-08-23T09:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| J&J Snack | 26 | Heartsaver | 2023-08-10T08:00:00-04:00 — 2023-08-10T14:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Residence | 26 | BLS, Heartsaver | 2021-10-28T16:00:00-04:00 — 2024-08-27T08:30:00-04:00 | label only | no | no | source_only, one_time_or_private | SOURCE-ONLY / DO NOT CANONICALIZE |
| Antylia Scientific | 24 | Heartsaver | 2023-07-13T08:00:00-04:00 — 2024-02-05T09:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Breakthrough Autism: New Centre | 24 | BLS | 2023-04-20T08:00:00-04:00 — 2023-07-20T08:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Carolina Stone Setting Co. | 23 | Heartsaver | 2022-12-22T08:00:00-05:00 — 2022-12-22T13:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Pruitt - Fayetteville | 21 | BLS | 2022-03-07T09:00:00-05:00 — 2022-03-11T09:00:00-05:00 | Fayetteville | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Raleigh Medical Group | 21 | BLS | 2024-02-14T11:30:00-05:00 — 2024-02-22T11:30:00-05:00 | Raleigh | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Brunswick Oral & Maxillofacial Surgery | 20 | BLS | 2024-12-17T08:00:00-05:00 — 2024-12-17T08:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| 4902 Merlot Court; Wilmington, NC | 19 | BLS, Heartsaver | 2019-12-13T09:00:00-05:00 — 2020-02-11T17:00:00-05:00 | 4902 Merlot Court, Wilmington | no | no | source_only, address_only | SOURCE-ONLY / DO NOT CANONICALIZE |
| Little Pirates Daycare | 19 | Heartsaver | 2021-07-28T17:30:00-04:00 — 2024-10-04T15:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| National Peening, Inc. | 19 | First Aid / CPR AED, Heartsaver | 2023-01-12T13:00:00-05:00 — 2024-10-24T12:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Mainscape Inc. | 18 | Heartsaver | 2020-03-03T08:00:00-05:00 — 2020-03-03T08:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Camp Lejeune | 17 | BLS, Heartsaver | 2021-07-06T18:00:00-04:00 — 2023-03-30T09:00:00-04:00 | label only | no | no | insufficient_specificity | AMBIGUOUS / REVIEW REQUIRED |
| SC - Myrtle Beach: Country Inn & Suites | 17 | BLS, PALS | 2020-07-22T09:00:00-04:00 — 2020-10-07T10:00:00-04:00 | Myrtle Beach | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Southport Health & Rehabilitation Center | 17 | BLS | 2022-09-05T08:00:00-04:00 — 2022-09-06T08:00:00-04:00 | Southport | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Breakthrough Autism: Mayfair | 16 | BLS | 2023-10-13T08:00:00-04:00 — 2024-07-10T16:30:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Church of the Servant | 16 | Family & Friends | 2023-12-05T18:00:00-05:00 — 2023-12-05T18:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Porters Neck Village | 16 | BLS | 2021-09-28T10:00:00-04:00 — 2023-04-27T13:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Riccobene Associates Family Dentistry: Leland | 16 | BLS | 2021-03-22T18:00:00-04:00 — 2023-08-25T14:00:00-04:00 | Leland | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Summit Plastic Surg & Derm: Supply | 16 | BLS | 2023-10-27T09:00:00-04:00 — 2023-10-27T09:00:00-04:00 | Supply | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| B'nai Israel Congregation | 15 | Heartsaver | 2023-06-07T19:00:00-04:00 — 2023-06-21T19:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| CarolinasDentist: The Pointe | 15 | BLS | 2024-03-05T19:00:00-05:00 — 2024-08-13T17:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Geosyntec Consultants of NC P.C. | 15 | Heartsaver | 2022-08-23T09:00:00-04:00 — 2024-09-04T09:00:00-04:00 | label only | no | no | insufficient_specificity | AMBIGUOUS / REVIEW REQUIRED |
| Pender EMS & Fire, Inc | 15 | BLS | 2022-05-28T09:00:00-04:00 — 2024-08-18T09:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Project Transition | 15 | Heartsaver | 2022-01-26T08:30:00-05:00 — 2023-04-14T16:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Hendersonville Family Dental | 14 | BLS | 2024-09-14T13:00:00-04:00 — 2024-09-14T13:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Thrive Family Dental | 14 | BLS | 2021-08-24T12:30:00-04:00 — 2023-07-17T08:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Trial Management Associates, LLC @ Floral Pkwy | 14 | BLS | 2022-11-11T13:00:00-05:00 — 2022-11-11T13:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Morningside of Wilmington | 13 | BLS | 2022-12-30T14:00:00-05:00 — 2024-05-15T13:00:00-04:00 | Wilmington | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Tassi Classes | 13 | BLS, Heartsaver | 2022-01-11T09:00:00-05:00 — 2024-06-04T11:30:00-04:00 | label only | no | no | source_only | SOURCE-ONLY / DO NOT CANONICALIZE |
| Associated Materials Inc. | 12 | Heartsaver | 2022-10-21T10:45:00-04:00 — 2022-10-21T10:45:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Balfour Beatty US: Military Cutoff Project | 12 | Heartsaver | 2020-08-19T08:00:00-04:00 — 2021-06-22T08:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Bradford Products, LLC | 12 | Heartsaver | 2021-08-06T12:30:00-04:00 — 2021-08-06T12:30:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Chambliss & Rabil Contractors | 12 | Heartsaver | 2023-02-15T14:00:00-05:00 — 2023-02-15T14:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Coastal Carolina Care | 12 | BLS | 2024-08-16T13:30:00-04:00 — 2024-08-16T13:30:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Dental Care at Leland Town Center | 12 | BLS | 2024-06-05T07:45:00-04:00 — 2024-06-05T07:45:00-04:00 | Leland | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| GLOW Acadamy | 12 | BLS, Heartsaver | 2024-02-24T09:00:00-05:00 — 2024-04-25T09:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Heraeus Group | 12 | Heartsaver | 2021-10-22T08:00:00-04:00 — 2023-12-04T08:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Kayak Carolina | 12 | BLS | 2024-07-15T18:30:00-04:00 — 2024-07-15T18:30:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Northchase Family Dentistry | 12 | BLS | 2020-11-11T14:00:00-05:00 — 2024-11-07T14:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Croatan Free Will Baptist Church | 11 | BLS, Heartsaver | 2021-06-07T12:30:00-04:00 — 2021-10-04T17:30:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Hoggard Family Dentistry | 11 | Heartsaver | 2023-10-12T14:00:00-04:00 — 2023-10-12T14:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| NC - Wilmington: Freya's Haus (55 Scotts Hill Loop Rd) Visit our hosts' social: | 11 | Heartsaver | 2024-08-10T15:00:00-04:00 — 2024-08-10T15:00:00-04:00 | 55 Scotts Hill Loop Rd, Wilmington | no | yes | html_markup | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Peak Performance Clinics Physical Therapy | 11 | BLS | 2023-08-11T11:00:00-04:00 — 2023-08-11T11:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Sheltering Arms, 165 McKinley Avenue Norwich, CT 06360 | 11 | BLS | 2023-11-13T16:30:00-05:00 — 2024-11-12T15:00:00-05:00 | 165 McKinley Avenue, CT 06360 | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Star Medical Clinic | 11 | BLS | 2022-06-25T18:00:00-04:00 — 2022-06-25T18:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Topsail Beach Fire Department | 11 | BLS | 2022-11-21T18:00:00-05:00 — 2022-11-21T18:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Acme-Delco-Riegelwood Fire-Rescue, Inc | 10 | BLS, Heartsaver | 2023-07-22T08:00:00-04:00 — 2023-07-22T08:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Brothers Steel Erectors & Welding LLC | 10 | Heartsaver | 2022-09-02T08:00:00-04:00 — 2024-09-24T15:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Carolina Yacht Club | 10 | Heartsaver | 2023-06-08T09:00:00-04:00 — 2023-06-08T09:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Scarless Vein Care: Wilmington | 10 | BLS | 2023-07-07T13:00:00-04:00 — 2023-07-07T13:00:00-04:00 | Wilmington | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Seaside Dental Center | 10 | BLS | 2020-08-12T17:00:00-04:00 — 2022-06-16T14:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Seaside Safety LLC, 1002 S. Front St | 10 | Heartsaver | 2021-06-22T10:00:00-04:00 — 2021-06-22T10:00:00-04:00 | 1002 S. Front St | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Balfour Beatty US: Effingham Parkway | 9 | Heartsaver | 2024-05-08T08:00:00-04:00 — 2024-05-08T08:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| CT - Colchester Town Hall, 127 Norwich Ave | 9 | BLS, Heartsaver | 2023-03-21T16:00:00-04:00 — 2023-09-16T08:00:00-04:00 | 127 Norwich Ave, Colchester | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Clinic for Special Children | 9 | BLS | 2022-06-04T10:00:00-04:00 — 2024-06-01T10:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Dunes Dental Services Inc | 9 | BLS | 2024-10-29T16:00:00-04:00 — 2024-10-29T16:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Figure Eight Island Yacht Club | 9 | Heartsaver | 2021-10-07T11:00:00-04:00 — 2021-10-07T11:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Simply Physicals of Jacksonville | 9 | BLS, Heartsaver | 2021-01-13T18:00:00-05:00 — 2021-01-28T18:00:00-05:00 | Jacksonville | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Turkey Creek Fire & Rescue, Station 1 | 9 | BLS | 2021-09-25T18:00:00-04:00 — 2023-05-31T01:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Wilmington Christian Academy | 9 | Heartsaver | 2021-07-17T10:00:00-04:00 — 2021-07-17T10:00:00-04:00 | Wilmington | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| CSE - Raleigh - 4700 Trademark Dr. Raleigh NC 27610 | 8 | Heartsaver | 2021-02-04T08:30:00-05:00 — 2021-02-04T08:30:00-05:00 | 4700 Trademark Dr, Raleigh, NC 27610 | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Holiday Inn Express: Raleigh / Thistledown | 8 | Heartsaver | 2021-07-23T14:00:00-04:00 — 2021-12-18T09:00:00-05:00 | Raleigh | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Huff Family - Wilmington | 8 | Heartsaver | 2023-02-24T08:30:00-05:00 — 2023-02-24T08:30:00-05:00 | Wilmington | no | no | source_only, one_time_or_private | SOURCE-ONLY / DO NOT CANONICALIZE |
| Pneuma Behavioral Health | 8 | BLS | 2024-07-19T14:00:00-04:00 — 2024-07-19T14:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Summit Plastic Surg & Derm: Wilmington | 8 | BLS | 2023-10-16T14:00:00-04:00 — 2023-10-16T14:00:00-04:00 | Wilmington | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Bladenboro Family Dentistry | 7 | BLS | 2022-07-26T08:00:00-04:00 — 2022-07-26T08:00:00-04:00 | Bladenboro | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| CSE - Bolivia - Holiday Inn Oak island | 7 | Heartsaver | 2021-01-18T12:30:00-05:00 — 2021-01-18T12:30:00-05:00 | Bolivia | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Christ Community Church | 7 | Heartsaver | 2024-08-20T10:00:00-04:00 — 2024-08-20T10:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Colchester Town Hall | 7 | Heartsaver | 2023-05-23T11:00:00-04:00 — 2024-08-29T16:00:00-04:00 | Colchester | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| FedUp Foods | 7 | First Aid / CPR AED | 2024-11-01T07:30:00-04:00 — 2024-11-01T07:30:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Holiday Inn Express: Southport / Southport-Supply Rd | 7 | Heartsaver | 2024-01-10T10:00:00-05:00 — 2024-01-10T10:00:00-05:00 | Southport, Supply | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Azalea Health & Rehab Center | 6 | BLS | 2021-04-30T09:00:00-04:00 — 2021-04-30T09:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Community Home Care & Hospice: Belville | 6 | BLS | 2022-12-09T09:00:00-05:00 — 2022-12-09T09:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Cragin Library, 8 Linwood Ave, Colchester, CT 06415 | 6 | Heartsaver | 2024-05-18T09:00:00-04:00 — 2024-05-18T09:00:00-04:00 | 8 Linwood Ave, Colchester, CT 06415 | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Grace Community Church of Topsail: Office | 6 | Heartsaver | 2022-02-05T09:00:00-05:00 — 2022-02-05T09:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| New Hanover County Public Library - Pine Valley Branch | 6 | BLS, Heartsaver | 2019-09-26T17:00:00-04:00 — 2019-11-14T17:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Quality Care Day Care & Cooperative Nursery School | 6 | Heartsaver | 2023-06-01T16:30:00-04:00 — 2023-06-01T16:30:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Smokey Tony's - Holly Ridge | 6 | BLS | 2020-06-18T09:30:00-04:00 — 2020-06-19T09:00:00-04:00 | Holly Ridge | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Summit Plastic Surg & Derm: Hampstead | 6 | BLS | 2024-04-02T16:00:00-04:00 — 2024-04-02T16:00:00-04:00 | Hampstead | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Topsail Island Association of Realtors | 6 | Family & Friends | 2022-02-02T10:00:00-05:00 — 2022-02-02T10:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Elderhaus: Wilmington / N.College Rd | 5 | BLS | 2024-08-09T12:00:00-04:00 — 2024-08-09T12:00:00-04:00 | Wilmington | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Filmwerks - Main Shop Warehouse | 5 | Heartsaver | 2020-12-02T12:30:00-05:00 — 2020-12-02T12:30:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Logan Marine | 5 | Heartsaver | 2021-06-25T13:00:00-04:00 — 2021-06-25T13:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Summerhouse on Everett Bay | 5 | Heartsaver | 2020-10-17T09:00:00-04:00 — 2020-10-17T09:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| 910CPR's Office | 4 | Other / legacy | 2024-08-17T09:00:00-04:00 — 2024-08-17T09:00:00-04:00 | label only | no | no | insufficient_specificity | AMBIGUOUS / REVIEW REQUIRED |
| Courtyard by Marriott in Jacksonville, NC | 4 | BLS | 2022-01-27T09:00:00-05:00 — 2023-06-24T10:00:00-04:00 | Jacksonville | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Grace Community Church of Topsail: S. Topsail Elem | 4 | Heartsaver | 2024-07-13T09:00:00-04:00 — 2024-07-13T09:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Treehouse Kids Preschool | 4 | Heartsaver | 2021-09-29T13:15:00-04:00 — 2021-09-29T13:15:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Victory Health Consultants | 4 | BLS | 2020-07-17T09:30:00-04:00 — 2020-07-17T09:30:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Walmart: Jacksonville, Marine Blvd | 4 | BLS | 2020-07-01T09:00:00-04:00 — 2020-07-01T09:30:00-04:00 | Jacksonville | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Coastal Carolina CPR Office - Long Leaf Office Park - Phlebotomy Programs | 3 | Phlebotomy | 2021-03-15T18:00:00-04:00 — 2021-05-17T17:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Move, Learn, Play, PC | 3 | BLS | 2020-01-17T13:00:00-05:00 — 2020-01-17T13:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Providence Baptist Church | 3 | Heartsaver | 2023-09-12T13:00:00-04:00 — 2023-09-12T13:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Residence - 6239 Mirage Way, Wilm | 3 | Family & Friends | 2024-01-04T15:30:00-05:00 — 2024-01-04T15:30:00-05:00 | 6239 Mirage Way | no | no | source_only, one_time_or_private | SOURCE-ONLY / DO NOT CANONICALIZE |
| Scarless Vein Care: Leland | 3 | BLS | 2021-03-24T16:45:00-04:00 — 2021-03-24T16:45:00-04:00 | Leland | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Surf City Dental | 3 | ACLS | 2024-10-07T14:00:00-04:00 — 2024-10-07T14:00:00-04:00 | Surf City | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Wallace Woman’s Club | 3 | Other / legacy | 2020-10-18T13:00:00-04:00 — 2020-10-18T14:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Action Therapy, Jacksonville, NC | 2 | BLS | 2021-09-21T13:00:00-04:00 — 2021-09-21T13:00:00-04:00 | Jacksonville | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Contail Road | 2 | Heartsaver | 2021-03-06T13:00:00-05:00 — 2021-03-06T13:00:00-05:00 | label only | no | no | source_only | SOURCE-ONLY / DO NOT CANONICALIZE |
| Enchanted Jungle Daycare, 67 Hayward Ave, Colchester, CT 06415 | 2 | Heartsaver | 2024-11-06T16:00:00-05:00 — 2024-11-06T16:00:00-05:00 | 67 Hayward Ave, Colchester, CT 06415 | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Freedom Village Dental | 2 | BLS | 2020-09-21T10:00:00-04:00 — 2020-09-21T10:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| ___TBD___ | 2 | BLS | 2024-02-23T06:30:00-05:00 — 2024-05-28T08:00:00-04:00 | label only | no | no | source_only, one_time_or_private | SOURCE-ONLY / DO NOT CANONICALIZE |
| 443 Holly View Lane Loris, SC 29569 | 1 | BLS | 2021-04-01T18:30:00-04:00 — 2021-04-01T18:30:00-04:00 | Loris, SC 29569 | no | no | source_only, address_only | SOURCE-ONLY / DO NOT CANONICALIZE |
| Airlie Oral Surgery | 1 | ACLS | 2023-03-08T08:00:00-05:00 — 2023-03-08T08:00:00-05:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Onslow Pines Park | 1 | Family & Friends | 2021-06-05T08:30:00-04:00 — 2021-06-05T08:30:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| River Run Plantation Clubhouse | 1 | Heartsaver | 2023-05-13T10:00:00-04:00 — 2023-05-13T10:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Roos Residence | 1 | BLS | 2020-03-01T12:00:00-05:00 — 2020-03-01T12:00:00-05:00 | label only | no | no | source_only, one_time_or_private | SOURCE-ONLY / DO NOT CANONICALIZE |
| Walmart: Jacksonville, Yopp Rd | 1 | BLS | 2022-02-02T23:00:00-05:00 — 2022-02-02T23:00:00-05:00 | Jacksonville | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Walmart: Whiteville, NC | 1 | BLS | 2020-06-09T09:00:00-04:00 — 2020-06-09T09:00:00-04:00 | label only | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Williams Love Grove Baptist Church - Herbert Estelle | 1 | Heartsaver | 2024-08-17T10:00:00-04:00 — 2024-08-17T10:00:00-04:00 | label only | no | yes | html_markup | CANONICAL HISTORICAL LOCATION CANDIDATE |
| Wilmington Health @ Medical Centre Dr | 1 | BLS | 2020-07-14T13:00:00-04:00 — 2020-07-14T13:00:00-04:00 | Wilmington | no | yes | named_venue | CANONICAL HISTORICAL LOCATION CANDIDATE |

The companion JSON includes provenance hashes and every proposed minimum archive-only canonical record.

NHCSO 2026 remains outside the supplied source period and was not reconstructed.
