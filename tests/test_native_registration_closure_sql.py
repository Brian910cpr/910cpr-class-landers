import json
import unittest
from pathlib import Path
from scripts.build_native_registration_closure import migration_sql

ROOT=Path(__file__).resolve().parents[1]


class NativeClosureSQLTests(unittest.TestCase):
    def test_native_policy_is_compiled_from_public_definition(self):
        policy=json.loads((ROOT/'docs/data/public-registration-closures.json').read_text(encoding='utf-8'))
        sql=migration_sql()
        self.assertNotIn('__POLICY_JSON__',sql)
        self.assertIn(json.dumps(policy,separators=(',',':')).replace("'","''"),sql)

    def test_guard_wraps_all_six_deployed_entrypoints_without_business_writes(self):
        sql=migration_sql()
        for name in ['landerware_create_public_order','landerware_register','queue_public_registration_intent','start_public_registration_intent','maxim_replace_registration']:
            self.assertIn(name,sql)
        self.assertIn('changed<>6',sql)
        for statement in ['insert into public.','update public.','delete from public.']:
            self.assertNotIn(statement,sql.lower())
        self.assertIn('pg_get_functiondef(f.oid)',sql)
        self.assertIn('security invoker',sql)
        self.assertIn('from public,anon,authenticated',sql)

    def test_actual_workspace_and_source_dates_checked_not_only_client_timestamp(self):
        sql=migration_sql()
        self.assertIn('w.starts_at,w.ends_at',sql)
        self.assertIn('w.id::text=p_external_id',sql)
        self.assertIn('s.consumption_start_at',sql)
        self.assertIn('registration_date_closed',sql)


if __name__=='__main__':unittest.main()
