"""No-network safety tests for the opt-in independent-session proof runner."""
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import Mock, patch

PATH = Path(__file__).with_name('customer_interaction_concurrency.py')
spec = importlib.util.spec_from_file_location('lockproof', PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
LOCAL = dict(host='127.0.0.1', dbname='issue371_synthetic')


class SafetyTests(unittest.TestCase):
    def test_numeric_loopback_allowed(self):
        for host in ('127.0.0.1', '::1'):
            runner.validate_local_settings({**LOCAL, 'host': host}, {})

    def test_remote_multihost_and_wrong_database_rejected(self):
        for params in ({}, {**LOCAL, 'host': 'localhost'},
                       {**LOCAL, 'host': '127.0.0.1,remote.example'},
                       {**LOCAL, 'host': 'remote.example'},
                       {**LOCAL, 'dbname': 'production'}):
            with self.subTest(params=params), self.assertRaises(ValueError):
                runner.validate_local_settings(params, {})

    def test_dsn_routing_and_session_overrides_rejected(self):
        for key in ('hostaddr', 'service', 'options'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                runner.validate_local_settings({**LOCAL, key: 'private-canary'}, {})

    def test_environment_overrides_stop_before_run_without_leaking_values(self):
        driver = types.ModuleType('psycopg')
        conninfo = types.ModuleType('psycopg.conninfo')
        conninfo.conninfo_to_dict = Mock(return_value=LOCAL)
        for key in ('PGHOSTADDR', 'PGSERVICE', 'PGSERVICEFILE', 'PGOPTIONS'):
            with (
                self.subTest(key=key),
                patch.dict(sys.modules, {'psycopg': driver, 'psycopg.conninfo': conninfo}),
                patch.dict(os.environ, {key: 'private-canary'}, clear=True),
                patch.object(sys, 'argv', [str(PATH), '--apply-to-empty-local']),
                patch.object(runner, 'run') as run,
                patch('sys.stderr', new_callable=io.StringIO) as stderr,
            ):
                with self.assertRaises(SystemExit) as exc:
                    runner.main()
                self.assertEqual(exc.exception.code, 2)
                run.assert_not_called()
                self.assertIn('no database contacted', stderr.getvalue())
                self.assertNotIn('private-canary', stderr.getvalue())

    def test_nonempty_schema_or_functions_never_write(self):
        for counts in ((1,), (0, 1)):
            observer = Mock()
            observer.__enter__ = Mock(return_value=observer)
            observer.__exit__ = Mock(return_value=False)
            observer.execute.side_effect = [Mock(fetchone=Mock(return_value=(n,))) for n in counts]
            driver = Mock(connect=Mock(return_value=observer))
            with self.subTest(counts=counts), self.assertRaises(RuntimeError):
                runner.run(driver, 'synthetic-unused')
            self.assertEqual(observer.execute.call_count, len(counts))
            for call in observer.execute.call_args_list:
                self.assertTrue(call.args[0].startswith('select count(*)'))

    def test_optimized_process_refuses_before_driver_import(self):
        for flag in ('-O', '-OO'):
            result = subprocess.run([sys.executable, flag, '-B', str(PATH), '--apply-to-empty-local'], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertIn('optimized Python disables proof assertions; no database contacted', result.stderr)
            self.assertNotIn('psycopg 3 missing', result.stderr)

    def test_consent_required_before_driver_import(self):
        result = subprocess.run([sys.executable, '-B', str(PATH)], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn('requires --apply-to-empty-local; no database contacted', result.stderr)


if __name__ == '__main__':
    unittest.main()
