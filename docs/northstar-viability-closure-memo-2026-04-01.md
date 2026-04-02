# Northstar Viability Closure Memo

Date: 2026-04-01

## Complete

- `app.northstarsafetyapp.com` is the working public front door and the main public routes respond successfully:
  - `/`
  - `/product`
  - `/pricing`
  - `/install`
  - `/contact`
  - `/support`
  - `/security`
  - `/healthz`
  - `/robots.txt`
  - `/sitemap.xml`
- Public pricing and commercial language are aligned around the active offer:
  - `$300` one-time founding pilot
  - `$149/month` explicit opt-in continuation
- The app now has a higher-trust customer account layer for a pilot team:
  - password change
  - password reset request and token flow
  - teammate invite links
  - named-user attribution still preserved
- The first-customer operator workflow is clearer in the product:
  - better first-run guidance
  - clearer empty-state language
  - search on evidence, alerts, and cases
  - renewal watch for expiring documents
  - product coverage summary export
  - case summary share/send surface
- A clean local customer-flow rehearsal now passes for:
  - founder login
  - invite creation
  - invite acceptance
  - password change
  - password reset
  - operator login
  - product coverage export
  - alerts filtering
  - evidence search

Proof artifact:

- `output/verification/northstar-phase18-local-proof.txt`

## In Progress

- The public app-domain copy and usability improvements are complete in code, but still depend on the latest Render deploy to become the live public experience if the running host is behind the local repo state.
- The hosted protected-route verification is only partially complete this round:
  - public routes are verified live
  - the old founder credential in `output/hosted-customer-proof/hosted-operator-handoff.txt` no longer works on `app.northstarsafetyapp.com`
  - that means protected-route verification on the current hosted workspace needs either the current password or a fresh named user before it can be re-proved end to end
- Real SMTP-triggered invite/reset/reminder delivery is wired in code, but still depends on live SMTP configuration in Render before it can be verified on the hosted stack.

## Externally Blocked

- Managed PostgreSQL on Render is still not verified live.
- SMTP is still not verified live.
- Shopify Billing API is still blocked by the Partner-app cutover, so direct Stripe remains the live commercial path.
- Hosted protected-route proof is blocked by the stale live founder credential unless a fresh password or new live named user is created.

## Good Enough For Customer 1

- Public landing, pricing, install, contact, support, and security surfaces are in place.
- Direct payment is ready through the live Stripe pilot and continuation links.
- The core product workflow is still good enough for a founder-led pilot:
  - sync
  - evidence review
  - alert review
  - case updates
  - exports
- Named users, teammate invites, and password flows are now in place for a small pilot team.

## Still Needed Before Customer 3 And Customer 10

- Hosted Postgres cutover with verified persistence
- Hosted SMTP with verified outbound delivery
- Repeatable live-user provisioning and credential recovery
- Stronger operator monitoring for failed syncs, failed alert refreshes, and failed email sends
- Cleaner multi-customer operational runbooks once more than one merchant is live at the same time

## Exact Next Founder Actions

1. Redeploy the latest `main` commit on Render if auto-deploy has not already picked it up.
2. Create or reset the live named founder user so hosted protected-route verification can be re-run.
3. Wire Render Postgres and set `NORTHSTAR_DATABASE_URL`.
4. Add SMTP credentials and use the Settings page SMTP test.
5. Keep using the direct Stripe pilot link until Shopify Partner billing is ready.

## Bottom Line

Northstar is materially more credible, safer for a first paying pilot, and less founder-fragile than it was before this pass. The biggest remaining risks are now host-side and operational, not product-shape uncertainty.
