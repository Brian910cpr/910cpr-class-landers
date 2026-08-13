alter table public.production_board_cards
  add column if not exists card_type text not null default 'task'
    check (card_type in ('task','epic','objective','strategic')),
  add column if not exists parent_card_id uuid references public.production_board_cards(id) on delete set null,
  add column if not exists implementation_status text not null default 'IDEA',
  add column if not exists original_work_score numeric(6,2),
  add column if not exists incremental_work_score numeric(6,2),
  add column if not exists separate_work_score numeric(6,2),
  add column if not exists bundled_work_score numeric(6,2),
  add column if not exists bundle_advantage numeric(6,4);

update public.production_board_cards
set original_work_score = coalesce(original_work_score, work_score),
    incremental_work_score = coalesce(incremental_work_score, work_score)
where original_work_score is null or incremental_work_score is null;

create index if not exists production_board_cards_parent_idx
  on public.production_board_cards(parent_card_id, lane, updated_at desc);

create table if not exists public.production_board_dependencies (
  id uuid primary key default gen_random_uuid(),
  blocked_card_id uuid not null references public.production_board_cards(id) on delete cascade,
  blocker_card_id uuid not null references public.production_board_cards(id) on delete cascade,
  relationship text not null default 'BLOCKED BY' check (relationship in ('BLOCKED BY')),
  reason text not null default '',
  created_at timestamptz not null default now(),
  unique(blocked_card_id, blocker_card_id),
  check(blocked_card_id <> blocker_card_id)
);

alter table public.production_board_dependencies enable row level security;
revoke all on public.production_board_dependencies from anon, authenticated;
grant select, insert, update, delete on public.production_board_dependencies to service_role;

insert into public.production_board_cards
  (title,project,owner,lane,value_score,work_score,summary,details,flags,brian_override,card_type,implementation_status,original_work_score,incremental_work_score,separate_work_score,bundled_work_score,bundle_advantage,context_manifest)
values
('Scheduling Control & Intelligence','Scheduling','Brian','doing',10,16,'Unified operational schedule visualization and decision support.','Shared foundation: calendar renderer, instructor availability, location state, conflict representation, and operational scheduling UI.',array['CUSTOMER IMPACT'],true,'epic','DESIGNING',16,16,26,16,0.3846,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Instructor tabs control the view while dynamic location lanes structure the selected day.","Instructor and location conflicts remain separate resource evaluations."],"open_questions":["Confirm room capacity and travel-buffer data contracts."],"related_cards":[],"implementation":{"repository":"D:\\Users\\ten77\\Documents\\GitHub\\910cpr-class-landers-global-page","branch":"codex/landerware-production-board","commit":null,"important_paths":["docs/admin/dashboard.html"],"status":"Design package; tabbed lanes approved for Dashboard attachment."}}'::jsonb),
('Scheduling Truth & Integrity','Scheduling','Brian','doing',10,10,'Keep operational reality and public availability synchronized.','Hot Sync, registration movement, refresh controls, and availability-state integrity.',array['BROKEN NOW','BLOCKING','CUSTOMER IMPACT'],false,'epic','READY',10,10,14,10,0.2857,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Committed operational work must immediately constrain public availability."],"open_questions":[],"related_cards":[],"implementation":{"repository":"E:\\GitHub\\910cpr-class-landers","branch":null,"commit":null,"important_paths":[],"status":"Mixed production and unfinished integrity work; verify each child."}}'::jsonb),
('Instructor Operations Lifecycle','Instructor Operations','Brian','next',10,18,'Carry instructor work from coverage through completion review and cards.','Needs instructor → assigned → prepared → teach → complete → Brian review → invoice/eCards.',array['CUSTOMER IMPACT'],false,'epic','DESIGNING',18,18,27,18,0.3333,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Session Workspace is an existing branch implementation and must not be rebuilt."],"open_questions":["Define the production packet and paperwork handoff."],"related_cards":[],"implementation":{"repository":"D:\\Users\\ten77\\Documents\\GitHub\\910cpr-class-landers-global-page","branch":"codex/session-workspace-instructor-packet","commit":"811687a1470e425a23e3e8eaafd096ee70147345","important_paths":[],"status":"Core Session Workspace built on branch; not on main or production."}}'::jsonb),
('Finish Durable Maxim','Maxim','Brian','doing',10,14,'Finish and release the already-built durable Maxim corporate workflow.','Built and validated on branch. Resolve hosting, Session Workspace, PostgreSQL migration testing, and Gmail blockers without rebuilding it.',array['BLOCKING','CUSTOMER IMPACT','REVENUE'],false,'epic','BUILT ON BRANCH / VALIDATED / BLOCKED / NOT DEPLOYED',14,14,26,14,0.4615,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Do not represent durable Maxim as unstarted.","Pending messages remain pending until Gmail confirms delivery."],"open_questions":["Select authenticated private hosting.","Validate migration against PostgreSQL."],"related_cards":[],"implementation":{"repository":"D:\\Users\\ten77\\Documents\\GitHub\\910cpr-class-landers-global-page","branch":"codex/maxim-durable-corporate-portal","commit":"3a728b225da60e2c606e5e5ed092ef2e771c08dc","important_paths":[],"status":"BUILT / VALIDATED IN BRANCH — NOT MERGED / NOT DEPLOYED"}}'::jsonb),
('Private LanderWare Platform','LanderWare Platform','Brian','next',10,12,'Provide authenticated hosting for private operational and record systems.','Required by Schedule Manager, Instructor My Classes, Session Workspace, Maxim administration, records search, and document access. Public scheduling and customer Session pages remain public.',array['BLOCKING'],false,'epic','READY / BLOCKING',12,12,20,12,0.4000,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Private operational systems require authenticated hosting; public scheduling remains public.","Do not prematurely choose a host architecture."],"open_questions":["Approve the authenticated production hosting architecture."],"related_cards":[],"implementation":{"repository":null,"branch":null,"commit":null,"important_paths":[],"status":"Enabling architecture not yet selected."}}'::jsonb),
('LanderWare Records / Filing Cabinet','LanderWare Records','Brian','next',10,20,'Create durable business records that survive rebuilt projections.','Person, Organization, Instructor, Session, Roster, membership, registration, requirement, credential, message, activity, and document records. Records survive; projections can be rebuilt.',array['CUSTOMER IMPACT'],false,'epic','DESIGNING',20,20,30,20,0.3333,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Generated HTML, JSON, availability, and dashboards are not permanent business records."],"open_questions":["Sequence record normalization after private hosting."],"related_cards":[],"implementation":{"repository":null,"branch":null,"commit":null,"important_paths":[],"status":"Architecture package; partial durable records exist in Session Workspace and Maxim branches."}}'::jsonb),
('LanderWare Messaging / Gmail Integration','Messaging','Brian','next',9,8,'Send from durable Message records and preserve confirmed Gmail identifiers.','Message → Gmail OAuth/API → send → capture Gmail message/thread ID → activity history. Never fake successful sends.',array['BLOCKING','CUSTOMER IMPACT'],false,'epic','BLOCKED',8,8,12,8,0.3333,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Unconfirmed messages remain pending or failed; never mark them sent."],"open_questions":["Configure Gmail OAuth/API."],"related_cards":[],"implementation":{"repository":null,"branch":null,"commit":null,"important_paths":[],"status":"Blocked: Gmail OAuth/API not configured."}}'::jsonb),
('Requirements Intelligence','Requirements Intelligence','Brian','next',10,16,'Model authoritative requirements across instructor, Session, student, and course.','PAM-driven matrix and historical Session Requirements Manifest snapshots. Do not encode requirements from memory.',array['CUSTOMER IMPACT'],false,'epic','DESIGNING',16,16,24,16,0.3333,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Rules must come from authoritative versioned sources.","Historical Session manifests must not change retroactively."],"open_questions":["Begin separate authoritative PAM ingestion after the catalog restructure."],"related_cards":[],"implementation":{"repository":"D:\\Users\\ten77\\Documents\\GitHub\\910cpr-class-landers-global-page","branch":"codex/session-workspace-instructor-packet","commit":"811687a1470e425a23e3e8eaafd096ee70147345","important_paths":[],"status":"Requirements Manifest foundation built in Session Workspace branch; authoritative rules not ingested."}}'::jsonb),
('Authoritative Program Reference Library','Program Reference','Brian','parked',9,11,'Preserve versioned program, discipline, course, guideline, and source documents.','Program → Discipline → Course → Guidelines Version → Document → Effective/As-of Date.',array[]::text[],false,'epic','IDEA',11,11,15,11,0.2667,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Original authoritative documents remain available after newer versions arrive."],"open_questions":[],"related_cards":[],"implementation":{"repository":null,"branch":null,"commit":null,"important_paths":[],"status":"Not implemented."}}'::jsonb),
('Document Intelligence / Vault','Documents','Brian','parked',9,13,'Attach retained source documents to durable LanderWare records.','Storage-provider-ready records with private Synology NAS as canonical future direction; Google may be backup/disaster recovery.',array[]::text[],false,'epic','IDEA',13,13,18,13,0.2778,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Do not make Google Drive the canonical permanent records vault.","Documents attach to records rather than forming a disconnected PDF archive."],"open_questions":["Select storage provider contract later."],"related_cards":[],"implementation":{"repository":null,"branch":null,"commit":null,"important_paths":[],"status":"Storage-provider-ready architecture only; NAS integration not started."}}'::jsonb),
('Universal Public Session Architecture','Sessions','Brian','next',10,12,'Give every committed public Session a stable landing page regardless of source.','Session records are permanent; rendered HTML is a rebuildable projection. Sources include Enrollware, Schedule Manager, corporate, manual, and Hot Sync.',array['CUSTOMER IMPACT','REVENUE'],false,'epic','DESIGNING',12,12,18,12,0.3333,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Every public committed/seated Session gets a stable LanderWare landing page regardless of source."],"open_questions":[],"related_cards":[],"implementation":{"repository":"D:\\Users\\ten77\\Documents\\GitHub\\910cpr-class-landers-global-page","branch":"codex/session-workspace-instructor-packet","commit":"811687a1470e425a23e3e8eaafd096ee70147345","important_paths":[],"status":"Partial public Session rendering built on Session Workspace branch; not production."}}'::jsonb),
('Public Discovery / AI Architecture','Public Discovery','Brian','parked',9,19,'Unify structured course/session data, availability, local intent, analytics, and internal linking.','Shared architecture for AI ingestion, occurrence pages, knowledge publishing, career pages, schema, and direct deep links.',array['REVENUE'],false,'epic','DESIGNING',19,19,29,19,0.3448,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Public discovery work shares durable structured source data and must preserve analytics."],"open_questions":[],"related_cards":[],"implementation":{"repository":"E:\\GitHub\\910cpr-class-landers","branch":null,"commit":null,"important_paths":[],"status":"Mixed existing production infrastructure and future packages."}}'::jsonb),
('Industry B2B Acquisition / Group Training 2.0','Group Training','Brian','parked',10,12,'Build original Coastal-NC industry acquisition after durable Maxim.','Study CPR-Professionals as benchmark/coach, never copy source. Connect industry intent through feasible dates and the durable operational lifecycle.',array['REVENUE'],false,'epic','BLOCKED',12,12,18,12,0.3333,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["B2B Acquisition starts only after durable Maxim unless Brian overrides.","CPR-Professionals is a benchmark, not a copy source."],"open_questions":[],"related_cards":[],"implementation":{"repository":"E:\\GitHub\\910cpr-class-landers","branch":null,"commit":null,"important_paths":[],"status":"Future acquisition package; blocked by durable Maxim."}}'::jsonb),
('3,000 BLS providers/year','Strategic Objective','Brian','next',10,10,'Reach 3,000 BLS providers yearly without proportionally increasing Brian’s workload.','Current context is approximately 1,200/year. Make 3,000 operationally easier than today’s 1,200.',array['REVENUE'],false,'objective','STRATEGIC',10,10,null,null,null,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Growth must come from leverage, automation, corporate accounts, instructors, and retention—not Brian teaching 2.5× more."],"open_questions":[],"related_cards":[],"implementation":{"repository":null,"branch":null,"commit":null,"important_paths":[],"status":"Strategic objective, not executable work."}}'::jsonb),
('Instructor / subcontractor economics','Strategic Objective','Brian','parked',8,8,'Evaluate whether productive subcontractor economics can increase provider volume and contribution.','Analyze volume tiers, card/admin cost, acquisition, retention, and a scalable Teach CPR; we handle the rest model. Do not change pricing without approval.',array['REVENUE'],false,'strategic','IDEA',8,8,null,null,null,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["No pricing change without separate analysis and approval."],"open_questions":["Model unit economics and volume tiers."],"related_cards":[],"implementation":{"repository":null,"branch":null,"commit":null,"important_paths":[],"status":"Strategic analysis not started."}}'::jsonb),
('Harbor Master implementation governance','Implementation Governance','Brian','next',7,2,'Require an organic Dockmaster/Harbor Master canon entry for substantive implementation.','Keep a comment-only canon pass over Session Workspace and corporate records work. No executable changes during that pass.',array[]::text[],false,'task','READY',2,2,null,null,null,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["The pending canon pass is comment-only and must not make executable changes."],"open_questions":[],"related_cards":[],"implementation":{"repository":"E:\\GitHub\\910cpr-class-landers","branch":null,"commit":null,"important_paths":[],"status":"Low-work governance task ready."}}'::jsonb),
('Historical paper / document ingestion','Documents','Brian','parked',7,10,'Retain, OCR, classify, confirm, attach, index, and search historical paperwork.','SCAN → retain original → OCR/extract → classify → suggest records → human confirm → attach → index/search. Do not build a disconnected PDF archive.',array[]::text[],false,'task','IDEA / PARKED',10,10,null,null,null,'{"status":"enriched","updated_at":"2026-08-13T11:51:37Z","related_threads":[],"decisions":["Human confirmation precedes attachment to durable records."],"open_questions":[],"related_cards":[],"implementation":{"repository":null,"branch":null,"commit":null,"important_paths":[],"status":"Future work; OCR/scanning not started."}}'::jsonb)
on conflict do nothing;

-- Reuse and parent existing executable cards. Titles are the stable catalog keys for this controlled pass.
update public.production_board_cards c set parent_card_id=p.id
from public.production_board_cards p
where p.title='Scheduling Control & Intelligence'
  and c.title in ('Tabbed instructor schedule lanes with overlapping cards','Converging location lanes','Gap Intelligence','Persistent instructor/admin schedule workspace','Location-aware instructor schedule visualization');

update public.production_board_cards c set parent_card_id=p.id
from public.production_board_cards p
where p.title='Scheduling Truth & Integrity'
  and c.title in ('Registration move/add recalculates public availability','Missing Hot Sync / Geosyntec visibility','Mobile Enrollware refresh control','Repeat-gap / family suppression policy review');

update public.production_board_cards c set parent_card_id=p.id
from public.production_board_cards p
where p.title='Instructor Operations Lifecycle'
  and c.title in ('Instructor coverage / offer yourself feature','Instructor Session Workspace','Daily instructor completion review queue');

update public.production_board_cards c set parent_card_id=p.id
from public.production_board_cards p
where p.title='Finish Durable Maxim'
  and c.title in ('Maxim Coming Due / Completed 14-day behavior','Maxim Trello-style personnel workflow','Maxim persistent audit history');

update public.production_board_cards c set parent_card_id=p.id
from public.production_board_cards p
where p.title='LanderWare Messaging / Gmail Integration'
  and c.title='Group Training email routing';

update public.production_board_cards c set parent_card_id=p.id
from public.production_board_cards p
where p.title='Universal Public Session Architecture'
  and c.title='Class-occurrence product pages';

update public.production_board_cards c set parent_card_id=p.id
from public.production_board_cards p
where p.title='Public Discovery / AI Architecture'
  and c.title in ('AI-ingestion optimization across all public pages','FAQ / knowledge publishing system','Career-specific CPR/BLS content pages','GA4/GTM preservation on new pages','BLS selector 3-column comparison matrix');

update public.production_board_cards c set parent_card_id=p.id
from public.production_board_cards p
where p.title='Industry B2B Acquisition / Group Training 2.0'
  and c.title in ('Group Training visual redesign','Group Training provisional self-booking');

update public.production_board_cards c set parent_card_id=p.id
from public.production_board_cards p
where p.title='Document Intelligence / Vault'
  and c.title='Historical paper / document ingestion';

-- Preserve original work and mark verified implementation states without changing existing score inputs.
update public.production_board_cards set
  implementation_status='BUILT / NOT ON MAIN / NOT PRODUCTION',
  context_manifest=jsonb_set(context_manifest,'{implementation}','{"repository":"D:\\Users\\ten77\\Documents\\GitHub\\910cpr-class-landers-global-page","branch":"codex/session-workspace-instructor-packet","commit":"811687a1470e425a23e3e8eaafd096ee70147345","important_paths":[],"status":"BUILT — NOT ON MAIN / NOT PRODUCTION; blocked by private authenticated hosting."}'::jsonb)
where title='Instructor Session Workspace';

update public.production_board_cards set
  implementation_status='BUILT ON BRANCH / VALIDATED / NOT DEPLOYED',
  context_manifest=jsonb_set(context_manifest,'{implementation}','{"repository":"D:\\Users\\ten77\\Documents\\GitHub\\910cpr-class-landers-global-page","branch":"codex/maxim-durable-corporate-portal","commit":"3a728b225da60e2c606e5e5ed092ef2e771c08dc","important_paths":[],"status":"Existing durable Maxim implementation; do not rebuild."}'::jsonb)
where title in ('Maxim Coming Due / Completed 14-day behavior','Maxim Trello-style personnel workflow','Maxim persistent audit history');

insert into public.production_board_dependencies(blocked_card_id,blocker_card_id,reason)
select blocked.id, blocker.id, x.reason
from (values
  ('Instructor Session Workspace','Private LanderWare Platform','Private authenticated production hosting is required.'),
  ('Finish Durable Maxim','Instructor Session Workspace','Durable Maxim production depends on the Session Workspace production path.'),
  ('Industry B2B Acquisition / Group Training 2.0','Finish Durable Maxim','B2B acquisition begins after durable Maxim unless Brian overrides.'),
  ('LanderWare Messaging / Gmail Integration','Private LanderWare Platform','Private authenticated operations are required for message administration.')
) x(blocked_title,blocker_title,reason)
join public.production_board_cards blocked on blocked.title=x.blocked_title
join public.production_board_cards blocker on blocker.title=x.blocker_title
on conflict(blocked_card_id,blocker_card_id) do update set reason=excluded.reason;

insert into public.production_board_activity(card_id,action,detail,actor)
select id,'catalog_restructured',jsonb_build_object('catalog_pass','2026-08-13','card_type',card_type,'parent_card_id',parent_card_id,'implementation_status',implementation_status),'Codex'
from public.production_board_cards
where not exists (
  select 1 from public.production_board_activity a
  where a.card_id=production_board_cards.id and a.action='catalog_restructured'
);
