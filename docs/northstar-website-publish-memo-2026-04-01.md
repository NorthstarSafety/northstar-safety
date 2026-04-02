## Northstar Website Publish Memo

Date: 2026-04-01

### What was fixed

- The Squarespace site availability was changed from `Private` to `Public`.
- The live root domain and `www` domain now load without the Squarespace private-site gate.
- The public header now presents the intended clean navigation:
  - `Product`
  - `Pricing`
  - `About`
  - `Contact`
- The live public `Product` and `Pricing` pages resolve to the clean marketing pages:
  - `https://www.northstarsafetyapp.com/product`
  - `https://www.northstarsafetyapp.com/pricing`
- The visible public experience no longer exposes the old `Product Draft` / `Pricing Draft` labels in the header.

### What was verified

- `https://northstarsafetyapp.com/` returns `200` and resolves to `https://www.northstarsafetyapp.com/`
- `https://www.northstarsafetyapp.com/` returns `200`
- `https://www.northstarsafetyapp.com/pricing` returns `200`
- `https://www.northstarsafetyapp.com/contact` returns `200`
- `https://www.northstarsafetyapp.com/product` returns `200`
- The site is publicly reachable from outside the Squarespace contributor view.
- The live browser view shows the clean header labels instead of the draft/storefront labels.

### Important note about Squarespace structure

- Inside Squarespace admin, the page manager still contains the older draft/storefront pages and the clean content pages separately.
- The current published experience is safe for prospects, but the admin structure is still partly legacy under the hood.
- If a future cleanup pass is done, it should be treated as a structural refactor, not a quick edit.

### Tiny polish items still left

- The homepage hero is still visually heavy because the screenshot treatment dominates the first fold.
- The `Product` and `Pricing` pages are now correct and presentable, but they are still fairly sparse.
- The homepage/browser title and some SEO-facing labels could still be tightened later from `northstarsafetyapp` to fully polished `Northstar Safety` metadata.

### Final status

Northstar's public site is now truly public, externally reachable, and safe to show prospects. The remaining work is polish, not a publish blocker.
