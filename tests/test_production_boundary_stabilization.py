from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_EVENT = (
    ROOT / "supabase/functions/public-event-registration/index.ts"
).read_text(encoding="utf-8")
STRIPE_WEBHOOK = (
    ROOT / "supabase/functions/stripe-registration-webhook/index.ts"
).read_text(encoding="utf-8")
RLS_MIGRATION = (
    ROOT / "supabase/migrations/20260831120000_secure_maxim_billing_code_rules.sql"
).read_text(encoding="utf-8")
HEARTSAVER_ROUTE = (
    ROOT / "docs/register/heartsaver-skills/index.html"
).read_text(encoding="utf-8")


def test_public_event_uses_unambiguous_canonical_relationships():
    assert "courses!class_sessions_course_id_fkey" in PUBLIC_EVENT
    assert "locations!class_sessions_location_id_fkey" in PUBLIC_EVENT
    assert "people!class_sessions_lead_instructor_id_fkey" in PUBLIC_EVENT
    assert '.from("customers")' in PUBLIC_EVENT
    assert '.from("registrations")' in PUBLIC_EVENT
    assert '.from("class_sessions")' in PUBLIC_EVENT
    assert '.from("landerware_' not in PUBLIC_EVENT


def test_public_event_survey_uses_existing_registration_column():
    assert '.from("registration_surveys")' not in PUBLIC_EVENT
    assert "optional_survey:survey" in PUBLIC_EVENT


def test_webhook_secret_is_environment_only():
    assert 'Deno.env.get("STRIPE_WEBHOOK_SECRET")' in STRIPE_WEBHOOK
    assert ("wh" + "sec_") not in STRIPE_WEBHOOK
    assert "if(!WEBHOOK_SECRET||!header)" in STRIPE_WEBHOOK


def test_billing_rules_are_not_browser_readable():
    normalized = " ".join(RLS_MIGRATION.lower().split())
    assert "alter table public.maxim_billing_code_rules enable row level security" in normalized
    assert "revoke all on table public.maxim_billing_code_rules from anon, authenticated" in normalized


def test_heartsaver_route_fails_over_to_live_session_selection():
    assert "location.replace('/heartsaver.html')" in HEARTSAVER_ROUTE
