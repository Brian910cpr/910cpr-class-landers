"""Local-only collector publisher proof; inherited empty-loopback target guard."""
import concurrent.futures
import unittest
import uuid
import board_collector_capability as capability
import board_intake_publication as owner
import board_dispatch_transaction as dispatch
import board_resolution_contention as foundation

CALL='select production_board_publish_observation(%s,%s,%s,%s,%s,%s,%s,%s,%s)'


class CollectorPublication(capability.CollectorCapability):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin.execute((foundation.ROOT/'data/audit/issue380_collector_publication_draft.sql').read_text())

    def observe(self,args):
        with self.collector() as conn:
            result=conn.execute(CALL,args).fetchone()[0]
            conn.commit()  # Do not acknowledge a provisional SQL return.
            return dict(result,committed=True)

    def race_publication(self,args,second,second_sql=CALL,collector_second=True,rollback=False):
        with self.collector() as a, (self.collector() if collector_second else self.pg.connect(foundation.DSN)) as b:
            if not collector_second:b.execute('set role service_role')
            for conn in (a,b):
                conn.execute("set statement_timeout='8s'");conn.commit()
            a.execute(CALL,args)
            def contender():
                try:
                    result=b.execute(second_sql,second).fetchone()[0];b.commit();return result
                except self.pg.Error as exc:
                    b.rollback();return str(exc)
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pending=pool.submit(contender)
                try:
                    self.wait_for_lock(b,pending)
                    a.rollback() if rollback else a.commit()
                    return pending.result(timeout=10)
                finally:a.rollback()

    def test_collector_publication_replay_conflict_and_audit(self):
        args=self.publication()
        result=self.observe(args)
        self.assertTrue(result['committed']);self.assertFalse(result['can_execute'])
        self.assertEqual(result['version'],'2')
        self.assertTrue(self.observe(args)['replayed'])
        with self.assertRaisesRegex(self.pg.Error,'idempotency_conflict'):
            self.observe((*args[:4],False,*args[5:]))
        row=self.admin.execute('select actor,request,resulting_version from production_board_collector_publications where request_id=%s',(args[3],)).fetchone()
        self.assertEqual(row[0],self.login);self.assertEqual(row[1]['actor'],self.login)
        self.assertEqual(row[2],2)
        self.assertEqual(self.admin.execute('select count(*) from production_board_observation_events where card_id=%s',(args[0],)).fetchone()[0],1)

    def test_collector_first_publication_contention_replay_stale_and_rollback(self):
        args=self.publication()
        self.assertTrue(self.race_publication(args,args)['replayed'])
        args=self.publication()
        self.assertIn('stale_card_version',self.race_publication(args,(*args[:3],uuid.uuid4(),*args[4:])))
        args=self.publication()
        self.assertFalse(self.race_publication(args,args,rollback=True)['replayed'])
        self.assertEqual(self.admin.execute('select count(*) from production_board_observation_events where card_id=%s',(args[0],)).fetchone()[0],1)

    def test_collector_serializes_owner_and_dispatch(self):
        args=self.publication()
        self.assertIn('stale_card_version',self.race_publication(args,(*args[:3],uuid.uuid4(),*args[4:]),owner.PUBLISH,False))
        args=self.publication()
        result=self.race_publication(args,(args[0],args[1],1,uuid.uuid4(),'selection',None),dispatch.CALL,False)
        self.assertEqual(result['reason'],'stale_card_version');self.assertFalse(result['can_execute'])
        # Owner wins first: collector waits and rejects the stale version.
        args=self.publication()
        with self.pg.connect(foundation.DSN) as a,self.collector() as b:
            a.execute('set role service_role');a.execute(owner.PUBLISH,args)
            b.execute("set statement_timeout='8s'");b.commit()
            def contender():
                try:b.execute(CALL,(*args[:3],uuid.uuid4(),*args[4:]));b.commit()
                except self.pg.Error as exc:b.rollback();return str(exc)
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pending=pool.submit(contender)
                try:self.wait_for_lock(b,pending);a.commit();self.assertIn('stale_card_version',pending.result(timeout=10))
                finally:a.rollback()

    def test_collector_rejects_invalid_stale_resolved_identity_and_time(self):
        args=self.publication();self.observe(args)
        for invalid,reason in [
            ((*args[:3],uuid.uuid4(),*args[4:]),'stale_card_version'),
            ((args[0],args[1]+1,2,uuid.uuid4(),*args[4:]),'intake_issue_immutable'),
            ((*args[:2],2,uuid.uuid4(),*args[4:7],'',args[8]),'invalid_intake_request'),
            ((*args[:2],2,uuid.uuid4(),*args[4:8],self.admin.execute("select clock_timestamp()-interval '6 minutes'").fetchone()[0]),'source_check_stale'),
        ]:
            with self.subTest(reason=reason),self.assertRaisesRegex(self.pg.Error,reason):self.observe(invalid)
        with self.pg.connect(foundation.DSN) as conn:
            conn.execute('set role service_role')
            conn.execute(foundation.CALL,(args[0],2,uuid.uuid4(),'owner-fixture','handled_manually','Fixed externally','synthetic',args[8]))
        with self.assertRaisesRegex(self.pg.Error,'card_resolved'):
            self.observe((*args[:2],3,uuid.uuid4(),*args[4:]))
        # Historical replay must not be interpreted as fresh eligibility.
        self.assertTrue(self.observe(args)['replayed'])
        self.assertFalse(self.observe(args)['can_execute'])

    def test_collector_provisional_response_and_receipt_failure_roll_back(self):
        args=self.publication()
        with self.collector() as conn:
            result=conn.execute(CALL,args).fetchone()[0]
            self.assertNotIn('committed',result)
            self.assertEqual(self.admin.execute('select count(*) from production_board_collector_publications where request_id=%s',(args[3],)).fetchone()[0],0)
            conn.rollback()
        self.admin.execute("create function fail_collector_receipt() returns trigger language plpgsql as $$ begin raise exception 'collector_receipt_failure'; end $$; create trigger fail_collector_receipt before insert on production_board_collector_publications for each row execute function fail_collector_receipt()")
        try:
            with self.assertRaisesRegex(self.pg.Error,'collector_receipt_failure'):self.observe(args)
            self.assertEqual(self.admin.execute('select row_version from production_board_cards where id=%s',(args[0],)).fetchone()[0],1)
            for table in ('production_board_dispatch_intake','production_board_observation_events','production_board_collector_publications'):
                self.assertEqual(self.admin.execute(f'select count(*) from {table} where card_id=%s',(args[0],)).fetchone()[0],0)
        finally:self.admin.execute('drop trigger fail_collector_receipt on production_board_collector_publications; drop function fail_collector_receipt()')
        self.assertFalse(self.observe(args)['replayed'])

    def test_collector_publisher_roles_and_receipt_immutability(self):
        args=self.publication();self.observe(args)
        for role in ('anon','authenticated','service_role'):
            with self.pg.connect(foundation.DSN) as conn:
                conn.execute(f'set role {role}')
                with self.assertRaises(self.pg.errors.InsufficientPrivilege):conn.execute(CALL,args)
                conn.rollback()
        for statement in ('update production_board_collector_publications set actor=current_user','delete from production_board_collector_publications'):
            with self.collector() as conn:
                with self.assertRaises(self.pg.errors.InsufficientPrivilege):conn.execute(statement)
                conn.rollback()


if __name__=='__main__':
    if not foundation.DSN:raise SystemExit('BLOCKED: explicit disposable ISSUE380_TEST_DSN required')
    unittest.main(verbosity=2)
