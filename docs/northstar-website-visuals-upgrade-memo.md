# Northstar Safety Website Visual Upgrade Memo

Date: March 23, 2026

## What changed

I replaced the visible generic Squarespace stock imagery on the main public pages with real Northstar product visuals pulled from the live Northstar workspace.

Updated pages:

- Home
- Product
- Pricing
- About

## Screens used

### Home

- Hero image: Northstar dashboard
  - Source: `C:\Users\onkha\OneDrive\Documents\New project\output\playwright\site-assets\northstar-dashboard-hero.png`
  - Why: It shows the product as a control tower immediately: coverage, missing evidence, open cases, and critical alerts.

- Secondary image: Northstar evidence queue
  - Source: `C:\Users\onkha\OneDrive\Documents\New project\output\playwright\site-assets\northstar-evidence-queue.png`
  - Why: It makes the monthly work concrete by showing missing and aging proof at SKU level.

### Product

- Main image: Northstar alert review
  - Source: `C:\Users\onkha\OneDrive\Documents\New project\output\playwright\site-assets\northstar-alert-review.png`
  - Why: It shows one of the clearest software-native workflows in the product: reviewing an official notice against the live catalog and recording false-positive handling.

### Pricing

- Main image: Northstar catalog coverage
  - Source: `C:\Users\onkha\OneDrive\Documents\New project\output\playwright\site-assets\northstar-products-catalog.png`
  - Why: It supports the pilot offer with a practical view of synced Shopify products, evidence health, and case counts.

### About

- Main image: Northstar case detail
  - Source: `C:\Users\onkha\OneDrive\Documents\New project\output\playwright\site-assets\northstar-case-trail.png`
  - Why: It reinforces Northstar's position as an operational system of record, not just a monitoring feed.

## Verification

Verified live on:

- `https://www.northstarsafetyapp.com/`
- `https://www.northstarsafetyapp.com/product`
- `https://www.northstarsafetyapp.com/pricing`
- `https://www.northstarsafetyapp.com/about`

Checks completed:

- visible placeholder stock imagery removed from the main sections on those pages
- product-led screenshots render on the live public site
- updated alt text is present on the new visible screenshots
- screenshots remain readable on desktop
- quick mobile check passed for Home and Product

## Remaining small polish items

- The home hero still uses a full product screenshot with overlay copy, so a tighter custom crop could improve mobile impact later.
- Some older Squarespace image assets still exist in the page internals, but they are not part of the visible public experience.

## Outcome

The live site now reads much more like a real B2B software company site and less like a template site using decorative stock art. The public-facing pages now explain Northstar visually through the actual product.
