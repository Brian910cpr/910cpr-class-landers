"""Exclusive gateway proof; no source attestation or production role provisioning."""
import unittest
import uuid
import board_collector_publication as publication
import board_resolution_contention as foundation


class CollectorGateway(publication.CollectorPublication):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not cls.admin.execute("select 1 from pg_roles where rolname='production_board_collector_executor'").fetchone():
            cls.admin.execute('create role production_board_collector_executor nologin nosuperuser nocreatedb nocreaterole noreplication nobypassrls')
        cls.admin.execute((foundation.ROOT/'data/audit/issue380_collector_gateway_draft.sql').read_text())
        publication.CALL='select production_board_private.production_board_publish_observation(%s,%s,%s,%s,%s,%s,%s,%s,%s)'

    def race_publication(self,args,second,second_sql=None,collector_second=True,rollback=False):
        return super().race_publication(args,second,second_sql or publication.CALL,collector_second,rollback)

    def test_authenticated_collector_write_is_audited_per_transition(self):
        args=self.publication();self.publish(args)
        self.observe((*args[:2],2,uuid.uuid4(),*args[4:]))
        self.observe((*args[:2],3,uuid.uuid4(),args[4],'already_corrected',*args[6:]))
        rows=self.admin.execute('select actor,prior,observed,resulting_version from production_board_observation_events where card_id=%s order by resulting_version',(args[0],)).fetchall()
        self.assertEqual([r[3] for r in rows],[3,4])
        self.assertTrue(all(r[0]==self.login for r in rows))
        self.assertEqual(rows[0][1]['provenance'],'owner_assertion')
        self.assertEqual(rows[1][1],rows[0][2])
        self.assertEqual(rows[1][2]['source_state'],'already_corrected')

    def test_initial_insert_is_audited_and_private_card_text_denied(self):
        args=self.publication();self.observe(args)
        event=self.admin.execute('select actor,prior,resulting_version from production_board_observation_events where card_id=%s',(args[0],)).fetchone()
        self.assertEqual(event,(self.login,None,2))
        for statement in ('select title from production_board_cards',
            "insert into production_board_observation_events(card_id,actor,observed,resulting_version) values(gen_random_uuid(),session_user,'{}',2)"):
            with self.collector() as conn:
                with self.assertRaises(self.pg.errors.InsufficientPrivilege):conn.execute(statement)
                conn.rollback()

    def test_collector_audit_failure_rolls_back_observation_and_version(self):
        args=self.publication();self.publish(args)
        self.admin.execute("create function fail_collector_audit() returns trigger language plpgsql as $$ begin raise exception 'collector_audit_failure'; end $$; create trigger fail_collector_audit before insert on production_board_observation_events for each row execute function fail_collector_audit()")
        try:
            with self.assertRaisesRegex(self.pg.Error,'collector_audit_failure'):
                self.observe((*args[:2],2,uuid.uuid4(),*args[4:]))
        finally:self.admin.execute('drop trigger fail_collector_audit on production_board_observation_events; drop function fail_collector_audit()')
        self.assertEqual(self.admin.execute('select row_version from production_board_cards where id=%s',(args[0],)).fetchone()[0],2)
        self.assertEqual(self.admin.execute('select provenance from production_board_dispatch_intake where card_id=%s',(args[0],)).fetchone()[0],'owner_assertion')
        for table in ('production_board_observation_events','production_board_collector_publications'):
            self.assertEqual(self.admin.execute(f'select count(*) from {table} where card_id=%s',(args[0],)).fetchone()[0],0)

    def test_raw_writes_and_executor_escalation_denied(self):
        args=self.publication();self.observe(args)
        statements=[
            "insert into production_board_dispatch_intake(card_id,issue_id) values(gen_random_uuid(),1)",
            "update production_board_dispatch_intake set checked_at=clock_timestamp()",
            "update production_board_cards set updated_at=clock_timestamp()",
            "insert into production_board_collector_publications(request_id,card_id,actor,request,resulting_version) values(gen_random_uuid(),gen_random_uuid(),session_user,'{}',2)",
            'set role production_board_collector_executor',
            'alter function production_board_private.production_board_publish_observation(uuid,bigint,bigint,uuid,boolean,text,boolean,text,timestamptz) security invoker',
            "create function public.gateway_spoof() returns int language sql as 'select 1'",
        ]
        for statement in statements:
            with self.subTest(statement=statement),self.collector() as conn:
                with self.assertRaises(self.pg.errors.InsufficientPrivilege):conn.execute(statement)
                conn.rollback()
        self.assertTrue(self.observe(args)['replayed'])
        self.assertFalse(self.observe(args)['can_execute'])


if __name__=='__main__':
    if not foundation.DSN:raise SystemExit('BLOCKED: explicit disposable ISSUE380_TEST_DSN required')
    unittest.main(verbosity=2)
