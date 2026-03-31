# Northstar Shopify Review Readiness

Date: 2026-03-23

## Current position

Northstar is materially closer to Shopify submission, but it is not fully submit-ready yet.

Northstar now has:

- a live public install page
- a real OAuth start path at `/install`
- a real OAuth callback route at `/auth/callback`
- a billing screen and Shopify Billing API mutation path
- compliance webhook handling
- app-uninstalled webhook handling
- privacy, terms, support, contact, and pricing pages

## What is now truly ready

### 1. Public trust layer

- public website and positioning pages
- privacy policy
- terms of service
- support page
- contact flow

### 2. Install scaffolding

- Shopify authorize URL generation for a real shop
- automatic OAuth start when Shopify provides the `shop` parameter
- stateful OAuth callback handling
- Shopify HMAC validation for callbacks and webhooks
- install metadata persistence in `shop_installs`

### 3. Billing-ready product path

- recurring billing mutation path is implemented
- billing status is visible in the app
- billing failures are surfaced clearly instead of failing silently

### 4. Minimum data posture

Northstar still keeps a narrow permissions posture:

- product data only for the current workflow
- no customer data required
- no order data required

That is favorable for future protected-customer-data review.

## What is still externally blocked

### 1. App ownership for billing

Northstar can call the Billing API, but the current Shopify app returns this live blocker:

`This Shopify app is still shop-owned. Move it into the Shopify Partners area before Northstar can use the Billing API.`

That means:

- billing code is implemented
- billing cannot complete on the current app until the app is migrated into Shopify Partners

### 2. Allowed redirect URLs in Shopify

The OAuth path now generates a real callback URL, but the live hosted domain still needs to be added in Shopify Dev Dashboard as an allowed redirect URL before a full install round-trip can be verified on that domain.

### 3. Multi-store workspace isolation

Northstar's current data model is still optimized for one live merchant workspace at a time.

That is acceptable for:

- a private live rollout
- a reviewer testing one store

It is not yet ideal for:

- broad public distribution across many simultaneous merchants

### 4. Submission package assets

Northstar still needs:

- App Store listing copy
- final screenshots
- reviewer instructions
- a clean recorded install and onboarding walkthrough

### 5. Embedded admin experience

Shopify's App Store requirements expect a consistent embedded admin experience. Northstar's current product is still strongest as a protected external workspace, so embedded admin polish remains a real submission blocker.

## Local readiness artifacts

- [`shopify.app.toml.example`](C:/Users/onkha/OneDrive/Documents/New%20project/shopify.app.toml.example)
- [`northstar_safety/app.py`](C:/Users/onkha/OneDrive/Documents/New%20project/northstar_safety/app.py)
- [`northstar_safety/services.py`](C:/Users/onkha/OneDrive/Documents/New%20project/northstar_safety/services.py)
- [`docs/northstar-public-launch-handoff.md`](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-public-launch-handoff.md)
- [`docs/northstar-phase-ten-memo.md`](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-phase-ten-memo.md)

## Next external step

Move the current Shopify app into Shopify Partners, then add the real hosted callback URL to the app configuration and re-run the install plus billing flow end to end.
