"""Dedicated collector capability proof; source acquisition remains unimplemented."""
import unittest
import uuid
from psycopg import sql
import board_intake_trust_boundary as trust
import board_resolution_contention as foundation


class CollectorCapability(trust.IntakeTrustBoundary):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not cls.admin.execute("select 1 from pg_roles where rolname='production_board_collector'").fetchone():
            cls.admin.execute('create role production_board_collector nologin nosuperuser nocreatedb nocreaterole noreplication nobypassrls')
        cls.admin.execute((foundation.ROOT/'data/audit/issue380_collector_capability_draft.sql').read_text())
        cls.login='issue380_collector_'+uuid.uuid4().hex
        cls.admin.execute(sql.SQL('create role {} login nosuperuser nocreatedb nocreaterole noreplication nobypassrls in role production_board_collector').format(sql.Identifier(cls.login)))

    @classmethod
    def tearDownClass(cls):
        cls.admin.execute(sql.SQL('drop role {}').format(sql.Identifier(cls.login)))
        super().tearDownClass()

    def collector(self):
        conn=self.pg.connect(foundation.DSN,user=self.login)
        conn.execute('set role production_board_collector')
        return conn

    def test_authenticated_collector_write_is_audited_per_transition(self):
        args=self.publication()
        self.publish(args)
        with self.collector() as conn:
            for state in ('action_required','already_corrected'):
                conn.execute("update production_board_dispatch_intake set provenance='authoritative_observation',source_state=%s,checked_at=clock_timestamp() where card_id=%s",(state,args[0]))
        rows=self.admin.execute('select actor,prior,observed,resulting_version from production_board_observation_events where card_id=%s order by resulting_version',(args[0],)).fetchall()
        self.assertEqual(len(rows),2)
        self.assertEqual([r[3] for r in rows],[3,4])
        self.assertTrue(all(r[0]==self.login for r in rows))
        self.assertEqual(rows[0][1]['provenance'],'owner_assertion')
        self.assertEqual(rows[1][1],rows[0][2])
        self.assertEqual(rows[1][2]['source_state'],'already_corrected')
        self.assertFalse(self.call((args[0],args[1],4,uuid.uuid4(),'selection',None))['can_execute'])

    def test_initial_insert_is_audited_and_private_card_text_denied(self):
        args=self.publication()
        with self.collector() as conn:
            conn.execute("""insert into production_board_dispatch_intake
                (card_id,issue_id,blocked,source_state,worker_safe,source_ref,checked_at,provenance)
                values(%s,%s,false,'action_required',false,'synthetic-source',clock_timestamp(),'authoritative_observation')""",args[:2])
        event=self.admin.execute('select actor,prior,observed,resulting_version from production_board_observation_events where card_id=%s',(args[0],)).fetchone()
        self.assertEqual(event[0],self.login)
        self.assertIsNone(event[1])
        self.assertEqual(event[2]['issue_id'],args[1])
        self.assertEqual(event[3],2)
        with self.collector() as conn:
            with self.assertRaises(self.pg.errors.InsufficientPrivilege):
                conn.execute('select title from production_board_cards')
            conn.rollback()
        with self.collector() as conn:
            with self.assertRaises(self.pg.errors.InsufficientPrivilege):
                conn.execute("""insert into production_board_observation_events
                    (card_id,actor,observed,resulting_version) values(%s,'spoofed','{}',2)""",(args[0],))
            conn.rollback()

    def test_collector_audit_failure_rolls_back_observation_and_version(self):
        args=self.publication();self.publish(args)
        self.admin.execute("create function fail_collector_audit() returns trigger language plpgsql as $$ begin raise exception 'collector_audit_failure'; end $$; create trigger fail_collector_audit before insert on production_board_observation_events for each row execute function fail_collector_audit()")
        try:
            with self.assertRaisesRegex(self.pg.Error,'collector_audit_failure'):
                with self.collector() as conn:
                    conn.execute("update production_board_dispatch_intake set provenance='authoritative_observation' where card_id=%s",(args[0],))
        finally:
            self.admin.execute('drop trigger fail_collector_audit on production_board_observation_events; drop function fail_collector_audit()')
        self.assertEqual(self.admin.execute('select row_version from production_board_cards where id=%s',(args[0],)).fetchone()[0],2)
        self.assertEqual(self.admin.execute('select provenance from production_board_dispatch_intake where card_id=%s',(args[0],)).fetchone()[0],'owner_assertion')
        self.assertEqual(self.admin.execute('select count(*) from production_board_observation_events where card_id=%s',(args[0],)).fetchone()[0],0)

    def test_capability_cannot_resolve_delete_rewrite_audit_or_escalate(self):
        args=self.publication();self.publish(args)
        statements=[
            "update production_board_cards set resolution_state='handled_manually'",
            'delete from production_board_dispatch_intake',
            'update production_board_observation_events set actor=current_user',
            'delete from production_board_observation_events',
            'set role service_role',
            "set session_replication_role='replica'",
        ]
        for statement in statements:
            with self.subTest(statement=statement), self.collector() as conn:
                with self.assertRaises(self.pg.errors.InsufficientPrivilege):
                    conn.execute(statement)
                conn.rollback()
        with self.pg.connect(foundation.DSN,user=self.login,autocommit=True) as conn:
            conn.execute('reset role')
            self.assertEqual(conn.execute('select session_user').fetchone()[0],self.login)
        routine='issue380_routine_'+uuid.uuid4().hex
        self.admin.execute(sql.SQL('create role {} login nosuperuser nocreatedb nocreaterole noreplication nobypassrls in role service_role').format(sql.Identifier(routine)))
        try:
            with self.pg.connect(foundation.DSN,user=routine) as conn:
                conn.execute('set role service_role')
                with self.assertRaises(self.pg.errors.InsufficientPrivilege):
                    conn.execute('set role production_board_collector')
                conn.rollback()
        finally:
            self.admin.execute(sql.SQL('drop role {}').format(sql.Identifier(routine)))


if __name__=='__main__':
    if not foundation.DSN:
        raise SystemExit('BLOCKED: explicit disposable ISSUE380_TEST_DSN required')
    unittest.main(verbosity=2)
