"""Opt-in PostgreSQL contention proof; never point this at an operational DB.

Requires psycopg 3 and an EMPTY disposable database named issue380_test_* on
127.0.0.1. Set ISSUE380_TEST_DSN explicitly; DATABASE_URL is never consumed.
Fixtures are retained for inspection. This is not a migration/install command.
"""
import concurrent.futures
import argparse
import os
from pathlib import Path
import time
import unittest
import uuid


def validate_target(info):
    if info.get('host') != '127.0.0.1' or info.get('hostaddr', '127.0.0.1') != '127.0.0.1':
        raise ValueError('explicit IPv4 loopback required')
    if not info.get('dbname', '').startswith('issue380_test_'):
        raise ValueError('disposable issue380_test_* database required')
    if info.get('service'):
        raise ValueError('service indirection forbidden')


DSN = os.environ.get('ISSUE380_TEST_DSN')
ROOT = Path(__file__).resolve().parents[2]
CALL = 'select public.production_board_resolve(%s,%s,%s,%s,%s,%s,%s,%s)'


class TargetSafety(unittest.TestCase):
    def test_reject_operational_or_indirect_targets(self):
        for info in ({}, {'host': 'production', 'dbname': 'issue380_test_x'},
                     {'host': '127.0.0.1', 'dbname': 'postgres'},
                     {'host': '127.0.0.1', 'dbname': 'issue380_test_x', 'hostaddr': '192.0.2.1'},
                     {'host': '127.0.0.1', 'dbname': 'issue380_test_x', 'service': 'prod'}):
            with self.assertRaises(ValueError):
                validate_target(info)
        validate_target({'host': '127.0.0.1', 'dbname': 'issue380_test_fixture'})


@unittest.skipUnless(DSN, 'BLOCKED: ISSUE380_TEST_DSN disposable local PostgreSQL not supplied')
class ResolutionContention(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        from psycopg.conninfo import conninfo_to_dict
        cls.pg = psycopg
        validate_target(conninfo_to_dict(DSN))
        cls.admin = psycopg.connect(DSN, autocommit=True, connect_timeout=5)
        print('PostgreSQL:', cls.admin.execute('select version()').fetchone()[0], flush=True)
        print('psycopg:', psycopg.__version__, 'libpq:', psycopg.pq.version(), flush=True)
        # Check effective target too, including environment/libpq overrides.
        effective = cls.admin.info.get_parameters()
        validate_target(effective)
        if cls.admin.execute("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname not in ('pg_catalog','information_schema') and n.nspname not like 'pg_toast%' and c.relkind in ('r','p','v','m','S','f')").fetchone()[0]:
            cls.admin.close()
            raise RuntimeError('database must be empty; no changes made')
        # Roles are cluster-global: use a dedicated local test cluster. Existing
        # roles are not modified; service_role must already bypass RLS if present.
        for role in ('anon', 'authenticated', 'service_role'):
            if not cls.admin.execute('select 1 from pg_roles where rolname=%s', (role,)).fetchone():
                cls.admin.execute(f'create role {role}' + (' bypassrls' if role == 'service_role' else ''))
        cls.admin.execute((ROOT / 'supabase/migrations/20260812161043_production_board.sql').read_text())
        cls.admin.execute((ROOT / 'data/audit/issue380_resolution_transaction_draft.sql').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.admin.close()

    def args(self, card=None, request=None, explanation='Fixed externally'):
        card = card or self.admin.execute("insert into production_board_cards(title) values ('Contention fixture') returning id").fetchone()[0]
        return (card, 1, request or uuid.uuid4(), 'owner-fixture', 'handled_manually', explanation, 'contention-fixture', '2026-10-13T00:00:00Z')

    def race(self, first, second, rollback=False):
        """Hold first transaction, observe second waiting, then release first."""
        with self.pg.connect(DSN, connect_timeout=5) as a, self.pg.connect(DSN, connect_timeout=5) as b:
            for conn in (a, b):
                conn.execute('set role service_role')
                conn.execute("set statement_timeout='8s'")
                conn.execute("set lock_timeout='6s'")
                conn.commit()
            pid = b.info.backend_pid
            result = a.execute(CALL, first).fetchone()[0]

            def contender():
                try:
                    value = b.execute(CALL, second).fetchone()[0]
                    b.commit()
                    return value
                except self.pg.Error as exc:
                    b.rollback()
                    return str(exc).splitlines()[0]

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(contender)
                try:
                    deadline = time.monotonic() + 4
                    while time.monotonic() < deadline:
                        row = self.admin.execute('select wait_event_type from pg_stat_activity where pid=%s', (pid,)).fetchone()
                        if row and row[0] == 'Lock':
                            print(self._testMethodName + ': observed contender Lock wait', flush=True)
                            break
                        if future.done():
                            self.fail('contender finished before lock release')
                        time.sleep(0.02)
                    else:
                        self.fail('did not observe real lock contention')
                finally:
                    a.rollback() if rollback else a.commit()
                other = future.result(timeout=10)
            return result, other

    def assert_effects(self, card, count):
        self.assertEqual(self.admin.execute('select row_version,resolution_state from production_board_cards where id=%s', (card,)).fetchone(), (2, 'handled_manually'))
        for table in ('production_board_resolution_events', 'production_board_activity'):
            self.assertEqual(self.admin.execute(f'select count(*) from {table} where card_id=%s', (card,)).fetchone()[0], count)

    def test_identical_request_replays_once(self):
        args = self.args()
        first, second = self.race(args, args)
        self.assertFalse(first['replayed'])
        self.assertEqual(second, dict(first, replayed=True))
        self.assert_effects(args[0], 1)

    def test_same_request_changed_payload_conflicts(self):
        args = self.args()
        _, second = self.race(args, self.args(args[0], args[2], 'Different explanation'))
        self.assertEqual(second, 'idempotency_conflict')
        self.assert_effects(args[0], 1)

    def test_request_reuse_across_cards_conflicts(self):
        args = self.args()
        other = self.args(request=args[2])
        _, second = self.race(args, other)
        self.assertEqual(second, 'idempotency_conflict')
        self.assert_effects(args[0], 1)
        self.assertEqual(self.admin.execute('select row_version,resolution_state from production_board_cards where id=%s', (other[0],)).fetchone(), (1, 'unresolved'))

    def test_distinct_request_stale_writer_rejected(self):
        args = self.args()
        _, second = self.race(args, self.args(card=args[0]))
        self.assertEqual(second, 'stale_card_version')
        self.assert_effects(args[0], 1)

    def test_rollback_releases_request_without_phantom_receipt(self):
        args = self.args()
        _, second = self.race(args, args, rollback=True)
        self.assertEqual(second, {'replayed': False, 'version': 2, 'state': 'handled_manually'})
        self.assert_effects(args[0], 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--guards-only', action='store_true', help='test target validation without claiming database proof')
    options = parser.parse_args()
    if not options.guards_only and not DSN:
        parser.error('BLOCKED: ISSUE380_TEST_DSN disposable local PostgreSQL not supplied; no contention proof ran')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TargetSafety)
    if not options.guards_only:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(ResolutionContention))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
