# Northstar Secrets Map

## Production host secrets

- `APP_SECRET_KEY`
  Purpose: signed user sessions and login safety

- `PUBLIC_BASE_URL`
  Purpose: permanent public URL

- `NORTHSTAR_DATABASE_URL`
  Purpose: managed PostgreSQL connection string

- `PUBLIC_SUPPORT_EMAIL`
  Purpose: support and trust pages

- `PUBLIC_SALES_EMAIL`
  Purpose: contact and sales routing

- `PUBLIC_DEMO_LINK`
  Purpose: demo CTA destination

- `BASIC_AUTH_USERNAME`
  Purpose: optional workspace protection during private rollout

- `BASIC_AUTH_PASSWORD`
  Purpose: optional workspace protection during private rollout

- `SMTP_MODE`
  Purpose: enable or disable real outbound email delivery

- `SMTP_HOST`
  Purpose: SMTP endpoint for support and website notifications

- `SMTP_PORT`
  Purpose: SMTP port

- `SMTP_USERNAME`
  Purpose: optional SMTP auth user for authenticated SMTP only

- `SMTP_PASSWORD`
  Purpose: optional SMTP auth password for authenticated SMTP only

- `SMTP_FROM_EMAIL`
  Purpose: sender address for operational mail

- `SMTP_REPLY_TO`
  Purpose: reply routing for outbound mail

For Google Workspace SMTP relay:

- use `SMTP_HOST=smtp-relay.gmail.com`
- keep `SMTP_STARTTLS=true`
- leave `SMTP_USERNAME` and `SMTP_PASSWORD` blank
- allowlist the host provider egress IPs in Google Workspace SMTP relay settings

## Shopify production secrets

- `SHOPIFY_CLIENT_ID`
  Purpose: OAuth install and embedded/admin-facing integration

- `SHOPIFY_CLIENT_SECRET`
  Purpose: OAuth callback validation and webhook validation

Optional:

- `SHOPIFY_ADMIN_TOKEN`
  Purpose: manual fallback or debugging only

## Non-secret but important config

- `SHOPIFY_APP_SCOPES=read_products`
- `SHOPIFY_BILLING_REQUIRED=true`
- `SHOPIFY_BILLING_PLAN_NAME=Northstar Safety Founding Plan`
- `SHOPIFY_BILLING_PRICE_USD=249`
- `SHOPIFY_BILLING_INTERVAL=EVERY_30_DAYS`
- `SHOPIFY_BILLING_TRIAL_DAYS=14`
- `ENABLE_LIVE_CPSC=true`
- `ENABLE_LIVE_HEALTH_CANADA=true`
