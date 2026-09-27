# Codex Reply: #297 delivery and approved Brunswick reconciliation

Timestamp: 2026-09-27T05:00:00Z / 01:00 EDT.
Branch: codex/issue-297-delivery-proof, based on main 08faa58dc23da6bd7c7b99650d3d69c144b3443e.
Substantive commits: 3d5f4e0f95ca961f9f90b2331dcaf47f8c78b745 and 1cd4e16bf43c2a5102db1460d2d13c5306beedde; merged in PR197 as b9297d128143b99b62d273770e0a7304a4d17b98. Related selector fix b3114af62da97823d3cb5487fedbec32b2885b12 merged in PR299.
State: MERGED / DEPLOYED; live incident path PROVEN. Remaining TBD identity and unattended source are unresolved, so the whole migration bridge is not HEALTHY.

## Source-backed result

The existing import path now promotes exact committed Enrollware classes into canonical class_sessions and current registrations, with stable external_class_id, course/location/instructor relationships, lifecycle/provenance, deduplication, source-owned cancellations/reschedules, atomic quarantine and freshness protection. There is no parallel schedule database. Missing, stale or mismatched authoritative proof is unknown/null, never zero. Public JSON contains no participant PII.

September 26 actual complete source rosters and canonical counts match 14186375=3, 14145607=0, 14184955=2. September 27 Renewal 14361098 / appointment 51485 and HeartCode 14421081 / appointment 51495 each match one current registration and exact source identities. All 18 reconciled registration identities matched the current roster's external registration/class IDs and customer identity fields. Two source registrations on the remaining TBD class are preserved as unpromoted evidence. Notices were not used to infer counts. No Enrollware booking was modified.

All 38 source classes (three September 26 and 35 future) were read from authenticated Enrollware class forms and complete rosters. They were re-read 04:25:29.547–04:26:07.011 UTC with no field or membership changes; all 20 individual registration statuses were re-read by 04:26:46 UTC, unchanged. Conservative source watermark: 04:25:29.547 UTC. Source SHA256: 22f7abab31d51343a7e6f84f936c10cf47b055f620d41ac9ced88520b7eb76cb. Ingest job: df4c3f85-cd02-4e2c-a425-2708d439a2aa. The original 34 canonical session IDs survived refresh.

## Owner-approved remaining location repair

Brian answered the existing clarification with: `Brunswick Oral & Maxillofacial Surgery; 90 Medical Cntr SW #100, Supply, NC`.

At 04:55:36.466563 UTC, the existing exact location hist_location_bfcd7cded3e37289fed07186 / e8500810-42f5-4cb8-872e-27e059ae2a06 was activated with that explicit approval reason through the existing status-audit trigger. Address/city/state and verified external location 202662 were populated; private visibility remains false. No location, booking, course or instructor was invented. The status event is f247281c-bbfc-498d-93a7-f9e684f64713.

The existing complete-roster RPC then reconciled all three classes at 04:55:46.930366 UTC, retaining the actual source observation timestamp rather than renewing it:

| External class | Canonical session | October 21 Eastern source time | Current count |
| --- | --- | --- | --- |
| 13895152 | 24f35176-69c1-4b1e-8a72-a69b4e5f9576 | 09:00–11:00 | 0 |
| 13895154 | e2658350-29b9-4e16-b5d6-3cbfb229dc14 | 11:15–12:30 | 0 |
| 13895155 | f407c43b-985c-4f84-a92f-6174590ad3ba | 13:00–15:00 | 0 |

Coverage is now 37/38 total source classes and 34/35 future classes. The explicit zero counts come from complete current empty rosters. Canonical course-consumption windows remain governed by the existing rules. The exact audited SQL, location status event, session joins and reconciliation metadata are in data/audit/issue297_brunswick_approved_reconciliation.json.

## Validation and monitoring evidence

The latest substantive CI run 36295036810 passed 52 Python tests, 17 actual TypeScript endpoint/projection tests and one isolated PostgreSQL lifecycle scenario. Exact commands, normal merge/deployment details and actual public selector proof are in Codex_Reply_Issue157_PublicDelivery_R5.md. This documentation/data follow-up adds no application-code changes.

Protected demand run 36294605571 passed repeated reads (35 known rows at that observation), OPTIONS 204 and unauthenticated 401. Owner workspace run 36295754030 passed after Brunswick reconciliation. Its broader date range returned 63 sessions, 48 available registration relationships and 18 explicitly unknown counts; those totals are broader than the 38-class proof set and are not represented as all current Enrollware coverage.

Health run 36295474368 at 04:50:48 correctly failed for the prior four gaps and did not duplicate its existing unchanged-condition alert. Health run 36295752896 at 04:56:39.866529 correctly reports 37 canonical external sessions and only 11341058 missing, posts the changed condition on existing #297, and fails instead of reporting green. Signature: 69ffe135750ed0a560626b546781d878dcfb92526ccbc4dabc84155383b1134d. The PII-free report is preserved inside data/audit/issue157_public_delivery_proof.json.

Observer configuration runs twice hourly and detects missing canonical sessions, registration relationships, mismatch and stale proof; protected-query failure also fails closed. Manual observer execution and change deduplication are proven. A post-merge actual cron event is not yet observed. Latest actual scheduled publisher events still precede the repair; the task follow-up described in the #157 R5 receipt watches that boundary. Configuration alone is not MONITORED/HEALTHY proof.

## Remaining exact blockers and next action

1. External class 11341058 is still the source's December 1 midnight instructor-renewal placeholder at inactive ___TBD___, with two pending registrations. The existing reconciliation operation returns unresolved_active_location; the production trigger requires an active/schedulable location. Brian's Brunswick answer does not resolve this separate class. Smallest owner action: identify its actual date/time and approved canonical location, or explicitly confirm how this placeholder commitment should be represented. Do not move/cancel real bookings or guess an active site to pass the gate.
2. An authorized unattended complete-roster export or completeness-guaranteed event source is not connected. Current authenticated browser access supplied real proof; the repository importer can consume a verified complete snapshot. The watermark expires at 05:25:29.547 UTC. Smallest infrastructure action: provide the existing importer an authorized recurring complete source with genuine source timestamps. Do not derive counts from notices, replay a timestamp as fresh, or treat a successful database read as renewed authority.
3. A subsequent actual GitHub scheduled publication must be observed and its deployed public selector checked. No new scheduled event has started after the repair as of the recorded observation. The normal workflows remain active; no permissions or protected-branch gate was bypassed.

BUILT and CONNECTED: yes. PROVEN: source-to-canonical incident coverage, 37-class current source reconciliation, and actual incident public selector. MERGED: yes. DEPLOYED: demand v2, owner workspace v7, five recorded SQL migrations, public revision 08faa58dc23da6bd7c7b99650d3d69c144b3443e. LIVE-VERIFIED: protected source projections and actual public incident selector. Whole persistent source-to-public loop: not HEALTHY because of the three boundaries above. Stage 6 remains gated.

New files in this delivery receipt branch: Codex_Reply_Issue157_PublicDelivery_R5.md; Codex_Reply_Issue297_CanonicalReconciliation_R2.md; data/audit/issue157_public_delivery_proof.json; data/audit/issue297_brunswick_approved_reconciliation.json. Earlier reports, receipts and complete source/config/test inventory remain unchanged and are linked in the prior #297 receipt. Private snapshots stay outside Git; supabase/.temp/cli-latest remains intentionally untracked. No unrelated checkout changes were included.

Next supervising action: preserve the merged repair, resolve only the TBD business decision and authorized complete-source dependency, and consume the later scheduled proof when available. Keep #297 open. Do not broaden into unrelated maintenance or create a new scheduling issue.
