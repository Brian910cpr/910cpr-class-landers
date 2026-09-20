# Codex Reply: Issue 268

- **Assignment:** Issue #268, mandatory 20-minute safety hold for every ChatGPT email
- **Timestamp:** 2026-09-20 13:07 EDT (UTC-04:00)
- **Branch:** `main`
- **Substantive commit:** `4447c6054aa73810dcc5becd30e20228a5836e18`
- **Work-item state:** `MERGED`
- **Persistent-system evidence state:** `BUILT`

## Finding

The connected Gmail action used in the incident supports immediate send and draft creation, but does not expose Gmail's native Schedule Send command. The safe cross-session design is therefore Gmail draft first plus a one-time 20-minute delayed-send task. Immediate send must never be used as a fallback.

## Work performed

- Created durable owner instruction issue #268.
- Added `Mandatory Outbound Email Safety Hold` to root `AGENTS.md`.
- Defined proposal contents, exact 20-minute hold, cancellation conditions, fresh hold after edits, fail-closed draft behavior, and post-send verification.
- Explicitly prohibited immediate-send fallback and post-send disclosure of avoidable concerns.

## Files changed

- `AGENTS.md`
- `Codex_Reply_Issue268.md` (this receipt)

## Validation

- Re-fetched `AGENTS.md` from GitHub `main`.
- Confirmed the new mandatory section is present.
- Confirmed it references issue #268.

## Deployment status

Repository policy is committed directly to `main`. No application deployment was required.

## Proof status and limitations

`BUILT`: The durable rule exists in the repository.

Not yet `PROVEN`: No real email has yet completed proposal → Gmail draft → 20-minute hold → verified transmission under this rule.

Not yet `MONITORED` or `HEALTHY`: There is no durable observer proving every future agent/email path obeys the rule.

## Failure/staleness condition

Any immediate outbound email, any delayed send without the complete proposal being presented first, any send after an objection, or any fallback from failed scheduling to immediate send violates the gate.

## Recommended next action

On the next legitimate low-risk email request, execute one controlled end-to-end cycle with a Gmail draft and a one-time 20-minute send task. Separately prove that an objection/edit during the window cancels the original deadline and requires a fresh full hold.

## User/account action required

None now. Brian may edit or cancel a pending draft during its 20-minute review window.
