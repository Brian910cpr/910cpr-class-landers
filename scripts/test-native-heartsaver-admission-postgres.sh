#!/usr/bin/env bash
set -euo pipefail
# Requires already-installed official PostgreSQL17 binaries; never installs or connects remotely.
# POSTGRES_ROOT supports an existing unpacked vendor package in disposable local CI.
ROOT=${POSTGRES_ROOT:-/tmp/native-pg17-regressions-20261111/root}
BIN=${POSTGRES_BIN:-$ROOT/usr/lib/postgresql/17/bin}
export PATH="$BIN:$PATH"
while IFS= read -r variable; do unset "$variable"; done < <(compgen -e | grep -E '^(PG|DATABASE_URL)' || true)
export PGPASSFILE=/dev/null PGPASSWORD='' PGCONNECT_TIMEOUT=3
PORT=${SKILLS_TEST_PORT:-55631}
RUN=$(mktemp -d /tmp/native-heartsaver-admission-pg17-XXXXXX)
trap 'pg_ctl -D "$RUN/data" -m fast -w stop > "$RUN/stop.log" 2>&1 || true' EXIT
INIT_ARGS=(); START_ARGS=()
if [[ -d "$ROOT/usr/share/postgresql/17" ]]; then INIT_ARGS=(-L "$ROOT/usr/share/postgresql/17"); START_ARGS=(-c "dynamic_library_path=$ROOT/usr/lib/postgresql/17/lib"); fi
initdb -D "$RUN/data" -U postgres -A trust --no-locale -E UTF8 --locale-provider=libc "${INIT_ARGS[@]}" > "$RUN/initdb.log" 2>&1
pg_ctl -D "$RUN/data" -l "$RUN/server.log" -o "-p $PORT -h 127.0.0.1 -k '' ${START_ARGS[*]} -c timezone=UTC -c max_connections=20" -w start > "$RUN/start.log" 2>&1
createdb -h 127.0.0.1 -p "$PORT" -U postgres skills_claim_test_120030
createdb -h 127.0.0.1 -p "$PORT" -U postgres skills_claim_test_120031
TEST=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../tests" && pwd)/native-heartsaver-admission-concurrency.mjs
SKILLS_TEST_PORT="$PORT" node "$TEST"
if [[ "${1:-}" == "--optional" ]]; then SKILLS_TEST_PORT="$PORT" node "$TEST" --optional; fi
printf 'Disposable PostgreSQL17 logs: %s\n' "$RUN"
