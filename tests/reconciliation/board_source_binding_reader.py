"""Canonical binding reader proof on guarded disposable local PostgreSQL."""
import unittest
import uuid
import board_collector_gateway as gateway
import board_resolution_contention as foundation

READ='select production_board_private.production_board_read_source_binding(%s)'


class SourceBindingReader(gateway.CollectorGateway):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin.execute((foundation.ROOT/'data/audit/issue380_source_binding_reader_draft.sql').read_text())

    def read_binding(self,card):
        with self.collector() as conn:
            return conn.execute(READ,(card,)).fetchone()[0]

    def test_reader_binds_identity_without_private_text_or_arbitrary_url(self):
        args=self.publication();args=(args[0],380,*args[2:]);self.publish(args)
        self.admin.execute("update production_board_cards set title='SECRET' where id=%s",(args[0],))
        before=self.admin.execute('select row_version from production_board_cards where id=%s',(args[0],)).fetchone()[0]
        result=self.read_binding(args[0])
        self.assertEqual(result,dict(decision='review',reason='underlying_source_check_required',can_execute=False,
            card_id=str(args[0]),issue_id=args[1],version=str(before),
            source_ref=f'https://github.com/Brian910cpr/910cpr-class-landers/issues/{args[1]}'))
        self.assertNotIn('SECRET',str(result))
        self.assertNotEqual(result['source_ref'],args[7])
        self.assertEqual(self.admin.execute('select row_version from production_board_cards where id=%s',(args[0],)).fetchone()[0],before)

    def test_missing_resolved_and_unsupported_bindings_fail_closed(self):
        args=self.publication()
        for card in (args[0],uuid.uuid4()):
            self.assertEqual(self.read_binding(card),dict(decision='review',reason='canonical_binding_missing',can_execute=False))
        self.publish(args)
        self.admin.execute(foundation.CALL,(args[0],2,uuid.uuid4(),'owner','handled_manually','external fix','fixture',args[8]))
        self.assertEqual(self.read_binding(args[0]),dict(decision='skip',reason='card_resolved',can_execute=False))
        large=self.publication();self.publish((large[0],9007199254740992,*large[2:]))
        self.assertEqual(self.read_binding(large[0])['reason'],'unsupported_issue_identity')
        with self.assertRaisesRegex(self.pg.Error,'invalid_card_id'):self.read_binding(None)

    def test_binding_is_not_lease_publisher_rejects_new_version(self):
        args=self.publication();self.publish(args)
        snapshot=self.read_binding(args[0]);self.assertEqual(snapshot['version'],'2')
        self.publish((*args[:2],2,uuid.uuid4(),*args[4:]))
        with self.assertRaisesRegex(self.pg.Error,'stale_card_version'):
            self.observe((*args[:2],int(snapshot['version']),uuid.uuid4(),*args[4:]))
        self.assertEqual(self.read_binding(args[0])['version'],'3')

    def test_reader_denies_routine_roles_and_preserves_rls(self):
        args=self.publication();self.publish(args)
        for role in ('anon','authenticated','service_role'):
            with self.pg.connect(foundation.DSN) as conn:
                conn.execute('set role '+role)
                with self.assertRaises(self.pg.errors.InsufficientPrivilege):conn.execute(READ,(args[0],))
                conn.rollback()
        self.admin.execute('drop policy collector_intake_read on production_board_dispatch_intake')
        try:self.assertEqual(self.read_binding(args[0])['reason'],'canonical_binding_missing')
        finally:self.admin.execute('create policy collector_intake_read on production_board_dispatch_intake for select to production_board_collector using(true)')


    def test_publisher_requires_mapping_and_exact_source_identity(self):
        signature='production_board_private.production_board_publish_observation(uuid,bigint,bigint,uuid,boolean,text,boolean,text,timestamptz)'
        baseline=self.admin.execute('select pg_get_functiondef(%s::regprocedure)',(signature,)).fetchone()[0]
        self.admin.execute((foundation.ROOT/'data/audit/issue380_publisher_source_binding_draft.sql').read_text())
        try:
            issue=self.admin.execute('select coalesce(max(issue_id),1000)+1 from production_board_dispatch_intake where issue_id<1000000').fetchone()[0]
            args=self.publication(issue=issue)
            ref=f'https://github.com/Brian910cpr/910cpr-class-landers/issues/{issue}'
            request=(*args[:7],ref,args[8])
            with self.assertRaisesRegex(self.pg.Error,'collector_source_binding_required'):self.observe(request)
            self.assertEqual(self.admin.execute('select row_version from production_board_cards where id=%s',args[:1]).fetchone()[0],1)
            self.publish(args)
            request=(*request[:2],2,*request[3:])
            for source in ('https://example.invalid/issues/380',ref+'?x=1',ref+'/',ref+'/371',ref.upper()):
                with self.subTest(source=source),self.assertRaisesRegex(self.pg.Error,'collector_source_identity_mismatch'):
                    self.observe((*request[:7],source,request[8]))
            self.assertEqual(self.admin.execute('select row_version from production_board_cards where id=%s',args[:1]).fetchone()[0],2)
            for table in ('production_board_observation_events','production_board_collector_publications'):
                self.assertEqual(self.admin.execute(f'select count(*) from {table} where card_id=%s',args[:1]).fetchone()[0],0)
            result=self.observe(request)
            self.assertEqual(result['version'],'3');self.assertFalse(result['can_execute'])
            self.assertTrue(self.observe(request)['replayed'])
            with self.assertRaisesRegex(self.pg.Error,'idempotency_conflict'):
                self.observe((*request[:7],ref+'/',request[8]))
            large=self.publication();self.assertGreater(large[1],9007199254740991);self.publish(large)
            with self.assertRaisesRegex(self.pg.Error,'collector_source_identity_mismatch'):
                self.observe((*large[:2],2,uuid.uuid4(),*large[4:7],ref,large[8]))
        finally:
            self.admin.execute(baseline)


if __name__=='__main__':
    if not foundation.DSN:raise SystemExit('BLOCKED: explicit disposable ISSUE380_TEST_DSN required')
    unittest.main(verbosity=2)
