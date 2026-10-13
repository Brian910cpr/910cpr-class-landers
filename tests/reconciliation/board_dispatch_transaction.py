"""Isolated real PostgreSQL dispatch proof; inherits the strict empty/local guard."""
import concurrent.futures
import time
import unittest
import uuid
import board_resolution_contention as foundation

CALL = 'select production_board_dispatch_decide(%s,%s,%s,%s,%s,%s)'


class DispatchTransaction(foundation.ResolutionContention):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin.execute((foundation.ROOT / 'data/audit/issue380_dispatch_transaction_draft.sql').read_text())

    def fixture(self, blocked=False, source='action_required', safe=True):
        card = self.admin.execute("insert into production_board_cards(title) values ('Dispatch fixture') returning id").fetchone()[0]
        issue = self.admin.execute('select coalesce(max(issue_id),296)+1 from production_board_dispatch_intake').fetchone()[0]
        self.admin.execute("insert into production_board_dispatch_intake values(%s,%s,%s,%s,%s,%s,clock_timestamp(),'authoritative_observation')",
                           (card, issue, blocked, source, safe, 'synthetic-authoritative-fixture'))
        return (card, issue, 2, uuid.uuid4(), 'selection', None)

    def call(self, args):
        with self.pg.connect(foundation.DSN) as conn:
            conn.execute('set role service_role')
            value = conn.execute(CALL, args).fetchone()[0]
            conn.commit()  # only return after deferred checks and commit
            return value

    def test_dispatch_reservation_replay_and_conflict(self):
        args = self.fixture()
        first = self.call(args)
        self.assertEqual(first['decision'], 'reserved')
        self.assertFalse(first['can_execute'])
        self.assertTrue(self.call(args)['replayed'])
        with self.assertRaisesRegex(self.pg.Error, 'idempotency_conflict'):
            self.call((*args[:4], 'pre_side_effect', uuid.uuid4()))
        other = (*args[:3], uuid.uuid4(), *args[4:])
        self.assertEqual(self.call(other)['reason'], 'reservation_active')
        check = (*args[:3], uuid.uuid4(), 'pre_side_effect', args[3])
        self.assertEqual(self.call(check)['reason'], 'runtime_fence_required')
        self.assertFalse(self.call(check)['can_execute'])

    def test_dispatch_resolution_between_checks_skips(self):
        args = self.fixture()
        self.call(args)
        with self.pg.connect(foundation.DSN) as owner:
            owner.execute('set role service_role')
            owner.execute(foundation.CALL, (args[0],2,uuid.uuid4(),'owner-fixture','handled_manually',
                                           'Fixed externally','fixture','2026-10-13T00:00:00Z'))
        result = self.call((*args[:3],uuid.uuid4(),'pre_side_effect',args[3]))
        self.assertEqual(result['decision'], 'skip')
        self.assertEqual(result['reason'], 'recorded_resolution')
        self.assertFalse(result['can_execute'])
        self.assertEqual(self.admin.execute("select count(*) from production_board_activity where card_id=%s and action='dispatch_decision'",(args[0],)).fetchone()[0],2)

    def test_dispatch_canonical_gates(self):
        for blocked, source, safe, reason in [
            (True,'action_required',True,'blocked_requires_explicit_reconciliation'),
            (False,'already_corrected',True,'propose_verified_resolved'),
            (False,'unknown',True,'authoritative_source_check_required'),
            (False,'action_required',False,'worker_safe_opt_in_required')]:
            args = self.fixture(blocked, source, safe)
            self.assertEqual(self.call(args)['reason'],reason)
        args = self.fixture()
        self.assertEqual(self.call((args[0],args[1]+1000,*args[2:]))['reason'],'canonical_intake_required')
        self.assertEqual(self.call((args[0],args[1],1,uuid.uuid4(),*args[4:]))['reason'],'stale_card_version')

    def test_dispatch_intake_change_invalidates_reservation(self):
        args = self.fixture()
        self.call(args)
        self.admin.execute('update production_board_dispatch_intake set blocked=true where card_id=%s',(args[0],))
        result = self.call((*args[:3],uuid.uuid4(),'pre_side_effect',args[3]))
        self.assertEqual(result['reason'],'stale_card_version')
        self.assertFalse(result['can_execute'])

    def test_dispatch_intake_identity_cannot_move(self):
        args = self.fixture()
        other = self.admin.execute("insert into production_board_cards(title) values ('Identity fixture') returning id").fetchone()[0]
        with self.assertRaisesRegex(self.pg.Error,'dispatch_intake_identity_immutable'):
            self.admin.execute('update production_board_dispatch_intake set card_id=%s where card_id=%s',(other,args[0]))
        self.assertEqual(self.admin.execute('select row_version from production_board_cards where id=%s',(args[0],)).fetchone()[0],2)

    def test_dispatch_stale_source_and_expired_lease(self):
        args = self.fixture()
        self.admin.execute("update production_board_dispatch_intake set checked_at=clock_timestamp()-interval '6 minutes' where card_id=%s",(args[0],))
        self.assertEqual(self.call((args[0],args[1],3,*args[3:]))['reason'],'source_check_stale')
        args = self.fixture()
        self.call(args)
        # Superuser fixture time travel only; service_role cannot edit decisions.
        self.admin.execute("update production_board_dispatch_decisions set lease_until=clock_timestamp()-interval '1 second' where request_id=%s",(args[3],))
        self.assertEqual(self.call((*args[:3],uuid.uuid4(),'pre_side_effect',args[3]))['reason'],'reservation_missing_or_expired')

    def test_dispatch_audit_failure_rolls_back_reservation(self):
        args = self.fixture()
        self.admin.execute("""create function fail_dispatch() returns trigger language plpgsql as $$ begin
          if new.action='dispatch_decision' then raise exception 'dispatch_audit_failure'; end if; return new; end $$;
          create trigger fail_dispatch before insert on production_board_activity for each row execute function fail_dispatch();""")
        try:
            with self.assertRaisesRegex(self.pg.Error,'dispatch_audit_failure'):
                self.call(args)
            self.assertEqual(self.admin.execute('select count(*) from production_board_dispatch_decisions where request_id=%s',(args[3],)).fetchone()[0],0)
        finally:
            self.admin.execute('drop trigger fail_dispatch on production_board_activity; drop function fail_dispatch()')
        self.assertEqual(self.call(args)['decision'],'reserved')

    def test_dispatch_roles(self):
        args = self.fixture()
        for role in ('anon','authenticated'):
            with self.pg.connect(foundation.DSN) as conn:
                conn.execute(f'set role {role}')
                with self.assertRaisesRegex(self.pg.Error,'permission denied'):
                    conn.execute(CALL,args)
        with self.pg.connect(foundation.DSN) as conn:
            conn.execute('set role service_role')
            with self.assertRaisesRegex(self.pg.Error,'permission denied'):
                conn.execute('delete from production_board_dispatch_decisions')

    def test_dispatch_competing_reservations_lock(self):
        args = self.fixture()
        other = (*args[:3],uuid.uuid4(),*args[4:])
        with self.pg.connect(foundation.DSN) as a, self.pg.connect(foundation.DSN) as b:
            for conn in (a,b):
                conn.execute('set role service_role')
                conn.execute("set statement_timeout='8s'")
                conn.commit()
            self.assertEqual(a.execute(CALL,args).fetchone()[0]['decision'],'reserved')
            def contender():
                value=b.execute(CALL,other).fetchone()[0]
                b.commit()
                return value
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pending=pool.submit(contender)
                try:
                    deadline=time.monotonic()+4
                    while time.monotonic()<deadline:
                        row=self.admin.execute('select wait_event_type from pg_stat_activity where pid=%s',(b.info.backend_pid,)).fetchone()
                        if row and row[0]=='Lock': break
                        time.sleep(.02)
                    else: self.fail('contender did not reach Lock wait')
                    print('dispatch competing reservations: observed Lock wait',flush=True)
                    a.commit()
                    self.assertEqual(pending.result(timeout=5)['reason'],'reservation_active')
                finally:
                    a.rollback()

    def wait_for_lock(self, conn, pending):
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            row = self.admin.execute('select wait_event_type from pg_stat_activity where pid=%s',
                                     (conn.info.backend_pid,)).fetchone()
            if row and row[0] == 'Lock':
                print(self._testMethodName + ': observed Lock wait', flush=True)
                return
            if pending.done():
                self.fail('contender finished before lock release')
            time.sleep(.02)
        self.fail('contender did not reach Lock wait')

    def test_dispatch_intake_writer_first_no_deadlock(self):
        args = self.fixture()
        with self.pg.connect(foundation.DSN) as writer, self.pg.connect(foundation.DSN) as dispatcher:
            for conn in (writer, dispatcher):
                conn.execute('set role service_role')
                conn.execute("set statement_timeout='8s'")
                conn.commit()
            # Model UPDATE's intake-row lock before its AFTER trigger touches card.
            writer.execute('select 1 from production_board_dispatch_intake where card_id=%s for update', (args[0],))
            def decide():
                value = dispatcher.execute(CALL, args).fetchone()[0]
                dispatcher.commit()
                return value
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pending = pool.submit(decide)
                try:
                    self.wait_for_lock(dispatcher, pending)
                    writer.execute('update production_board_dispatch_intake set blocked=true where card_id=%s', (args[0],))
                    writer.commit()
                    result = pending.result(timeout=10)
                    self.assertEqual(result['reason'], 'stale_card_version')
                    self.assertFalse(result['can_execute'])
                finally:
                    writer.rollback()
            self.assertEqual(self.admin.execute('select row_version from production_board_cards where id=%s', (args[0],)).fetchone()[0], 3)

    def test_dispatch_reader_first_intake_writer_waits(self):
        args = self.fixture()
        with self.pg.connect(foundation.DSN) as dispatcher, self.pg.connect(foundation.DSN) as writer:
            for conn in (dispatcher, writer):
                conn.execute('set role service_role')
                conn.execute("set statement_timeout='8s'")
                conn.commit()
            self.assertEqual(dispatcher.execute(CALL, args).fetchone()[0]['decision'], 'reserved')
            def change():
                writer.execute('update production_board_dispatch_intake set blocked=true where card_id=%s', (args[0],))
                writer.commit()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                pending = pool.submit(change)
                try:
                    self.wait_for_lock(writer, pending)
                    dispatcher.commit()
                    pending.result(timeout=10)
                finally:
                    dispatcher.rollback()
            result = self.call((*args[:3], uuid.uuid4(), 'pre_side_effect', args[3]))
            self.assertEqual(result['reason'], 'stale_card_version')
            self.assertFalse(result['can_execute'])


if __name__ == '__main__':
    if not foundation.DSN:
        raise SystemExit('BLOCKED: explicit disposable ISSUE380_TEST_DSN required')
    unittest.main(verbosity=2)
