# Issue 338: October 10 cross-course suppression diagnosis

Timestamp: 2026-10-02T11:21:37.277181+00:00
Branch: fix/public-renewal-margin-20261002. Existing production cf1f28fa; read-only investigation, no implementation/deployment.
State: VERIFIED reproduction and policy/source diagnosis; fix BLOCKED pending precise public-bridge authorization. No denied rewrite retried.

Customer reproduction in Chrome: BLS Initial209806, Renewal359474, HeartCodeSkills210549 and ASAP/all-options all have no selectableOctober10, no warning, zeroJavaScripterrors. Full HeartsaverFA/CPR/AED209809 shows exactly one2PMscheduledclass and its real LanderWare registrationlink. Preserve thisdesiredsinglefullHSoccurrence. HSresolvedfeed separately contains a noonblended329495 syntheticoffer; it is not booked occupancy and is hidden in the full-HS-only selection.

Actualsourcecommitments in America/New_York:
- Approved business DoNotSchedule calendar has overlapping ADR/shift/post-shift blocks endingSaturday07:00. Its approvedinverseavailableblock is07:00 to nextmidnight. This is the business workblockingcalendar, not indiscriminate personalpubliccalendar input.
- Canonical LanderWare HSFA/CPR/AEDsession lw-b48b53c7-df11-409f-a8f0-61b72a7f17e9, course209809, Shipyard:14:00-16:30Eastern (18:00-20:30UTC), oneactivecanonicalregistration, count_available=true and demand_status=current. Consumptionintervalsame in currentpublicprojection. PublishedPII-freeprojection doesnot identify the enrollee, so Gordonname not independentlyconfirmed.
- No other October10 real session appears in publicschedulefuture. admin_schedule lacks thiscanonical-onlyevent while schedule_future/anchor_state include it; don'tmistake missingadminprojection for a freeperiod. Do notinferwholedayoccupied or countunknownaszero.

Rootcause: BLSfeedmarksOct10occupied but hasnoOct10reconciliationissue/blockeddate. Effectiveproductioncompatibility for HSanchor209809 allows only329495 (HSblended), not anyBLS209806/359474/210549. barnacle_compatible at apply_anchor_policy.py389-390 rejects disallowedpairs. Since BLS cannot receivebarnacle status, finalize_selector_payload555-557 removes syntheticoffers on occupieddates unless role=barnacle. Auditcategory563-565 isORPHAN_SYNTHETIC_OFFER, not stale roster or actualall-daycollision. Metadata808suppressedoffers isglobal, not anOct10count. No upstreamregen/auditdownload, so exactOct10pre-finalizationcandidatecount unobserved. This distinction is recorded in evidence.json.

Freshnesschecked11:14-11:20UTC: BLSvalidUntil12:06:03UTC; HS12:06:41UTC, bothfresh. Feedexpiry/filtercheckboxes do notexplain Oct10. One-course/daymetadata is legacy/global, not proofallSaturdaybooked or directcause ofthiscrossfamilyrejection.

Minimal required behaviorfix: permit reviewed BLS full/skills attachments at legitimate edges of the existingHSoccupiedblock; generate/classifyvalidatededgeoffers with agreedcourse duration/cleanup, capability/location/travel/leadtime/conflict androster/freshness safeguards. Keep209809singlefulloccurrence; do notduplicatefullHS. CrosscoursecompatibilitymustnotlimitallBLS to anchors ofitsownfamily. Exactfuturestarttimesneed approvedconsumption/cleanup rules; currentpublicBLS120/HeartCode60 differfrompendingowner120+30/45+15 rules. Do notpromiseparticularnewstartsfromoldtimings. ImplementOct10crosscoursefixtureasregression whenexactbridgeapprovalarrives. No productionedit, policyflip, sourcewrite, sessionmovement or schedulingpublishperformed.

Evidence: review/oct10-bls-diagnosis/evidence.json (sourceintervals, realanchor, allowedpairs, browser variants andlink, flags, freshness andtrace). Supporting transientbrowser script C:/Users/ten77/AppData/Local/Temp/oct10_browser.py; GET-only, no bookingssubmitted. ScopefocusedonOct10, no broad audit/build/tests. Original unrelatedfiles and pendingworkpreserved.

Nextparentaction: tell Brian Saturdayisnotbookedall day: work ends07:00, existingHSclass14:00-16:30, oldcrosscoursecompatibility+occupieddatefilter hideBLS. RetainHSfullview and request/await precisebridgeanswer; no retryuntilauthorized. Persistenthealthnotassessedinthisread-onlydiagnosis; missingGitHubscheduleddelivery remains separatelyunresolved.
