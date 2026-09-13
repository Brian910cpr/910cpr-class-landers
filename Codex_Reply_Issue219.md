# Issue 219: Instructor document controls
Timestamp: 2026-09-13T18:00:00Z
Branch: codex/instructor-document-controls
Substantive commit: 49d92365595652b1d411ccc5eeb3dedfb857f5f8
Work-item state: IN_PROGRESS
Evidence state: CONNECTED. Backend deployed and database transaction proven with rollback-only fixtures; authenticated production browser proof remains pending.

## Findings and changes
The instructor workbench listed file names without view or removal actions. Added View with an in-page PDF/image preview and a new-tab fallback, Remove with the exact file/class confirmation, and refreshed counts/health after removal. Cancel sends no mutation.
The backend looks up the document by BOTH session and document UUID, creates private five-minute viewing links, and calls an atomic database removal/audit transaction. The storage object and complete attachment metadata are retained for recovery. Repeat removal is idempotent. Documents referenced as compliance evidence return a clear conflict until replacement.
The existing workbench login is retained. It is a shared portal-session boundary, not individually attributed instructor identity or assignment enforcement. The audit records the authenticated session fingerprint without claiming a person's identity. This update does not broaden or repair that pre-existing identity model.

## Files
- docs/admin/instructor-workbench.html
- docs/assets/instructor-workbench.js
- supabase/functions/instructor-workbench/index.ts
- supabase/functions/instructor-workbench/documents.ts
- supabase/migrations/20260913174555_instructor_document_controls.sql
- tests/instructor_documents.test.cjs
- tests/instructor_documents_ui.test.cjs
- tests/instructor_documents_rollback.sql
- .github/workflows/verify-instructor-documents.yml

## Validation
- 16 behavior tests passed: authentication denial, class/document scoping, private signed links, missing file, confirmation, idempotence, compliance conflict, CORS, filename escaping, preview, cancellation, removal refresh and error states.
- Deno type check and frontend syntax check passed; git diff --check passed.
- Database rollback suite passed against the target project: client-role execution denied, invalid session denied, wrong class denied, evidence protected, atomic audit/removal succeeded, repeat request produced one audit, recovery snapshot restored the attachment. All fixtures rolled back.
- instructor-workbench Edge Function version 4 deployed; exported index.ts and documents.ts match committed source.
- Production OPTIONS returns 204 and allows DELETE; anonymous GET and DELETE return 401 with no-store.
- Browser Class History is signed out. Authenticated production viewing/removal has not been claimed as proven. The cloud browser blocks the local preview URL, so local UI behavior was checked with a DOM harness.

## Delivery and recovery
The database migration and API are deployed. The frontend awaits PR merge/deployment and live asset verification.
Direct git push had no credential helper; used the authenticated GitHub connector with a tree verified byte-for-byte equal to the locally tested commit tree.
The existing workflow will run focused checks when these files change. This is not an ongoing synthetic production monitor, so no MONITORED/HEALTHY claim is made.
Recovery: restore class_session_documents from class_session_audit.details.removed_attachment; original private storage objects remain. Revert the frontend/API commit to roll back controls without changing prior removal evidence.
Next action: merge the focused PR, verify production HTML/JS, and record deployment evidence on #219. Obtain a normal signed-in workbench session for full production click-through if available; do not create test credentials or bypass authentication.
User/account action: none needed to ship; a signed-in browser is required only for remaining production UI proof.
