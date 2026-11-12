#!/usr/bin/env bash
set -euo pipefail
: "${PG17_ROOT:?Set PG17_ROOT to the installed PostgreSQL17 root directory}"
ROOT=$PG17_ROOT
REPO=$(cd "$(dirname "$0")/.." && pwd)
export PATH="$ROOT/usr/lib/postgresql/17/bin:$PATH"
export LD_LIBRARY_PATH="$ROOT/usr/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}"
[[ "$(postgres --version)" == *' 17.'* ]] || { echo 'PostgreSQL17 required' >&2; exit 2; }
while IFS= read -r variable; do unset "$variable"; done < <(compgen -e | grep -E '^(PG|DATABASE_URL)' || true)
export PGPASSFILE=/dev/null PGPASSWORD='' PGCONNECT_TIMEOUT=3
RUN=$(mktemp -d /tmp/native-skills-offer-lease-pg17-XXXXXX)
trap 'pg_ctl -D "$RUN/data" -m fast -w stop > "$RUN/stop.log" 2>&1 || true' EXIT
initdb -D "$RUN/data" -U postgres -A trust --no-locale -E UTF8 --locale-provider=libc -L "$ROOT/usr/share/postgresql/17" > "$RUN/initdb.log" 2>&1
pg_ctl -D "$RUN/data" -l "$RUN/server.log" -o "-p 55465 -h 127.0.0.1 -k '' -c dynamic_library_path=$ROOT/usr/lib/postgresql/17/lib -c timezone=UTC -c max_connections=25" -w start > "$RUN/start.log" 2>&1
createdb -h 127.0.0.1 -p 55465 -U postgres skills_claim_test_233000
printf 'Started isolated synthetic cluster: %s\n' "$RUN"
createdb -h 127.0.0.1 -p 55465 -U postgres skills_claim_test_233001
SKILLS_TEST_PORT=55465 NATIVE_SKILLS_LEASE_CHAIN=bls node "$REPO/tests/native-skills-offer-lease-concurrency.mjs"
SKILLS_TEST_PORT=55465 NATIVE_SKILLS_LEASE_CHAIN=full node "$REPO/tests/native-skills-offer-lease-concurrency.mjs"
