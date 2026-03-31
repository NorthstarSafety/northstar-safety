# Northstar Safety Setup Guide

## Local run

1. Install requirements:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. Start the app:

   ```powershell
.\.venv\Scripts\python.exe run_safety.py
   ```

3. Open:

   ```text
   http://127.0.0.1:8000
   ```

## Private pilot environment variables

Use either the root `.env.example` or `northstar_safety/.env.example` as reference.

Key values:

- `APP_HOST`
- `APP_PORT`
- `NORTHSTAR_DATA_DIR`
- `BASIC_AUTH_USERNAME`
- `BASIC_AUTH_PASSWORD`
- `SHOPIFY_STORE_DOMAIN`
- `SHOPIFY_ADMIN_TOKEN`
- `SHOPIFY_CLIENT_ID`
- `SHOPIFY_CLIENT_SECRET`
- `SHOPIFY_API_VERSION`
- `ENABLE_LIVE_CPSC`

## Live pilot quick start

1. Start Northstar.
2. Open `/settings`.
3. Set:
   - `Catalog mode` to `Shopify live`
   - `Shopify store domain`
   - either a direct admin token or the Shopify app client credentials
4. Save settings.
5. Run **Sync connected Shopify store**.
6. If the store is empty, import [`northstar-pilot-products.csv`](..\northstar_safety\static\northstar-pilot-products.csv) into Shopify and sync again.
7. Fill the compliance profile fields Shopify does not provide.
8. Attach the first evidence document.
9. Run **Ingest official alerts**.
10. Review matches and keep the case trail current.

## Verified live workflow

This workspace has already been verified on real synced Shopify products:

- `BIC-HC-001` - Bicystar Convertible High Chair
- `SNS-FEED-001` - SnackSprout Silicone Feeding Set

Verified steps:

- live Shopify sync
- product-profile completion
- document attachment on both SKUs
- live CPSC ingest
- confirmed true recall match
- dismissed false positives with written reasons
- updated case status and action log

## Suggested founder demo path

1. Dashboard
2. Products
3. Bicystar product detail
4. Bicystar alert detail
5. Bicystar case detail
6. SnackSprout product detail
7. Settings

Reference:

- [`docs/demo-script.md`](demo-script.md)

## Smoke test

Run:

```powershell
.\.venv\Scripts\python.exe scripts\northstar_smoke_test.py
```

Set `NORTHSTAR_BASE_URL` when testing a non-local environment.

## Current persistence paths

- database: `northstar_safety_data\northstar_safety.db`
- uploads: `northstar_safety_data\uploads`

## Important note

Northstar preserves demo fallback, but the current workspace is no longer an empty live-store setup. It contains a real synced pilot catalog and a verified case workflow.
