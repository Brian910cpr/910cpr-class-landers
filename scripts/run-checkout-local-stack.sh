#!/usr/bin/env bash
set -euo pipefail
umask 077
# One disposable runner; never links or deploys a hosted Supabase project.
STACK_ROOT="${RUNNER_TEMP:?}/checkout-local-stack"
export SUPABASE_HOME="$RUNNER_TEMP/checkout-supabase-home"
mkdir -p "$STACK_ROOT/supabase" "$SUPABASE_HOME" "$RUNNER_TEMP/checkout-cli"
trap 'cd "$STACK_ROOT"; if "$RUNNER_TEMP/checkout-cli/supabase" stop >/dev/null 2>&1; then printf "CLEANUP: disposable local services stopped.\n"; else printf "CLEANUP: stop not confirmed; disposable runner teardown remains required.\n"; fi' EXIT
curl --fail --location --silent --show-error https://github.com/supabase/cli/releases/download/v3.1.0/supabase_3.1.0_linux_amd64.tar.gz -o "$RUNNER_TEMP/checkout-cli/cli.tar.gz"
printf '%s  %s\n' dbe9fd66771337fc198727da86b9d3551302f87a7091cd8781be2a4cd0c8ac4d "$RUNNER_TEMP/checkout-cli/cli.tar.gz" | sha256sum --check --status
tar -xzf "$RUNNER_TEMP/checkout-cli/cli.tar.gz" -C "$RUNNER_TEMP/checkout-cli" supabase
CLI="$RUNNER_TEMP/checkout-cli/supabase"
"$CLI" --version
# Fresh project only: no repository migration auto-application, no hosted link.
cp -R "$GITHUB_WORKSPACE/supabase/functions" "$STACK_ROOT/supabase/"
printf '[experimental]\nstack = true\n[db]\nmajor_version = 17\n[functions.public-registration]\nverify_jwt = false\n[functions.stripe-registration-webhook]\nverify_jwt = false\n' > "$STACK_ROOT/supabase/config.toml"
cd "$STACK_ROOT"
"$CLI" start --help > "$RUNNER_TEMP/checkout-cli/start-help.txt"
grep -q -- '--runtime' "$RUNNER_TEMP/checkout-cli/start-help.txt"
grep -q -- '--output-format' "$RUNNER_TEMP/checkout-cli/start-help.txt"
# stdout may contain generated local credentials: never print or upload it.
"$CLI" start --runtime native --exclude studio,realtime,analytics,pooler,mail --output-format json > "$RUNNER_TEMP/checkout-stack-private.json" 2> "$RUNNER_TEMP/checkout-stack-start-private.log"
node "$GITHUB_WORKSPACE/tests/local-supabase-service-proof.mjs" "$RUNNER_TEMP/checkout-stack-private.json"
printf 'STRIPE_EXPECTED_LIVEMODE=false\nNATIVE_COURSE_BASKETS_ENABLED=true\n' > "$RUNNER_TEMP/checkout-test.env"
node -e 'process.stdout.write("STRIPE_WEBHOOK_SECRET=whsec_local_"+require("node:crypto").randomBytes(32).toString("hex")+"\n")' >> "$RUNNER_TEMP/checkout-test.env"
"$CLI" functions serve --env-file "$RUNNER_TEMP/checkout-test.env" > "$RUNNER_TEMP/checkout-functions-private.log" 2>&1 &
FUNCTION_PID=$!
node "$GITHUB_WORKSPACE/tests/local-supabase-application-proof.mjs" "$RUNNER_TEMP/checkout-stack-private.json" "$RUNNER_TEMP/checkout-test.env"
kill "$FUNCTION_PID" 2>/dev/null || true
"$CLI" stop > /dev/null 2>&1
printf 'Disposable local Supabase services stopped; runner teardown removes this test workspace.\n'
