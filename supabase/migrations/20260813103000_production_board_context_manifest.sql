alter table public.production_board_cards
  add column if not exists context_manifest jsonb not null default '{
    "status": "pending",
    "updated_at": null,
    "related_threads": [],
    "decisions": [],
    "open_questions": [],
    "related_cards": [],
    "implementation": {
      "repository": null,
      "branch": null,
      "commit": null,
      "important_paths": [],
      "status": "unverified"
    }
  }'::jsonb;

update public.production_board_cards
set context_manifest = jsonb_set(context_manifest, '{updated_at}', to_jsonb(now()))
where context_manifest->>'updated_at' is null;

update public.production_board_cards
set context_manifest = '{
  "status": "enriched",
  "updated_at": "2026-08-13T10:30:00Z",
  "related_threads": [
    {
      "id": "6a7c8dee-96cc-83ea-9066-0a0e39ca4c4d",
      "source": "chatgpt",
      "title": "Tabbed Lanes Scheduling",
      "relevance": "primary",
      "reason": "Original instructor-tab, overlapping-card, dynamic-location, and collision-model discussion.",
      "confidence": 1.0,
      "review_status": "confirmed"
    },
    {
      "id": "019ff6bb-4477-79c3-9d76-10947004d1f7",
      "source": "codex",
      "title": "Build LanderWare production board",
      "relevance": "implementation",
      "reason": "Production Board schema, API, repository, migration, and release work.",
      "confidence": 1.0,
      "review_status": "confirmed"
    },
    {
      "id": "019ff1e5-fb08-76f2-bc89-720269258c4b",
      "source": "codex",
      "title": "Fix public availability filters",
      "relevance": "adjacent",
      "reason": "Availability and resource-fit behavior that the schedule lanes must explain without conflating resources.",
      "confidence": 0.9,
      "review_status": "confirmed"
    }
  ],
  "decisions": [
    "Instructor tabs control the view: ALL, BRIAN, AMY, GRAVES, and UNASSIGNED.",
    "The ALL view stacks simultaneous cards in a Google Calendar-style overlap layout.",
    "Locations converge dynamically for the selected day instead of becoming permanent top-level tabs.",
    "Instructor conflicts and location-capacity conflicts are separate evaluations.",
    "Other instructors and unrelated locations must not block the selected instructor unless the scheduled work consumes a shared required resource."
  ],
  "open_questions": [
    "Which shared resources besides instructor and location must participate in availability blocking?",
    "How are rooms and per-location simultaneous-class capacities represented?",
    "What travel and setup or cleanup buffers apply between locations?"
  ],
  "related_cards": [
    {"id": null, "title": "Converging location lanes", "relationship": "dependent design", "confidence": 1.0, "review_status": "confirmed"},
    {"id": null, "title": "Persistent instructor/admin schedule workspace", "relationship": "parent workspace", "confidence": 1.0, "review_status": "confirmed"},
    {"id": null, "title": "Location-aware instructor schedule visualization", "relationship": "overlapping scope", "confidence": 1.0, "review_status": "confirmed"}
  ],
  "implementation": {
    "repository": "D:\\Users\\ten77\\Documents\\GitHub\\910cpr-class-landers-global-page",
    "branch": "codex/landerware-production-board",
    "commit": null,
    "important_paths": [
      "docs/admin/dashboard.html",
      "docs/admin/production.html",
      "docs/admin/production.js",
      "supabase/functions/production-board/index.ts"
    ],
    "status": "Production Board exists; tabbed lanes are approved for attachment to the Dashboard but not yet implemented."
  }
}'::jsonb
where title = 'Tabbed instructor schedule lanes with overlapping cards';

insert into public.production_board_activity(card_id, action, detail, actor)
select id, 'context_enriched', jsonb_build_object('manifest_version', 1, 'related_threads', 3), 'Codex'
from public.production_board_cards
where title = 'Tabbed instructor schedule lanes with overlapping cards'
  and not exists (
    select 1 from public.production_board_activity a
    where a.card_id = production_board_cards.id
      and a.action = 'context_enriched'
  );
