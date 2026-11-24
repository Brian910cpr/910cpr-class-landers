# Codex Read — Issue 380 R20

Round: DELTAWATCH-20261013T112900Z-7F3C
Reviewed handoff: Codex_Reply_Issue380_20261013_R20.md
Reviewed substantive commit: 1fc8976ad8df7991fb1bc36f3de94bd44e6fd137
Reviewed tip: 0f83b40aa6387e482d885798510377b3f688a5a0

Delta Watch inspected the SQL lock-order change, its primary report, contention regressions, receipt, and green PR workflows.

Disposition: accepted as meaningful BUILT-only progress. The negative control reproduced the prior intake/card deadlock. The draft now locks intake before card, matching intake DML ordering; the reported final PostgreSQL suite passed 16/16 with eight observed Lock waits, and backend/auth passed 68/68. All decisions remain can_execute=false.

Keep SQL outside migrations and PR #381 draft, unmerged, and undeployed. Next same-stream work is the authenticated typed-intake publisher using the same lock order with expected-version, idempotency, audit, and provenance tests, followed by installed consumer and external side-effect fencing. Missing-intake, bulk/multi-card, and trusted-role ordering limits remain open. No Brian action now.