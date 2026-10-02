# Issue338 current two-date BLS diagnosis R8

Timestamp:2026-10-02T09:46UTC
Branch:fix/calendar-open-shifts-20261002
Previous local commit:c9d05d520
State:customer scheduling repair NOT COMPLETE; diagnostic VERIFIED, public model edit BLOCKED awaiting precise owner approval.

## Exact reproduced view

Current GET-only Chrome /bls.html matches Brian's screenshot:Initial/In Person selected,ASAP/compare unchecked,all five time checkboxes unchecked,SmartFilter empty. Exactly two enabled October dates:Oct2 at12:45PM andOct12 at5:00PM. Zero page errors. No filter caused the missing dates.

At09:41-43UTC the public feed generatedAt was2026-10-02T02:24:44.800964 Eastern (06:24UTC); validUntil07:55:07UTC,already expired. Raw October course209806 has433 offers on19 dates:431 dynamic appointments and2 real seated classes. The actual browser's datesForPublication plus Initial course filtering removes expired dynamic appointments and leaves exactlyOct2/Oct12,one offer each. Two highlighted dates are not the raw total offer count. This is safe fail-closed expiry behavior,not a reason to expose stale offers.

The page sets a refreshing message internally but does not visibly show it in this ready-with-real-classes view; browser body had no refreshing warning. That display omission makes the two-date result look like ordinary monthly availability. Current pixels are captured through explicit browser/date/checkbox evidence in current-two-date-bls-diagnosis.json; parent supplied screenshot interpretation,so no Library file needed here.

## Refresh and additional suppression

A genuinely scheduled admin refresh36973245914 at06:22:37UTC succeeded and Pages36973792793 completed. Admin cadence did recover once after the earlier diagnostic, but latest admin history still has no newer run through09:44UTC. Public workflow's latest scheduled run remains36970091836 at05:41UTC. Thus previous one-run recovery did not establish sustained cadence and the feed expired again. No workflow was triggered in this read-only diagnosis.

The live anchor policy still isdaily-anchor-stack-v1,808 suppressed offers,zero barnacle positions,one_course_type_per_calendar_day=true. October reconciliation has26STALE_ROSTER,2STALE_ANCHOR and3MISSING_CANONICAL_SESSION issues. These additionally suppress synthetic offers on their affected dates; they do not explain the disappearance ofall431 rawInitial dynamic offers from the current view—the expiry gate does. F&F genuine date mismatch remains protected. No unknown count was converted tozero/free.

Local owner-timing/model tests remain separate from live implementation. The branch has not been pushed/merged/deployed. Live Initial dynamic offers showduration120/scheduler consumption120,where owner requires120instruction+30cleanup=150. Live HeartCode offers showduration60/consumption60 rather than explicit45instruction+15cleanup. No live real booking start was changed here. The local Operations model/lab considers both skills andfull at merged edges, but live public generation still loopsfree-grid candidate_starts and then per-session dailyanchor compaction. Freshening that incumbent output alone cannot prove or implement Brian's requested behavior.

## Smallest safe actions

Immediate recovery:existing `gh workflow run refresh-admin-availability.yml --ref main` can fetch/validate current sources and restore current dynamic publication,under existing prior recovery approval. It was NOT run in this explicitly read-only turn. Do not extend expiry or bypass freshness. It would restore eligible incumbent Initial dates,not fix merged-block behavior.

Actual model repair still blocked:replace public candidate geometry at scripts/block_start_time_selector.py:1170 and per-session selection at scripts/apply_anchor_policy.py:331/540 with proven merged real occupied blocks andedge candidates,including fullInitial offers as well asskills,then allcurrent roster/projection/freshness/URL/collision/travel checks. The prior denied proposal also supplied a new scripts/public_block_edges.py and marker-based finalizer path. No denied edit was retried. Exact review error remainsR3; preserving safeguards is necessary but automatic review still required trusted authorization for the exact replacement.

Existing issue338body documents general calendarrelease approval but explicitly describes an admin/display-only implementation. Its subsequent Codex receipts are diagnostic records,not a verified direct owner answer to the precise public-selector replacement question. Brian's intended customer-facing result is clear from current instructions; additional exact approval remains pending as parent stated. Do not invent a received approval or use old generated issue text as evidence of it. Parent should relay this diagnosis promptly and distinguish emergencyexpiry recovery from the still-unimplemented publicblock-edge repair.

No source/booking/registration/payment mutation,no publicdeployment or PR,no manualrefresh,no safeguardrelaxation. Earl/Jackson edits and trackedPython caches excluded from staging. Read-only Python imports created/cache artifacts may exist;no broadcleanup performed. Full task remainsopen.
