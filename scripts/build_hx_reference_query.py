#!/usr/bin/env python3
"""Build a read-only, PII-hashed production-reference query for an Hx payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.payload.read_text(encoding="utf-8"))
    records = payload["records"]
    hashes = sorted({
        value for record in records for value in (
            record.get("person", {}).get("email_hash"), record.get("person", {}).get("phone_hash")
        ) if value
    })
    class_ids = sorted({str(r.get("session", {}).get("source_id") or "") for r in records if r.get("session", {}).get("source_id")})
    hash_sql = ",".join(quote(value) for value in hashes) or "''"
    class_sql = ",".join(quote(value) for value in class_ids) or "''"
    query = f"""with customer_hashes as (
  select id,
    encode(extensions.digest(convert_to(lower(btrim(coalesce(email,''))),'utf8'),'sha256'),'hex') email_hash,
    encode(extensions.digest(convert_to(regexp_replace(coalesce(phone,''),'\\D','','g'),'utf8'),'sha256'),'hex') phone_hash
  from public.customers
)
select jsonb_build_object(
  'customers',(select coalesce(jsonb_agg(to_jsonb(c)),'[]'::jsonb) from customer_hashes c where c.email_hash in ({hash_sql}) or c.phone_hash in ({hash_sql})),
  'sessions',(select coalesce(jsonb_agg(jsonb_build_object('id',id,'source',source,'source_record_id',external_class_id,'external_class_id',external_class_id,'course_id',course_id,'start_at',start_at)),'[]'::jsonb) from public.class_sessions where external_class_id in ({class_sql})),
  'registrations','[]'::jsonb
) reference;
"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(query, encoding="utf-8")
    print(json.dumps({"identity_hashes": len(hashes), "class_ids": len(class_ids), "query_bytes": len(query)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
