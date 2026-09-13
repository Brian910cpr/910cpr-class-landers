# Issue 219: Reconcile unified owner authentication
Timestamp: 2026-09-13T18:01:35.436281+00:00
Branch: codex/instructor-document-controls
State: IN_PROGRESS; frontend PR awaiting merge.
Evidence: CONNECTED. API version 5 deployed; 18 behavior tests and rollback database suite passed.

PR 221 (76ebb52a) landed while document controls were being developed and moved this workbench to the unified owner key. The first document API deployment was based on the prior exported version. Version 5 now preserves the new shared owner-auth implementation and its denial of corporate sessions. The reconciled frontend retains the unified login form and fetch wrapper, clears document previews on lock, and includes both document actions.

An additional migration updates the backend-only removal RPC to use an actor label supplied by the already authenticated server rather than an obsolete portal session. The RPC remains SECURITY INVOKER, executable only by service_role. No public/client grants were added.

Validation: 18 backend/DOM checks passed, including corporate-session denial and cleanup on owner lock. Deno check passed. Production rollback tests verify grants, exact class scope, linked evidence protection, atomic audit/removal, idempotence, and recovery. All fixtures rolled back.

Access limitation: the newly merged workbench is owner-only. These document controls are implemented on that existing surface; individual instructor sign-in and assignment-based authorization are not yet implemented. Do not give instructors the owner key or claim separate instructor access is complete. Issue 219 must remain open for the instructor access requirement and authenticated production proof.

Changes relative to the earlier receipt: reconcile the three shared workbench files, add the owner-auth migration, adapt the existing tests, and preserve PR 221's owner-auth dependency unchanged. Deployment details are on PR 222 and issue 219. The remote merge commit identifies the exact reconciled tree.

Next action: merge PR 222 after CI, verify deployed HTML/JS and rejection paths, then finish instructor identity/assignment integration through the existing authorized instructor portal when that identity source is available. No user-level action is needed to publish these controls; separate instructor access requires a real instructor authentication context.
