create table public.production_board_cards (
  id uuid primary key default gen_random_uuid(),
  title text not null check (length(trim(title)) between 1 and 180),
  project text not null default 'LanderWare',
  owner text not null default 'Brian',
  lane text not null default 'parked' check (lane in ('doing','next','decision','parked')),
  value_score numeric(6,2) not null default 5 check (value_score >= 0),
  work_score numeric(6,2) not null default 5 check (work_score > 0),
  summary text not null default '',
  details text not null default '',
  flags text[] not null default '{}',
  brian_override boolean not null default false,
  manual_rank integer,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.production_board_thoughts (
  id uuid primary key default gen_random_uuid(),
  card_id uuid not null references public.production_board_cards(id) on delete cascade,
  body text not null check (length(trim(body)) between 1 and 10000),
  author text not null default 'Brian',
  created_at timestamptz not null default now()
);

create table public.production_board_activity (
  id bigint generated always as identity primary key,
  card_id uuid not null references public.production_board_cards(id) on delete cascade,
  action text not null,
  detail jsonb not null default '{}'::jsonb,
  actor text not null default 'Brian',
  created_at timestamptz not null default now()
);

create index production_board_cards_lane_rank_idx on public.production_board_cards(lane, brian_override desc, manual_rank, updated_at desc);
create index production_board_thoughts_card_idx on public.production_board_thoughts(card_id, created_at desc);
create index production_board_activity_card_idx on public.production_board_activity(card_id, created_at desc);

alter table public.production_board_cards enable row level security;
alter table public.production_board_thoughts enable row level security;
alter table public.production_board_activity enable row level security;
revoke all on public.production_board_cards, public.production_board_thoughts, public.production_board_activity from anon, authenticated;

insert into public.production_board_cards(title,project,lane,value_score,work_score,summary,flags,brian_override,manual_rank) values
('Tabbed instructor schedule lanes with overlapping cards','Instructor Schedule','doing',10,4,'Show simultaneous work clearly in instructor-specific lanes.',array['CUSTOMER IMPACT'],true,1),
('Registration move/add recalculates public availability','Enrollware / Hot Sync','doing',10,5,'Recompute public inventory immediately after registration changes.',array['BROKEN NOW','BLOCKING','CUSTOMER IMPACT'],false,2),
('Missing Hot Sync / Geosyntec visibility','Enrollware / Hot Sync','doing',9,3,'Make hidden operational commitments visible in the admin workspace.',array['BROKEN NOW','BLOCKING'],false,3),
('Converging location lanes','Instructor Schedule','next',9,4,'Let location lanes converge without hiding conflicts.',array[]::text[],false,null),
('Gap Intelligence','Scheduling','next',10,5,'Surface usable gaps and explain why openings are accepted or rejected.',array['REVENUE'],false,null),
('Persistent instructor/admin schedule workspace','Instructor Schedule','next',10,6,'Create the durable daily scheduling workspace.',array['CUSTOMER IMPACT'],false,null),
('Mobile Enrollware refresh control','Enrollware / Hot Sync','next',7,2,'Make availability refresh practical from a phone.',array['BROKEN NOW'],false,null),
('Group Training email routing','Group Training','next',8,3,'Route group requests reliably to the right operational inbox.',array['CUSTOMER IMPACT','REVENUE'],false,null),
('Maxim Coming Due / Completed 14-day behavior','Maxim','next',9,4,'Keep recent completions visible for 14 days and renewals correctly queued.',array['CUSTOMER IMPACT'],false,null),
('GA4/GTM preservation on new pages','Public Site','next',8,2,'Keep analytics intact as new pages are introduced.',array['REVENUE'],false,null),
('Repeat-gap / family suppression policy review','Scheduling','decision',9,4,'Review policy without eliminating legitimate repeat-gap behavior.',array['BRIAN OVERRIDE'],false,null),
('Group Training provisional self-booking','Group Training','decision',9,6,'Decide guardrails for provisional group self-booking.',array['REVENUE'],false,null),
('Instructor coverage / offer yourself feature','Instructor Schedule','decision',8,6,'Let instructors volunteer for uncovered work with owner review.',array[]::text[],false,null),
('Maxim Trello-style personnel workflow','Maxim','parked',8,7,'Expand the personnel flow into a visual operational workflow.',array[]::text[],false,null),
('Maxim persistent audit history','Maxim','parked',9,5,'Preserve every personnel and registration transition.',array['CUSTOMER IMPACT'],false,null),
('Instructor Session Workspace','Instructor Operations','parked',9,7,'Give instructors a focused per-session workspace.',array[]::text[],false,null),
('Daily instructor completion review queue','Instructor Operations','parked',8,5,'Queue classes needing roster, card, invoice, or completion review.',array[]::text[],false,null),
('AI-ingestion optimization across all public pages','Public Site','parked',8,7,'Improve machine-readable public content without harming conversion.',array[]::text[],false,null),
('Class-occurrence product pages','Public Site','parked',9,8,'Create durable occurrence pages grounded in real inventory.',array['REVENUE'],false,null),
('FAQ / knowledge publishing system','Public Site','parked',7,6,'Publish reusable customer answers and structured knowledge.',array[]::text[],false,null),
('Career-specific CPR/BLS content pages','Public Site','parked',8,6,'Serve focused guidance for career-specific training needs.',array['REVENUE'],false,null),
('Group Training visual redesign','Group Training','parked',7,5,'Improve clarity and conversion of the group training experience.',array['REVENUE'],false,null),
('Location-aware instructor schedule visualization','Instructor Schedule','parked',9,7,'Show travel and location feasibility directly in scheduling lanes.',array[]::text[],false,null);

insert into public.production_board_activity(card_id,action,detail)
select id,'seeded',jsonb_build_object('lane',lane,'value',value_score,'work',work_score) from public.production_board_cards;
