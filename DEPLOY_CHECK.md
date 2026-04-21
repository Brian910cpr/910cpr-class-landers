# Deploy Check

## Files changed
- `docs/css/lander.css`
- `docs/assets/hub-ui.js`
- `scripts/build_slug_hubs.py`
- `scripts/build_request_group_session.py`
- `scripts/hub_utils.py`
- `docs/bls.html`
- `docs/acls.html`
- `docs/pals.html`
- `docs/heartsaver.html`
- `docs/uscg-elementary-first-aid-cpr.html`
- `docs/group-training.html`
- `docs/request_group_session.html`

## What publishes the site
- This repo appears to publish as a branch-based GitHub Pages site, not an Actions-built Pages site.
- There is no `.github/workflows` Pages workflow in the repo.
- The repo’s active branch is `main`, and the public site files live in `docs/`.
- `docs/CNAME` is set to `www.910cpr.com`, which matches the live custom domain.

## Public URLs that should reflect the update
- `https://www.910cpr.com/bls`
- `https://www.910cpr.com/acls`
- `https://www.910cpr.com/pals`
- `https://www.910cpr.com/heartsaver`
- `https://www.910cpr.com/uscg-elementary-first-aid-cpr`
- `https://www.910cpr.com/group-training`
- `https://www.910cpr.com/request_group_session.html`

## How to confirm the newest commit is live
1. Push the commit to the publishing branch.
2. Open one of the URLs above.
3. Hard refresh the page.
4. Confirm the updated hero section, quick-pick tab chips, polished date cards, and shared tab behavior are visible.
5. Confirm `request_group_session.html?program=BLS%20On-Site` preselects the matching tab and program field.

## Cache delay
- A short GitHub Pages propagation delay is normal after push.
- Browser cache can also lag a little, especially for CSS and JS, so a hard refresh may be needed.
