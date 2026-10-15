"""Compile native guards from the same explicit closure JSON as public selectors.

No network or deployment. Existing RPC implementations/permissions are preserved;
the migration inserts an assertion before their first executable statement.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def migration_sql():
    policy = json.loads((ROOT/'docs/data/public-registration-closures.json').read_text(encoding='utf-8'))
    if policy.get('schemaVersion') != 'public-registration-closures.v1':
        raise ValueError('invalid closure policy')
    literal = json.dumps(policy, separators=(',', ':')).replace("'", "''")
    return (ROOT/'supabase/sql/native_registration_closure.sql.in').read_text(encoding='utf-8').replace('__POLICY_JSON__', literal)


if __name__ == '__main__':
    print(migration_sql())
