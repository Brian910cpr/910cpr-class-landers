# ChatGPT review handoff: group training funnel amendment

Read `data/audit/group_training_funnel_audit.md` and `data/audit/group_training_image_inventory.md` in full.

## Primary implementation

- `docs/group-training.html`
- `docs/assets/group-training.css`
- `docs/assets/group-training.js`
- `scripts/build_group_authority_pages.py`
- `docs/group-training/*/index.html`
- `supabase/functions/group-training/core.mjs`
- `supabase/functions/group-training/index.ts`
- `supabase/migrations/20260906010000_group_training_requests.sql`
- `tests/group_training_funnel.test.cjs`
- `tests/test_group_training_public.py`

## Exact local results

```text
node behavioral suite: pass
group-training Python suite: pass
broader targeted Python suite: 21/22 pass
unrelated failure: schedule-index parity, 127 existing IDs
```

Cloudflare Pages passed for PR head `445ca112de0eef2407d484d1f7f2287f562c2cbd`. Review SQL transaction/locks/RLS and exact course matching against preview Supabase; inspect `data/audit/group-training-screenshots/`; keep the seven-industry/five-market quality boundary; require Supabase integration, GTM/GA4, keyboard, and true 200% zoom evidence before merge.

No production merge or deployment was performed. Cloudflare, Supabase, and GA4 authentication are unavailable in this environment.
