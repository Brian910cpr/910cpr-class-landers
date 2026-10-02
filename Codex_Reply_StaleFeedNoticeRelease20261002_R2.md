# Issue 338: warning release customer-surface proof

Timestamp: 2026-10-02T10:21:39.268401+00:00
Branch: fix/stale-feed-notice-20261002
Release: PR #339 merged as fd28f7cf9836738b5fdab1cc2e39e154b284b69f.
Current verified production commit: ee182ed47193c0f016d073f577179a4c58337e4e.
Work-item state: VERIFIED warning release; IN_PROGRESS public refresh follow-through.
Persistent evidence: PROVEN warning customer surface and push-triggered admin refresh; scheduled reliability is not HEALTHY.

All eight changed live HTML pages and four checked JSON feeds byte-match the current production commit. Chrome loaded all eight with zero JavaScript errors and hidden warning on fresh data. An isolated browser response interception changed only a copied feed validUntil: stale BLS shows the warning, removes dynamic offers, preserves October 2 12:45 PM and October 12 5 PM classes and the identical real Enrollware enrollment links. No live feed, session, booking, registration, payment or source object was changed. Fresh Initial view includes 19 October dates. HTTP503 interception displays the failed-load message and no offers.

Important limitation: total network failure already clears scheduleDates in the existing catch block; real bookings are consequently unavailable in that failed view. This release does not add cached/source fallbacks. Stale successfully downloaded feeds preserve real bookings. The originally stronger failed-fetch booking-retention assertion failed and exposed this limitation; the final checks explicitly distinguish these behaviors instead of claiming a fallback exists.

Production Pages run 36994080896 succeeded for merged warning. Admin push refresh 36994082058 succeeded; its Pages run 36994585614 succeeded for ee182ed47. Public push refresh 36994082057 is still in its configured full validated build at this checkpoint. These are push events, not scheduled-recovery evidence. Cloudflare preview and preflight succeeded separately; GitHub Pages is the verified production host.

Live feed observation at 10:19 UTC: admin_schedule 10:13:10Z; admin_availability 10:13:12Z. BLS validUntil 11:43:29Z; Heartsaver 11:44:08Z, both unexpired. JSON generatedAt is a legacy source timestamp and not the publication expiry.

Evidence files added in this round: this receipt; review/calendar-open-shifts/live-notice-verification.json; live-notice-stale.png; live-notice-failed.png. Exact eight paths, hashes, enabled dates, notices, booking links and feed timestamps are recorded in the JSON. Screenshot visually inspected: readable notice and retained real registration card. Verification script: C:/Users/ten77/AppData/Local/Temp/verify_live_notice.py (GET-only browser; intercepted responses local). Local previous checks: 3 controlled Chrome cases and 27 existing selector tests passed; no broader suite or local full chain repeated.

Remaining reliability remedy supported by evidence: public cron runs every 30 minutes but renewal begins only within 10 minutes of expiry, while an observed prior build took roughly 7 minutes plus queue/deployment. This can miss a renewal window even without dropped triggers. Establish renewal lead time covering cadence plus measured build/queue/deploy margin and test unchanged-input expiry boundaries without extending validUntil. Public fallback also publishes admin_schedule but not admin_availability; independently assess adding the existing availability publisher after fresh inputs. Missing scheduled trigger delivery still has no proven root cause: escalate the existing exact-run/API evidence bundle to GitHub support and define an independent observer/recovery/escalation boundary. Neither a new scheduler nor any workflow change is implemented here. Brian must not remain the routine observer.

Denied public block-edge/selector rewrite remains paused; no retry, roster relaxation, production bridge or pending owner timing/model change included. Original unrelated changes and lab remain preserved. Account/owner action is needed only for the separate exact public-rewrite approval and any GitHub support escalation, not this warning verification. Next action: follow public push run 36994082057 to terminal state and verify resulting publication/deployment; observe genuine scheduled runs separately before claiming automatic recovery.
