# Northstar Safety Deployment Guide

## Current status

Northstar now supports:

- a public website at `/`
- a workspace at `/workspace`
- a public install page at `/install`
- a billing screen at `/billing`
- Shopify OAuth callback handling at `/auth/callback`
- Shopify compliance and uninstall webhooks

## Recommended provider now

Render is the default permanent-host recommendation for the current build because it fits Northstar's Docker plus single-disk SQLite shape without forcing a larger infrastructure jump yet.

## Temporary public sharing

If you need a fast public demo before a permanent deploy, you can run Northstar locally and expose it through `localtunnel`.

Example:

```powershell
cmd /c start "" /min cmd /k "npx localtunnel --port 8000 --local-host 127.0.0.1 > localtunnel.log 2>&1"
```

Northstar now detects forwarded host headers, so public pages render the tunnel URL correctly even when `PUBLIC_BASE_URL` is still localhost.

## Recommended permanent shape

Use one small Ubuntu VM or container with:

- Python 3.11+
- PostgreSQL for the application database
- persistent storage for uploads and backups under `northstar_safety_data`
- HTTPS via Caddy
- a stable `PUBLIC_BASE_URL`
- Shopify app redirect URLs updated to match the final host
- SMTP credentials for outbound support and contact delivery

Recommended domain split:

- marketing site: `https://www.northstarsafetyapp.com`
- app host: `https://app.northstarsafetyapp.com`

## Docker

Files:

- [`Dockerfile`](C:/Users/onkha/OneDrive/Documents/New%20project/Dockerfile)
- [`docker-compose.northstar.yml`](C:/Users/onkha/OneDrive/Documents/New%20project/docker-compose.northstar.yml)

Run:

```powershell
docker compose -f docker-compose.northstar.yml up --build -d
```

## VM / systemd

Files:

- [`deploy/northstar-safety.service`](C:/Users/onkha/OneDrive/Documents/New%20project/deploy/northstar-safety.service)
- [`deploy/Caddyfile`](C:/Users/onkha/OneDrive/Documents/New%20project/deploy/Caddyfile)
- [`run_production.py`](C:/Users/onkha/OneDrive/Documents/New%20project/run_production.py)

Suggested process:

1. Copy the repo to `/srv/northstar-safety`
2. Create a virtualenv
3. Install `requirements.txt`
4. Copy [`.env.example`](C:/Users/onkha/OneDrive/Documents/New%20project/.env.example) to `.env`
5. Set `NORTHSTAR_DATA_DIR=/srv/northstar-safety/data`
6. Set `PUBLIC_BASE_URL` to the final live hostname
7. Set `PUBLIC_SUPPORT_EMAIL` and `PUBLIC_DEMO_LINK`
8. Configure Shopify credentials and app settings
9. Add the live `/auth/callback` URL in Shopify Dev Dashboard
10. Install the systemd unit and Caddy config
11. Start the service and run the smoke test

## Minimum production env

- `APP_HOST=0.0.0.0`
- `APP_PORT=8000`
- `APP_SECRET_KEY=<strong random value>`
- `NORTHSTAR_DATA_DIR=/srv/northstar-safety/data`
- `NORTHSTAR_DATABASE_URL=postgresql://...`
- `PUBLIC_BASE_URL=https://app.your-domain`
- `PUBLIC_SUPPORT_EMAIL=support@your-domain`
- `PUBLIC_DEMO_LINK=https://your-calendly-or-mailto`
- `SHOPIFY_CLIENT_ID`
- `SHOPIFY_CLIENT_SECRET`
- `SHOPIFY_BILLING_REQUIRED=true`
- `SMTP_MODE=smtp`
- `SMTP_HOST`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL=support@your-domain`

Optional:

- `BASIC_AUTH_USERNAME`
- `BASIC_AUTH_PASSWORD`
- `SHOPIFY_ADMIN_TOKEN`
- `ENABLE_LIVE_HEALTH_CANADA=true`

## Verification after deploy

Run:

```powershell
.\.venv\Scripts\python.exe scripts\northstar_smoke_test.py
```

Then verify manually:

- `/install` opens
- `/billing` loads
- `/robots.txt` returns the live domain in the sitemap line
- Shopify authorize URLs point back to your live `/auth/callback`

You can also run:

```powershell
.\.venv\Scripts\python.exe scripts\northstar_launch_check.py
```

Or point it at a public URL:

```powershell
$env:NORTHSTAR_BASE_URL="https://your-public-domain"
.\.venv\Scripts\python.exe scripts\northstar_launch_check.py
```

Create a backup artifact:

```powershell
.\.venv\Scripts\python.exe scripts\northstar_backup.py
```

Migrate the live workspace into PostgreSQL:

```powershell
.\.venv\Scripts\python.exe scripts\northstar_migrate_to_postgres.py --target-url "postgresql://..."
```

## Remaining production blockers

- migrate the current Shopify app into Shopify Partners so Billing API can complete
- add the permanent host to Shopify redirect URLs
- finish App Store submission assets
- move beyond the current single-store workspace model before broad public distribution
