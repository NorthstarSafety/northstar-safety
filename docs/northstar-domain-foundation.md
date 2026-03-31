# Northstar Safety Domain Foundation

Date: 2026-03-23

## Recommended primary domain

**Primary choice:** `northstarsafety.co`

Why this wins:

- exact-match brand available right now
- short
- easy to read and say out loud
- credible for a B2B software company
- clean enough for the root site, business email, and `app.` product subdomain

## Important note about the `.com`

`northstarsafety.com` is already registered and appears to belong to an existing NorthStar Safety business. That makes it a poor choice to build around.

## Backup domain options

Ranked backups:

1. `northstarsafety.io`
2. `northstarsafetyhq.com`
3. `northstarsafetyapp.com`
4. `northstarsafety.ai`

Why these backups:

- `.io` keeps the exact brand and still feels credible for SaaS
- `hq.com` is the cleanest business-grade `.com` variation
- `app.com` is understandable, but less elegant
- `.ai` is available, but less aligned than `.io` for this product

## Purchase status

Not purchased yet.

Reason:

- no Squarespace, registrar, or payment credentials were available in this workspace
- no usable browser-based registrar access was available to complete checkout safely

## Recommended domain structure

Use:

- root marketing site: `northstarsafety.co`
- marketing `www`: `www.northstarsafety.co`
- product app: `app.northstarsafety.co`

Recommended business emails:

- `support@northstarsafety.co`
- `hello@northstarsafety.co`
- `founder@northstarsafety.co`

## Best registrar path

Fastest path for this project:

- buy the domain through **Squarespace Domains** if the main priority is a fast Squarespace site and Google Workspace setup

Good alternative:

- buy through **Namecheap** if you want registrar separation and easy DNS control

## Squarespace setup path

### If you buy the domain through Squarespace

1. Buy `northstarsafety.co`
2. Attach it to the Squarespace marketing site
3. Set `northstarsafety.co` as the primary domain
4. Redirect `www.northstarsafety.co` to the root domain

This is the cleanest route if the site will live entirely on Squarespace.

### If you buy the domain through a third-party registrar

When connecting the root domain to Squarespace, use the records Squarespace currently requires:

- verification CNAME from the Squarespace Domains panel to `verify.squarespace.com`
- `www` CNAME to `ext-cust.squarespace.com`
- root A records:
  - `198.185.159.144`
  - `198.185.159.145`
  - `198.49.23.144`
  - `198.49.23.145`

After adding those records:

- wait up to 24 to 48 hours
- refresh the domain in Squarespace until it shows connected

## Business email setup

Recommended provider:

- **Google Workspace**

### If the domain is managed through Squarespace with default Squarespace nameservers

Squarespace says Google Workspace MX records are added automatically when you sign up through Squarespace.

Use this path:

1. In Squarespace, open the domain
2. Open the Google Workspace or Email panel
3. Start a Google Workspace plan
4. Create:
   - `hello@northstarsafety.co`
   - `support@northstarsafety.co`
   - `founder@northstarsafety.co`

### If the domain is registered elsewhere

Use Google Workspace directly or through Squarespace, then add the required MX records in the registrar DNS panel.

Recommended order:

1. create Google Workspace
2. verify the domain
3. add Google MX records
4. create the three mailbox users

## `app.` subdomain setup

Do **not** point `app.` to Squarespace.

Reserve `app.northstarsafety.co` for the real Northstar product.

When the app host is ready:

1. add `app.northstarsafety.co` as a custom domain on the app host
2. if using Render, add `app.northstarsafety.co` to the web service
3. create a DNS record at the domain provider:
   - `app` as a `CNAME`
   - value: the Render service's `onrender.com` hostname
4. verify the domain in Render
5. test HTTPS and the app login flow

## Clean launch structure

Use this exact structure:

- `northstarsafety.co` -> Squarespace marketing site
- `www.northstarsafety.co` -> redirect to root
- `app.northstarsafety.co` -> live Northstar product
- business email on `@northstarsafety.co`

## Exact next steps for the founder

1. Buy `northstarsafety.co`
2. If available and budget allows, also buy `northstarsafety.io` defensively
3. Connect the root domain to Squarespace
4. Set up Google Workspace email
5. Create the three email addresses
6. Leave `app.` unused until the production host is ready
7. Later, point `app.` to the production app host

## Suggested immediate purchase checklist

- domain: `northstarsafety.co`
- registrar: Squarespace Domains
- primary site URL: `https://northstarsafety.co`
- app URL reserved: `https://app.northstarsafety.co`
- email users:
  - `hello`
  - `support`
  - `founder`
