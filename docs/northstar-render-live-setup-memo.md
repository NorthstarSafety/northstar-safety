# Northstar Render Live Setup Memo

Date: 2026-03-30

## What was completed

- Opened the live Render new-service flow against the repo `NorthstarSafety/northstar-safety`
- Confirmed Render detected the repo as a Docker service on branch `main`
- Configured the service name as `northstar-safety`
- Imported the current Northstar production env set into Render
- Expanded the advanced section and configured:
  - persistent disk mount path: `/data`
  - persistent disk size: `1 GB`
  - health check path: `/healthz`
  - Docker build context directory: `.`
  - Dockerfile path: `./Dockerfile`
- Cleared the remaining invalid environment-row state so the Render form would submit cleanly

## Render blocker reached

Render accepted the form and then opened the **Add Card** billing modal before it would create the service.

That is the current hard blocker.

The deploy is not failing because of Northstar code or Render form validation anymore.

## Env vars filled in Render

Filled:

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

Still blocked or not yet available:

- `NORTHSTAR_DATABASE_URL`
- `SMTP_HOST`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- permanent custom domain value for `PUBLIC_BASE_URL`

## What is not live yet

- No Render service URL yet, because the service has not been created past the billing gate
- No managed PostgreSQL database yet, because the Render resource creation has not completed
- No hosted route verification yet, because the app has not reached a live Render URL
- No DNS change yet for `app.northstarsafetyapp.com`

## Exact next founder click

1. In the open Render **Add Card** modal, complete the billing-card form and submit it.
2. Let Render finish creating the `northstar-safety` service.
3. Copy the generated `onrender.com` URL.
4. Run the hosted launch check:

```powershell
$env:NORTHSTAR_BASE_URL="https://YOUR-RENDER-URL"
.\.venv\Scripts\python.exe scripts\northstar_launch_check.py
```

5. Verify:
   - `/`
   - `/install`
   - `/billing`
   - `/healthz`
   - `/robots.txt`
   - `/sitemap.xml`
6. If Render provisions PostgreSQL separately instead of wiring it automatically in this manual flow, create the managed database and set `NORTHSTAR_DATABASE_URL`.
7. Only after the temporary Render URL works, add `app.northstarsafetyapp.com` and update `PUBLIC_BASE_URL`.

## Practical note

The live Render Blueprint route appeared unstable in the current dashboard session, so this setup was driven through Render's standard manual web-service flow using the same repo and deployment assumptions. That got the setup all the way to the billing gate without changing the Northstar deployment shape.
