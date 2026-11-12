#!/usr/bin/env bash
# Local-only, fresh cluster, TCP loopback. Requires already-approved PG17 binaries.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
: "${PG17_BIN:?Set PG17_BIN to the installed PostgreSQL17 bin directory}"
: "${PG17_SHARE:?Set PG17_SHARE to the matching share directory}"
: "${PG17_LIB:?Set PG17_LIB to the matching extension-library directory}"
BIN=$PG17_BIN
SHARE=$PG17_SHARE
LIB=$PG17_LIB
PORT=${NATIVE_SKILLS_SEATS_TEST_PORT:-55449}
[[ "$PORT" =~ ^[0-9]+$ ]] && ((PORT>0 && PORT<65536)) || exit 2
export PATH="$BIN:$PATH"
[[ "$(postgres --version)" == *' 17.'* ]] || { echo 'PostgreSQL17 required' >&2; exit 2; }
# Do not inherit hosted database routing or credential-bearing environment.
while IFS= read -r variable; do unset "$variable"; done < <(compgen -e | grep -E '^(PG|DATABASE_URL)' || true)
export PGPASSFILE=/dev/null PGPASSWORD='' PGCONNECT_TIMEOUT=3
RUN=$(mktemp -d /tmp/native-skills-seats-pg17-XXXXXX)
DATA="$RUN/data"
trap 'pg_ctl -D "$DATA" -m fast -w stop > "$RUN/stop.log" 2>&1 || true' EXIT
initdb -D "$DATA" -U postgres -A trust --no-locale -E UTF8 --locale-provider=libc -L "$SHARE" > "$RUN/initdb.log" 2>&1
pg_ctl -D "$DATA" -l "$RUN/server.log" -o "-p $PORT -h 127.0.0.1 -k '' -c dynamic_library_path=$LIB -c timezone=UTC -c max_connections=20" -w start > "$RUN/start.log" 2>&1
createdb -h 127.0.0.1 -p "$PORT" -U postgres skills_claim_test_509474
SKILLS_TEST_PORT="$PORT" node "$ROOT/tests/native-skills-seated-concurrency.mjs"
printf 'Local cluster/log directory: %s\n' "$RUN"
