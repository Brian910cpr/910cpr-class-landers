# Codex Read — Issue #334 Native Anchor R2

- **Round:** 20261011T032638Z-I334-NATIVE-ACCEPT-R1
- **Reply reviewed:** `Codex_Reply_Issue334_NativeAnchor_R2.md`
- **Receipt tip:** `098704f0206829998201fb642052704561c1dfd2`
- **Substantive commits:** `548139d242ef73c89d5114239ee4fbae4353b257`, `32c1bb19785252708579df63b6a16774616cd5f2`
- **Merged PRs:** #377, #378

Reviewed both PR diffs, the mapping and native eligibility gates, the exact canonical-URL follow-up, the focused regression matrix, deployment results, and the recorded live proof.

## Acceptance

The native class-page presentation repair is accepted:

- Native LanderWare rows resolve presentation only from the active course map, without guessing from titles.
- A scheduled native CTA requires existing candidate identity, current canonical demand, a public location, an active known course, positive registration proof, and the exact canonical LanderWare registration URL.
- A substituted legacy Enrollware URL now fails closed even if it is syntactically valid.
- Closed, cancelled, rescheduled, completed, stale, private-location, and unknown-course cases remain guarded.
- PRs #377 and #378 merged; the final Pages deployment succeeded.
- The October 13 page was live-verified with mapped Heartsaver/AHA metadata and the canonical registration CTA. No booking or payment was submitted.

Keep #334 open. This proves the page repair and one successful publication, not cloud-independent recurring health.

## Remaining gate

The existing owner-level gate is unchanged: approve/create a repository-restricted fine-grained GitHub token with Actions read/write and store it only as Cloudflare's encrypted `GITHUB_ACTIONS_TOKEN`; engineering can then activate and verify the cloud timer, configure `AVAILABILITY_WATCHDOG_HEALTH_URL`, and prove independent observer health.
