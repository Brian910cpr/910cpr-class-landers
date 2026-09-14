# Codex reply: Issue 226, connected class record details and intake

Timestamp: 2026-09-14T18:01:38Z
Assignment: https://github.com/Brian910cpr/910cpr-class-landers/issues/226
Work-item state: MERGED and DEPLOYED
Evidence level: CONNECTED. Public assets and production function deployment are verified. The authenticated browser workflow is not yet PROVEN, MONITORED or HEALTHY.
Branch: `codex/class-record-details-intake`
Application commit on feature branch: `c80e2d7b84115ad224ab095b1f027f3fb86e98d0`
Merged application commit: `c54e39a1d5bc209d03721f3cd25535b9b379ea53`
Pull request: https://github.com/Brian910cpr/910cpr-class-landers/pull/237

## Implemented

- The All Classes roster now shows the issued credential/eCard number inline beside each participant.
- Participant names link to a protected canonical person record page with identity, organization, class history and credential history.
- The class detail lists attached files with separate View and Download controls. Private Storage objects are exposed only through short-lived signed URLs after owner authorization and class/document ownership checks.
- A class-scoped intake area accepts dropped files, selected files and pasted text. It always retains the original input before parsing.
- CSV, TSV, text and XLSX rows are parsed into review proposals. Exact normalized email/name matches are labeled matched; multiple candidates are labeled ambiguous; no candidate is labeled unmatched. Parsing never silently overwrites a participant or issued credential.
- PDF and image originals are retained and labeled as needing extraction. OCR was intentionally not represented as completed.
- Parsed proposals are recorded in the existing private class audit trail. The implementation reuses `class_sessions`, `registrations`, `customers`, `participant_credentials`, `class_session_documents` and the existing private `class-session-docs` bucket; it creates no duplicate registry.

## Deployment and verification

Supabase Edge Function `canonical-session-workspace` is active at version 6 with deployment hash `5cf8c0ab11c2773eeeff2eb54ece63116b637d0a0fa292c52feb070fde94b297`. It retains the existing owner-session authorization path. An unauthenticated production class-detail request returned HTTP 401, as expected.

The deployed public copies of these files matched the merged local files byte for byte on 2026-09-14:

- `docs/admin/all-classes.html`
- `docs/admin/all-classes.js`
- `docs/admin/person-record.html`
- `docs/admin/person-record.js`
- `docs/admin/all-classes-record.css`

The selected production class was read through the canonical database during development and had one participant credential and two attached document records. The credential value and participant contact details are intentionally omitted from this repository receipt.

Local checks passed:

- Four Deno behavioral tests for CSV matching, ambiguous matching, the repository XLSX sample and identifier validation.
- Deno type check for the intake/parser module.
- JavaScript syntax checks for both admin browser modules.
- Existing All Classes Python unit suite.
- `git diff --check`.

The full edge-function Deno check could not finish downloading an existing JSR dependency in this execution environment. The changed parser module checked independently, and Supabase accepted and activated the complete function bundle.

No schema or RLS changes were made. Existing Supabase security-advisor findings therefore remain outside this work item and are not represented as fixed.

## Proof contract and remaining verification

Expected owner workflow: open All Classes, choose a class, see participant credential numbers and attached files, open a participant record, then optionally attach and parse a dropped file or pasted block. Intake proposals must visibly distinguish matched, ambiguous and unmatched rows, and the original attachment must remain recoverable.

Visible failure behavior: class/person reads, signed-file access and intake upload/parse failures surface as errors in the admin UI. An unsupported extraction format remains attached and reports that extraction is needed. The owner is still the routine observer; no independent monitoring or health assertion was added.

Remaining proof: run the protected workflow in an authenticated production browser, including one controlled test upload/paste and cleanup or retention decision. Authenticated browser control was unavailable in this session because the Work browser action was denied by the current usage limit. That restriction was not bypassed. This is the only reason the complete workflow remains CONNECTED rather than PROVEN.

Recovery: the application change is isolated in merged commit `c54e39a1d5bc209d03721f3cd25535b9b379ea53`, and the Edge Function can be returned to its prior deployed version if the authenticated verification exposes a regression. Originals are retained in private Storage and parsed proposals are audit events, so parsing does not destructively replace canonical participant data.
