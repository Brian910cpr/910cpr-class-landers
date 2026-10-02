# GitHub Support evidence summary — prepared locally, not sent

Repository: Brian910cpr/910cpr-class-landers. Default branch: main.
Prepared: 2026-10-02 UTC. No secrets or participant details included.

Issue: expected scheduled workflow events are absent for hours, while the same active workflows execute successfully via manual dispatch and push. Exact provider/account cause is unknown. Please investigate event delivery; do not assume a build failure.

| Workflow | ID | Cron UTC | Latest verified scheduled run | Created/start UTC | Completed UTC | Result |
|---|---|---|---|---|---|---|
| Refresh public site from Enrollware iCal | 301038681 | 13,43 * * * * | 36970091836 | 2026-10-02 05:41:46 | 05:48:57 | success |
| Refresh admin availability | 315399794 | 7,17,27,37,47,57 * * * * | 36973245914 | 2026-10-02 06:22:37 | 06:29:31 | success |

Correction to an earlier report: 06:22 was ADMIN, not PUBLIC. Pages run36973792793 (event=dynamic, created06:29:29, completed06:30:25) deployed admin-produced commit1715e1f4f5116f2d4a16bcdb47c934ebbe300bb7. It is not evidence of a public schedule event.

Later successful non-scheduled controls:
- Admin36991931458 at09:48:47, event=workflow_dispatch, success.
- Admin36994082058 at10:11:23, event=push, success.
- Public36994082057 at10:11:23, event=push, success; completed full job in6m49s.
- Public36996017646, event=push after approved renewal-margin PR340; success, created10:32:18UTC, completed10:38:36UTC; final publication cf1f28fa038883672b1e0961c824bbe4ba4413d4 and Pages36996592688 completed10:39:34UTC.

Both workflow histories were checked unfiltered and exact known runs fetched directly. Workflow state active; earlier evidence shows repository not archived/disabled, Actions enabled, default main. Those facts do not establish the root cause. Read-only latest history snapshots: review/public-renewal-margin/public-runs-checkpoint.json and admin-runs-checkpoint.json.

Separate REST inconsistency at05:39UTC: event=schedule omitted known recent runs and returned September11/older; unfiltered and exact run endpoints showed October2 schedule events. Filtered request ID CAEA:10CF44:1F5DE0:68915D:6ABF4378; unfiltered ID CAEE:1A618E:20A2B4:6C8CBC:6ABF4379. Both response dates current with60second cache limit; no-cache date-scoped query still omitted expected new events. Please investigate this separately from actual missing delivery.

Requested investigation: explain missing default-branch schedule events for both workflow IDs after the last exact runs above, confirm scheduled actor/account eligibility or delivery throttling, identify whether events were delayed/dropped and why, and explain the filtered REST omissions. Supply a concrete provider/account remedy if applicable. No workflow disable/enable, security setting, access, credential or scheduling-chain changes were made to diagnose this.

Independent application defect fixed separately: public cadence30minutes with old renewal lookahead10minutes could miss unchanged-feed renewal plus ~7minute build/queue/deployment. PR340 raises lookahead to45minutes while leaving offer expiry intact. This cannot restore undelivered GitHub triggers.

Official schedule behavior reference: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule . GitHub documents potential delays/dropped jobs under load; this is a possible explanation, not a proven diagnosis here. Cron already avoids minute zero.

Owner/account admin approval is required before submitting this external Support request. No request has been sent. A durable independent observer/recovery mechanism requires separate scope and must not rely on Brian remembering routine checks.
