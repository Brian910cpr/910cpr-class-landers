"""Local security review of the unapplied resolution draft.

Uses the contention harness's explicit loopback/empty-database safety gates.
The bypass reproducer records an OPEN rollout blocker, not secure behavior.
No production connection, migration, credential or HTTP auth is exercised.
"""
import unittest

from board_resolution_contention import DSN, CALL, ResolutionContention, TargetSafety


class ResolutionSecurity(ResolutionContention):
    def denied(self, role, statement, params=()):
        with self.pg.connect(DSN, autocommit=True, connect_timeout=5) as conn:
            conn.execute(f'set role {role}')
            with self.assertRaises(self.pg.errors.InsufficientPrivilege):
                conn.execute(statement, params)

    def test_untrusted_roles_cannot_read_write_or_invoke(self):
        args = self.args()
        for role in ('anon', 'authenticated'):
            for statement, params in (
                (CALL, args),
                ('select * from production_board_resolution_events', ()),
                ('select * from production_board_cards', ()),
                ("update production_board_cards set resolution_state='handled_manually' where id=%s", (args[0],)),
                ('delete from production_board_resolution_events', ()),
                ('truncate production_board_resolution_events', ()),
                ("insert into production_board_resolution_events(request_id,card_id,actor,request,prior_state,new_state,resulting_version) values(%s,%s,'forged','{}','unresolved','handled_manually',2)", (args[2], args[0])),
            ):
                with self.subTest(role=role, statement=statement):
                    self.denied(role, statement, params)
        self.assertEqual(self.admin.execute('select row_version from production_board_cards where id=%s', (args[0],)).fetchone()[0], 1)

    def test_service_event_history_cannot_update_delete_truncate(self):
        args = self.args()
        with self.pg.connect(DSN, autocommit=True) as conn:
            conn.execute('set role service_role')
            conn.execute(CALL, args)
        for statement in ("update production_board_resolution_events set actor='rewritten'", 'delete from production_board_resolution_events', 'truncate production_board_resolution_events'):
            self.denied('service_role', statement)
        self.assert_effects(args[0], 1)

    def test_rls_still_denies_rows_if_untrusted_select_accidentally_granted(self):
        # Transaction-scoped synthetic misgrant; rolled back, never persisted.
        with self.pg.connect(DSN) as conn:
            for role in ('anon', 'authenticated'):
                conn.execute(f'grant select on production_board_resolution_events to {role}')
                conn.execute(f'set local role {role}')
                self.assertEqual(conn.execute('select count(*) from production_board_resolution_events').fetchone()[0], 0)
                conn.execute('reset role')
            conn.rollback()

    def test_functions_are_invoker_with_fixed_search_path(self):
        rows = self.admin.execute("select proname,prosecdef,proconfig from pg_proc where oid in ('public.production_board_resolve(uuid,bigint,uuid,text,text,text,text,timestamptz)'::regprocedure,'public.production_board_bump_version()'::regprocedure)").fetchall()
        self.assertEqual(len(rows), 2)
        for name, definer, config in rows:
            self.assertFalse(definer, name)
            self.assertIn('search_path=""', config)

    def test_open_blocker_service_direct_write_bypasses_resolution_audit(self):
        args = self.args()
        with self.pg.connect(DSN, autocommit=True) as conn:
            conn.execute('set role service_role')
            conn.execute("update production_board_cards set resolution_state='handled_manually', row_version=900 where id=%s", (args[0],))
        self.assertEqual(self.admin.execute('select row_version,resolution_state from production_board_cards where id=%s', (args[0],)).fetchone(), (2, 'handled_manually'))
        for table in ('production_board_resolution_events', 'production_board_activity'):
            self.assertEqual(self.admin.execute(f'select count(*) from {table} where card_id=%s', (args[0],)).fetchone()[0], 0)
        print('OPEN SECURITY GATE: service_role direct card UPDATE resolves without event/activity; version trigger alone is not an audit boundary', flush=True)


if __name__ == '__main__':
    if not DSN:
        raise SystemExit('BLOCKED: explicit disposable ISSUE380_TEST_DSN required; no security proof ran')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TargetSafety)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(ResolutionSecurity))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
