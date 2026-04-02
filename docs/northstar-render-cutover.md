# Northstar Render Cutover

Date: 2026-03-23

## Chosen provider

Render is the recommended permanent-host path for the current Northstar build.

Why this fits the current product:

- Dockerfile already exists
- Northstar is still a single-store pilot product
- Render can provision the app and the managed PostgreSQL database together
- uploads and local backup artifacts can still live on one attached disk
- HTTPS and custom domains are straightforward in Render

## Blueprint

Use [`render.northstar.yaml`](C:/Users/onkha/OneDrive/Documents/New%20project/render.northstar.yaml).

Important note:

- Render Blueprints are applied from a Git repository in the Render dashboard.
- If Northstar is not yet in a connected remote repo, create or push the repo first, or use an equivalent provider path that accepts a Docker source.

## Exact cutover sequence

1. Create a new Render web service from this repo or uploaded codebase
2. Point Render at `render.northstar.yaml`
3. Let the Blueprint create the managed PostgreSQL database
4. Attach a persistent disk mounted at `/data`
5. Fill in the required secret env vars
6. Deploy once on the default Render URL
7. Confirm `/healthz`, `/install`, `/billing`, `/robots.txt`, and `/sitemap.xml`
8. Add the permanent custom domain
9. Update `PUBLIC_BASE_URL`
10. Re-run the deploy
11. Update Shopify app URLs to the permanent domain

## Required env vars

- `PUBLIC_BASE_URL`
- `APP_SECRET_KEY`
- `NORTHSTAR_DATABASE_URL` via the Blueprint database link
- `PUBLIC_SUPPORT_EMAIL`
- `PUBLIC_SALES_EMAIL`
- `PUBLIC_DEMO_LINK`
- `SHOPIFY_CLIENT_ID`
- `SHOPIFY_CLIENT_SECRET`
- `SMTP_MODE`
- `SMTP_HOST`
- `SMTP_AUTH_REQUIRED`
- `SMTP_HELO_DOMAIN`
- `SMTP_FROM_EMAIL`
- optional `SMTP_USERNAME`
- optional `SMTP_PASSWORD`

Recommended SMTP path for the current Google Workspace setup:

- `SMTP_HOST=smtp-relay.gmail.com`
- `SMTP_PORT=587`
- `SMTP_AUTH_REQUIRED=false`
- `SMTP_STARTTLS=true`
- leave `SMTP_USERNAME` and `SMTP_PASSWORD` blank
- `SMTP_HELO_DOMAIN=app.northstarsafetyapp.com`
- allowlist the Render outbound IPs in Google Workspace SMTP relay

Recommended:

- `BASIC_AUTH_USERNAME`
- `BASIC_AUTH_PASSWORD`

## After first deploy

Run:

```powershell
.\.venv\Scripts\python.exe scripts\northstar_launch_check.py
```

And against the public URL:

```powershell
$env:NORTHSTAR_BASE_URL="https://your-render-domain"
.\.venv\Scripts\python.exe scripts\northstar_launch_check.py
```
