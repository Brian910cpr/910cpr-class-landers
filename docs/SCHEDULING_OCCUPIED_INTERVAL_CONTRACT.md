# Class occupancy and flexible turnaround

Owner approval: 2026-10-15, message `Sentinel_7a99f4491ab48191871b6c3b4c006224`.

Use the class's canonical unavailable interval for scheduling decisions. Any genuinely required extra reservation must already be in that interval before availability is shown. A new class may touch the recorded occupied end. Do not append an additional cleanup veto when validating or explaining a displayed offer.

For the October 17 example, BLS session14377157 has a recorded occupied interval10:00–12:00. That interval alone does not make noon unavailable. If an authoritative explicit reservation extends it to12:30, noon is unavailable and a12:30 adjacent start can be considered. Room flexibility does not authorize simultaneous teaching by the same instructor. Preserve actual teaching, travel, ADR, holds and other explicit occupied space.

The active layered runtime already applies this model:

- Existing classes retain supplied canonical consumption bounds.
- New candidates include their configured total reservation before conflict checking and publication. Current full candidates generally reserve120 instruction+30 additional minutes; skills reserve45+15. These are existing candidate reservations, not a second veto appended to a prior class. Evidenced course exceptions remain intact.
- The engine uses half-open collision checks. Touching boundaries do not conflict. Real shared-room or instructor overlap still conflicts.
- The public feed distinguishes teaching duration from total consumption and publishes the reservation's `occupiedUntil`. That exact interval is the interval to revalidate, including across midnight. Do not reconstruct it by adding cleanup to a teaching end a second time.
- A new explicit commitment can invalidate an old displayed offer. Recheck current facts before a booking; do not promise that a cached selection reserves capacity.

The incident's public Register link goes directly to Enrollware. This repository does not control that service's checkout validator. Local tests prove the active engine's collision predicate agrees with its published occupied intervals; they do not prove Enrollware checkout or an atomic booking transaction. The verified-certifi exact-page request returnedHTTP403. Do not claim external acceptance or bypass the access restriction.

For customer explanations, identify the actual unavailable interval and its authoritative source. Do not tell someone that an advertised adjacent time is impossible solely because an additional cleanup period was inferred after it was offered. If the source interval and actual operational requirement disagree, reconcile the explicit occupied interval and future offers consistently; preserve existing bookings.

PR408 carries the regression proof. No runtime buffer deletion or broader scheduling cutover is required for the already-compliant touching-boundary behavior. Publishing the provenance metadata can follow normal targeted release review; live external checkout consistency and CyberPC rendered-browser verification remain separate proof gates.
