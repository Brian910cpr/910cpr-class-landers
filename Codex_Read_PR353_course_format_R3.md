# PR353 course-format consolidation repair

Production V2 policy now explicitly uses course-level full-class consolidation. Existing catalog course IDs distinguish program/format; no competing catalog or guessed production IDs were added. Booked or unknown-count full classes suppress additional same-course full choices, not unrelated formats in the same family. All physical collision, qualification, coverage and unknown-count safeguards remain.

Engine retains explicit legacy family scope for existing fixtures/consumers, rejects invalid scopes and emits course-specific rejection reasons in production mode.

Validation: 61 targeted publication, adapter, cache and customer-render pipeline tests passed. Regression covers a distinct same-family full format with both a paid booking and unknown count, preserving source counts and ensuring every admitted option lies outside occupancy. Syntax parsed. Fresh real-source probe pending.

Public deployment remains stopped under the existing acceptance hold. This is a local persisted and pushed source repair, not a public activation. Remaining instructor-coverage acceptance work remains open.
