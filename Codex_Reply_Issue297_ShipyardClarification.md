# Codex Reply: Issue 297 Shipyard clarification

Timestamp: 2026-09-27T06:11:03.984289Z (02:11 EDT).
Branch: `codex/issue-297-shipyard-clarification`; base commit `e8627d810d548e761b0992e3908655e3705e8740`.
State: VERIFIED existing production decision; documentation-only owner clarification. No application deployment required.

Brian clarified: “TBD will be 4018 Shidyard.” In the existing #297 context this confirms **4018 Shipyard Blvd, Wilmington, NC** for the former TBD item, external class 11341058. It does not reverse Brian's separate confirmation that this item is a renewal deadline/placeholder.

Read-only production SQL at the timestamp above verified resolved decision `7d41cbb5-8e3b-47a3-a0de-653c07a2864f`: `approved_location_key=910cpr-office-shipyard`, canonical location `910CPR Office - Shipyard Blvd`, source external location `247652`, and `classification=renewal_deadline`. No canonical instructional class was fabricated. The current production decision already matches this clarification; no database or booking mutation was needed.

Changed file: this new immutable receipt only. All prior receipts remain unchanged. Verification: existing issue history, previous R4 receipt, and current canonical decision agree. No source/build/tests were changed, so no generator or deployment was run. The SQL inspection does not renew registration freshness.

The authorized location question is resolved. Existing unattended-roster-source and actual scheduled-refresh proof limits remain as documented in `Codex_Reply_Issue297_CanonicalReconciliation_R4.md`; the scheduled-event watch continues. Stage 6 stays gated. No new owner action is required for this location clarification. Record this confirmation on existing #297 and retain the existing decision.
