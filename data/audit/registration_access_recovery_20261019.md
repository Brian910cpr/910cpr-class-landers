# Restore registration account access

Updated October19,2026. This supplements the registration cutover audit; its original Cloudflare IP-token blocker now has a working existing-OAuth alternative.

## Stripe — owner reconnect

1. In this ChatGPT/Codex account, open Plugins (Apps on some versions), then Installed and Stripe.
2. Open its app/connected-account section and choose Reconnect or Sign in/Connect if the expired connection is shown that way.
3. Sign in to the Stripe account used by910CPR and approve the requested existing connection. Return to this chat and say Stripe reconnected.
4. Codex verifies by listing available Stripe accounts; then confirm the intended account and test/live context before account-specific operations. A plugin being installed/enabled does not prove its OAuth connection is valid. Last connector result was UNAUTHORIZED; no unchanged failing call was retried.

Source: https://learn.chatgpt.com/docs/plugins and https://learn.chatgpt.com/docs/dots/computers-and-apps . No API key needs to be pasted into chat.

## Cloudflare — use the existing browser login

Verified read-only: omitting CLOUDFLARE_API_TOKEN from one child command makes Wrangler4.151.1 whoami succeed with existing OAuth for account9acb24ab8037cc5abe5518f7758455fd. The saved environment token stays intact; an existing cached OAuth login supplies the authorized alternative. Therefore the owner does not need to change the token's IP allowlist now. An IP-filtered token verification endpoint alone would not prove account API access.

That existing OAuth grant lacks email_sending:write. To complete the Email Sending permission refresh, run the supplied PowerShell helper interactively:

```powershell
& "$env:USERPROFILE\Documents\Codex\2026-10-10\codex-p0-diagnostic-repair-automatic-instruction\outputs\Restore-CheckoutCloudflareLogin.ps1"
```

In the browser page it opens, sign in to the same910CPR Cloudflare account and approve the scope addition. The helper reads ONLY existing scope metadata for its output, preserves that existing scope set, adds email_sending:write, uses the pinned Wrangler version and verifies with whoami. It omits the environment API token only inside its own process and restores it in finally. Existing OAuth file is refreshed by Wrangler after consent; no deployment, payment or email send is performed. Python3.12 and npx are already present on this machine. Source version: ops/scripts/Restore-CheckoutCloudflareLogin.ps1.

After completion, tell Codex Cloudflare email permission refreshed. Codex checks the account/scopes and actual required resource access before proceeding. Basic account listing is not proof that the sender domain, email consumer or deployment exists. Existing Workers/Pages/Queues scopes were present; unrelated newly offered AI permissions are not added by this helper.

References: https://developers.cloudflare.com/workers/wrangler/system-environment-variables/ , https://developers.cloudflare.com/fundamentals/api/how-to/restrict-tokens/ . Wrangler login --help and --scopes-list were checked locally. No need to remove the machine-wide API token, change global environment variables or request a global API key.

## Work continuing independently

PR416's main integration is prepared at81bce570eda8155358d4d3a665f494d704a808d7, with parentsbc05ad533d8f2909b7dbfae1773036ea5fe1aec1 and0ccbefc0822bb3ba73b41adb5625ef5663e14674. It preserves current scheduling projections and resolves only the message-history HTML asset conflict. The integrated80-test suite passes. Account restoration remains separate from rollout authorization and controlled payment/delivery/backup/observer proof. Enrollware booking stays available. Customer Interaction Studio and its canceled provisioning remain stopped.
