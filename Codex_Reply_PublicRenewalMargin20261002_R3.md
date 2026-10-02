# Issue 338: renewal release final customer-surface proof

Timestamp: 2026-10-02T10:42:41.350956+00:00
Branch: fix/public-renewal-margin-20261002.
Code: PR340 merged as6c192747bcf7ab8c13eb60752661be8e42e6f66e; source7f9a0569a.
Final production: cf1f28fa038883672b1e0961c824bbe4ba4413d4.
State: VERIFIED bounded margin release. Persistent evidence: PROVEN local gate and real push-triggered end-to-end publication; genuine scheduled renewal/recovery not observed, not HEALTHY.

Refresh36996017646 (event=push, created/start10:32:18UTC) succeeded at10:38:36UTC. Its new margin-test step passed in production Linux/PowerShell; existing zero-duration, strict-link, Anchor and inventory checks also passed. Pages36996592688 (event=dynamic) deployed cf1f28fa at10:39:34UTC. All PRchecks passed before merge; Cloudflarepreview/preflight separate successes. Local10focusedtests passed, ASTparse/gitdiffcheck passed. No broader local suite/fullbuild rerun; existing remote pipeline did its configured validated build.

At 2026-10-02T10:40:13.728703+00:00, eight live HTML pages and four live JSON feeds byte-match finalproduction. GET-only Chrome: BLS and Heartsaver zero JavaScript errors, fresh notice hidden, October5 starts07:45/08:15/08:45/09:15/09:45/10:15 and live appointment links rendered. BLS Initial19Octoberdates; Heartsaver17. BLS actualOctober2/October12 real Enrollware booking links retained. Admin schedule comparison against pre-change6c192747 proves all29actualsessionstarts unchanged, no added/removedsessions. No sourceobjects/sessions/registrations/payments or calendarstarts changed by this assignment.

Final BLS validUntil12:06:03.607508UTC; Heartsaver12:06:41.814704UTC. Fresh publications validated from sources; no existing lease extended, staleoffers exposed or denied geometry/roster changes. Push forces build, so this proves release path and refreshed customer inventory; actual due-lease scheduled selection remains supported by deterministic real-gate tests, not an observed schedule event.15minute processingbudget cannot guaranteearbitrarilylongqueue/outage.

Corrected scheduled history from exact run APIs:
- PUBLIC36970091836: event=schedule, created/start05:41:46UTC, updated/completed05:48:57UTC, success.
- ADMIN36973245914: event=schedule, created/start06:22:37UTC, updated/completed06:29:31UTC, success.
- Pages36973792793: event=dynamic,06:29:29->06:30:25UTC, deployed admin-produced1715e1f4. Earlier description of06:22 as public was incorrect; it is corrected here and on originatingissue.
Latest unfilteredhistories stillshow no latergenuineschedule events for eitherworkflow. Successfulmanual/pushruns do not prove triggerrecovery. Exact timeline saved in review/public-renewal-margin/exact-run-timeline.json.

Evidence: thisreceipt; review/public-renewal-margin/final-refresh-live-proof.json; exact-run-timeline.json; github-support-evidence-summary.md. Supportsummary preparedlocally withworkflowIDs,crons,exactruns, RESTrequestIDs, correctionandquestions; notsubmitted externally. Verification script C:/Users/ten77/AppData/Local/Temp/verify_final_renewal_refresh.py accepts productionSHA andPagesrun. PreviousR1/R2receipts/evidencepreserved. Noadditionalapplicationchange inthisround; originalunrelatedEarl/Jackson/caches/pendingbridge/lab preserved.

Remaining blockers:
1. Denied publicblock-edge/selector bridge awaits preciseowneranswer/approval. No retry or guardrelaxation.
2. MissingGitHubscheduleeventdelivery needs platform/accountinvestigation. Exactintervention: owner/accountadmin approves/submits localSupportsummary askingdelivery/actor/throttling/rootcause andRESTfilteromissions; no supportrequestsent. No newworkflowchain,security/accesschanges, adminavailabilitypublication or total-fetchfallback introduced.

Proofcontract: desiredrenewalvalidated/live beforeexpiry; expected30minutecheck,45minlookahead; lastsuccessfulpush end-to-endproof above; failureexpiry/missedcycle/overbudget; observercurrentlyboundedCodex/ChatGPT and its durableindependenthealth unproved; recoveryexistingapprovedrefresh; platform/accountescalationasabove. Brian mustnotserve asroutineobserver. Nextparentaction: reportcompletedboundedrelease, correctedtimeline and remainingblockers. No needpoll completedpushruns. Anyindependentobserver or supportsubmission remainsseparatelyauthorizedscope.
