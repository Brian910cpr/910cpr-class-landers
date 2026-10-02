# Issue338 stale-feed warning isolated release
Timestamp:2026-10-02 UTC
Branch:fix/stale-feed-notice-20261002
Base:6534786d3a23db0cbb47cb4bbe9c7b4c3e36ad7e
State:IN_PROGRESS release; warning BUILT and locally browser-proven. No denied scheduling change.

Problem:expired appointments fail closed correctly, but when real classes remain, the existing message setter only stores the warning; ready-state rendering never displays it. Brian sees two real Initial dates without an explanation.

Change:visible aria-live status notice above calendar, hidden/cleared on fresh success. Authoritative14-line template insertion plus identical generated notice blocks on exactly8 public boards. Deterministicrefresh helper reads the existingtemplate and canonical page config,with no feed/session/candidate generation. Browser regression covers stale/fresh/failure and realbooking-link retention. No expiry,roster,projection,coursepolicy,candidate,travel,registration orpayment change. The blocked merged-block replacement is excluded.

Checks:3 local Chrome cases passed,zeroerrors;27 existing expiry/selector JS tests passed;scoped whitespace checks passed. Arender-only fixture preview and screenshot were inspected. No fullbuild chain run locally; targetedhelper updated8expectedHTMLfiles only. Broader suites not repeated for the rendering-only change. Original dirty Earl/Jackson andcachefiles remain in originalcheckout;releaseworktree containsnone ofthem.

Release authorization:parent explicitly requested isolated push/review/merge/deploy of warning only. PR/deployment/liveverification pending at this receipt. Inspect standard public-refresh CI triggered by the authoritative template change separately from Pages. Persistentevidence isBUILT/local proof,notHEALTHY. Lastcurrentlive recovery6534786d3 remainsunexpired11:21UTC;stableautomaticcadence/rootGitHubtriggercause remainsunproved. No security/settings/workflowchain change.

Next:push this narrowbranch,draftPR,review/check/merge,waitPages,verifylivefresh/staleviews via isolatedGETbrowser interception without alteringlivefeed. Record resultingPR/commits/deployment/validation onissue338. Furtherbarnacle work remainspaused pendingpreciseownerapproval.
