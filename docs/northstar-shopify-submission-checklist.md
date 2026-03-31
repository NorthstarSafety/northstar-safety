# Northstar Shopify Submission Checklist

Date: 2026-03-23

## App object

- Create or link a Shopify CLI-managed app in the correct Partner organization
- Confirm the app is no longer shop-owned
- Confirm the app handle and client ID match the production app configuration

## Hosting

- Deploy Northstar on a permanent HTTPS domain
- Set `PUBLIC_BASE_URL` to that domain
- Confirm `/install`, `/auth/callback`, `/billing`, `/webhooks/shopify/compliance`, and `/webhooks/shopify/app-uninstalled` are reachable

## Shopify app configuration

- Set `application_url`
- Add allowed redirect URLs
- set scopes to the minimum required set
- register compliance webhooks
- register `app/uninstalled`

## Install flow

- Install from a Shopify-owned surface
- confirm Northstar receives the `shop` parameter and redirects immediately into OAuth
- Approve access scopes
- Return to Northstar successfully
- Verify the workspace lands in a live connected state

## Billing

- Run the recurring subscription flow from `/billing`
- Approve the plan in Shopify
- Confirm the app installation shows an active subscription

If billing is still blocked externally:

- use direct invoicing for private pilots
- keep the pricing page and founder docs aligned with that interim path

## Uninstall / reinstall

- Uninstall the app from Shopify
- Confirm Northstar records the uninstall webhook
- Reinstall the app
- Confirm the shop returns to an active install state

## Reviewer package

- final app listing copy
- screenshots
- support contact
- privacy policy
- terms of service
- reviewer test instructions

## Embedded experience

- decide whether the review build will be embedded in Shopify admin
- if yes, add the required App Bridge integration and verify the app works correctly inside admin
- if no, confirm whether the current external workspace model is acceptable for the intended distribution path before submission

## Final founder button

After the app is moved into Shopify Partners and the permanent host is live, the next button is:

- open the permanent `/install` page
- install on the target store
- then open `/billing` and complete the subscription approval
