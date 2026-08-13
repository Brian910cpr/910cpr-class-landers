update public.production_board_cards
set lane='doing', brian_override=true, implementation_status='IMPLEMENTING / REVIEW BRANCH',
    value_score=10, work_score=6, original_work_score=6, incremental_work_score=6,
    separate_work_score=10, bundled_work_score=6, bundle_advantage=0.4000,
    summary='Improve current public discovery through durable class pages, cleaner crawl signals, current availability, accurate Event data, and useful internal links.',
    details='Architecture decision: B on the outside. C underneath. The future backend should make later public-discovery work easier, not delay today''s visibility improvements.',
    flags=array['BRIAN OVERRIDE','CUSTOMER IMPACT','REVENUE'],
    context_manifest=jsonb_set(context_manifest,'{decisions}',
      '["B on the outside. C underneath.","C should make future public-discovery work easier, not delay today''s visibility improvements.","Internal production language must never appear on public surfaces."]'::jsonb)
where title='Public Discovery / AI Architecture';

insert into public.production_board_cards
  (title,project,owner,lane,value_score,work_score,summary,details,flags,brian_override,card_type,implementation_status,original_work_score,incremental_work_score,separate_work_score,bundled_work_score,bundle_advantage,context_manifest)
values
('RAW SEO POWE-AH — Discovery Surface Sprint','Public Discovery','Brian','doing',10,6,
 'Ship durable public Session behavior, cleaner crawl signals, discovery monitoring, and the BLS/Wilmington cohort.',
 'One bundled implementation package. Internal project language is private and prohibited from customer-facing output.',
 array['BRIAN OVERRIDE','CUSTOMER IMPACT','REVENUE'],true,'epic','IMPLEMENTING / REVIEW BRANCH',6,6,10,6,0.4000,
 '{"status":"enriched","updated_at":"2026-08-13T13:30:00Z","decisions":["Public pages use customer-native language only."],"open_questions":[],"related_cards":[],"implementation":{"repository":"D:\\Users\\ten77\\Documents\\GitHub\\910cpr-class-landers-global-page","branch":"codex/inventory-discovery-sprint","commit":null,"important_paths":["scripts/build_landers.py","scripts/build_index_and_sitemap.py","scripts/audit_public_discovery.py"],"status":"Implementation complete locally; review branch not deployed."}}'::jsonb),
('Stop Letting Multiple Generators Independently Reinterpret Reality','LanderWare Platform','Brian','next',9,16,
 'Build the increasingly authoritative C-style LanderWare truth layer underneath the evolved public discovery architecture.',
 'Future backend package: shared Course, Session, Location, and Requirement truth; near-real-time inventory; unified lifecycle; API; observability. Must not block the current discovery sprint.',
 array['ARCHITECTURAL'],false,'epic','NEXT / ARCHITECTURAL',16,16,26,16,0.3846,
 '{"status":"enriched","updated_at":"2026-08-13T13:30:00Z","decisions":["B on the outside. C underneath.","C should make future public-discovery work easier, not delay today''s visibility improvements."],"open_questions":[],"related_cards":[],"implementation":{"repository":null,"branch":null,"commit":null,"important_paths":[],"status":"Future architecture; not started and not blocking current work."}}'::jsonb)
on conflict do nothing;

insert into public.production_board_cards
  (title,project,owner,lane,value_score,work_score,summary,details,flags,brian_override,card_type,implementation_status,original_work_score,incremental_work_score,context_manifest,parent_card_id)
select child.title,'Public Discovery','Brian','doing',child.value_score,child.work_score,child.summary,child.details,
       array['CUSTOMER IMPACT'],true,'task','IMPLEMENTING / REVIEW BRANCH',child.work_score,child.work_score,
       '{"status":"enriched","updated_at":"2026-08-13T13:30:00Z","decisions":[],"open_questions":[],"related_cards":[],"implementation":{"status":"Included in the public discovery review branch; not deployed."}}'::jsonb,
       parent.id
from public.production_board_cards parent
cross join (values
 ('Durable Session URLs / lifecycle',10::numeric,3::numeric,'Keep each public class URL useful through scheduled, full, cancelled, rescheduled, and completed states.','Preserve history and route visitors to legitimate next classes.'),
 ('Crawl-surface cleanup',9,2,'Publish deliberate robots, sitemap, canonical, and duplicate-route signals.','Remove rolling date permutations from canonical sitemap inventory.'),
 ('Discovery health monitoring',8,1,'Detect stale upcoming rows, sitemap contamination, broken class pages, schema issues, missing booking URLs, and private-language leaks.','Private report only.'),
 ('BLS + Wilmington pilot',9,2,'Connect BLS course choices, Wilmington, current classes, and direct registration.','Preserve Initial, Renewal, and HeartCode distinctions.')
) child(title,value_score,work_score,summary,details)
where parent.title='RAW SEO POWE-AH — Discovery Surface Sprint'
  and not exists(select 1 from public.production_board_cards c where c.title=child.title);
