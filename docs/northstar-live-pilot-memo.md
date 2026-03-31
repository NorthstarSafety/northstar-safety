# Northstar Safety Live Pilot Memo

## What changed with real store data

Northstar is connected to the real Shopify store `p0ubv0-zg.myshopify.com` using the installed private app credentials.

The biggest product change from the real pilot run was not schema drift. It was operational truth:

- Shopify token exchange works through the modern client-credentials flow.
- The real store currently returns zero products.
- The app previously treated an empty product table as a reason to reseed the demo catalog on startup.

That would have made the pilot misleading, because a live but empty store would have looked populated with fake products after a restart.

## Product changes made because of that

- added `Client ID` and `Client secret` support in Settings
- added automatic Shopify access-token minting and caching
- allowed live sync to run with either a direct token or client credentials
- changed zero-product live syncs to clear demo products instead of leaving stale seed data in place
- fixed startup seeding so an empty connected Shopify store stays empty across restarts
- added live empty-state copy, a pilot checklist, and a downloadable Shopify import CSV

## Verified live-store result

- real token exchange succeeded
- real GraphQL catalog access succeeded
- sync completed successfully against the live store
- current live result: `0` products returned by Shopify
- CPSC ingestion still runs successfully against the same workspace
- the dashboard, products, evidence, alerts, cases, and settings pages all render cleanly in the live empty-store state

## Practical next step

To complete the first end-to-end live catalog walkthrough, add at least one real or test product in Shopify admin and run **Sync connected Shopify store** again. The importer, evidence generation, matching, and triage surfaces are ready for that next sync.
