# LanderWare Design Ethos

LanderWare exists to become the durable operating system for 910CPR, not a permanent wrapper around Enrollware.

Enrollware is an experienced incumbent, migration source, and reference architecture. Its accumulated decisions deserve study because they encode years of training-business experience. They are not automatically correct for 910CPR, and they are not a reason to preserve Enrollware as a dependency.

## Core Doctrine

**Learn it -> ingest it -> reproduce the required capability natively -> improve where justified -> cut the dependency loose.**

For every feature, workflow, data object, or operational rule that Enrollware currently provides or influences, ask:

> **If Enrollware were cancelled tomorrow, what would stop working?**

Anything 910CPR actually relies on must end in one of three states:

1. **Native LanderWare replacement**
2. **Replacement by a deliberately chosen cheaper/better external service**
3. **Explicitly unnecessary and retired**

There is no fourth long-term state called "leave it in Enrollware because it already works there."

## Experienced-Incumbent Check

Before inventing a new training-business workflow, data model, or user journey, investigate how mature systems solve the same problem, beginning with Enrollware where applicable.

Ask:

- What objects does the incumbent keep separate?
- What lifecycle states does it preserve?
- What audit/provenance does it retain?
- What edge cases caused the feature to evolve this way?
- What is attached to a Course, Class/Session, Registration, Person, Organization, Instructor, Location, Product, Inventory item, Document, Payment, or Credential relationship rather than copied everywhere?
- What happens before class, during class, after class, and after certification?
- What customer, instructor, compliance, billing, or reporting problem is the design quietly solving?

Do not copy a design merely because the incumbent uses it. But do not get creative without first asking:

> **Why did the experienced big dog not do it this way?**

If LanderWare chooses a materially different design, the reason should be identifiable: a 910CPR-specific operating advantage, simpler workflow, better data integrity, lower cost, better automation, better customer experience, or removal of a known incumbent limitation.

## Learn the Landscape Before Replacing It

Feature discovery is migration work.

Maintain an **Enrollware Exit Gap List** covering the capabilities 910CPR actually uses or may depend on, including hidden/administrative behavior. For each capability, capture:

- what the feature does
- where it lives in Enrollware
- which data objects it uses
- what triggers it
- what it changes
- downstream effects
- reports/audit evidence it produces
- integrations involved
- whether 910CPR currently uses it
- LanderWare replacement state
- migration/backfill needs
- cutover verification

Examples include registration, self-rescheduling, student portal, file-upload questions, waitlists, appointment scheduling, keycode/product inventory, instructors and qualifications, locations, organizations/clients, campaigns/reminders, check-in, scores, rosters, certification issuance, documents, billing/payment references, privacy/consent, audit trails, SEO/rich results, integrations/webhooks, and reporting.

The goal is not feature-count parity. The goal is **operational independence without surprise regressions**.

## Canonical Object Discipline

Prefer durable reusable objects and explicit relationships over copied labels and page-specific state.

The core landscape includes, at minimum:

- Person
- Organization
- Course
- Session/Class occurrence
- Registration
- Instructor qualification/assignment
- Location
- Add-On
- eProduct / inventory / keycode
- Document / evidence
- Payment / billing reference
- Credential / certification
- Requirement / completion state
- Audit / provenance event

When a new field or behavior is proposed, first decide which object or relationship actually owns it.

Do not solve a Person problem by adding another copied field to Session. Do not solve an inventory problem with a boolean on Registration. Do not treat Organization as free-text on a person when the business relationship itself has history and billing consequences.

## Lifecycle Over Snapshots

LanderWare should model the real operational lifecycle, not only the final record.

Examples:

- expected participant != checked-in participant
- checked in != attended
- attended != completed
- completed != certified
- registered != paid
- paid != fulfilled
- name on pre-class roster != official final roster
- product assigned != product consumed
- session scheduled != session completed

Transitions should preserve history and provenance rather than overwrite the previous truth.

## One Truth, Many Views

Admin, instructor, student, employer/client, public registration, scheduling, finance, and reporting surfaces should project the same canonical objects rather than maintain independent versions of reality.

A UI may simplify what it displays, but it must not create a competing source of truth.

## Migration Without Entrapment

During the transition, Enrollware data may remain authoritative for specific legacy operations. That is a temporary migration condition, not a design destination.

Every new LanderWare feature touching an Enrollware-owned area should answer:

1. What is authoritative today?
2. What will become authoritative in LanderWare?
3. How will historical/current data be ingested or reconciled?
4. How will dual-write or transition ambiguity be prevented?
5. What proves the LanderWare replacement is safe?
6. What exact dependency can then be removed?

Avoid building new unnecessary dependencies on Enrollware APIs, IDs, URLs, or workflows merely because they are convenient during migration. Preserve external IDs for provenance and reconciliation, but keep the LanderWare domain model independently meaningful.

## Replace Behavior, Not Screens

Do not clone Enrollware page-for-page.

First understand the business capability and invariant. Then build the simplest LanderWare workflow that preserves or improves it.

Examples:

- replicate safe rescheduling semantics, not necessarily Enrollware's reschedule screen
- replicate keycode inventory/accountability, not necessarily its keycode UI
- replicate final-roster compliance and provenance, not necessarily its roster page layout
- replicate student-history continuity while improving fragmented legacy identity handling

## Intentional Improvement

LanderWare should be willing to exceed the incumbent where 910CPR has a clear advantage.

Good reasons include:

- one canonical Person across all sources
- stronger organization/client relationships
- better class/session lifecycle visibility
- less duplicate data entry
- more reliable automation
- explicit provenance
- mobile-friendly instructor operations
- simpler customer actions
- better recovery and observability
- lower recurring software cost
- fewer manual handoffs

Improvement should solve a real problem, not demonstrate architectural cleverness.

## Exit Is a Product Requirement

Enrollware removal is complete only when:

- every relied-upon capability has a replacement or explicit retirement decision
- required historical/current data is preserved
- public registration works
- schedule/availability remains correct
- payments/billing paths work
- products/keycodes/fulfillment work
- instructor operations work
- class completion, roster, and certification workflows work
- student/customer history remains accessible
- required integrations are replaced
- operational reports/audit evidence remain sufficient
- live cutover has been proven
- rollback/recovery is understood

Do not cancel first and discover hidden dependencies afterward.

## Decision Test for Every Significant Feature

Before implementation, answer:

1. **What real operating problem are we solving?**
2. **How does Enrollware or another mature training platform solve it today?**
3. **Why is that design shaped that way?**
4. **Which canonical LanderWare object owns the truth?**
5. **What lifecycle/history must survive?**
6. **Are we replacing, improving, or retiring the incumbent capability?**
7. **Does this move us closer to Enrollware independence or accidentally deepen the dependency?**
8. **How will we prove the replacement works in production?**

If those questions have not been considered, the design is not ready for implementation.

## North Star

LanderWare should feel like it was designed by people who understand the training business deeply, not by people who merely understood the current screen they were replacing.

Study the experienced systems. Preserve the hard-earned lessons. Remove their constraints. Own the data. Own the workflow. Prove the replacement. Then remove the dependency.
