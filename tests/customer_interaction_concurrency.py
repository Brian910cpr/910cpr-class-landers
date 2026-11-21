"""Opt-in real PostgreSQL lock proof; synthetic, empty localhost database only.

Requires psycopg 3 supplied by the operator (this script installs nothing).
See docs/CUSTOMER_INTERACTION_CONCURRENCY.md. Never point at production.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import sys
from pathlib import Path
import time
import uuid


def uid():
    return str(uuid.uuid4())


def record(**patch):
    ident = uid()
    return dict(id=ident, case_id=uid(), expected_version=0, kind="phone",
                status="in_progress", source="manual", source_id=ident,
                document={"notes": "Synthetic concurrency fixture"}, **patch)


def rpc(conn, function, value, request=None):
    assert function in {"save_customer_interaction", "switch_customer_interaction",
                        "save_customer_follow_up_task"}
    return conn.execute(f"select public.{function}(%s::uuid,%s,%s::jsonb)",
                        (request or uid(), "synthetic-lock-proof", json.dumps(value))).fetchone()[0]


def task(active):
    return dict(id=uid(), case_id=active["case_id"], interaction_id=active["id"],
                expected_version=0, source_key="synthetic:" + uid(), title="Synthetic callback",
                status="pending", provenance={"evidence": "Synthetic owner promise"})


def fixture(conn):
    previous = record()
    previous["kind"] = "email"
    rpc(conn, "save_customer_interaction", previous)
    active = record()
    interrupt = dict(operation="interrupt", previous={**previous, "expected_version": 1,
                     "status": "paused"}, active=active)
    request = uid()
    rpc(conn, "switch_customer_interaction", interrupt, request)
    return active, dict(operation="resume", interrupt_request_id=request,
                       previous={**previous, "expected_version": 2},
                       active={**active, "expected_version": 1, "status": "resolved"})


def race(psycopg, dsn, observer, first, second, expected_error=None):
    """Hold the first RPC's real transaction open; observe the second waiting on it."""
    with psycopg.connect(dsn, autocommit=True) as a, psycopg.connect(dsn, autocommit=True) as b:
        for conn in (a, b):
            conn.execute("set statement_timeout='12s'")
            conn.execute("set lock_timeout='10s'")
            conn.execute("set role service_role")
            assert conn.execute("show transaction_isolation").fetchone()[0] == "read committed"
        a.execute("begin isolation level read committed")
        first_result = first(a)
        pid_a = a.info.backend_pid
        pid_b = b.info.backend_pid
        assert pid_a != pid_b
        # The third session observes actual server lock waiting, not a timing guess.
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(second, b)
            try:
                deadline = time.monotonic() + 5
                while True:
                    blockers = observer.execute("select pg_blocking_pids(%s)", (pid_b,)).fetchone()[0]
                    if pid_a in blockers:
                        break
                    if future.done() or time.monotonic() > deadline:
                        raise AssertionError("second RPC did not demonstrably wait on first session")
                    time.sleep(0.025)
                a.execute("commit")
                try:
                    second_result = future.result(timeout=13)
                except psycopg.Error as exc:
                    assert expected_error and exc.sqlstate == expected_error, exc.sqlstate
                    second_result = {"sqlstate": exc.sqlstate}
                else:
                    assert expected_error is None, "expected conflict was absent"
            finally:
                a.execute("rollback")  # Releases locks on any failed assertion before joining worker.
        return first_result, second_result


def validate_local_settings(params, environ):
    """Fail closed before connect; libpq hostaddr/service defaults can reroute host."""
    if any(environ.get(key) for key in ("PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE", "PGOPTIONS")):
        raise ValueError("libpq routing/session environment overrides forbidden; no database contacted")
    if (params.get("host") not in ("127.0.0.1", "::1")
            or not params.get("dbname", "").startswith("issue371_")
            or any(params.get(key) for key in ("hostaddr", "service", "options"))):
        raise ValueError("explicit loopback host and issue371_* database without overrides required; no database contacted")


def run(psycopg, dsn):
    if sys.flags.optimize:
        raise RuntimeError("optimized Python disables proof assertions; no database contacted")
    root = Path(__file__).resolve().parents[1]
    with psycopg.connect(dsn, autocommit=True) as observer:
        if observer.execute("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public'").fetchone()[0] != 0:
            raise RuntimeError("public schema must be empty")
        if observer.execute("select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public'").fetchone()[0] != 0:
            raise RuntimeError("public functions must be absent")
        # Roles are provisioned separately, never silently created in a shared cluster.
        for name in ("anon", "authenticated", "service_role"):
            assert observer.execute("select count(*) from pg_roles where rolname=%s", (name,)).fetchone()[0] == 1, f"missing role {name}"
        observer.execute("create table public.landerware_people(id uuid primary key)")
        for name in ("20261010210607_customer_interaction_storage.sql",
                     "20261010211804_customer_interaction_interruptions.sql",
                     "20261010212019_customer_follow_up_task_mutations.sql"):
            observer.execute((root / "supabase/migrations" / name).read_text(encoding="utf-8"))
        with psycopg.connect(dsn, autocommit=True) as setup:
            setup.execute("set role service_role")
            for scenario in ("create-first", "resume-first", "complete-first", "reopen-first", "two-tasks"):
                active, resume = fixture(setup)
                obligation = task(active)
                request_a, request_b = uid(), uid()
                task_write = lambda c: rpc(c, "save_customer_follow_up_task", obligation, request_a)
                resume_write = lambda c: rpc(c, "switch_customer_interaction", resume, request_b)
                error = None
                if scenario == "create-first":
                    first, second, error = task_write, resume_write, "40001"
                elif scenario == "resume-first":
                    first, second, error = resume_write, task_write, "40001"
                elif scenario in ("complete-first", "reopen-first"):
                    rpc(setup, "save_customer_follow_up_task", obligation)
                    completion = {**obligation, "expected_version": 1, "status": "complete",
                                  "completion_evidence": "Synthetic owner confirmed callback"}
                    if scenario == "complete-first":
                        first = lambda c: rpc(c, "save_customer_follow_up_task", completion, request_a)
                        second = resume_write
                    else:
                        rpc(setup, "save_customer_follow_up_task", completion)
                        obligation = {**obligation, "expected_version": 2}
                        first, second, error = task_write, resume_write, "40001"
                else:
                    another = task(active)
                    first = task_write
                    second = lambda c: rpc(c, "save_customer_follow_up_task", another, request_b)
                first_result, second_result = race(psycopg, dsn, observer, first, second, error)
                # Successful request replay cannot duplicate immutable events or change the receipt.
                assert first(setup) == first_result
                if not error:
                    assert second(setup) == second_result
                else:
                    assert observer.execute("select count(*) from customer_interruption_events where request_id=%s::uuid", (request_b,)).fetchone()[0] == (1 if scenario == "resume-first" else 0)
                    failed_request = request_a if scenario == "resume-first" else request_b
                    assert observer.execute("select count(*) from customer_task_events where request_id=%s::uuid", (failed_request,)).fetchone()[0] == 0
                for request in (request_a, request_b):
                    count = observer.execute("select (select count(*) from customer_task_events where request_id=%s::uuid)+(select count(*) from customer_interruption_events where request_id=%s::uuid)", (request, request)).fetchone()[0]
                    failed = error and request == (request_a if scenario == "resume-first" else request_b)
                    assert count == (0 if failed else 1), "duplicate or missing immutable receipt"
                if scenario == "two-tasks":
                    assert observer.execute("select count(*) from customer_follow_up_tasks where interaction_id=%s::uuid", (active["id"],)).fetchone()[0] == 2
                if scenario in ("create-first", "reopen-first"):
                    # A failed second save in resume must roll back the previous record and its audit.
                    previous_id = resume["previous"]["id"]
                    assert observer.execute("select status,version from customer_interactions where id=%s::uuid", (previous_id,)).fetchone() == ("paused", 2)
                    assert observer.execute("select count(*) from customer_interaction_events where interaction_id=%s::uuid", (previous_id,)).fetchone()[0] == 2
                assert observer.execute("select count(*) from customer_interactions i join customer_follow_up_tasks t on t.interaction_id=i.id where i.status='resolved' and t.status in ('proposed','pending','snoozed')").fetchone()[0] == 0
                print(json.dumps({"scenario": scenario, "observed_blocking": True,
                                  "expected_conflict": error, "retry_equal": True, "result": "PASS"}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply-to-empty-local", action="store_true",
                        help="Explicitly authorize fixture/migration writes to an empty issue371_* localhost DB")
    args = parser.parse_args()
    if not args.apply_to_empty_local:
        parser.error("requires --apply-to-empty-local; no database contacted")
    if sys.flags.optimize:
        parser.error("optimized Python disables proof assertions; no database contacted")
    try:
        import psycopg
        from psycopg.conninfo import conninfo_to_dict
    except ImportError:
        parser.error("psycopg 3 missing; no database contacted or dependency installed")
    dsn = os.environ.get("ISSUE371_LOCAL_DSN", "")
    try:
        params = conninfo_to_dict(dsn)
    except Exception:
        parser.error("invalid local connection settings; no database contacted")
    try:
        validate_local_settings(params, os.environ)
    except ValueError as exc:
        parser.error(str(exc))
    try:
        run(psycopg, dsn)
    except Exception as exc:
        # Do not print driver exception strings, which can contain connection secrets.
        print(json.dumps({"result": "FAIL", "type": type(exc).__name__,
                          "sqlstate": getattr(exc, "sqlstate", None)}))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
