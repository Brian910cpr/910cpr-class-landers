# Issue 141: scheduling lifecycle and postclass roster design gate

Date: 2026-09-11 (America/New_York)

Status: design approved for review; no schema, outbound automation, document upload, or production write is enabled by this document.

## Existing canonical anchors

This proposal extends the existing LanderWare model rather than creating Maxim-only records:

- `landerware_people`, `landerware_organizations`, and `landerware_person_organizations` own identity and employer relationships.
- `landerware_certification_requirements` owns the participant/course obligation and expiration evidence.
- `landerware_sessions`, `landerware_rosters`, `landerware_registrations`, and `landerware_roster_memberships` own the selected class and participant relationship.
- `landerware_documents.related_record_ids` is the existing durable artifact relationship point.
- `landerware_activity_events` and `landerware_messages` own lifecycle provenance and communication audit.
- `landerware_self_service_tokens` is the closest existing reusable scheduling-token anchor, but it needs explicit purpose, lifecycle, and rotation semantics before reuse.

The historical promotion in PR #147 targets older base tables (`class_sessions`, `customers`, and `registrations`). Their authoritative DDL is not checked in. A later migration must first introspect and document the production relationship between those tables and the `landerware_*` model. It must not guess or duplicate imported history.

## Proposed state model

Attendance and completion are independent positive-fact domains. SQL `NULL` is not used as shorthand for absent.

| Domain | Values | Rule |
|---|---|---|
| requirement lifecycle | `scheduling_required`, `scheduling_requested`, `scheduled`, `completed`, `cancelled`, `not_interested` | `required_by` is mandatory before entering `scheduling_requested`. |
| scheduling lifecycle | `not_requested`, `requested`, `selected`, `change_requested`, `rescheduled`, `closed` | A selection changes the registration/session relationship, not participant identity. |
| attendance status | `unknown`, `present`, `absent`, `excused`, `other_verified` | Only affirmative evidence may move `unknown` to another value. |
| completion status | `unknown`, `incomplete`, `completed` | Missing scores, paperwork, or cards never changes attendance. |
| closeout status | `not_due`, `instructor_closeout_required`, `verified`, `exception` | A passed session with unknown attendance creates internal work only. |
| employer visibility | `participant_only`, `status_visible`, `joint_followup` | Visibility is based on deadline risk/client policy, never punishment wording. |

Required durable fields for the requirement/scheduling aggregate:

- `requirement_id`, `person_id`, `organization_id`, `eligible_course_id`
- `expiration_date`, `required_by`, and `required_by_source`
- `current_registration_id`, `current_session_id`
- `scheduling_status`, `attendance_status`, `completion_status`, `closeout_status`
- `missed_count` (internal only), `last_participant_communication_at`, `employer_visibility`
- affirmative attendance assertion: `asserted_status`, `asserted_by`, `asserted_at`, `source_type`, `source_record_id` or `document_id`
- creation/change timestamps and immutable activity-event references

`required_by_source` must distinguish an expiration-derived deadline from an explicit sender/client deadline. If neither is available, create an internal exception and do not send a scheduling request.

## Allowed transitions and gates

1. `scheduling_required -> scheduling_requested` requires a participant, eligible course/calendar, and `required_by`.
2. `scheduling_requested -> scheduled` requires a successful canonical registration/session selection. The event and confirmation message share an idempotency key.
3. `scheduled -> completed` requires positive completion evidence; completion is never inferred from elapsed time.
4. After a passed session, `attendance_status=unknown` produces `instructor_closeout_required`. It produces no participant or employer message.
5. `attendance_status=absent` requires an authorized human assertion or a positively matched authoritative attendance artifact with provenance.
6. Verified absence may transition the requirement to `rescheduling_requested`; the existing person/requirement is retained and a replacement registration supersedes the prior registration.
7. A new selection transitions to `rescheduled` and immediately creates a neutral confirmation containing the same self-service link.
8. Completion/cancellation/not-interested closes the token and the open scheduling lifecycle as policy permits.

Outbound missed-class automation must reject a recipient unless all of these are true: verified `absent`, provenance complete, requirement still open, token valid, eligible calendar resolvable, message idempotency key unused, and no human-review stop. Employer visibility additionally requires an explicit deadline/client-policy decision.

Bulk anomaly stop: default to human review when either (a) at least 5 absences are proposed for one session and they exceed 40% of roster membership, or (b) the source assertion applies the same absence fact to an entire roster. These are proposed conservative defaults and require owner approval before implementation. A stopped batch writes an internal audit event; it sends nothing.

## Token behavior

- Generate at least 256 bits of random material; store only SHA-256, never the bearer value.
- Bind the token to `person_id + requirement_id + organization_id + eligible_course_id` and purpose `schedule_or_reschedule`.
- Do not bind it permanently to one session. The current selection is read from the canonical requirement/registration relationship.
- Reuse the same link while the requirement is open and the token is unexpired/unrevoked. A selection does not consume it.
- Rotate on suspected disclosure, identity/employer change, course-eligibility change, or policy-driven expiration. Revocation is immediate and audited.
- Require server-side allowlisted course/session resolution and deadline checks on every open and selection. Never trust participant IDs, dates, course IDs, or organization IDs supplied by the browser.
- Record open, selection, change, confirmation, rotation, revocation, and failure as activity events without storing the bearer token.

## Communication behavior

Participant templates remain neutral at every attempt: “Sorry we missed you,” “No worries,” and a direct invitation to choose another time. They never expose attempt count or say “again,” “failed to attend,” or that an employer is being notified.

Employer status messaging is separate or CC-based according to client policy: “We’re still working to get [participant] scheduled before the required-by date.” It reports status and next action, not blame. Every rendered message stores template version, recipients, requirement/registration/session references, idempotency key, delivery state, and provider reference.

## Compact KJ-1958-derived roster field map

This is labeled **LanderWare course-specific postclass roster — derived from KJ-1958 field requirements**. It must not claim to be an unmodified AHA form.

### One page for up to 10 participants

| Page zone | Fields |
|---|---|
| compact identity header | AHA logo when licensed/available; 910CPR logo; optional host logo with clean text fallback; exact course/path; session ID; page 1 of 1 |
| TC / TS / host strip | Allied100 LLC; TC WI20877; 910CPR LLC training site; training-site address; actual course/host location |
| course facts | start date/time; end date/time; total instruction hours; student-manikin ratio; number of cards issued; card issue date |
| instructor facts | lead instructor name/ID/card expiration; compact assisting-instructor name/ID/card-expiration rows when applicable |
| participant grid (10 rows) | name/email; mailing address; telephone; Complete/Incomplete; remediation/date completed |
| attestation footer | lead-instructor attestation text; signature; signature date; document packet/artifact references |

Known values are prefilled from canonical records. Unknown values display blank or `UNKNOWN` for human closeout. Missing downstream data never produces an absence status.

### More than 10 participants

- Generate one responsibility page per instructor for at most 10 assigned participants.
- Repeat session identity, exact course/path, TC/TS/host strip, page number, and responsible instructor identity on every page.
- Page 1 retains the full course-facts and lead-attestation block. Continuation pages retain a compact responsibility attestation/signature block for their assigned instructor.
- Never automatically assign participants to an assisting instructor. Missing coverage/assignment is a blocking packet exception.
- The packet manifest links cover/roster pages, signed skills checklists, exam answer sheets, card reports, and other artifacts to the canonical session and, where applicable, registration/person/requirement IDs.
- The host logo is resolved from an approved organization/location image reference. Missing artwork falls back to host name and does not block generation.

## Admin/Maxim surfaces

- Maxim sender: required-by field and exception banner before “Send scheduling request”; canonical eligible-course calendar is reused.
- Participant link: identity/context summary, deadline, eligible dates/times, current selection, and one select/change action; no re-registration form.
- Session closeout: roster with separate attendance and completion controls, provenance capture, closeout exceptions, packet generation, and artifact list.
- Historical session inspector: session facts, participants, documents, requirements/card state, and audit timeline. This must be implemented through the issue #129 read-only browser/auth boundary when that paused dependency is reactivated, not as a parallel public UI.
- Participant inspector: past classes and open requirement/scheduling lifecycle.

## Implementation gates and current blockers

1. PR #147 must be reviewed/merged or an explicit integration base selected; it is open and its Cloudflare Pages check currently fails.
2. Issue #129 explicitly pauses record-browser implementation. Historical browser UI work is blocked until that issue returns to the queue.
3. Production DDL for the older `class_sessions` / `customers` / `registrations` silos must be introspected and committed/documented before a bridging migration.
4. Owner approval is required for the proposed bulk anomaly thresholds and deadline derivation policy.
5. Official/logo assets and use rights must be identified before packet rendering.
6. No outbound automation may be enabled until tests prove unknown attendance cannot send messages, each recipient has affirmative provenance, idempotent replay sends zero duplicates, and anomaly stop behavior is fail-closed.

## Recommended next implementation slice

After PR #147 integration and schema introspection, add only the attendance-assertion and scheduling-request state migration plus database tests. Do not enable outbound sends. Prove: explicit absence assertion succeeds with provenance; missing evidence stays unknown; passed time/missing score cannot create absence; required-by is mandatory; token replay changes a selection without duplicating the person or requirement; and bulk anomaly candidates enter review without messages.
