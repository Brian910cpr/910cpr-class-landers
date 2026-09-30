# Codex read acknowledgment — BLS Initial launch

Reviewed the handoff `Codex_Reply_BlsInitialLaunch_20260930.md` and the narrowly referenced launch path.

Verified:
- PR #317 merged as `ab67888dfcf481125c9bc263eb70b385c517292b`.
- Production migrations for BLS add-ons and per-student billing codes were applied.
- `public-registration` v7 is active.
- The launch exposed a backend contract mismatch with existing #297 canonical-session state: BLS Initial sessions can be routed to native registration from static schedule data even when canonical eligibility required by the order RPC is missing or not public/open.
- Do not weaken the #297 fail-closed publication guard.

Next safe work remains repository-side containment: native BLS routing should require proven canonical public/open eligibility, otherwise fall back to the existing appointment URL. Add a GET→POST behavioral regression for the exact session path before re-enabling broader native routing.

No feature-expansion follow-on was dispatched. Backend stabilization remains higher priority.
