# Northstar Public Launch Handoff

Date: 2026-03-23

## Live public URL right now

Temporary public tunnel for the current session:

- [https://short-crews-cough.loca.lt](https://short-crews-cough.loca.lt)

This URL is live only as long as the local tunnel process and local Northstar app are running.
If the tunnel rotates, check [`localtunnel.log`](C:/Users/onkha/OneDrive/Documents/New%20project/localtunnel.log) for the current public URL.

## What is working on the live URL

- public homepage
- product, pricing, Shopify, security, support, contact, privacy, and terms pages
- install page at `/install`
- billing page at `/billing`
- `robots.txt`
- `sitemap.xml`

## Important limitation of the current live URL

This is a temporary tunnel, not a permanent production host.

Use it for:

- founder demos
- sharing the public website
- validating install-link generation

Do not treat it as the final production deployment.

## Exact next step for a permanent launch

1. Deploy Northstar on a stable host or VM
2. Set `PUBLIC_BASE_URL` to the final HTTPS domain
3. Add that domain's `/auth/callback` URL to Shopify's allowed redirect URLs
4. Point the install CTA and Shopify app config at that host
5. Re-run the OAuth install flow end to end
6. Re-test billing after the Shopify app is moved into Shopify Partners

## Public install flow status

Northstar now generates a real Shopify authorization URL from the install page.

Example live callback target generated from the public URL:

- `https://short-crews-cough.loca.lt/auth/callback`

That callback is now handled by the app, but the final hosted callback URL still needs to be added in Shopify Dev Dashboard before a complete public install round-trip can be verified on the tunnel or final host.

## Billing status

Northstar now includes a Billing API path and billing UI, but the current Shopify app is blocked from charging because it is still shop-owned instead of Partner-owned.

## Files to use for the permanent move

- [`Dockerfile`](C:/Users/onkha/OneDrive/Documents/New%20project/Dockerfile)
- [`deploy/Caddyfile`](C:/Users/onkha/OneDrive/Documents/New%20project/deploy/Caddyfile)
- [`run_production.py`](C:/Users/onkha/OneDrive/Documents/New%20project/run_production.py)
- [`.env.example`](C:/Users/onkha/OneDrive/Documents/New%20project/.env.example)
- [`shopify.app.toml.example`](C:/Users/onkha/OneDrive/Documents/New%20project/shopify.app.toml.example)
