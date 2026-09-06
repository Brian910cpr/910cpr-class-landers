# ChatGPT review handoff: group training funnel

Review the full primary report at `data/audit/group_training_funnel_audit.md` without summarizing away its limitations.

Important implementation files:

- `docs/group-training.html`
- `docs/assets/group-training.css`
- `docs/assets/group-training.js`
- `scripts/build_group_authority_pages.py`
- `docs/group-training/*/index.html`
- `docs/request_group_session.html`
- `scripts/build_request_group_session.py`
- `scripts/build_index_and_sitemap.py`
- `docs/sitemap.xml`
- `supabase/migrations/20260906010000_group_training_requests.sql`
- `supabase/functions/group-training/index.ts`
- `tests/group_training_funnel.test.cjs`
- `tests/test_group_training_public.py`

Exact verification output:

```text
group training funnel unit tests passed
.....
----------------------------------------------------------------------
Ran 5 tests in 0.602s

OK
```

Review questions:

1. Does the public request edge function match the deployed LanderWare schema and acceptable public abuse controls?
2. Should organization deduplication be added before launch rather than creating a new organization for each idempotent request?
3. Which selector artifact offer type is contractually approved for a private traveling group candidate? The code intentionally rejects `seated_class`.
4. Which exact pricing rules are approved for public estimates?
5. Can an owner complete GTM Preview, GA4 DebugView, preview Supabase integration, mobile, and 200% browser checks before merge?
6. Is there a public-use/consent inventory for industry photos?

The branch intentionally does not emit `group_session_reserved`, claim immediate confirmation, publish industry-city pages, or deploy production changes.
