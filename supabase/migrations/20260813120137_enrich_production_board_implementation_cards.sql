update public.production_board_cards
set context_manifest = jsonb_set(jsonb_set(context_manifest, '{status}', '"enriched"'::jsonb), '{updated_at}', to_jsonb(now()))
where title in ('Instructor Session Workspace','Maxim Coming Due / Completed 14-day behavior','Maxim Trello-style personnel workflow','Maxim persistent audit history');

insert into public.production_board_cards
  (title,project,owner,lane,value_score,work_score,summary,details,flags,brian_override,card_type,parent_card_id,implementation_status,original_work_score,incremental_work_score,context_manifest)
select 'Validate durable Maxim migration against PostgreSQL','Maxim','Brian','next',9,3,
  'Run and verify the existing durable-Maxim migration against real PostgreSQL.',
  'The branch implementation was validated locally except for actual PostgreSQL migration execution because Docker/Postgres was unavailable. Validate the existing migration; do not rebuild Maxim.',
  array['BLOCKING'],false,'task',parent.id,'READY / BLOCKING',3,3,
  '{"status":"enriched","updated_at":"2026-08-13T12:01:37Z","related_threads":[],"decisions":["Validate the existing migration rather than rebuilding durable Maxim."],"open_questions":[],"related_cards":[],"implementation":{"repository":"D:\\Users\\ten77\\Documents\\GitHub\\910cpr-class-landers-global-page","branch":"codex/maxim-durable-corporate-portal","commit":"3a728b225da60e2c606e5e5ed092ef2e771c08dc","important_paths":["supabase/migrations"],"status":"Migration exists on branch; PostgreSQL execution remains unverified."}}'::jsonb
from public.production_board_cards parent
where parent.title='Finish Durable Maxim'
  and not exists (select 1 from public.production_board_cards where title='Validate durable Maxim migration against PostgreSQL');

insert into public.production_board_activity(card_id,action,detail,actor)
select id,'catalog_restructured',jsonb_build_object('catalog_pass','2026-08-13','implementation_status',implementation_status),'Codex'
from public.production_board_cards
where title='Validate durable Maxim migration against PostgreSQL'
  and not exists (select 1 from public.production_board_activity a where a.card_id=production_board_cards.id and a.action='catalog_restructured');
