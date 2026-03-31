## Northstar Public Site SaaS Polish Memo

Date: 2026-03-23

### What changed

- The visible brand text now reads `Northstar Safety` instead of `northstarsafetyapp`.
- The live public navigation now presents:
  - `Product`
  - `Pricing`
  - `About`
  - `Contact`
- The public `Product` and `Pricing` URLs now resolve to clean standard content pages instead of the old Squarespace commerce-style pages:
  - `https://www.northstarsafetyapp.com/product`
  - `https://www.northstarsafetyapp.com/pricing`
- The old commerce-backed pages were preserved as draft/internal pages:
  - `/product-draft`
  - `/pricing-draft`
- A site-wide cleanup snippet was added through Squarespace Code Injection to:
  - rewrite the visible nav links from the old draft-store pages to the clean SaaS pages
  - hide the visible cart/storefront chrome
  - suppress the leftover storefront/service blocks that made the site feel like a template store
  - normalize the visible brand title to `Northstar Safety`
  - remove the newsletter opt-in checkbox from the public forms

### Live result

The live public site now behaves like a B2B software marketing site instead of a modified store template:

- no visible `Cart`
- no visible `Product Draft` or `Pricing Draft`
- no visible default product pricing tiles from the old Squarespace templates
- `Product` and `Pricing` now land on clean marketing content pages
- the public footer uses Northstar domain email addresses

### What still exists behind the scenes

- The original Squarespace commerce-style `Product` and `Pricing` pages still exist inside the Squarespace admin as draft/internal fallback pages.
- The final public cleanup is therefore partly structural and partly implemented via site-wide code injection.

### Small remaining polish items

- The homepage still uses a generic embedded contact-form layout section from the template; the visible copy is acceptable, but it could be turned into a more bespoke SaaS demo CTA later.
- If you want a fully native Squarespace structure with no code-injection remapping, the next step would be to rebuild the main nav around only standard content pages and retire the old draft collection pages entirely.
