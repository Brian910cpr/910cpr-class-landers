# Delta Watch acknowledgement — Issue #371 follow-up UI R1

Reviewed at 2026-10-13T20:58:30Z.

Reviewed `Codex_Reply_Issue371_FollowUpUI_20261013T2015Z_R1.md`, substantive commit `8fd58e47222ec63226f201fa9076cff43112c33a`, and the receipt commit `bcda2ed2b880e2183739dd48372e1771d995eebe`.

Accepted as BUILT-only progress:

- The default-off Studio now uses the existing task coordinator for explicit promised follow-up capture tied to a confirmed interaction.
- Navigation and interruption/resume are blocked by unsaved, uncertain, or conflicted task state; uncertain writes reuse the same request, conflicts retain exportable evidence, lock clears task data, and paginated task reads fail closed.
- Resume reloads fresh task state and preserves `follow_up_due` for outstanding obligations.
- Reported validation passed 61/61 CRM/auth Node tests and 11/11 Chromium tests, plus syntax and diff checks.

Safety boundary remains authoritative: task lookup and the two-interaction resume RPC are separate transactions, so concurrent task creation or disposition can race the UI snapshot. Keep the gate disabled and PR #372 draft, unmerged, and undeployed.

Next same-stream work: implement shared-lock transactional task/resume consistency with concurrent-create and concurrent-disposition proof, then task status controls and saved-only NEXT. Genuine owner-session runtime/database recovery and usable backup/restore proof remain required before a separate rollout GO.

No Brian action is needed for safe continuation.
