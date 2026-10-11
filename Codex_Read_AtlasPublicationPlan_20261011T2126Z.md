# Codex read — Atlas publication plan

- Reviewed at: 2026-10-11T21:26:00Z
- Reviewed reply: `Codex_Reply_AtlasPublicationPlan_20261011.md`
- Reviewed commit: `8c156baa68fbbdd4655b320adb2fe65bf14e19ab`
- Disposition: acknowledged; plan persisted, implementation deferred.

The phased rule is recorded consistently: publish verified paid-seat classes first; later publish selected offers strictly more than 28 days out; remove unpaid offers at the 28-day boundary; retain classes with paid seats; preserve Anchor/Barnacle reconciliation and prevent simultaneous instructor conflicts. The document correctly leaves payment-pending, volume/times, instructors, cadence, duplicate prevention, Atlas mapping, and retry behavior unresolved rather than guessing.

No automation, Atlas publication, merge, or deployment occurred. Backend stabilization remains higher priority. Resume with one verified paid-seat class after authenticated Atlas access is available, confirm current fields and existing listings, persist the source-class-to-Atlas-listing mapping, and verify the public listing before any batch work.