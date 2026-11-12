#!/usr/bin/env bash
# Disposable local synthetic PostgreSQL 17 only. Never reads connection secrets.
set -euo pipefail
ROOT=${NATIVE_TEST_PG17_ROOT:-/tmp/native-pg17-regressions-20261111/root}
BIN=$ROOT/usr/lib/postgresql/17/bin
HERE=$(cd "$(dirname "$0")/.." && pwd)
export PATH="$BIN:$PATH" LD_LIBRARY_PATH="$ROOT/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
[[ "$(postgres --version)" == *' 17.'* ]] || { echo 'PostgreSQL 17 required' >&2; exit 2; }
while IFS= read -r variable; do unset "$variable"; done < <(compgen -e | grep -E '^(PG|DATABASE_URL)' || true)
export PGPASSFILE=/dev/null PGPASSWORD='' PGCONNECT_TIMEOUT=3
RUN=$(mktemp -d "${TMPDIR:-/tmp}/native-booking-pg17-XXXXXX")
PORT=55803
STARTED=false
cleanup(){
 if [[ "$STARTED" == true ]]; then
  pg_ctl -D "$RUN/data" -m fast -w stop > "$RUN/stop.log" 2>&1
  if [[ ! -e "$RUN/data/postmaster.pid" ]]; then rm -rf -- "$RUN/data"; fi
 fi
}
trap cleanup EXIT
initdb -D "$RUN/data" -U postgres -A trust --no-locale -E UTF8 --locale-provider=libc -L "$ROOT/usr/share/postgresql/17" > "$RUN/initdb.log" 2>&1
pg_ctl -D "$RUN/data" -l "$RUN/server.log" -o "-p $PORT -h 127.0.0.1 -k '' -c dynamic_library_path=$ROOT/usr/lib/postgresql/17/lib -c timezone=UTC -c max_connections=15" -w start > "$RUN/start.log" 2>&1
STARTED=true
createdb -h 127.0.0.1 -p "$PORT" -U postgres skills_claim_test_121198
printf 'Isolated synthetic cluster: %s; port: %s\n' "$RUN" "$PORT"
SKILLS_TEST_PSQL="$BIN/psql" SKILLS_TEST_PORT="$PORT" node "$HERE/tests/native-booking-identity-postgres.mjs" "$@"
