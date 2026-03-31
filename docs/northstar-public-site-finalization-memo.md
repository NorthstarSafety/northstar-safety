## Northstar Public Site Finalization Memo

Date: 2026-03-23

### What is complete

- The public site is live on:
  - `https://northstarsafetyapp.com`
  - `https://www.northstarsafetyapp.com`
- The root domain resolves cleanly to the `www` site and both return `200`.
- Google Workspace is active for `northstarsafetyapp.com`.
- `support@northstarsafetyapp.com` is active as the Google Workspace admin mailbox.
- `hello@northstarsafetyapp.com` and `founder@northstarsafetyapp.com` were added as aliases on the support mailbox so inbound mail can route without paying for extra seats yet.
- The public site now has working public pages at:
  - `/`
  - `/about`
  - `/contact`
  - `/who-its-for`
  - `/book-a-demo`
  - `/privacy-policy`
  - `/terms-of-service`
  - `/support`
  - `/security`
- The placeholder business contact details in the visible footer and main trust/contact pages were replaced with Northstar domain email addresses.
- The app remains separate from the marketing site. No `app.` DNS cutover was done inside Squarespace.

### Public structure in use

- Marketing site:
  - `www.northstarsafetyapp.com`
- Root redirect:
  - `northstarsafetyapp.com`
- Future product app:
  - `app.northstarsafetyapp.com`

### Email status

- Active mailbox:
  - `support@northstarsafetyapp.com`
- Active aliases on that mailbox:
  - `hello@northstarsafetyapp.com`
  - `founder@northstarsafetyapp.com`

### What still needs polish

- The `Product` and `Pricing` navigation pages are still tied to Squarespace commerce-style collection pages rather than pure marketing content pages.
- The site still shows a commerce-oriented header state (`Cart`) because those collection pages exist in the current Squarespace structure.
- The site is now presentable to prospects, but if you want a fully corporate marketing finish, the next best improvement is to replace or restyle those commerce collection pages.

### Recommended next founder click

If you want the next highest-leverage cleanup step, do this next:

1. Replace the Squarespace commerce-style `Product` and `Pricing` pages with standard marketing content pages or hide the commerce chrome through site styling/custom code.
2. Leave `app.northstarsafetyapp.com` reserved until the real Northstar app host is ready.
3. If you want separate sending identities later, create paid Google Workspace users for `hello@...` and `founder@...`; for now they work as aliases on the support inbox.
