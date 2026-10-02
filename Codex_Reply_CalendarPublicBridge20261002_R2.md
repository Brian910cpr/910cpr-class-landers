# Issue338 public path checkpoint R2
Timestamp:2026-10-02 UTC
Branch:fix/calendar-open-shifts-20261002
Implementation commit:a547ee6d1
State:BLOCKED for production bridge; existing calendar implementation BUILT.

Automatic approval review rejected the proposed combined production edit before execution. Reason: broad untested public booking candidate-generation rewrite together with relaxing missing/stale-roster synthesis blockers creates material invalid-offer/publication risk without clear authorization for that exact policy change. No rejected production edit ran; no push, PR, merge, deployment or refresh occurred.

Completed unaffected work:read concurrent PR333 and currentmain (no newer main commits), inspected existing public publication/validation and workflow executions; proved an isolated offline planner with8 tests passing. Proof artifacts are in review/calendar-open-shifts/offline-proof; they are not imported by runtime, are not an end-to-end public implementation, and do not relax any production rule. Coverage:skills11/13 ->11/14 ->10/14; full150min pre/post candidates and chain growth; multiple blocks/no scatter; offsite nonmerge; overnight; hourlywide/halfhourtight; immutable bookings; unknown durationfails. Existing focused actualcalendar and lab checks remain as previous receipt; no production bridge tests can be claimed passed.

Refresh evidence:workflow315399794 active; latest run36948145959 was scheduled2026-10-02T00:52:13Z and all steps succeeded. Prior scheduled run36927521781 also succeeded. No failed refresh invocation appears in latest5 executions; scheduled heartbeat did not execute for over4hours despite cron7,17,27,37,47,57. Therefore no generator failure has been established. Do not misreport successful old runs as current health, extend expiry, or claim the missing heartbeat is fixed. Existing publicationexpiry correctly exposes stale data.

Exact proposed policy requiring review:derive candidates from merged real occupied blocks (not individual-anchor nearest scans), both supported short skills and full classes at each edge; constrain fullbarnacles after qualification/URL/conflictvalidation; on free days thin genuinely free intervals. Missing/stale headcounts remain unknown and diagnostic only IF source and canonical starts agree and occupancy interval is resolved; moved/missing/stale session projections, unresolved occupancy, source freshness and actual collisions still fail closed. Production implementation remains pending.

Next parent action:confirm approval for that exact policy change in response to automatic-review rejection, then resume implementation and targeted tests followed by authorized push/review/merge/deploy/refresh/liveverification. No credential or access changes are requested. Existing owner release approval otherwise remains in force. Earl/Jackson changes untouched.
