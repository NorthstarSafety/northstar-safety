# Northstar Founder Launch Runbook

Date: 2026-03-23

## First credential

Get access to:

1. the permanent Render account or chosen host
2. the permanent domain / DNS
3. the Shopify Partner organization for the production app

## First deploy

1. Use [`render.northstar.yaml`](C:/Users/onkha/OneDrive/Documents/New%20project/render.northstar.yaml)
2. Let the Blueprint provision the managed PostgreSQL database
3. Set the env vars in [`northstar-secrets-map.md`](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-secrets-map.md)
4. Deploy to the provider URL first
5. Run [`scripts/northstar_launch_check.py`](C:/Users/onkha/OneDrive/Documents/New%20project/scripts/northstar_launch_check.py)

## First permanent domain

1. Add `app.northstarsafetyapp.com` as the custom domain on the host
2. Update `PUBLIC_BASE_URL`
3. Redeploy
4. Verify `/robots.txt` and `/sitemap.xml`

## First Shopify production app step

1. Create or link the production app in Shopify Partners
2. Set `application_url` to `/app`
3. Set redirect URL to `/auth/callback`
4. Set scopes to `read_products`
5. Register compliance and uninstall webhooks

## First install

1. Open the permanent `/install` page or the Shopify-owned app surface
2. Confirm OAuth approval
3. Return to Northstar successfully
4. Confirm the shop shows as an active install

## First billing approval

1. Open `/billing`
2. Start the recurring plan approval
3. Confirm the subscription becomes active

If billing is still blocked:

- invoice the pilot directly
- keep the pricing page honest
- continue onboarding pilots while the Partner-managed app finishes cutover

## First pilot onboarding

1. Sync the live catalog
2. Upload the first evidence packet
3. Refresh official alerts
4. Review the first alert match
5. Open the first case

## First revenue path

If App Store approval is still pending:

- sell private pilots directly
- use the install page and external workspace
- bill by invoice until Shopify-native billing is available on the production app
