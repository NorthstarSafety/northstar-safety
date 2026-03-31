# Northstar Partner Cutover

Date: 2026-03-23

## Why this cutover exists

The current Shopify app is still shop-owned. Shopify billing is blocked until the app is moved into the correct Partner-managed structure.

## Clean cutover recommendation

Do not force the current shop-owned app into submission work.

Instead:

1. create or link a Partner-managed app with Shopify CLI
2. point that app at the permanent Northstar host
3. copy the final URLs and scopes into the app config
4. test install, billing, uninstall, and reinstall on that app

## Minimum app config to carry forward

- app name: Northstar Safety
- application URL: permanent public Northstar domain
- redirect URL: `<permanent-domain>/auth/callback`
- scopes: `read_products`
- compliance webhooks
- `app/uninstalled` webhook

## Temporary commercial bridge

Until the Partner-managed app is billing-live:

- keep selling private pilots directly
- invoice the first pilots manually
- move them into Shopify-native billing after the production app is ready
