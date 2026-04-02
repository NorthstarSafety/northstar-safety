# Northstar Render Live Setup Memo

Date: 2026-03-30

## What is live now

Northstar is live on Render at:

- `https://northstar-safety.onrender.com`
- latest hosted runtime behavior now includes the relative `/static/...` asset path fix from the recent production-hardening push
- hosted verification now also runs through the new remote-only mode in `scripts/northstar_launch_check.py`

The Render service is:

- service name: `northstar-safety`
- type: Docker web service
- plan: `Starter`
- repo: `NorthstarSafety/northstar-safety`
- branch: `main`
- disk mount: `/data`
- disk size: `1 GB`
- health check path: `/healthz`
- build context: `.`
- Dockerfile path: `./Dockerfile`

## What was verified live

Hosted route checks:

- `/` -> `200`
- `/install` -> `200`
- `/billing` -> `200`
- `/healthz` -> `200`
- `/robots.txt` -> `200`
- `/sitemap.xml` -> `200`

Hosted workflow proof:

- updated the live workspace settings at `/settings`
- set the connected Shopify store domain to `p0ubv0-zg.myshopify.com`
- confirmed the hosted workspace now shows the connected live store target
- restored the hosted workspace back to `Shopify live` mode after the latest deploy came up on a fresh SQLite-backed settings state
- ran a hosted catalog sync successfully
- Northstar reported: `Synced 2 products from My Store.`
- re-ran official alert ingestion successfully from the hosted workspace
- Northstar reported: `Live CPSC recalls ingested and re-matched against the catalog. | Live Health Canada recalls ingested and re-matched against the catalog.`
- the hosted workspace now shows live Shopify products, live alerts, and an open case view
- created the first live named workspace user for the founder
- verified live sign-in to the hosted workspace using the named user session
- added an attributed case timeline event in the hosted workspace as the named founder user
- downloaded a live hosted case summary proof artifact to `output/hosted-customer-proof/hosted-case-summary-case-223e4f33a6.txt`
- downloaded a second hosted case summary after the latest deploy verification to `output/hosted-customer-proof/hosted-case-summary-case-0934551fbb-rerun.txt`

## What was configured in Render

Configured in the Render service:

- `APP_NAME`
- `APP_ENV`
- `APP_HOST`
- `SESSION_COOKIE_SECURE`
- `NORTHSTAR_DATA_DIR`
- `NORTHSTAR_UPLOAD_DIR`
- `NORTHSTAR_BACKUP_DIR`
- `ENABLE_LIVE_CPSC`
- `ENABLE_LIVE_HEALTH_CANADA`
- `SHOPIFY_API_VERSION`
- `SHOPIFY_APP_SCOPES`
- `SHOPIFY_BILLING_REQUIRED`
- `SHOPIFY_BILLING_PLAN_NAME`
- `SHOPIFY_BILLING_PRICE_USD`
- `SHOPIFY_BILLING_INTERVAL`
- `SHOPIFY_BILLING_TRIAL_DAYS`
- `SHOPIFY_BILLING_TEST_MODE`
- `APP_SECRET_KEY`
- `PUBLIC_BASE_URL`
- `PUBLIC_SUPPORT_EMAIL`
- `PUBLIC_SALES_EMAIL`
- `PUBLIC_DEMO_LINK`
- `PUBLIC_COMPANY_NAME`
- `PUBLIC_COMPANY_LOCATION`
- `PUBLIC_SUPPORT_HOURS`
- `PUBLIC_REVIEW_MODE`
- `SMTP_MODE`
- `SMTP_FROM_EMAIL`
- `SMTP_REPLY_TO`
- `SHOPIFY_CLIENT_ID`
- `SHOPIFY_CLIENT_SECRET`
- `NORTHSTAR_LAUNCH_CHANNEL`

Configured in the hosted Northstar workspace:

- `shopify_store_domain = p0ubv0-zg.myshopify.com`

## What is still blocked or incomplete

Still not complete:

- Render PostgreSQL is not provisioned or wired yet, so this deploy is still running on SQLite-on-disk rather than `NORTHSTAR_DATABASE_URL`
- SMTP delivery is still not configured
- `app.northstarsafetyapp.com` is not attached yet
- Shopify Billing API is still blocked by the app ownership / Partner cutover path
- the latest deploy appears to have come up with a fresh SQLite-backed workspace state, so durable production persistence should still be treated as unresolved until PostgreSQL is live

## Current scripted hosted check

Using the remote-only launch check against the live Render URL with the named founder account now returns the real hosted blockers:

- database: SQLite
- smtp: blocked
- billing: blocked because the app is still shop-owned and not yet in Shopify Partners

The same hosted check also confirms:

- `/`, `/login`, `/install`, `/healthz`, `/robots.txt`, and `/sitemap.xml` are all reachable
- the hosted workspace accepts the named founder login
- the expected Shopify store `p0ubv0-zg.myshopify.com` is visible
- the hosted workspace is showing 2 live products

## Exact Postgres and SMTP handoff

Because the remaining blockers are now provider-side rather than code-side, the smallest exact handoff is:

1. In Render, create a managed PostgreSQL database in the same region as the web service.
2. Copy the Render internal database URL into `NORTHSTAR_DATABASE_URL` on the `northstar-safety` web service.
3. Redeploy the service.
4. If any SQLite state still matters, run `scripts/northstar_migrate_to_postgres.py` once against the old SQLite file and the new Postgres URL during the cutover.
5. For SMTP, use Google Workspace SMTP relay on `support@northstarsafetyapp.com` with:
   - `SMTP_MODE=smtp`
   - `SMTP_HOST=smtp-relay.gmail.com`
   - `SMTP_PORT=587`
   - `SMTP_USERNAME=`
   - `SMTP_PASSWORD=`
   - `SMTP_FROM_EMAIL=support@northstarsafetyapp.com`
   - `SMTP_REPLY_TO=support@northstarsafetyapp.com`
   - `SMTP_STARTTLS=true`
   - Render egress IPs allowlisted in Google Workspace SMTP relay
6. Redeploy again and use the Settings page test-email button.

If Google Workspace relay is not working yet, the exact remaining blocker is: allowlist the Render outbound IPs inside Google Workspace SMTP relay settings.

## Important live note

The hosted Render app is now serving the newer runtime behavior with relative static asset URLs, so the production-hardening deploy has landed. The remaining Render risk is no longer the stale build. It is the fact that the live stack is still SQLite-backed and not yet on managed PostgreSQL.

## Exact next founder actions

1. Create a managed PostgreSQL database and set `NORTHSTAR_DATABASE_URL`.
2. If any SQLite state still matters, run `scripts/northstar_migrate_to_postgres.py` during the cutover.
3. Add SMTP credentials:
   - `SMTP_HOST`
   - `SMTP_FROM_EMAIL`
   - optional `SMTP_USERNAME`
   - optional `SMTP_PASSWORD`
4. Sign in with the live named workspace user and confirm the password is stored safely in the local operator handoff.
5. Add `app.northstarsafetyapp.com` to the Render service and then update DNS.
6. After the custom domain is live, update `PUBLIC_BASE_URL`.
7. Move the Shopify app into Partners before using `/billing/start`, because the live blocker is: `This Shopify app is still shop-owned. Move it into the Shopify Partners area before Northstar can use the Billing API.`
8. Keep first-pilot revenue on direct invoice until the Shopify Partner billing cutover is complete.

## Practical revenue state

Northstar is now live enough to support direct pilot demos and private paid-pilot onboarding on the Render URL, with the biggest remaining production risk being the SQLite-to-PostgreSQL cutover rather than the web deployment itself.
