# Codex handoff acknowledged: Community event cutoff

Reviewed: 2026-10-04T11:27:00Z
Source handoff: `Codex_Reply_CommunityEventCutoff20261004.md`
PR: #345
Merge commit: `e7ff747175dd817885bad210f979a4a04cde27a0`

Review result: ACCEPTED for pre-cutoff publication.

Evidence reviewed:
- PR #345 is merged.
- Source integrity, Cloudflare Pages preflight, GitHub Pages build/deployment all completed successfully.
- Diff is limited to the two event pages, one versioned cutoff asset, the focused Playwright verification script, and the handoff receipt.
- The cutoff is explicit: 2026-10-04 11:30 America/New_York (15:30Z).
- Submission, click, keyboard, requestSubmit, asynchronous response, and re-enable paths are guarded after cutoff.
- The focused verification reports 12 passing before/at/after cases across both pages and mobile/desktop widths, with no real registrations or payments.
- Live `/earl/` and `/jackson/` currently expose the new October 4 build and remain open before cutoff as intended.

Remaining verification:
- Confirm both live pages show the red event-passed state and disabled registration after 15:30Z.
- No additional repository change or Codex round is requested unless that post-cutoff verification fails.
- No scheduling V2, backend session, payment, or availability changes were included.

## Superseding owner directive — 09:00 cutoff

Directive received: 2026-10-04T12:26:34Z
Repair PR: #347
Repair merge commit: `2cdd0ae38db713aa9ec6bdb156b8c9d58d1ce5b3`

The 11:30 America/New_York cutoff above was superseded by Brian's explicit instruction to close both `/earl/` and `/jackson/` at 09:00 America/New_York (13:00Z) on October 4.

Repair evidence:
- Client cutoff and the focused test clock now target 13:00Z.
- Both pages use cache-busted release `community-cutoff-20261004-r2` / `community-event-cutoff-20261004-r2`.
- PR #347 Source integrity and Cloudflare Pages preflight completed successfully.
- GitHub Pages deployment run #4349 (run 37202221286) completed successfully.
- Both live pages exposed the r2 build and remained open before 13:00Z as intended.

Remaining verification:
- Confirm both live pages show the red event-passed state and disabled registration at or after 13:00Z.
