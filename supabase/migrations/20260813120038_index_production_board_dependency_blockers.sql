create index if not exists production_board_dependencies_blocker_idx
  on public.production_board_dependencies(blocker_card_id);
