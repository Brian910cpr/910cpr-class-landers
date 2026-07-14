# Selector page promotion audit

## Pages promoted
- `bls-schedule.html` -> `bls.html`
- `acls-schedule.html` -> `acls.html`
- `pals-schedule.html` -> `pals.html`
- `hsi-schedule.html` -> `hsi.html`
- `heartsaver-schedule.html` -> `heartsaver.html`

- `arc-schedule.html` -> `arc.html` (redirect only; ARC selector authority not validated)

## Selector artifacts used
- `bls`: `docs/data/block-selector-availability/bls.json`
- `acls`: `docs/data/block-selector-availability/acls.json`
- `pals`: `docs/data/block-selector-availability/pals.json`
- `hsi`: `docs/data/block-selector-availability/hsi.json`
- `heartsaver`: `docs/data/block-selector-availability/heartsaver.json`

## Fragments supported
- `bls`: `#initial`, `#renewal`, `#heartcode`
- `acls`: `#initial`, `#renewal`, `#heartcode`
- `pals`: `#initial`, `#renewal`, `#heartcode`
- `hsi`: `#bls`, `#bls-first-aid`, `#first-aid-cpr-aed`, `#cpr-aed`

## Checks
- Scoped broken links: `0`
- Scoped self-loops: `0`
- ARC promoted: `false` — no validated ARC selector artifact exists.
- HSI unsupported variants use request actions, not fake availability.
