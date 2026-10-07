# PR 362 anchored-day release proof
State: VERIFIED / PROVEN
Verified: 2026-10-07, America/New_York
Source branch: codex/v2-anchored-day-open-gap
Source commit: 2ebb55043a8f33cbe1f881a05aba099650a1a7c8
Merge commit: 9fd3e2c337bc423d7985bd9e01140237c45994e8
Published commit: dc90fed708bd3f6b00da12b497ecae08b8b1f36e
PR: https://github.com/Brian910cpr/910cpr-class-landers/pull/362
Production refresh 37667658159: success
GitHub Pages deployment 37668088926: success

Root cause: a separate free calendar window on a day with an instructor's existing class was treated as an unanchored open day. Final publication now excludes detached open-day choices while preserving actual classes and attached barnacles. Independent instructors and genuinely unanchored dates retain open-day options.

Changed source: scripts/layered_publication_adapter.py
Regression test: tests/test_layered_publication_adapter.py
61 targeted tests passed; all PR checks passed.

Actual public browser verification, October 20, desktop 1440 and mobile 390:
- bls.html, course 209806: only star 11:45 AM, existing session 14655539.
- heartsaver.html, course 344085: only 10:00 AM.
- heartsaver.html, course 209809: only 9:15 AM.
- All three have real Enrollware registration URLs; detached evening choices removed.
- No JavaScript errors or horizontal overflow in six browser checks.
Proof JSON: C:\Users\ten77\Documents\Codex\2026-10-06\209811\outputs\Anchored_Day_Calendar_Verification.json

Bookings and unknown occupancy preserved. No secrets or security policy changes. Unrelated docs/Earl/index.html and docs/Jackson/index.html remain untouched and uncommitted. No owner action required for this release. This is end-to-end release proof, not a claim of continuously healthy monitoring.
