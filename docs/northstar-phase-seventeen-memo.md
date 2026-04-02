# Northstar Phase 17 Memo

Date: 2026-03-30

## What is now live

- Render is serving the current Northstar behavior on `https://northstar-safety.onrender.com`
- relative static asset paths are live
- the hosted founder account works
- the hosted workspace is restored to `Shopify live`
- hosted sync still pulls 2 Shopify products from `p0ubv0-zg.myshopify.com`
- hosted official alert ingest still works for CPSC and Health Canada
- hosted case attribution and case summary export were re-verified after the latest deploy
- the launch check script now has a remote-only mode so hosted verification no longer depends on the local database

## What is still blocked

- Render PostgreSQL is not created or wired yet
- SMTP credentials are still missing in Render
- `app.northstarsafetyapp.com` still does not resolve in DNS
- Shopify Billing API is still blocked because the app is shop-owned rather than Partner-managed
- Render/DNS dashboard access is still missing from this machine, so the remaining host-side work cannot be completed directly here

## What was narrowed exactly

- Postgres blocker: create the managed Render database and set `NORTHSTAR_DATABASE_URL`
- SMTP blocker: set `SMTP_HOST`, `SMTP_PORT`, `SMTP_AUTH_REQUIRED=false`, `SMTP_HELO_DOMAIN`, `SMTP_FROM_EMAIL`, and `SMTP_REPLY_TO`, then allowlist Render egress IPs for Google relay
- Domain blocker: add `app.northstarsafetyapp.com` in Render first, then create the DNS record Render provides
- Billing blocker: move the Shopify app into Shopify Partners before using `/billing/start`

## Exact next founder action

1. In Render, create the managed PostgreSQL database.
2. Add its internal connection string to `NORTHSTAR_DATABASE_URL`.
3. Redeploy Northstar.
4. In Google Workspace SMTP relay, allowlist the Render outbound IPs for `support@northstarsafetyapp.com`.
5. Add these SMTP credentials in Render and use the settings page test-email button:
   - `SMTP_MODE=smtp`
   - `SMTP_HOST=smtp-relay.gmail.com`
   - `SMTP_PORT=587`
   - `SMTP_AUTH_REQUIRED=false`
   - `SMTP_USERNAME=`
   - `SMTP_PASSWORD=`
   - `SMTP_HELO_DOMAIN=app.northstarsafetyapp.com`
   - `SMTP_FROM_EMAIL=support@northstarsafetyapp.com`
   - `SMTP_REPLY_TO=founder@northstarsafetyapp.com`
   - make sure `support@northstarsafetyapp.com` is a real Workspace mailbox or alias under the Workspace-owned domain
6. Add `app.northstarsafetyapp.com` as a custom domain in Render.
7. Create the matching DNS record at the domain provider using the Render target.
8. Update `PUBLIC_BASE_URL` to `https://app.northstarsafetyapp.com`.
9. Redeploy again.
10. Keep charging by direct invoice until the Shopify Partner billing cutover is done.

## Revenue readiness

Northstar is good enough to support the first paid pilot on the current Render URL with direct invoice, but it is not yet host-safe enough for a real customer until PostgreSQL replaces SQLite.
