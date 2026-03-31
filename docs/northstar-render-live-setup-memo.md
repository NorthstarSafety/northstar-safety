# Northstar Render Live Setup Memo

Date: 2026-03-30

## What is live now

Northstar is live on Render at:

- `https://northstar-safety.onrender.com`

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
- ran a hosted catalog sync successfully
- Northstar reported: `Synced 2 products from My Store.`
- the hosted workspace now shows live Shopify products, live alerts, and an open case view

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
- no named workspace user has been created yet

## Important live note

After the first deploy succeeded, a Render-safe polish fix was pushed to `main` in commit `f894c2f`:

- enables proxy headers in `run_production.py`
- switches template static assets to relative `/static/...` paths

That change is in GitHub now, but the Render service was still serving the older build at the time of this memo. The hosted app is already usable, but one more deploy should pull in the clean static-asset URL behavior.

## Exact next founder actions

1. In Render, trigger a deploy of the latest commit (`f894c2f`) for `northstar-safety`.
2. Create a managed PostgreSQL database and set `NORTHSTAR_DATABASE_URL`.
3. Add SMTP credentials:
   - `SMTP_HOST`
   - `SMTP_USERNAME`
   - `SMTP_PASSWORD`
   - `SMTP_FROM_EMAIL`
4. Create the first named workspace user in `https://northstar-safety.onrender.com/settings`.
5. Add `app.northstarsafetyapp.com` to the Render service and then update DNS.
6. After the custom domain is live, update `PUBLIC_BASE_URL`.
7. Keep first-pilot revenue on direct invoice until the Shopify Partner billing cutover is complete.

## Practical revenue state

Northstar is now live enough to support direct pilot demos and private paid-pilot onboarding on the Render URL, with the biggest remaining production risk being the SQLite-to-PostgreSQL cutover rather than the web deployment itself.
