# Northstar Reviewer Instructions

## Test goal

Verify that Northstar can be installed on a Shopify store, connect the live catalog, and expose a usable safety workflow.

## Entry point

1. Open the public Northstar install page
2. Enter the Shopify store domain
3. Continue to Shopify and approve the requested product access

## After returning to Northstar

1. Confirm the workspace loads successfully
2. Open the dashboard
3. Confirm products appear after sync
4. Open a product and confirm evidence items exist
5. Open alerts and confirm the alert-review screen loads
6. Open billing and confirm the pricing flow is visible

## Webhook behavior

Northstar subscribes to:

- compliance topics
- `app/uninstalled`

## What Northstar does not currently require

- customer data
- order data
- storefront theme access

## Best review path

Use a store that has at least one product so the catalog and evidence workflow are visible immediately after install.
