"""Disposable PostgreSQL typed publication/dispatch integration proof."""
import concurrent.futures
import unittest
import uuid
import board_dispatch_transaction as dispatch
import board_resolution_contention as foundation

PUBLISH='select production_board_publish_intake(%s,%s,%s,%s,%s,%s,%s,%s,%s)'

class IntakePublication(dispatch.DispatchTransaction):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin.execute((foundation.ROOT/'data/audit/issue380_intake_publication_draft.sql').read_text())

    def publication(self, card=None, issue=None, version=1):
        card=card or self.admin.execute("insert into production_board_cards(title) values('Publication fixture') returning id").fetchone()[0]
        issue=issue or self.admin.execute('select coalesce(max(issue_id),1000)+1 from production_board_dispatch_intake').fetchone()[0]
        now=self.admin.execute('select clock_timestamp()').fetchone()[0]
        return (card,issue,version,uuid.uuid4(),True,'unknown',False,'synthetic-owner-assertion',now)

    def publish(self,args):
        with self.pg.connect(foundation.DSN) as conn:
            conn.execute('set role service_role')
            result=conn.execute(PUBLISH,args).fetchone()[0]
            conn.commit()
            return result

    def test_publication_create_update_replay_conflict(self):
        args=self.publication()
        self.assertEqual(self.publish(args)['version'],'2')
        self.assertTrue(self.publish(args)['replayed'])
        self.assertEqual(self.admin.execute('select row_version from production_board_cards where id=%s',(args[0],)).fetchone()[0],2)
        with self.assertRaisesRegex(self.pg.Error,'idempotency_conflict'):
            self.publish((*args[:4],False,*args[5:]))
        updated=(*args[:2],2,uuid.uuid4(),False,'action_required',True,*args[7:])
        self.assertEqual(self.publish(updated)['version'],'3')
        rows=self.admin.execute("select detail from production_board_activity where card_id=%s and action='intake_published' order by created_at",(args[0],)).fetchall()
        self.assertEqual(len(rows),2)
        self.assertIsNone(rows[0][0]['prior'])
        self.assertTrue(rows[1][0]['prior']['blocked'])
        self.assertEqual(rows[1][0]['provenance'],'owner_assertion_not_source_verification')

    def test_publication_rejects_stale_resolved_identity_and_time(self):
        args=self.publication();self.publish(args)
        with self.assertRaisesRegex(self.pg.Error,'stale_card_version'):
            self.publish((*args[:3],uuid.uuid4(),*args[4:]))
        with self.assertRaisesRegex(self.pg.Error,'intake_issue_immutable'):
            self.publish((args[0],args[1]+1,2,uuid.uuid4(),*args[4:]))
        old=self.admin.execute("select clock_timestamp()-interval '6 minutes'").fetchone()[0]
        with self.assertRaisesRegex(self.pg.Error,'source_check_stale'):
            self.publish((*args[:2],2,uuid.uuid4(),*args[4:8],old))
        with self.pg.connect(foundation.DSN) as owner:
            owner.execute('set role service_role')
            owner.execute(foundation.CALL,(args[0],2,uuid.uuid4(),'owner-fixture','handled_manually','Fixed externally','synthetic',args[8]))
        with self.assertRaisesRegex(self.pg.Error,'card_resolved'):
            self.publish((*args[:2],3,uuid.uuid4(),*args[4:]))
        self.assertEqual(self.admin.execute('select count(*) from production_board_intake_publications where card_id=%s',(args[0],)).fetchone()[0],1)

    def test_publication_audit_failure_atomic_rollback_and_retry(self):
        args=self.publication()
        self.admin.execute("""create function fail_publication() returns trigger language plpgsql as $$ begin
        if new.action='intake_published' then raise exception 'publication_audit_failure'; end if; return new; end $$;
        create trigger fail_publication before insert on production_board_activity for each row execute function fail_publication();""")
        try:
            with self.assertRaisesRegex(self.pg.Error,'publication_audit_failure'):self.publish(args)
            self.assertEqual(self.admin.execute('select row_version from production_board_cards where id=%s',(args[0],)).fetchone()[0],1)
            self.assertEqual(self.admin.execute('select count(*) from production_board_dispatch_intake where card_id=%s',(args[0],)).fetchone()[0],0)
            self.assertEqual(self.admin.execute('select count(*) from production_board_intake_publications where request_id=%s',(args[3],)).fetchone()[0],0)
        finally:self.admin.execute('drop trigger fail_publication on production_board_activity; drop function fail_publication()')
        self.assertFalse(self.publish(args)['replayed'])

    def test_owner_assertion_cannot_become_authoritative_reservation(self):
        args=self.publication()
        args=(*args[:4],False,'action_required',True,*args[7:])
        self.publish(args)
        result=self.call((args[0],args[1],2,uuid.uuid4(),'selection',None))
        self.assertEqual(result['decision'],'review')
        self.assertEqual(result['reason'],'authoritative_source_check_required')
        self.assertFalse(result['can_execute'])
        self.assertEqual(self.admin.execute('select provenance from production_board_dispatch_intake where card_id=%s',(args[0],)).fetchone()[0],'owner_assertion')

    def test_owner_republication_downgrades_previous_source_observation(self):
        args=self.fixture()
        self.assertEqual(self.call(args)['decision'],'reserved')
        publication=self.publication(args[0],args[1],2)
        publication=(*publication[:4],False,'action_required',True,*publication[7:])
        self.publish(publication)
        result=self.call((args[0],args[1],3,uuid.uuid4(),'selection',None))
        self.assertEqual(result['reason'],'authoritative_source_check_required')
        self.assertEqual(result['decision'],'review')
        prior=self.call((*args[:3],uuid.uuid4(),'pre_side_effect',args[3]))
        self.assertEqual(prior['reason'],'stale_card_version')
        self.assertFalse(prior['can_execute'])

    def test_publication_roles(self):
        args=self.publication()
        for role in ('anon','authenticated'):
            with self.pg.connect(foundation.DSN) as conn:
                conn.execute(f'set role {role}')
                with self.assertRaisesRegex(self.pg.Error,'permission denied'):conn.execute(PUBLISH,args)
        with self.pg.connect(foundation.DSN) as conn:
            conn.execute('set role service_role')
            with self.assertRaisesRegex(self.pg.Error,'permission denied'):conn.execute('delete from production_board_intake_publications')

    def test_publication_competing_first_publishers(self):
        args=self.publication()
        with self.pg.connect(foundation.DSN) as a,self.pg.connect(foundation.DSN) as b:
            for conn in (a,b):
                conn.execute('set role service_role');conn.execute("set statement_timeout='8s'");conn.commit()
            a.execute(PUBLISH,args)
            def contender():
                try:b.execute(PUBLISH,(*args[:3],uuid.uuid4(),*args[4:]));b.commit()
                except self.pg.Error as exc:b.rollback();return str(exc)
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pending=pool.submit(contender)
                try:
                    self.wait_for_lock(b,pending);a.commit()
                    self.assertIn('stale_card_version',pending.result(timeout=10))
                finally:a.rollback()
        self.assertEqual(self.admin.execute('select count(*) from production_board_intake_publications where card_id=%s',(args[0],)).fetchone()[0],1)

    def test_publication_then_dispatch_waits_and_rechecks(self):
        args=self.fixture();publication=self.publication(args[0],args[1],2)
        with self.pg.connect(foundation.DSN) as a,self.pg.connect(foundation.DSN) as b:
            for conn in (a,b):
                conn.execute('set role service_role');conn.execute("set statement_timeout='8s'");conn.commit()
            a.execute(PUBLISH,publication)
            def contender():
                value=b.execute(dispatch.CALL,args).fetchone()[0];b.commit();return value
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pending=pool.submit(contender)
                try:
                    self.wait_for_lock(b,pending);a.commit()
                    self.assertEqual(pending.result(timeout=10)['reason'],'stale_card_version')
                finally:a.rollback()
        self.assertEqual(self.call((args[0],args[1],3,uuid.uuid4(),'selection',None))['decision'],'skip')

    def test_dispatch_then_publication_invalidates_pre_side_effect(self):
        args=self.fixture();publication=self.publication(args[0],args[1],2)
        with self.pg.connect(foundation.DSN) as a,self.pg.connect(foundation.DSN) as b:
            for conn in (a,b):
                conn.execute('set role service_role');conn.execute("set statement_timeout='8s'");conn.commit()
            a.execute(dispatch.CALL,args)
            def contender():
                value=b.execute(PUBLISH,publication).fetchone()[0];b.commit();return value
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pending=pool.submit(contender)
                try:
                    self.wait_for_lock(b,pending);a.commit()
                    self.assertEqual(pending.result(timeout=10)['version'],'3')
                finally:a.rollback()
        check=self.call((*args[:3],uuid.uuid4(),'pre_side_effect',args[3]))
        self.assertEqual(check['reason'],'stale_card_version');self.assertFalse(check['can_execute'])

if __name__=='__main__':
    if not foundation.DSN:raise SystemExit('BLOCKED: explicit disposable ISSUE380_TEST_DSN required')
    unittest.main(verbosity=2)
