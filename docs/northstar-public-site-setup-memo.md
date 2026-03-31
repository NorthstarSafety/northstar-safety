# Northstar Public Site Setup Memo

Date: 2026-03-23

## What is done

- The purchased domain is **`northstarsafetyapp.com`**.
- The domain is connected to Squarespace.
- SSL is active on the Squarespace website connection.
- The root domain currently redirects to `https://www.northstarsafetyapp.com/`.
- Google Workspace MX records are live for the domain.
- The Google Workspace plan is active on **Business Starter**.
- The initial mailbox user **`support@northstarsafetyapp.com`** exists and is marked as an administrator in Squarespace.
- The main Squarespace site copy was updated on the core visible pages:
  - Home
  - Services
  - About
  - Contact
- The site footer identity was updated to Northstar Safety and now includes:
  - `support@northstarsafetyapp.com`
  - `hello@northstarsafetyapp.com`

## What is blocked

### Public launch blocker

Squarespace is still showing the site as **Private** and the public site is blocked behind:

- **`UPGRADE TO PUBLISH`**

This means the website is still on a trial/private configuration and will not become publicly visible until a paid Squarespace site plan is activated.

### Email activation blocker

Google Workspace still shows:

- **Accept Google Workspace Terms of Service**

That means the mailbox setup is not fully activated yet even though:

- billing is live
- MX records are live
- the `support` admin user exists

The likely final activation step is to sign in as the Google Workspace admin user for the domain and accept Google's terms.

## What was improved in the Squarespace site

### Home page

- headline updated to Northstar positioning
- product-safety workflow copy replaced the default business-services copy
- demo CTA copy improved

### Services page

- rewritten as the Northstar product/workflow page

### About page

- rewritten as the Northstar company/about page

### Contact page

- rewritten as the demo/contact page with the domain support address

### Footer

- replaced generic template footer language with Northstar branding and domain email addresses

## What still needs manual finishing inside Squarespace

- upgrade the Squarespace site plan so the website can be public
- rename the starter navigation page labels from the Squarespace defaults to the final Northstar sitemap labels
- add the remaining supporting pages if you want the full public site set before launch:
  - Who It's For
  - Pricing
  - Book a Demo
  - Privacy Policy
  - Terms of Service
  - Support
  - Security

## Future app subdomain

Do **not** point the app into Squarespace.

Use this structure:

- public site: `northstarsafetyapp.com`
- public site redirect: `www.northstarsafetyapp.com`
- product app later: `app.northstarsafetyapp.com`

When the Northstar app host is ready:

1. add `app.northstarsafetyapp.com` as a custom domain on the app host
2. create an `app` DNS record at the domain provider
3. point `app` to the production host target
4. test HTTPS and app login

## Exact next founder action

1. In Squarespace, click **`UPGRADE TO PUBLISH`**
2. In Squarespace Google Workspace settings, click **`ACCEPT TERMS`**
3. Complete the Google Workspace admin activation for `support@northstarsafetyapp.com`
4. Confirm the welcome/invitation email for the support admin user
5. Finish page-label cleanup in Squarespace Pages
6. Later, add `app.northstarsafetyapp.com` when the production app host is live
