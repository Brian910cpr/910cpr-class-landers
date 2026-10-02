# Issue338 refresh verification R4
Timestamp:2026-10-02T05:34UTC
Branch:fix/calendar-open-shifts-20261002
Previous local commit:446ffa110
State:VERIFIED manual refresh recovery only; BLOCKED pending public block-edge code approval.

Authorized existing refresh run36968821283 SUCCESS; produced production commita87a4d5d5a3b72eaabf143d8696e95b82b324625 (26 expected projection/audit files). Existing publication validator passed; no booked sessions, registrations or payments were edited. GitHub Pages deployment36969265705 SUCCESS for that exactcommit.

At05:33UTC live admin_schedule/admin_availability/BLS/Heartsaver JSON bytes exactly matched the production commit. Schedule generated05:26:41UTC; availability05:26:42UTC; selectors validuntil06:57UTC. Live GET-only Chrome /bls.html and /heartsaver.html:zero page errors; no refreshing/unavailable warning; Oct5 enabled and rendered07:45,08:15,08:45,09:15,09:45,10:15 starts for selected inperson courses. Links retain appointmentDayId260776 and BLS209806/HS344085 course IDs; no registration was submitted. Live BLS retained FridayOct2 12:45PM realclass. These are incumbent outputs, not pending owner-timing/block-edge code.

Freshness verification:review/calendar-open-shifts/public-calendar-refresh-verification.json. Source dates and SHA256 hashes preserved. Manual refresh recovery evidence PROVEN for projectionpublication->Pages->actualpubliccalendar, not MONITORED/HEALTHY:ten-minute scheduled heartbeat still not shown recovered; no independent observer-health proof. Existing expiry is unchanged.

Family&Friends session14495100 read-only trace at05:30UTC:
- Enrollware iCal:2026-10-03T13:00:00-04:00 to14:45-04:00,RoomB Shipyard; not marked cancelled in thatevent.
- Fresh public schedule projection matches Saturday13:00-14:45.
- Fresh reconciliation records canonicalStart2026-10-02T12:45:00+00:00, which is Friday08:45AM Eastern. STALE_ANCHOR blocks Oct2 andOct3.
This actual move/projection discrepancy persists after refreshing, so do not weaken its protection or silently remove a booking. Canonical value is from sanitized reconciliation evidence; no authenticated canonical-service query or mutation was performed. Direct urllib TLS verification of Enrollware failed certificate-expired; sourceevent was read through existing repository fetch_ical_text helper (which already contains a TLS fallback), with no transport/config change. That source-read provenance is a limitation.

Production bridge still awaits the owner's answer. No rejected edit rerun or workaround. Second rejection action: functions.exec->tools.exec_command(require_escalated), proposed scripts/public_block_edges.py plus candidate-generation edits in scripts/block_start_time_selector.py and marker-based replacement of per-session legacy selection in scripts/apply_anchor_policy.py, followed by local unittests. Roster blocked_dates/projection/freshness/conflict checks unchanged. Rejected before CreateProcess; nothing executed.
Exact reason: "Despite retaining roster checks, this still rewrites the production public selector and bypasses the existing anchor-policy path, with unverified candidate metadata and potentially bypassed safeguards; the exact production change lacks trusted user authorization."
Full rejection including refusal/remediation text:Codex_Reply_CalendarPublicBridge20261002_R3.md. Await precise owner approval already requested by parent, not roster relaxation. Local branch has not been pushed/opened/merged/deployed. Earl/Jackson edits preserved.
