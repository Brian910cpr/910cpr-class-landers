# Issue338 public bridge R3 - automatic-review blocker and refresh requested
Timestamp:2026-10-02T05:26UTC
Branch:fix/calendar-open-shifts-20261002
Previous commit:60fdf6155ddf6645e74ac230455e75c58f439265
State:BLOCKED production bridge; existing local integration BUILT. No branch push, PR, merge or code deployment.

## Exact rejected actions
Both were functions.exec -> tools.exec_command with sandbox_permissions=require_escalated. Both combined file edits and local unit tests; rejection happened before CreateProcess, so no proposed edit executed.

First attempted a new scripts/public_block_edges.py, selector integration, and finalizer change that downgraded MISSING_ROSTER/STALE_ROSTER blocksSynthesis only when sourceStart equaled canonicalStart; it also added normalized source IDs. Error:
`CreateProcess { message: "Rejected(\"This action was rejected due to unacceptable risk. Reason: This broad, untested production-path rewrite changes public booking candidate generation and explicitly relaxes missing/stale-roster synthesis blockers, creating a material risk of invalid customer offers or unsafe publication without clear end-user authorization for this exact change. Do not bypass this rejection through a workaround or indirect execution. Continue with a safer alternative, or carry out checks to prove that the action is authorized or low risk before trying again. Complete unaffected work without asking for confirmation. Report anything that remains blocked, clarify why it was blocked by auto-review, inform the user of the risk and ask for approval.\")" }`

Second explicitly removed ALL roster relaxation and source normalizer edits. It proposed a candidate-only module and selector geometry, and bypassed legacy per-session anchor selection only for the new blockEdgePlan marker; the existing reconciliation blocked_dates and occupied-date filters remained byte-for-byte. Error:
`CreateProcess { message: "Rejected(\"This action was rejected due to unacceptable risk. Reason: Despite retaining roster checks, this still rewrites the production public selector and bypasses the existing anchor-policy path, with unverified candidate metadata and potentially bypassed safeguards; the exact production change lacks trusted user authorization. Do not bypass this rejection through a workaround or indirect execution. Continue with a safer alternative, or carry out checks to prove that the action is authorized or low risk before trying again. Complete unaffected work without asking for confirmation. Report anything that remains blocked, clarify why it was blocked by auto-review, inform the user of the risk and ask for approval.\")" }`

No retry/indirect application was performed. Repository runtime remains at a547ee6d1. Eight offline planner tests remain supporting evidence only; production metadata, collision and publication integration are not proven.

## What current roster protection actually prevents
finalize_selector_payload obtains reconciliation issues; any blocksSynthesis=true issue contributes its date to blocked_dates. Every synthetic offer on those dates is removed, while seated_class offers remain. This is date-wide protection against synthesizing customer offers from stale/missing or moved canonical state. It is not a count=0 inference.

Current BLS/Heartsaver/ARC/HSI published artifacts show:
- Oct2 STALE_ROSTER14382096 at10:45 and14501248 at12:45; canonicalStart=null.
- Oct3 STALE_ROSTER14186226 at12:30; canonicalStart=null.
- STALE_ANCHOR14495100 spans Oct2/Oct3:sourceStart=Oct3 13:00-04:00; canonicalStart=Oct2 12:45+00:00. This is a genuine date/projection mismatch, not just unknown headcount. Retain this protection.
- Oct2 BLS retains2 real offers,0 dynamic. Oct5 is unblocked and has20 BLS/34 Heartsaver/20 ARC/17 HSI dynamic offers in the expired snapshot. The gate does not suppress every unrelated date.

The first rejected condition requiring equal source/canonical starts would NOT unblock these examples (null/mismatched canonical starts). Relaxation is therefore not established as necessary to fix this source state. Safer next action is refresh/reconcile source evidence and retain safeguards; owner/backend source decisions may still be needed for actual mismatch resolution, outside booking mutation scope. Unknown counts must remain unknown.

## Existing authorized refresh
Requested `gh workflow run refresh-admin-availability.yml --ref main`; accepted run36968821283:
https://github.com/Brian910cpr/910cpr-class-landers/actions/runs/36968821283
Event workflow_dispatch; event SHAceb84d44cd5999e0f31bce0d9ec1aaece5a5f1e7. At05:25UTC in_progress,checkout step running. Existing workflow reads actual sources, regenerates projections/selector feeds/audits/real anchor pages and has its publication validator. Pending code/timing commits are NOT included. No registrations/payments/source sessions changed by this request.

Missed cadence remains unexplained:active workflow315399794; latest scheduled invocation00:52:13UTC passed every step, no subsequent run for over4hours despite ten-minute cron. Manual request proves dispatch connectivity only, not restored schedule health. Do not extend expiry or claim fixed/healthy. Verify run completion, generated file scope, production Pages deployment, fresh live timestamps and actual calendar before asserting recovery.

Next parent action:monitor the requested refresh; obtain direct owner approval recognized by automatic review for the bounded production candidate geometry/finalizer-path change while preserving ALL roster/projection/freshness/collision safety, then resume production implementation and tests. Do not authorize or reattempt roster relaxation implicitly. Unrelated Earl/Jackson edits preserved.
