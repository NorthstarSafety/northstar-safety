# Northstar Safety Phase 5 Memo

## What changed

Phase 5 turned Northstar from a live-connected prototype into a more credible private pilot product.

The work focused on the places where a design partner will feel friction fastest:

- getting from empty live store to first real SKU
- making product pages usable when Shopify leaves key compliance fields blank
- making match review less ambiguous
- making the app safer to expose in a private environment
- packaging a clean deployment path

## Product changes

- added a pilot checklist and recommended-next-step system on the dashboard and settings page
- added a downloadable Shopify import CSV for the first live test products
- added editable compliance profiles on product pages for classification, supplier, origin, age grade, and jurisdictions
- added readiness scoring and clearer evidence rollups on products
- tightened alert review with clearer guidance, review metadata, and required dismissal reasons
- added optional basic auth for private pilot deployment
- added deployment assets:
  - `Dockerfile.northstar`
  - `docker-compose.northstar.yml`
  - `scripts/northstar_smoke_test.py`

## What real usage changed

The live store did not force major schema changes. It forced workflow changes.

The important lesson was that a real but empty store is still a real pilot state, and the product needs to guide the operator through it instead of pretending demo data is live data.

That led to:

- persistent empty-live handling
- a stronger first-sync experience
- a faster path to import the first real test SKUs

## Current pilot state

- live Shopify auth works
- live Shopify sync works
- live CPSC ingestion works
- current connected store still returns zero products
- the installed Shopify app currently has read product access, so the first test SKU still needs to be created or imported in Shopify admin
- the next step is to import or create the first real Shopify product and rerun sync
