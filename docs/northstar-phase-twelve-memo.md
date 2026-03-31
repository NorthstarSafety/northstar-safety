# Northstar Phase 12 Memo

Date: 2026-03-23

## What is done

- permanent-host cutover pack is prepared
- Render is chosen as the default permanent-host path
- Shopify Partner cutover docs are prepared
- the revenue bridge is clearer and documented
- a thin `/app` admin-facing layer now exists
- uninstall and reinstall-state behavior are verified
- the launch checker now reports real blockers in one command

## What is blocked by access

- permanent host account credentials
- permanent domain and DNS access
- Shopify Partner organization access for the production app

## What is blocked by Shopify policy or fit

- the current app is still shop-owned for billing
- the current product is still strongest as an external workspace
- full public App Store fit likely still needs more embedded-admin polish

## What makes money first

The fastest revenue path is still:

- direct paid pilots
- private install/onboarding
- external Northstar workspace
- direct invoicing until Shopify-native billing is ready on the Partner-managed app

## Exact next step when credentials arrive

1. deploy with the Render cutover pack
2. add the permanent domain
3. link the Partner-managed Shopify app
4. run install
5. run billing
6. onboard the first paid pilot on the permanent host
