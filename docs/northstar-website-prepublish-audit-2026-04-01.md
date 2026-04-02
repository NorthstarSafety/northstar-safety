# Northstar Website Pre-Publish Audit

Date: 2026-04-01

## Current status

- The Squarespace site is still private.
- The contributor-view homepage is readable, but the public presentation still needs one more careful polish pass before publishing.
- The main visible trust risk is not the product itself. It is the Squarespace site structure and homepage presentation.

## What was verified live

- The custom domain still resolves to a private-site gate for logged-out visitors.
- The contributor-view homepage is available inside Squarespace.
- The homepage uses a large product screenshot section that is carrying too much of the message and makes the hero feel heavier than it should.
- The Squarespace page manager still shows `Product Draft` and `Pricing Draft` in Main Navigation, with normal `Product` and `Pricing` pages sitting in `Not Linked`.
- That page structure is the main risk behind the site still feeling partly like a repurposed storefront.

## Highest-impact issues to resolve before publish

1. Main navigation structure
   - The header should present a clean B2B order: `Product`, `Pricing`, `About`, `Contact`.
   - The storefront-backed draft pages should not be the long-term source for the public product and pricing experience.

2. Homepage hero readability
   - The current hero relies too heavily on a darkened product screenshot.
   - The section needs either a simpler layout or lighter treatment so the message reads faster.

3. Pricing clarity
   - The pricing story should be explicit and easy to scan:
     - `$300` one-time founding pilot
     - one store
     - first 10 priority SKUs
     - 30-day pilot
     - `$149/month` only after explicit pilot signoff

4. CTA consistency
   - The site should consistently push toward one next step:
     - `Book a Demo`
   - Payment links should stay off the public homepage as the primary CTA.

## Recommended copy source of truth

Use these files as the clean source copy for the public site:

- `docs/northstar-squarespace-site-kit.md`
- `docs/northstar-one-page.md`
- `docs/northstar-paid-pilot-offer.md`
- `docs/northstar-pricing-cutover-memo.md`
- `northstar_safety/templates/public_home.html`
- `northstar_safety/templates/public_pricing.html`

## Safe publish checklist

Before turning the site public:

1. Confirm Main Navigation reads:
   - Product
   - Pricing
   - About
   - Contact

2. Confirm homepage hero reads clearly without the screenshot overpowering the text.

3. Confirm pricing page states the founding pilot plainly and does not mix old pilot pricing.

4. Confirm footer/legal pages are linked:
   - Privacy Policy
   - Terms of Service
   - Support
   - Security

5. Confirm the site no longer routes visitors into storefront-style `Product` / `Pricing` behavior.

6. Confirm the site is switched from private to public only after the above are checked in a logged-out browser.

## Bottom line

Northstar's public site is close enough that the remaining work is mostly presentation and Squarespace page structure, not missing business substance. The product, offer, and trust materials are already stronger than the current public shell. The final pre-publish pass should focus on clean navigation, clearer hero presentation, and a tighter pricing story.
