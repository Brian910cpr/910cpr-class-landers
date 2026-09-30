# Dark-mode registration-page repair

- **Timestamp:** 2026-09-30, America/New_York
- **Branch:** `codex/bls-registration-preview-20260930`
- **Implementation commit:** `302de345c0e7ea4b099e97e55cf83b0ff4475da1`
- **State:** VERIFIED locally; pending push, pull request, merge, and production deployment.

## Finding

The shared dark-theme stylesheet applies dark input fills and light heading/label text with `!important`. The standalone registration page kept a white form panel and light student card, so labels became nearly invisible against the panel while the fields appeared blank/dark.

## Work performed

Added a narrowly scoped dark-mode layer in `docs/register/index.html`. It gives the registration shell and student card dark surfaces, restores readable form text, keeps editable inputs white with dark typed text, and preserves a visible focus outline and secondary action.

## Validation

- `git diff --check` passed.
- Read-only live API check for BLS session `14501248` returned the real October 2 BLS class, location, and $75 price.
- The live registration screen was opened without submitting the form or creating a hold.

## Known unrelated worktree changes

`docs/Earl/index.html` and `docs/Jackson/index.html` were already modified by a Windows case-collision condition. They were not staged or changed by this work.

## Deployment and next action

No deployment has occurred. Push this branch, open and merge a focused PR, then verify the real registration route in dark mode. This changes presentation only; it does not change holds, Stripe Checkout, registration data, or Enrollware routing.

- **Persistent-system evidence:** `BUILT` for this visual repair. The registration checkout itself remains unproven for production migration.
- **User/account action required:** none.
