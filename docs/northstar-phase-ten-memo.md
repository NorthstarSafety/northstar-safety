# Northstar Phase 10 Memo

Date: 2026-03-23

## What changed

Northstar moved from "public-looking" to "publicly reachable and install-aware."

The biggest product changes were:

- real public install page at `/install`
- real Shopify OAuth start path
- real Shopify OAuth callback handler
- persisted Shopify install metadata
- billing screen and Billing API path
- Shopify uninstall webhook handling
- better public URL handling behind a reverse proxy or tunnel

## What real launch requirements changed in the product

### Public URL handling

Northstar now derives its public base URL from forwarded headers when the configured base URL is still localhost. That makes temporary public tunnels usable without rewriting the app configuration first.

### Install flow

Northstar no longer depends only on manual credential entry in settings. The app can now generate a Shopify authorize URL and handle the callback on return.

### Billing visibility

Northstar now exposes the commercial path in-product. When billing is blocked, the founder sees the exact Shopify blocker instead of an ambiguous failure.

### Review posture

Northstar now has:

- compliance webhook handling
- app uninstall handling
- a clearer install surface
- a clearer billing surface

## What is fully ready

- public website
- temporary live public URL
- public install page
- OAuth callback implementation
- billing UI and mutation path
- Shopify compliance webhook handling
- uninstall webhook handling

## What is still blocked externally

- the current Shopify app must be moved into Shopify Partners before Billing API charges can complete
- the final hosted callback URL must be added to Shopify redirect settings
- the workspace is still single-store oriented, not fully multi-tenant

## Exact next step

Move the Shopify app into Shopify Partners, add the final hosted callback URL, and run one end-to-end install plus billing confirmation on the permanent host.
