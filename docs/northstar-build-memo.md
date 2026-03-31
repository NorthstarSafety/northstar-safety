# Northstar Safety Build Memo

## What exists now

Northstar Safety is a server-rendered FastAPI pilot product for Shopify child-product merchants. The live product includes:

- dashboard
- products and SKU list
- product detail and compliance profile
- evidence queue and document uploads
- alerts feed
- match review controls
- cases and action log
- settings and pilot admin

## Core capabilities

- real Shopify Admin GraphQL catalog sync
- Shopify client-ID/client-secret token exchange with cached token refresh
- demo fallback when live credentials are missing
- live CPSC ingest
- evidence checklist generation by product classification
- missing and stale evidence states
- alert-to-product matching with confidence and rationale
- confirm and dismiss review flow with required false-positive reasons
- investigation case trail with notes and timestamps
- optional basic auth for private pilot deployment

## What real SKU usage changed

Using the connected live Shopify store changed the product in practical ways:

- importer now handles live title, vendor, type, and SKU changes cleanly
- case reopening is fixed so a newly high-confidence live overlap reopens its case correctly
- case lists now prioritize active work ahead of closed history
- founder demo data is no longer hypothetical:
  - `BIC-HC-001` is a live synced recall-demo SKU
  - `SNS-FEED-001` is a live synced non-alert evidence SKU

## Current validated workspace state

- 2 live Shopify products
- 2 attached product documents
- 1 confirmed recall overlap
- 6 dismissed false positives
- 1 open investigation case under review
- completed pilot checklist on the dashboard

## Architecture

- backend: FastAPI
- rendering: Jinja templates
- storage: SQLite
- uploads: local disk
- deployment target: small VM or container

This remains the right stack for a founder-run pilot because it is fast to iterate, cheap to host, and easy to debug.

## What is still intentionally not built

- Shopify write-back actions
- user accounts beyond shared basic auth
- automated notifications
- Health Canada or other secondary live feeds
- managed secrets or object storage
- formal filing workflows

## Deployment posture

Northstar is deployment-ready:

- root [`Dockerfile`](..\Dockerfile) targets Northstar
- compose file exists
- systemd unit exists
- Caddy reverse-proxy example exists

I did not complete a remote cloud deployment from this workspace because Docker is not installed on this machine and no external hosting credentials were available.
