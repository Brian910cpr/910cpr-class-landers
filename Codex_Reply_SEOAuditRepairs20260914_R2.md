# SEO audit repairs, deployment verification

- Assignment: 2026-09-14 SEO audit repairs, deployment round 2
- Timestamp: 2026-09-14 15:36 UTC
- Branch: `main`
- Pull request: `#234`
- Squash merge commit: `22b0c0d5cd0e7a05933911748a7be82f0e5a43d1`
- Expired-page follow-up commits: `4669a5e5156b720040928260524e35ce04515be4`, `c85e8b088557c59740cc0f80768c4ffa6f702418`
- Work-item state: `VERIFIED` for the deployed group funnel and three known expired pages. `BUILT` for the new hourly retirement workflow and static 14-to-21-day projection pending their first production generation cycles.

## Production evidence

- PR #234 source-integrity and Cloudflare preflight checks passed before merge.
- GitHub Pages deployed the merged group funnel. Browser verification confirmed `group-training.html` contains the inline request form, its BLS hero CTA stays on-page, selecting the ACLS tab changes the form program to ACLS, and the form submit control becomes enabled after JavaScript initializes.
- `group.html` redirects to `group-training.html#request-form`.
- `request_group_session.html` remains functional and returns `noindex,follow`.
- Browser verification confirmed expired class pages `14047880`, `14058362`, and `14123264` now return `noindex,follow`, display “This class has ended,” and expose no registration CTA.
- BLS, ACLS, PALS, and Heartsaver public routes all loaded their normal interactive selector shells after deployment.

## Remaining operational status

- The static 14-to-21-day projection is merged into the production selector generator but is not yet visible on the four core pages because those generated pages have not completed a fresh availability build.
- HOT_SYNC remains the blocker for the normal availability build. Until that credential mismatch is repaired, public inventory freshness is not `HEALTHY`.
- The new hourly retirement workflow is deployed and observable in GitHub Actions, but it has not yet completed its first scheduled end-to-end cycle. Its evidence level remains `BUILT`, not `PROVEN` or `HEALTHY`.

## Next action

Synchronize the HOT_SYNC endpoint credential and GitHub Actions secret, rerun the public and admin availability workflows, verify fresh timestamps and the 14-to-21-day projection on the four core pages, then observe one successful hourly retirement run. This remaining step requires account-level credential access if the endpoint and secret cannot be rotated through repository automation.
