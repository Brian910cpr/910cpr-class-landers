# DEPLOY_CHECK

Files changed:
- `scripts/build_slug_hubs.py`
- `scripts/hub_utils.py`
- `scripts/build_request_group_session.py`
- `docs/assets/hub-ui.js`
- `docs/css/lander.css`
- `docs/bls.html`
- `docs/acls.html`
- `docs/pals.html`
- `docs/heartsaver.html`
- `docs/uscg-elementary-first-aid-cpr.html`
- `docs/group-training.html`
- `docs/request_group_session.html`

What publishes the site:
- This repo appears to use GitHub Pages from the `main` branch and the `docs/` folder.
- There is no GitHub Actions Pages workflow in `.github/workflows` in this checkout.
- `docs/CNAME` points the site at `www.910cpr.com`.

Public URLs that should reflect the update:
- `https://www.910cpr.com/bls.html`
- `https://www.910cpr.com/acls.html`
- `https://www.910cpr.com/pals.html`
- `https://www.910cpr.com/heartsaver.html`
- `https://www.910cpr.com/uscg-elementary-first-aid-cpr.html`
- `https://www.910cpr.com/group-training.html`
- `https://www.910cpr.com/request_group_session.html`

How to confirm the newest commit is live:
- Open one of the URLs above and hard refresh.
- View page source and confirm it includes `/assets/hub-ui.js`.
- Confirm the visible hero, tab, and card styling matches the new shared hub layout.
- Check that the published HTML matches the latest commit on `main`.

Cache delay:
- GitHub Pages usually updates within a few minutes after the commit reaches the publishing branch.
- A short browser or CDN cache delay is possible, so a hard refresh may be needed.
