# Community event page cutoff

Timestamp: October 4, 2026 UTC. Branch: fix/community-event-cutoff-20261004.
Work item: owner-requested /earl and /jackson replacement at 11:30 AM America/New_York today (15:30 UTC).
State: locally VERIFIED; publication pending at receipt creation. Commit: git log on this branch.

Both canonical pages preserve their current layout and existing organization logos. Existing owner edits were already identical to current main's lowercase page contents; originals remain untouched. A versioned asset applies the red event-passed banner at the cutoff, disables registration fields/buttons and course-registration switches, guards submission/response handlers, and rechecks open/resumed tabs. All four organization logo destinations remain live. Verified Facebook links are added in the post-event follow-up section. No future free Mobile Mermaid event was verified; the fallback makes no claim that none exist. Footer updated timestamp and owner copy-details control included.

Validation: node syntax check passed; 12 intercepted browser cases passed across two pages, 390/1280 widths, before/at/after cutoff. Before-cutoff valid submission reaches a mocked API; no post-cutoff POST occurs via click/keyboard/requestSubmit/dispatched submit, and attempted re-enabling is closed again. Already-open transition and organization links tested. No real registrations/payments created. A pre-existing Jackson quoted success-message syntax defect was repaired as part of preserving functional registration.

Timing mechanism: client clock compares an explicit EDT timestamp, not a new server task. Exact timeout plus page-load/focus/pageshow/visibility checks and direct handler guards. Browser clock correctness remains a limitation; old already-open versions cannot acquire new code without reload. Static asset URL is versioned. No backend/session changes or V2 deployment.

Files: docs/earl/index.html, docs/jackson/index.html, docs/assets/community-event-cutoff.js, scripts/check_community_event_cutoff.py, this receipt. Windows case-colliding uppercase alias files are left unstaged; original dirty changes/pycs remain untouched. No broad generators run.

GitHub Pages hosting confirmed main:/docs, www.910cpr.com. Public completion requires merge, successful Pages build, and live HTML/asset/browser verification; this receipt does not yet claim that. No Cloudflare deployment requested. Current V2 work preserved at 2dc11c641 with latest handoff receipt; no scheduling data modified.
